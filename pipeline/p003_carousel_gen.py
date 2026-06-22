#!/usr/bin/env python3
"""P003 选题轮播图生成 · 一群 Agent 抢着帮我实现.

输出: publish/P003/xhs/page_{01..06}.png · 1080x1620 · 2:3

P01 封面: GPT-image-2 报纸风（API 调用）
P02-P06: Pillow 本地渲染（备忘录风/对比表/拼贴风），零 API 成本

用法:
    python3 pipeline/p003_carousel_gen.py              # 全部生成
    python3 pipeline/p003_carousel_gen.py --skip-cover # 只本地图（调试）
    python3 pipeline/p003_carousel_gen.py --only 1     # 只生成 P01
"""
from __future__ import annotations

import argparse
import base64
import io
import logging
import os
import sys
import time
import urllib.request
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "publish" / "P003" / "xhs"
W, H = 1080, 1620

FONT_REG = "/System/Library/Fonts/PingFang.ttc"
FONT_BOLD = "/System/Library/Fonts/PingFang.ttc"
FONT_SONG = "/System/Library/Fonts/STSong.ttf"

PAPER = (250, 246, 238)
INK = (28, 28, 28)
RED = (200, 48, 48)
GREEN = (38, 154, 90)
GRAY = (140, 140, 140)
LINE = (210, 205, 195)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("p003")


def _font(size: int, bold: bool = False, index: int = 0) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD if bold else FONT_REG
    try:
        return ImageFont.truetype(path, size, index=index)
    except Exception:
        return ImageFont.truetype(FONT_REG, size, index=0)


def _song(size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(FONT_SONG, size)
    except Exception:
        return _font(size)


def _draw_rounded_rect(draw: ImageDraw.ImageDraw, xy: tuple, radius: int, fill) -> None:
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill)


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    for raw_line in text.split("\n"):
        if not raw_line:
            lines.append("")
            continue
        current = ""
        for ch in raw_line:
            test = current + ch
            bbox = font.getbbox(test)
            if bbox[2] - bbox[0] > max_width:
                lines.append(current)
                current = ch
            else:
                current = test
        if current:
            lines.append(current)
    return lines


# ─── P02: 备忘录 · "我的全部输入" ───────────────────────────────────
def _gen_page_02() -> Image.Image:
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    y = 120
    title_font = _font(56, bold=True)
    draw.text((80, y), "我的全部输入", fill=INK, font=title_font)
    y += 90

    sub_font = _font(36)
    draw.text((80, y), "总计 23 个字", fill=GRAY, font=sub_font)
    y += 100

    draw.line([(80, y), (W - 80, y)], fill=LINE, width=2)
    y += 60

    memo_font = _font(42)
    user_input = "「抛出一个选题，一群 agent 抢着帮我实现。\n最终交付图文。制作过程本身也是素材。\n全自动高产。成本低。」"
    lines = _wrap_text(user_input, memo_font, W - 200)
    for line in lines:
        draw.text((100, y), line, fill=INK, font=memo_font)
        y += 62

    y += 80
    draw.line([(80, y), (W - 80, y)], fill=LINE, width=2)
    y += 60

    note_font = _font(32)
    draw.text((80, y), "没有需求文档。没有设计稿。没有排期。", fill=GRAY, font=note_font)
    y += 50
    draw.text((80, y), "就这一句话。", fill=RED, font=_font(36, bold=True))

    tag_font = _font(28)
    draw.text((80, H - 100), "P003 · page 02 · 备忘录风", fill=GRAY, font=tag_font)
    return img


