#!/usr/bin/env python3
"""W27X06 小红书 8 张轮播 · 报价草稿 + 演示工具."""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "publish" / "2026-W27" / "D06-xhs-自动报价草稿" / "xhs"
W, H = 1080, 1620
PAPER = (252, 248, 240)
INK = (28, 28, 28)
RED = (200, 48, 48)
GRAY = (120, 120, 120)
LINE = (210, 205, 195)
GREEN = (38, 154, 90)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    p = "/System/Library/Fonts/PingFang.ttc"
    try:
        return ImageFont.truetype(p, size, index=1 if bold else 0)
    except Exception:
        return ImageFont.load_default()


def wrap(text: str, fnt: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    lines, cur = [], ""
    for ch in text:
        test = cur + ch
        if fnt.getbbox(test)[2] <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines


def draw_page(num: int) -> Image.Image:
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 8], fill=RED)

    if num == 1:
        d.text((80, 120), "报价单改到崩溃", fill=INK, font=font(88, True))
        d.text((80, 240), "我做了个自动报价草稿", fill=RED, font=font(64, True))
        d.text((80, 400), "示意 · 非真实客户", fill=GRAY, font=font(28))
        d.text((80, 1350), "收藏这张 · 字段表在 P6", fill=GRAY, font=font(32))
    elif num == 2:
        d.text((80, 100), "痛点", fill=RED, font=font(40, True))
        lines = wrap("客户一句「按上次再改」= Excel 又要开第八版。改一行，总价对不上。", font(48, True), 920)
        y = 200
        for ln in lines:
            d.text((80, y), ln, fill=INK, font=font(48, True))
            y += 70
    elif num == 3:
        d.text((80, 100), "以前", fill=GRAY, font=font(36))
        d.text((80, 160), "手工 Excel · 版本 v3 v8 满天飞", fill=INK, font=font(52, True))
        d.text((80, 320), "现在", fill=GREEN, font=font(36))
        d.text((80, 380), "改两行明细 → 点一下出草稿", fill=INK, font=font(52, True))
    elif num == 4:
        d.text((80, 80), "演示小工具 · 输入", fill=INK, font=font(40, True))
        d.rectangle([60, 160, W - 60, 900], outline=LINE, width=3)
        d.text((90, 200), "客户：张姐 · 母婴店", fill=INK, font=font(36))
        d.text((90, 280), "项目：活动拍摄包", fill=INK, font=font(36))
        d.text((90, 360), "明细：探店视频 2 条 · 800", fill=INK, font=font(32))
        d.text((90, 440), "[ 生成草稿 ]", fill=INK, font=font(36))
        d.rectangle([90, 430, 320, 490], outline=INK, width=2)
        d.text((80, 950), "pipeline/demo_tools/quote_draft", fill=GRAY, font=font(26))
    elif num == 5:
        d.text((80, 80), "一键生成 · 预览", fill=INK, font=font(40, True))
        d.rectangle([60, 160, W - 60, 1100], fill=(255, 255, 255), outline=LINE, width=3)
        d.text((90, 200), "活动拍摄 · 报价草稿", fill=INK, font=font(44, True))
        d.text((90, 280), "合计：¥2000（示意）", fill=RED, font=font(40, True))
        d.text((90, 360), "说明：正式报价以双方确认为准", fill=GRAY, font=font(28))
    elif num == 6:
        d.text((80, 100), "报价字段表（可收藏）", fill=INK, font=font(48, True))
        rows = ["项目名", "数量", "单价", "小计", "备注", "说明语"]
        y = 220
        for r in rows:
            d.rectangle([80, y, W - 80, y + 56], outline=LINE)
            d.text((100, y + 12), r, fill=INK, font=font(32))
            y += 60
    elif num == 7:
        d.text((80, 120), "适合谁", fill=INK, font=font(44, True))
        y = 240
        for t in ["定制 / 本地服务", "销售跟单常改价", "小微 B2B 报价"]:
            d.text((100, y), "· " + t, fill=INK, font=font(40))
            y += 80
    else:
        d.text((80, 200), "你报价最烦哪一步？", fill=INK, font=font(56, True))
        d.text((80, 320), "改规格 · 算价 · 跟客户解释", fill=GRAY, font=font(40))
        d.text((80, 500), "评论区吐槽一句", fill=RED, font=font(48, True))
        d.text((80, 1300), "W27X06 · 讨论型 CTA", fill=GRAY, font=font(28))

    d.text((80, H - 60), f"W27X06 · {num}/8", fill=GRAY, font=font(24))
    return im


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", type=int, nargs="*")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    pages = args.only or list(range(1, 9))
    for n in pages:
        p = OUT / f"page_{n:02d}.png"
        draw_page(n).save(p, "PNG")
        print(f"  {p}")


if __name__ == "__main__":
    main()
