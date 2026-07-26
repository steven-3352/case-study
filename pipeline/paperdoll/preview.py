#!/usr/bin/env python3
"""可视校验入口 · 把风格包 × 版式 × 真立绘渲成成片,人肉读图.

不是测试(测试断言数值),是**给眼睛看的**——背景读不读得出「城市/舞台/影棚」、
大字是不是压在人后、多人图谁是谁一眼分不分得清,这些只有渲出来看才知道。
「跑通不报错」不等于「好看」,见项目铁律「门禁是地板不是目标」。

    python -m pipeline.paperdoll.preview single   # 单人 6 套 × 各自风格包
    python -m pipeline.paperdoll.preview multi    # 多人 3 套
    python -m pipeline.paperdoll.preview all
"""
from __future__ import annotations

import pathlib
import sys

from PIL import Image

from . import backgrounds, poster, style_packs

CANVAS = (1080, 1920)
DOLLS_DIR = pathlib.Path("publish/语音厅")
OUT = pathlib.Path("tmp/paperdoll_poster")

# 单人:版式 → 风格包,一套版式配一个能凸显它的包
SINGLE_CASES: dict[str, str] = {
    "single-vertical-name": "ink-scroll",
    "single-stacked-hero": "urban-night",
    "single-side-column": "studio-seamless",
    "single-baseline-strip": "dark-stage",
    "single-poster-grid": "flat-graphic",
    "single-zen-void": "zen-void",
}

SINGLE_CONTENT: dict[str, dict[str, str]] = {
    "single-vertical-name": dict(
        hero="诺兰", hero_sub="NOLAN", label="声之羁绊 · премьера",
        lyric="月光落在\n你没说完的那句话上", meta="2026 · 语音厅限定",
        micro="NO.007 / 22:47"),
    "single-stacked-hero": dict(
        hero="诺兰", hero_sub="THE NIGHT IS OURS", label="URBAN NIGHT",
        lyric="霓虹把整座城\n烧成你的名字", meta="EP.03 · 都市线",
        micro="01:24:07"),
    "single-side-column": dict(
        hero="诺兰\n特辑", hero_sub="STUDIO CUT", label="OFFICIAL",
        lyric="纯色影棚里\n只有你和光", meta="2026 春季物料", micro="STU-07"),
    "single-baseline-strip": dict(
        hero="明月天涯", hero_sub="UNDER THE SAME MOON", label="PERFORMANCE",
        lyric="灯灭之后 你还在", meta="主打歌 · 现场版", micro="LIVE 07"),
    "single-poster-grid": dict(
        hero="诺兰", hero_sub="POSTER SERIES", label="VOL.07",
        lyric="把日子过成\n一张海报", meta="平面特辑", micro="GRID-2026",
        seal="兰"),
    "single-zen-void": dict(
        hero="留白", lyric="说不出口的\n都留给月亮", seal="兰"),
}

# 多人:版式 → (风格包, 立绘名列表, 内容)
MULTI_CASES: dict[str, tuple[str, list[str], dict[str, str]]] = {
    "duo-split": (
        "luxe-interior", ["诺兰", "轩珩"],
        dict(hero="双生", hero_sub="TWIN FLAME", name_l="诺兰", name_r="轩珩",
             label="CP 限定", lyric="两条线终于交汇", micro="DUO-07")),
    "group-grid": (
        "studio-seamless", ["诺兰", "轩珩", "中里毅2"],
        dict(hero="MOONLIGHT", hero_sub="FIRST ALBUM",
             label="DEBUT", member_row="诺兰    轩珩    中里毅",
             index_row="01        02        03", meta="2026", micro="GRP-01")),
    "group-stack": (
        "dark-stage", ["诺兰", "轩珩", "中里毅2"],
        dict(hero="ENCORE", hero_sub="THE FINAL STAGE",
             label="PERFORMANCE", member_row="诺兰 · 轩珩 · 中里毅",
             lyric="最后一首 一起唱完", meta="2026 巡演", micro="LIVE-END")),
}


def _load(name: str) -> Image.Image:
    return Image.open(DOLLS_DIR / f"{name}.png").convert("RGBA")


def _render_one(layout_name: str, pack_name: str, doll_names: list[str],
                content: dict[str, str]) -> Image.Image:
    lay = poster.get(layout_name)
    pack = style_packs.get(pack_name)
    seed = abs(hash(layout_name)) % 9999
    bg = backgrounds.render(CANVAS, pack, seed=seed)
    dolls = [_load(n) for n in doll_names]
    ok, msg = poster.check_thickness(lay, content)
    print(f"  {layout_name:24} × {pack_name:16} 厚度门: {'✓' if ok else '✗'} {msg}")
    return poster.render_poster(bg, dolls, lay, content, pack)


def _sheet(imgs: list[Image.Image], cols: int, pad: int = 24) -> Image.Image:
    tw = max(i.width for i in imgs)
    th = max(i.height for i in imgs)
    scale = 520 / tw
    tw, th = round(tw * scale), round(th * scale)
    rows = (len(imgs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw + (cols + 1) * pad,
                              rows * th + (rows + 1) * pad), (30, 30, 32))
    for idx, im in enumerate(imgs):
        r, c = divmod(idx, cols)
        thumb = im.convert("RGB").resize((tw, th), Image.LANCZOS)
        sheet.paste(thumb, (pad + c * (tw + pad), pad + r * (th + pad)))
    return sheet


def run(mode: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    imgs: list[Image.Image] = []
    if mode in ("single", "all"):
        print("单人:")
        for lay_name, pack_name in SINGLE_CASES.items():
            im = _render_one(lay_name, pack_name, ["诺兰"], SINGLE_CONTENT[lay_name])
            im.convert("RGB").save(OUT / f"{lay_name}__{pack_name}.png")
            imgs.append(im)
        _sheet(imgs, 3).save(OUT / "_single_hi.png")
        print(f"  → {OUT / '_single_hi.png'}")
    if mode in ("multi", "all"):
        print("多人:")
        multi_imgs: list[Image.Image] = []
        for lay_name, (pack_name, dolls, content) in MULTI_CASES.items():
            im = _render_one(lay_name, pack_name, dolls, content)
            im.convert("RGB").save(OUT / f"{lay_name}__{pack_name}.png")
            multi_imgs.append(im)
        _sheet(multi_imgs, 3).save(OUT / "_multi_hi.png")
        print(f"  → {OUT / '_multi_hi.png'}")


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "all")