# ─── P03: 工种分工表 ─────────────────────────────────────────────────
def _gen_page_03() -> Image.Image:
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    y = 100
    draw.text((80, y), "系统自动拆出 9 个工种", fill=INK, font=_font(52, bold=True))
    y += 90
    draw.text((80, y), "每个角色有明确职责和独立产出", fill=GRAY, font=_font(32))
    y += 80

    roles = [
        ("编导", "选题立项 + 四形态拆分", RED),
        ("记者", "真实性调研 + 数据证据链", GREEN),
        ("纪录片导演", "故事弧线 + 情绪锚点", INK),
        ("执行导演", "分镜表 + 节奏控制", INK),
        ("摄像/视觉", "画面清单 + B-roll", INK),
        ("编剧", "三版脚本 + 前 3s 钩子", GREEN),
        ("视觉设计", "风格路线 + 配色方案", RED),
        ("剪辑", "三平台规格 + 时长卡控", GRAY),
        ("运营", "发布文案 + 私信路径", GREEN),
    ]

    for role, desc, color in roles:
        _draw_rounded_rect(draw, (80, y, 280, y + 56), 8, color)
        draw.text((95, y + 8), role, fill=(255, 255, 255), font=_font(30, bold=True))
        draw.text((300, y + 12), desc, fill=INK, font=_font(30))
        y += 72

    y += 40
    draw.line([(80, y), (W - 80, y)], fill=LINE, width=2)
    y += 40
    draw.text((80, y), "⚡ 可串行扮演，也可并行调 Agent", fill=GRAY, font=_font(30))

    draw.text((80, H - 100), "P003 · page 03 · 工种分工表", fill=GRAY, font=_font(28))
    return img


# ─── P04: 各工种产出片段拼贴 ────────────────────────────────────────
def _gen_page_04() -> Image.Image:
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    draw.text((80, 100), "他们同时开工", fill=INK, font=_font(52, bold=True))
    draw.text((80, 180), "每个工种独立产出，互不阻塞", fill=GRAY, font=_font(30))

    cards = [
        ("记者笔记", [
            "✓ 用户输入 23 字",
            "✓ 9 工种全 AI",
            "✓ 单条成本 < ¥2",
            "✓ 外包对照 ¥200-500",
        ], (255, 255, 255), GREEN),
        ("编剧 v0/vA/vB", [
            "v0  我说了一句话…",
            "vA  一个想法 3 天放弃",
            "vB  外包¥500 vs ¥2",
            "→ 选 vA（痛点先行）",
        ], (255, 255, 255), RED),
        ("分镜表", [
            "P01  报纸风封面",
            "P02  备忘录·我的输入",
            "P03  工种分工表",
            "P04  各工种产出（本页）",
            "P05  成本对比",
            "P06  CTA",
        ], (255, 255, 255), INK),
        ("视觉路线", [
            "封面 P002 报纸风",
            "内页 P001 真实风",
            "配色 米白 + 黑 + 红",
            "字体 PingFang",
        ], (255, 255, 255), GRAY),
    ]

    card_w, card_h = 440, 540
    gap_x, gap_y = 40, 30
    start_x, start_y = 80, 260

    for i, (title, items, bg, accent) in enumerate(cards):
        col = i % 2
        row = i // 2
        x = start_x + col * (card_w + gap_x)
        y = start_y + row * (card_h + gap_y)
        _draw_rounded_rect(draw, (x, y, x + card_w, y + card_h), 16, bg)
        draw.rectangle((x, y, x + card_w, y + 8), fill=accent)
        draw.text((x + 24, y + 30), title, fill=accent, font=_font(34, bold=True))
        draw.line([(x + 24, y + 90), (x + card_w - 24, y + 90)], fill=LINE, width=1)

        item_y = y + 110
        for it in items:
            wrapped = _wrap_text(it, _font(28), card_w - 48)
            for w_line in wrapped:
                draw.text((x + 24, item_y), w_line, fill=INK, font=_font(28))
                item_y += 40
            item_y += 8

    draw.text((80, H - 100), "P003 · page 04 · 同时开工", fill=GRAY, font=_font(28))
    return img


