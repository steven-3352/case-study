"""Phase 1b 断言工具 —— items_yaml(t,k) == items_py(t,k) 逐元素相等。

对 219 个真实帧的 t 值逐个比对，frozen dataclass 比较是字段级的，
能抓住 center/crop/grey/scan_split 任何一个字段的差异。

用法:
    python3 -m mv_engine.tools.assert_items [--version a|b]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "pipeline" / "voice_room"))
sys.path.insert(0, str(ROOT / "pipeline"))

import paperdoll_engine as pe                         # noqa: E402
import mv_engine.session as _sess                    # noqa: E402
import mingyue_render as mr                          # noqa: E402
from mingyue.loader import load                      # noqa: E402

# 初始化路径 —— 断言工具不走 _init_worker，需要手动设
pe._PATHS = pe.PVPaths(assets_dir=mr.ASSETS, wav=mr.WAV, out_dir=mr.OUT, slug="mingyue")
_sess.configure(mr.ASSETS, mr.TEX, mr.GEN)


def run(version: str) -> list[str]:
    shots_py   = mr.A_SHOTS   if version == "a" else mr.B_SHOTS
    yaml_path  = (ROOT / "pipeline" / "voice_room" / "mingyue" /
                  f"shots_{version}.yaml")
    shots_yaml = load(yaml_path)

    if len(shots_py) != len(shots_yaml):
        return [f"shot 数量不符: py={len(shots_py)} yaml={len(shots_yaml)}"]

    n = round((mr.SEG_T1 - mr.SEG_T0) * mr.FPS)
    bad: list[str] = []

    for i in range(n):
        t = mr.SEG_T0 + i / mr.FPS
        sh_py   = mr.active(shots_py,   t)
        sh_yaml = mr.active(shots_yaml, t)

        if sh_py.sid != sh_yaml.sid:
            bad.append(f"f{i:05d} sid: py={sh_py.sid} yaml={sh_yaml.sid}")
            continue

        k_py   = sh_py.k(t)
        k_yaml = sh_yaml.k(t)

        its_py   = sh_py.items(t, k_py)
        its_yaml = sh_yaml.items(t, k_yaml)

        if len(its_py) != len(its_yaml):
            bad.append(f"f{i:05d} {sh_py.sid}: len py={len(its_py)} yaml={len(its_yaml)}")
            continue

        for j, (ip, iy) in enumerate(zip(its_py, its_yaml)):
            if ip != iy:
                bad.append(f"f{i:05d} {sh_py.sid} item[{j}]: py={ip!r} yaml={iy!r}")
                if len(bad) >= 20:
                    bad.append("(太多差异,截断)")
                    return bad

    return bad


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase 1b items 断言")
    ap.add_argument("--version", nargs="*", default=["a", "b"])
    args = ap.parse_args()

    ok = True
    for v in args.version:
        bad = run(v)
        if bad:
            print(f"\n✗ version={v} · {len(bad)} 处差异:")
            for b in bad:
                print(f"  {b}")
            ok = False
        else:
            print(f"✓ version={v} · 219 帧 × items 逐元素相等")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
