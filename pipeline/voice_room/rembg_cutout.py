#!/usr/bin/env python3
"""纸片人 MV · 通用立绘抠图去背 → 透明底 PNG（rembg）.

这是**通用工具**：传 <in> [out] [--model] 即可对任意立绘去背复用。
模型默认 isnet-anime（动漫立绘专用，边缘/发丝最准），失败回退 u2net。
无参数时回退语音厅 4 张原图（向后兼容旧调用）。

用法：
    python3 rembg_cutout.py in.png                 # 输出 in_cutout.png（同目录）
    python3 rembg_cutout.py in.png out.png          # 指定输出
    python3 rembg_cutout.py in.png out.png --model u2net
    python3 rembg_cutout.py                         # 无参：语音厅 4 张（兼容）
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rembg import new_session, remove

ROOT = Path(__file__).resolve().parents[2]
_LEGACY_SRC = ROOT / "publish" / "语音厅"
_LEGACY_OUT = _LEGACY_SRC / "script_v2_assets"
_LEGACY_NAMES = ["cy", "诺兰", "轩珩", "中里毅2"]


def _make_session(model: str):
    try:
        return new_session(model), model
    except Exception as e:  # noqa: BLE001
        print(f"[warn] {model} 不可用 ({e})，回退 u2net")
        return new_session("u2net"), "u2net"


def cutout(session, src: Path, dst: Path) -> bool:
    if not src.exists():
        print(f"[skip] 缺失: {src}")
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    out = remove(
        src.read_bytes(),
        session=session,
        alpha_matting=True,
        alpha_matting_foreground_threshold=270,
        alpha_matting_background_threshold=20,
        alpha_matting_erode_size=11,
    )
    dst.write_bytes(out)
    print(f"[ok] {dst.name} ({len(out) // 1024} KB)")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="rembg 立绘抠图去背")
    ap.add_argument("src", nargs="?", type=Path, help="输入 png（缺省=语音厅 4 张）")
    ap.add_argument("dst", nargs="?", type=Path, help="输出 png（缺省=<src>_cutout.png）")
    ap.add_argument("--model", default="isnet-anime", help="rembg 模型（默认 isnet-anime）")
    args = ap.parse_args()

    session, model = _make_session(args.model)
    print(f"[info] 使用模型: {model}")

    if args.src is None:                     # 向后兼容：语音厅 4 张
        ok = sum(cutout(session, _LEGACY_SRC / f"{n}.png",
                        _LEGACY_OUT / f"{n}_cutout.png") for n in _LEGACY_NAMES)
        print(f"[done] {ok}/{len(_LEGACY_NAMES)} 抠图完成 → {_LEGACY_OUT}")
        return 0 if ok == len(_LEGACY_NAMES) else 1

    dst = args.dst or args.src.with_name(f"{args.src.stem}_cutout.png")
    return 0 if cutout(session, args.src, dst) else 1


if __name__ == "__main__":
    sys.exit(main())
