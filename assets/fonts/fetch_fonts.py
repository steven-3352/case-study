#!/usr/bin/env python3
"""下载纸片人 MV 海报排版所需的可商用字体。

字体二进制不入库（见 .gitignore），换机器/新克隆后跑一次本脚本即可。
只收录 SIL OFL 1.1 授权字体——可自由商用、可嵌入、可修改，无需额外报备。
厂商声明类字体（阿里巴巴普惠体 / OPPO Sans / HarmonyOS Sans）授权条款各异且
禁止再分发，本脚本不代下，需要时请自行从官网获取后放入本目录。

    python3 assets/fonts/fetch_fonts.py
"""
from __future__ import annotations

import io
import sys
import urllib.request
import zipfile
from pathlib import Path

FONT_DIR = Path(__file__).resolve().parent

# name -> (url, 是否 zip, zip 内需要提取的后缀)
SOURCES: dict[str, tuple[str, bool]] = {
    "SmileySans-Oblique.ttf": (
        "https://github.com/atelier-anchor/smiley-sans/releases/download/v2.0.1/smiley-sans-v2.0.1.zip",
        True,
    ),
    "LXGWWenKai-Regular.ttf": (
        "https://github.com/lxgw/LxgwWenKai/releases/download/v1.522/LXGWWenKai-Regular.ttf",
        False,
    ),
    "LXGWWenKai-Medium.ttf": (
        "https://github.com/lxgw/LxgwWenKai/releases/download/v1.522/LXGWWenKai-Medium.ttf",
        False,
    ),
}


def fetch(name: str, url: str, is_zip: bool) -> None:
    target = FONT_DIR / name
    if target.exists():
        print(f"  skip  {name}（已存在）")
        return
    print(f"  fetch {name} …")
    with urllib.request.urlopen(url, timeout=300) as resp:
        payload = resp.read()
    if is_zip:
        with zipfile.ZipFile(io.BytesIO(payload)) as zf:
            for member in zf.namelist():
                if member.endswith((".ttf", ".otf")) and "/" not in member:
                    (FONT_DIR / member).write_bytes(zf.read(member))
    else:
        target.write_bytes(payload)


def main() -> int:
    print(f"字体目录：{FONT_DIR}")
    for name, (url, is_zip) in SOURCES.items():
        try:
            fetch(name, url, is_zip)
        except Exception as exc:
            print(f"  FAIL  {name}: {exc}", file=sys.stderr)
            return 1
    print("完成。系统字体（思源黑体 / Songti）不由本脚本管理，见 pipeline/paperdoll/fonts.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