# ─── P05: 成本/时间对比表 ──────────────────────────────────────────
def _gen_page_05() -> Image.Image:
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    draw.text((80, 100), "外包 vs Agent", fill=INK, font=_font(56, bold=True))
    draw.text((80, 185), "同一条小红书图文，两条路线", fill=GRAY, font=_font(30))

    rows = [
        ("项目", "外包", "Agent 团队"),
        ("沟通需求", "2 天", "1 句话"),
        ("等初稿", "3 天", "10 分钟"),
        ("修改轮次", "2-3 轮", "0 轮"),
        ("成本", "¥200-500", "< ¥2"),
        ("可复制性", "改一条改一次", "脚本化"),
        ("过程素材", "无", "全程留档"),
    ]

    table_x = 80
    table_y = 290
    col_widths = [240, 320, 360]
    row_h = 90

    for r, row in enumerate(rows):
        y = table_y + r * row_h
        bg = (235, 230, 220) if r == 0 else PAPER
        if r == 0:
            draw.rectangle((table_x, y, table_x + sum(col_widths), y + row_h), fill=INK)
        elif r % 2 == 0:
            draw.rectangle((table_x, y, table_x + sum(col_widths), y + row_h), fill=bg)

        x = table_x
        for c, cell in enumerate(row):
            if r == 0:
                font = _font(32, bold=True)
                color = (255, 255, 255)
            elif c == 0:
                font = _font(30, bold=True)
                color = INK
            elif c == 1:
                font = _font(30)
                color = GRAY
            else:
                font = _font(32, bold=True)
                color = RED if "¥" in cell or "天" in cell else GREEN
            draw.text((x + 24, y + 26), cell, fill=color, font=font)
            x += col_widths[c]

    bottom_y = table_y + len(rows) * row_h + 60
    draw.line([(80, bottom_y), (W - 80, bottom_y)], fill=LINE, width=2)
    bottom_y += 50

    draw.text((80, bottom_y), "= 你只动了一次嘴", fill=INK, font=_font(44, bold=True))
    bottom_y += 70
    draw.text((80, bottom_y), "其余的活，9 个 Agent 接力跑完", fill=RED, font=_font(36, bold=True))

    draw.text((80, H - 100), "P003 · page 05 · 成本对比", fill=GRAY, font=_font(28))
    return img


# ─── P06: 总结 + CTA ────────────────────────────────────────────────
def _gen_page_06() -> Image.Image:
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    y = 140
    draw.text((80, y), "你现在看到的这条", fill=INK, font=_font(58, bold=True))
    y += 100
    draw.text((80, y), "就是这么做出来的", fill=RED, font=_font(58, bold=True))
    y += 130

    draw.line([(80, y), (W - 80, y)], fill=LINE, width=2)
    y += 60

    summary = [
        "1 句话想法",
        "9 个 AI 工种自动分工",
        "10 分钟交付",
        "成本 < ¥2",
        "制作过程本身就是素材",
    ]
    for line in summary:
        draw.text((100, y), "•", fill=RED, font=_font(40, bold=True))
        draw.text((140, y), line, fill=INK, font=_font(40))
        y += 70

    y += 60
    draw.line([(80, y), (W - 80, y)], fill=LINE, width=2)
    y += 60

    draw.text((80, y), "你最烦的", fill=INK, font=_font(46, bold=True))
    y += 70
    draw.text((80, y), "那个重复活", fill=INK, font=_font(46, bold=True))
    y += 70
    draw.text((80, y), "是哪一个？", fill=RED, font=_font(46, bold=True))

    draw.text((80, H - 100), "P003 · page 06 · CTA", fill=GRAY, font=_font(28))
    return img


# ─── P01: 报纸风封面（GPT-image-2）─────────────────────────────────
COVER_PROMPT = """
A full-page vertical 1990s Chinese tabloid newspaper layout, 2:3 portrait,
beige off-white paper background with halftone print texture, ink stipple shading,
slightly desaturated sepia tone, vintage 1990s gossip magazine aesthetic.

TOP MASTHEAD STRIP (thin black border, sans-serif Chinese + English):
"AI小系统日报 · THE AGENT TIMES · 2026.06.19 · 创刊号 · 免费"

MAIN HEADLINE (large black serif Chinese characters, bold, ~80pt):
"抛个选题，9 个 AI 抢着干"

SUB-HEADLINE (smaller italic Chinese, ~36pt):
"一个人的内容团队：全自动 · 高产 · 成本 < ¥2"

RED LEAD QUOTE BOX (red background, white Chinese text):
"📍 全程 0 人工排版 · 制作过程本身也是素材"

CENTER ILLUSTRATION area:
Nine cartoon characters seated around a large round editorial desk, each
holding a different prop: one with a reporter notebook, one with a camera,
one with a clapperboard, one with a script, one typing on laptop, one holding
a color palette, one with scissors, one with a megaphone, one with a magnifying
glass. All leaning in eagerly. Overhead view, warm desk lamp lighting. The
desk has scattered papers and a single post-it note reading "23字". Tabloid
editorial room vibe.

SIDE PROPS:
Three red oval newspaper stamps in corners reading '号外' '抢稿' '首发'

BODY TEXT block (Chinese newspaper serif body font, 2-column lower half):
"【本报讯】昨日凌晨，一名创业中年人向本报 AI 编辑系统提交了仅 23 字选题。系统在 10 分钟内自动调度 9 个工种完成全部图文生产。总成本不到 2 元人民币。"
(rest should appear as authentic-looking Chinese tabloid filler text)

RIGHT SIDEBAR (red box with white Chinese title, bullet items with ▸):
title: "参与工种"
items:
  ▸ 编导
  ▸ 记者
  ▸ 纪录片导演
  ▸ 编剧
  ▸ 视觉设计
  ▸ 运营

BOTTOM RIGHT CORNER: a circular red wax stamp with bold Chinese characters
"首发" rotated about -12 degrees, slightly faded ink texture.

Overall: authentic Chinese 1990s gossip tabloid, ink stipple halftone print,
mobile-readable typography, vertical aspect ratio for mobile carousel.
DO NOT include any English watermarks or signature.
""".strip()


