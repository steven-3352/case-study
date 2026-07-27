"""solve_shots CLI —— 输入镜头边界+素材+可选 pin,输出 solved shots + 报告。

用法:
    python3 -m mv_engine.tools.solve_shots \
        --in pipeline/voice_room/mingyue/shots_a.yaml \
        --out /tmp/shots_a.solved.yaml

**输入 YAML 里的 pin 规则**:
- `cam.size0` / `cam.size1` / `cam.ease` 若已声明,求解器不改
- 顶层 `pin: {move: push_slow, trans: cut}` 强制某镜用指定模板
- 其它字段(bg/fx/note/layout/subject/t)原样透传

输出的 shots.solved.yaml 会保留原字段,把 solver 选出的 (family, move, trans)
写进新的 `cam` + 追加 `solver_note` 说明。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "pipeline"))
sys.path.insert(0, str(ROOT / "pipeline" / "voice_room"))

from mv_engine.solver import solve   # noqa: E402
from mv_engine.solver.templates import MOVE_TEMPLATES  # noqa: E402


def _shot_to_meta(s: dict) -> dict:
    """把 YAML shot 转成 solver 输入的 meta dict。"""
    cam  = s.get("cam", {})
    pin  = s.get("pin", {})
    return {
        "sid":     s["sid"],
        "t":       s["t"],
        "family":  pin.get("family"),
        "move":    pin.get("move"),
        "size0":   cam.get("size0"),
        "size1":   cam.get("size1"),
        "trans":   pin.get("trans"),
        # 原字段透传,用于最终 emit
        "_orig":   s,
    }


def _emit_shot(solved: dict, orig: dict) -> dict:
    """把 solver 结果合并回原 shot 结构。solver 选的 cam_kwargs 覆盖原 cam。"""
    out = dict(orig)
    new_cam = dict(orig.get("cam", {}))
    new_cam.update(solved["cam_kwargs"])
    out["cam"] = new_cam
    out["solver_note"] = (
        f"move={solved['move']} family={solved['family']} "
        f"trans={solved.get('trans', 'cut')} "
        f"size={solved['size0']}→{solved['size1']}"
    )
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="分镜求解器 CLI")
    ap.add_argument("--in", dest="src", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--width", type=int, default=16, help="beam 宽度")
    ap.add_argument("--report", type=Path, help="可选:solver_report.md 路径")
    ap.add_argument("--verify-gate", action="store_true",
                    help="求解后用 Phase 0 预测器渲 track,过 gate_check_motion")
    args = ap.parse_args()

    src = yaml.safe_load(args.src.read_text(encoding="utf-8"))
    metas = [_shot_to_meta(s) for s in src["shots"]]

    solved, report = solve(metas, width=args.width)
    if not solved:
        print(f"✗ solver 未找到合法解: {report.get('error')}")
        return 1

    out = {"shots": [_emit_shot(sv, m["_orig"]) for sv, m in zip(solved, metas)]}
    args.out.write_text(yaml.safe_dump(out, allow_unicode=True, sort_keys=False),
                        encoding="utf-8")
    print(f"→ {args.out}")
    print(f"  score = {report['score']:.3f}")
    for k, v in report["parts"].items():
        print(f"    {k:<18} {v:+.3f}")

    if args.verify_gate:
        import json                                             # noqa: PLC0415
        import paperdoll_engine as pe                           # noqa: PLC0415
        import mingyue_render as mr                             # noqa: PLC0415
        import mv_engine.session as _sess                       # noqa: PLC0415
        from mv_engine.track import Session as TrSession, predict_track  # noqa: PLC0415
        from mingyue.loader import load as load_shots           # noqa: PLC0415
        from gate_check_motion import check_track               # noqa: PLC0415

        pe._PATHS = pe.PVPaths(assets_dir=mr.ASSETS, wav=mr.WAV, out_dir=mr.OUT, slug="mingyue")
        _sess.configure(mr.ASSETS, mr.TEX, mr.GEN)

        shots = load_shots(args.out)
        tr_sess = TrSession(mr)
        track = predict_track(shots, mr.SEG_T0, mr.SEG_T1, mr.FPS, tr_sess)
        motion_path = args.out.with_suffix(".motion.json")
        motion_path.write_text(json.dumps(track, ensure_ascii=False), encoding="utf-8")

        ok, report = check_track(motion_path)
        print(f"\ngate_check_motion:")
        print(f"  {'✓' if ok else '✗'} {report.strip().splitlines()[0]}")
        if not ok:
            for ln in report.strip().splitlines()[1:]:
                print(f"    {ln}")

    if args.report:
        lines = [f"# solver_report · {args.src.name}", "",
                 f"- score: **{report['score']:.3f}**"]
        for k, v in report["parts"].items():
            lines.append(f"  - {k}: `{v:+.3f}`")
        lines.append("")
        lines.append("| sid | move | family | size | trans |")
        lines.append("|-----|------|--------|------|-------|")
        for sh in solved:
            lines.append(f"| {sh['sid']} | {sh['move']} | {sh['family']} | "
                         f"{sh['size0']}→{sh['size1']} | {sh.get('trans', 'cut')} |")
        args.report.write_text("\n".join(lines), encoding="utf-8")
        print(f"→ {args.report}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
