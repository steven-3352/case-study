"""验预测器 —— 拿真渲出来的 motion.json 当 ground truth。

两条线,数值那条不是最重要的:

1. 逐帧 bbox 偏差:p95 < 画宽 0.2%,max < 1%
2. **`gate_check_motion` 在预测轨迹与真实轨迹上判定完全一致、冻结窗列表完全一致**

第 2 条才是真要求。预测器存在的意义是替代那个门,数值差多少是手段,
门判得一样才是目的 —— 数值再漂亮但把某个冻结窗漏了,这个预测器就是坏的。
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "pipeline" / "voice_room"))
sys.path.insert(0, str(ROOT / "pipeline" / "mv_engine"))

import mingyue_render as mr  # noqa: E402
import paperdoll_engine as pe  # noqa: E402
import track as T  # noqa: E402


def _load_gate():
    spec = importlib.util.spec_from_file_location(
        "gate_check_motion", ROOT / "pipeline" / "gate_check_motion.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def gate_report(gate, data: dict, tmp: Path) -> tuple[bool, str]:
    """跑真门。`check_track` 只吃路径,所以先落盘。

    比对**整份 report** 而不只是 ok 位 —— report 里带着冻结窗区间、最死窗口、
    硬切数。整份一致才等于「判定一致 + 冻结窗列表一致」,只比 ok 位会放过
    「同样 FAIL 但冻在别的地方」这种预测器失真。
    """
    tmp.write_text(json.dumps(data, ensure_ascii=False))
    return gate.check_track(tmp)


def compare(real: dict, pred: dict, w: int) -> dict:
    rt = {round(r["t"], 3): r for r in real["track"]}
    pt = {round(r["t"], 3): r for r in pred["track"]}
    shared = sorted(set(rt) & set(pt))
    if not shared:
        return {"n": 0}
    d = np.asarray([[abs(a - b) for a, b in zip(rt[t]["bbox"], pt[t]["bbox"])]
                    for t in shared], dtype=float)
    # 中心偏差取欧氏距离,尺寸偏差取各自绝对值
    center = np.hypot(d[:, 0], d[:, 1])
    return {
        "n": len(shared),
        "only_real": sorted(set(rt) - set(pt))[:5],
        "only_pred": sorted(set(pt) - set(rt))[:5],
        "center_p95": float(np.percentile(center, 95)),
        "center_max": float(center.max()),
        "w_p95": float(np.percentile(d[:, 2], 95)),
        "h_p95": float(np.percentile(d[:, 3], 95)),
        "w_max": float(d[:, 2].max()),
        "h_max": float(d[:, 3].max()),
        "frame_w": w,
        "worst_t": shared[int(center.argmax())],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="验 track.py 预测器")
    # 默认指向现渲基线,不指 publish/ —— 那边的 motion.json 是旧代码的产物,
    # 拿它当 ground truth 会去验一个已经不存在的行为。
    ap.add_argument("--truth-root", type=Path,
                    default=ROOT / ".cache" / "mv_engine" / "baseline")
    ap.add_argument("--version", nargs="*", default=["a", "b"])
    ap.add_argument("--p95-frac", type=float, default=0.002)
    ap.add_argument("--max-frac", type=float, default=0.01)
    ap.add_argument("--dump", type=Path, help="把预测轨迹写到此目录")
    args = ap.parse_args()

    pe._PATHS = pe.PVPaths(assets_dir=mr.ASSETS, wav=mr.WAV, out_dir=mr.OUT, slug="mingyue")
    gate = _load_gate()
    session = T.Session(mr)
    bad = 0

    for v in args.version:
        real = json.loads((args.truth_root / v / "motion.json").read_text())
        shots = mr.A_SHOTS if v == "a" else mr.B_SHOTS
        pred = T.predict_track(shots, mr.SEG_T0, mr.SEG_T1, mr.FPS, session)
        if args.dump:
            args.dump.mkdir(parents=True, exist_ok=True)
            (args.dump / f"{v}_pred.json").write_text(json.dumps(pred, ensure_ascii=False))

        st = compare(real, pred, mr.W)
        if st["n"] == 0:
            print(f"[{v}] ✗ 没有可比帧")
            bad += 1
            continue

        p95_lim = args.p95_frac * mr.W
        max_lim = args.max_frac * mr.W
        ok_num = st["center_p95"] < p95_lim and st["center_max"] < max_lim
        print(f"[{v}] {st['n']} 帧  中心 p95={st['center_p95']:.2f}px "
              f"({st['center_p95'] / mr.W * 100:.3f}%W, 限 {p95_lim:.1f}) "
              f"max={st['center_max']:.2f}px "
              f"({st['center_max'] / mr.W * 100:.3f}%W, 限 {max_lim:.1f}) @t={st['worst_t']}")
        print(f"     尺寸 w_p95={st['w_p95']:.2f} h_p95={st['h_p95']:.2f} "
              f"w_max={st['w_max']:.2f} h_max={st['h_max']:.2f}")
        if st["only_real"] or st["only_pred"]:
            print(f"     ⚠ 帧集合不齐 只在真={st['only_real']} 只在预测={st['only_pred']}")

        wd = Path(args.dump) if args.dump else Path("/tmp")
        wd.mkdir(parents=True, exist_ok=True)
        ok_r, rep_r = gate_report(gate, real, wd / f"{v}_real_gate.json")
        ok_p, rep_p = gate_report(gate, pred, wd / f"{v}_pred_gate.json")
        ok_gate = (ok_r, rep_r) == (ok_p, rep_p)
        print(f"     门: 真={'OK' if ok_r else 'FAIL'} 预测={'OK' if ok_p else 'FAIL'} · "
              f"report {'逐字一致 ✓' if ok_gate else '不一致 ✗'}")
        if not ok_gate:
            print("       --- 真 ---")
            for ln in rep_r.splitlines():
                print("       " + ln)
            print("       --- 预测 ---")
            for ln in rep_p.splitlines():
                print("       " + ln)

        if not (ok_num and ok_gate):
            bad += 1

    print("\n" + ("✓ 预测器可用" if bad == 0 else f"✗ {bad} 个版本未达标"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