def _gen_page_01_api() -> Image.Image | None:
    load_dotenv(ROOT / ".env")
    api_key = os.environ.get("GPT_IMAGE_API_KEY")
    base_url = os.environ.get("GPT_IMAGE_BASE_URL")
    model = os.environ.get("GPT_IMAGE_MODEL", "gpt-image-2")
    if not api_key or not base_url:
        log.warning("GPT_IMAGE_API_KEY 或 BASE_URL 未设置，跳过封面")
        return None
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url, timeout=300.0, max_retries=2)
    for attempt in range(1, 5):
        try:
            t0 = time.time()
            resp = client.images.generate(model=model, prompt=COVER_PROMPT, size="1024x1536", n=1)
            first = resp.data[0]
            b64 = getattr(first, "b64_json", None)
            if b64:
                raw_bytes = base64.b64decode(b64)
            else:
                url = getattr(first, "url", None)
                if url:
                    with urllib.request.urlopen(url) as r:
                        raw_bytes = r.read()
                else:
                    raise RuntimeError(f"无 b64/url: {first!r}")
            img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
            final = img.resize((W, H), Image.LANCZOS)
            dt = time.time() - t0
            log.info("  ✓ P01 cover (%.1fs, %d KB) attempt=%d", dt, len(raw_bytes) // 1024, attempt)
            return final
        except Exception as exc:
            log.warning("  ✗ P01 attempt=%d: %s", attempt, exc)
            time.sleep(5 * attempt)
    log.error("P01 封面生成失败，全部重试用尽")
    return None


# ─── main ────────────────────────────────────────────────────────────
LOCAL_PAGES = {
    2: _gen_page_02,
    3: _gen_page_03,
    4: _gen_page_04,
    5: _gen_page_05,
    6: _gen_page_06,
}


def main() -> int:
    ap = argparse.ArgumentParser(description="P003 轮播图生成")
    ap.add_argument("--skip-cover", action="store_true", help="跳过 P01 API 调用")
    ap.add_argument("--only", type=int, nargs="*", help="只生成指定页 (1-6)")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pages_to_gen = set(args.only) if args.only else {1, 2, 3, 4, 5, 6}

    ok = 0
    if 1 in pages_to_gen and not args.skip_cover:
        img = _gen_page_01_api()
        if img:
            out = OUT_DIR / "page_01.png"
            img.save(out, "PNG", optimize=True)
            log.info("✓ saved %s (%d KB)", out.name, out.stat().st_size // 1024)
            ok += 1
        else:
            log.warning("P01 跳过")
    elif 1 in pages_to_gen:
        log.info("--skip-cover: P01 跳过")

    for page_num, gen_fn in LOCAL_PAGES.items():
        if page_num not in pages_to_gen:
            continue
        img = gen_fn()
        out = OUT_DIR / f"page_{page_num:02d}.png"
        img.save(out, "PNG", optimize=True)
        log.info("✓ saved %s (%d KB)", out.name, out.stat().st_size // 1024)
        ok += 1

    log.info("完成 %d/%d 页", ok, len(pages_to_gen))
    return 0


if __name__ == "__main__":
    sys.exit(main())
