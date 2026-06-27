#!/usr/bin/env python3
"""W27D04 小红书 8 张轮播 · P003 hybrid 模式.

P01 封面: GPT-image-2 报纸风(API)
P02-P08: Pillow 本地渲染(数据卡 / 私信卡 / 反差大字 / 报价表 / 押注卡)

输出: publish/2026-W27/D04-内容服务测水/xhs/page_{01..08}.png · 1080×1620 · 2:3

用法:
    python3 pipeline/p004_video/gen_xhs_d04.py              # 全部
    python3 pipeline/p004_video/gen_xhs_d04.py --skip-cover # 只本地图(调试)
    python3 pipeline/p004_video/gen_xhs_d04.py --only 1 4   # 指定页
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

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "publish" / "2026-W27" / "D04-内容服务测水" / "xhs"
W, H = 1080, 1620

FONT_REG = "/System/Library/Fonts/PingFang.ttc"
FONT_BOLD = "/System/Library/Fonts/PingFang.ttc"
FONT_SONG = "/System/Library/Fonts/STSong.ttf"
FONT_MONO = "/System/Library/Fonts/Menlo.ttc"

# 色板(对齐 D04 自燃测水调:深底 + 红/橙警示 + 绿肯定)
PAPER = (250, 246, 238)
INK = (28, 28, 28)
INK_SOFT = (90, 90, 90)
RED = (200, 48, 48)
RED_DEEP = (140, 30, 30)
GREEN = (38, 154, 90)
ORANGE = (235, 130, 40)
GRAY = (140, 140, 140)
LINE = (210, 205, 195)
LINE_DARK = (180, 175, 165)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("d04xhs")


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD if bold else FONT_REG
    try:
        return ImageFont.truetype(path, size, index=1 if bold else 0)
    except Exception:
        return ImageFont.load_default()


def _mono(size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(FONT_MONO, size)
    except Exception:
        return _font(size)


def _song(size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(FONT_SONG, size)
    except Exception:
        return _font(size, bold=True)


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    if not text:
        return [""]
    lines: list[str] = []
    line = ""
    for ch in text:
        if font.getbbox(line + ch)[2] > max_width:
            lines.append(line)
            line = ch
        else:
            line += ch
    if line:
        lines.append(line)
    return lines


def _draw_rounded_rect(draw: ImageDraw.ImageDraw, xy: tuple, radius: int, fill, outline=None, width=0) -> None:
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def _draw_stamp(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, color=RED) -> None:
    f = _font(28, bold=True)
    bbox = f.getbbox(text)
    w_, h_ = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = 14
    box = (x, y, x + w_ + pad * 2, y + h_ + pad * 2)
    draw.rounded_rectangle(box, radius=8, outline=color, width=4)
    draw.text((x + pad, y + pad - 4), text, fill=color, font=f)


# ───────────────────────────────────────────────────────────────────────
# P02: 4 周真实数据(metrics.csv 一片红)
# ───────────────────────────────────────────────────────────────────────
def _gen_page_02() -> Image.Image:
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    draw.text((80, 110), "这是我账号的", fill=INK, font=_font(56, bold=True))
    draw.text((80, 200), "4 周真实数据", fill=RED, font=_font(72, bold=True))

    draw.line([(80, 320), (W - 80, 320)], fill=LINE_DARK, width=3)

    # 数据表
    rows = [
        ("W26 D01", "美甲店", "32", "0"),
        ("W26 D02", "团购馆", "26", "0"),
        ("W26 D03", "试吃私域", "30", "0"),
        ("W26 D04", "复购流失", "22", "0"),
        ("W26 D08", "电商私域", "11", "0"),
        ("---", "---", "---", "---"),
        ("累计", "5 条", "121", "0"),
    ]
    y = 380
    # header
    draw.text((100, y), "选题", fill=INK_SOFT, font=_font(30, bold=True))
    draw.text((360, y), "钉子人群", fill=INK_SOFT, font=_font(30, bold=True))
    draw.text((720, y), "播放", fill=INK_SOFT, font=_font(30, bold=True))
    draw.text((900, y), "评论", fill=INK_SOFT, font=_font(30, bold=True))
    y += 60
    draw.line([(80, y), (W - 80, y)], fill=LINE, width=2)
    y += 16
    for col1, col2, col3, col4 in rows:
        if col1 == "---":
            draw.line([(80, y + 24), (W - 80, y + 24)], fill=LINE_DARK, width=2)
            y += 60
            continue
        is_total = col1 == "累计"
        f1 = _font(36, bold=is_total)
        f2 = _font(36, bold=is_total)
        f3 = _mono(40)
        col3_color = RED_DEEP if is_total else RED
        col4_color = RED_DEEP if is_total else RED
        draw.text((100, y), col1, fill=INK if is_total else INK_SOFT, font=f1)
        draw.text((360, y), col2, fill=INK if is_total else INK_SOFT, font=f2)
        draw.text((720, y), col3, fill=col3_color, font=f3)
        draw.text((900, y), col4, fill=col4_color, font=f3)
        y += 80

    # 大字 stamp
    _draw_stamp(draw, 80, H - 280, "几乎为 0", color=RED)
    draw.text((300, H - 270), "— 但真实", fill=INK, font=_font(48, bold=True))

    draw.text((80, H - 60), "数据来源:本账号 ops/metrics.csv · 4 周抖音播放(节选)",
              fill=GRAY, font=_font(22))
    return img


# ───────────────────────────────────────────────────────────────────────
# P03: 今早 3 条私信(示意)
# ───────────────────────────────────────────────────────────────────────
def _gen_page_03() -> Image.Image:
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    draw.text((80, 110), "今早 6:00–9:30", fill=INK, font=_font(48, bold=True))
    draw.text((80, 180), "陆续收到 3 条私信", fill=RED, font=_font(56, bold=True))

    msgs = [
        ("06:42", "餐饮老板 · 张", "看到你那条 AI 出片,能给我店里也做一套吗?", (255, 230, 230)),
        ("08:15", "美容店主 · 林", "你这个 AI 内容怎么收费?可以包月吗?", (230, 250, 240)),
        ("09:21", "教培负责人 · 王", "店里需要小红书,自己做不来,你能接吗?", (255, 245, 220)),
    ]
    y = 320
    for when, who, txt, color in msgs:
        # 卡片
        _draw_rounded_rect(draw, (80, y, W - 80, y + 280), 24, color, outline=LINE_DARK, width=2)
        # 示意水印
        draw.rounded_rectangle((W - 200, y + 16, W - 100, y + 56), radius=6, fill=ORANGE)
        draw.text((W - 188, y + 22), "示意", fill="white", font=_font(22, bold=True))
        # who + time
        draw.text((110, y + 28), who, fill=INK, font=_font(34, bold=True))
        draw.text((110, y + 72), when, fill=INK_SOFT, font=_mono(26))
        # 文本(自动折行)
        lines = _wrap_text(txt, _font(36), W - 240)
        ty = y + 130
        for line in lines:
            draw.text((110, ty), line, fill=INK, font=_font(36))
            ty += 50
        y += 310

    draw.text((80, H - 60), "私信内容仿真 · 不指代真实店家", fill=GRAY, font=_font(22))
    return img


# ───────────────────────────────────────────────────────────────────────
# P04: 我先承认 —— 自己都没做起来,凭啥收钱
# ───────────────────────────────────────────────────────────────────────
def _gen_page_04() -> Image.Image:
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    draw.text((80, 140), "我先承认 ——", fill=GRAY, font=_song(58))

    y = 380
    draw.text((80, y), "自己账号", fill=INK, font=_font(110, bold=True))
    y += 140
    draw.text((80, y), "都做不起来", fill=INK, font=_font(110, bold=True))
    y += 200

    # 大问号
    draw.text((80, y), "凭啥", fill=INK_SOFT, font=_font(96, bold=True))
    draw.text((300, y), "收钱?", fill=RED, font=_font(120, bold=True))

    # 底部小字
    draw.text((80, H - 200), "我这条不是反驳,是先把这话替你说了。",
              fill=INK, font=_font(40, bold=True))
    draw.text((80, H - 130), "你可能会发现,接下来我答得很意外。",
              fill=INK_SOFT, font=_song(36))
    return img


# ───────────────────────────────────────────────────────────────────────
# P05: 反转 —— 扑得彻底 = 避坑清单
# ───────────────────────────────────────────────────────────────────────
def _gen_page_05() -> Image.Image:
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    draw.text((80, 140), "我反过来想 ——", fill=GREEN, font=_song(58))

    # 主反转大字
    y = 320
    draw.text((80, y), "扑得彻底", fill=INK, font=_font(112, bold=True))
    y += 140
    draw.text((80, y), "=", fill=RED, font=_font(120, bold=True))
    y += 140
    draw.text((80, y), "精确避坑清单", fill=RED, font=_font(112, bold=True))

    # 列点
    y += 200
    draw.line([(80, y), (W - 80, y)], fill=LINE_DARK, width=3)
    y += 50

    points = [
        "▸ 哪种钩子前 3s 就被划走",
        "▸ 哪种封面老板看不懂",
        "▸ 哪种文案 AI 味重",
        "▸ 哪种数据是平台假高",
        "▸ 哪种 CTA 评论门槛太高",
    ]
    for p in points:
        draw.text((100, y), p, fill=INK, font=_font(40))
        y += 64

    # 底部强调
    draw.text((80, H - 130), "这是 4 周真试错才能买回来的清单。",
              fill=INK, font=_font(38, bold=True))
    draw.text((80, H - 70), "免费可以学,知道在哪个坑要花钱。",
              fill=INK_SOFT, font=_song(32))
    return img


# ───────────────────────────────────────────────────────────────────────
# P06: 系统真实成本拆解
# ───────────────────────────────────────────────────────────────────────
def _gen_page_06() -> Image.Image:
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    draw.text((80, 100), "这套系统的", fill=INK, font=_font(52, bold=True))
    draw.text((80, 180), "真实成本", fill=RED, font=_font(76, bold=True))

    # 大单价
    draw.text((80, 350), "单条 < ¥3", fill=GREEN, font=_font(140, bold=True))

    # 成本明细表
    y = 580
    _draw_rounded_rect(draw, (80, y, W - 80, y + 540), 24, (245, 245, 240),
                       outline=LINE_DARK, width=2)
    y += 50
    draw.text((120, y), "明细", fill=INK_SOFT, font=_font(32, bold=True))
    draw.line([(120, y + 60), (W - 120, y + 60)], fill=LINE, width=2)

    items = [
        ("图(GPT-image-2 中转)", "¥0.30"),
        ("配音(MiniMax / Edge-TTS)", "¥1.00"),
        ("文案(本地 LLM 调用)", "¥0.50"),
        ("渲染(本地 capture_frames 并行)", "¥0.00"),
        ("人工时间(选题 + 校审 ~5 分钟)", "¥1.07"),
    ]
    ry = y + 90
    for k, v in items:
        draw.text((120, ry), k, fill=INK, font=_font(34))
        draw.text((W - 230, ry), v, fill=ORANGE, font=_mono(36))
        ry += 60

    draw.line([(120, ry + 10), (W - 120, ry + 10)], fill=GREEN, width=3)
    ry += 30
    draw.text((120, ry), "合计", fill=INK, font=_font(40, bold=True))
    draw.text((W - 280, ry), "¥2.87", fill=GREEN, font=_mono(48))

    draw.text((80, H - 60), "公开口径:今日 commit 8e13d3c 截帧并行 3.4× 后实际成本",
              fill=GRAY, font=_font(22))
    return img


# ───────────────────────────────────────────────────────────────────────
# P07: 三档报价(实体店老板用)
# ───────────────────────────────────────────────────────────────────────
def _gen_page_07() -> Image.Image:
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    draw.text((80, 100), "三档报价", fill=INK, font=_font(64, bold=True))
    draw.text((80, 180), "(实体店老板用)", fill=GRAY, font=_song(40))

    tiers = [
        ("轻档", "99", "4 条/月", "文 + 图 + 标签", PAPER, INK),
        ("中档 · 推荐", "299", "14 条/月", "同上 + 每周答疑 1 次", (235, 250, 240), GREEN),
        ("重档", "599", "14 条/月", "同上 + 周复盘报告", PAPER, INK),
    ]
    y = 320
    for tier, price, qty, feat, bg, accent in tiers:
        is_mid = "推荐" in tier
        _draw_rounded_rect(draw, (80, y, W - 80, y + 260), 24, bg,
                           outline=accent if is_mid else LINE_DARK,
                           width=4 if is_mid else 2)
        # 档位 + 价格
        draw.text((110, y + 24), tier, fill=accent if is_mid else INK_SOFT,
                  font=_font(36, bold=True))
        # 价
        draw.text((110, y + 80), f"¥{price}", fill=accent, font=_font(120, bold=True))
        draw.text((360, y + 130), "/月", fill=INK_SOFT, font=_font(34))
        # 数量
        draw.text((620, y + 60), qty, fill=ORANGE, font=_font(48, bold=True))
        # 含什么
        draw.text((620, y + 130), feat, fill=INK, font=_font(28))
        # 推荐角标
        if is_mid:
            _draw_rounded_rect(draw, (W - 220, y + 16, W - 110, y + 60), 14, GREEN)
            draw.text((W - 200, y + 22), "推荐", fill="white", font=_font(26, bold=True))
        y += 290

    # 承诺
    y = H - 200
    _draw_rounded_rect(draw, (80, y, W - 80, y + 130), 18, (255, 240, 220),
                       outline=ORANGE, width=3)
    draw.text((110, y + 24), "14 条交付不行你说停",
              fill=INK, font=_font(40, bold=True))
    draw.text((110, y + 76), "剩下的原路退",
              fill=ORANGE, font=_font(40, bold=True))
    return img


# ───────────────────────────────────────────────────────────────────────
# P08: 测水 + 押注 CTA
# ───────────────────────────────────────────────────────────────────────
def _gen_page_08() -> Image.Image:
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    draw.text((80, 100), "但我不知道", fill=INK, font=_font(56, bold=True))
    draw.text((80, 180), "这价能不能行", fill=RED, font=_font(76, bold=True))

    draw.text((80, 320), "所以这条不是广告,是测水。",
              fill=INK_SOFT, font=_song(42))

    # CTA 方式
    y = 460
    _draw_rounded_rect(draw, (80, y, W - 80, y + 360), 24, (245, 245, 240),
                       outline=LINE_DARK, width=2)
    draw.text((120, y + 30), "测水方式", fill=ORANGE, font=_font(36, bold=True))
    items = [
        "▸ 评论扣档位号 + 你的行业",
        "▸ 扣 0 = 不付,也算一票",
        "▸ 凑齐 10 个,我开 3 个名额",
        "▸ 免费做 1 条 demo 给你看",
    ]
    iy = y + 100
    for it in items:
        draw.text((140, iy), it, fill=INK, font=_font(38))
        iy += 60

    # 押注
    y = 880
    _draw_rounded_rect(draw, (80, y, W - 80, y + 460), 24, (28, 28, 28))
    draw.text((110, y + 30), "下月数据真公开", fill=ORANGE, font=_font(44, bold=True))
    draw.text((110, y + 110), "押我赢:", fill="white", font=_font(36))
    draw.text((280, y + 110), "模板全公开", fill=GREEN, font=_font(36, bold=True))
    draw.text((110, y + 170), "押我输:", fill="white", font=_font(36))
    draw.text((280, y + 170), "账号停更", fill=RED, font=_font(36, bold=True))
    draw.line([(110, y + 240), (W - 190, y + 240)], fill=(80, 80, 80), width=2)
    draw.text((110, y + 270), "你押我赢还是输?", fill="white", font=_font(48, bold=True))
    draw.text((110, y + 350), "评论区告诉我,数字最大那一边赢。",
              fill=(180, 180, 180), font=_song(32))

    draw.text((80, H - 40), "W27D04 · 测水 · 不达预期不收钱 · 履约担保口径",
              fill=GRAY, font=_font(20))
    return img


# ───────────────────────────────────────────────────────────────────────
# P01: 封面(GPT-image-2 报纸风)
# ───────────────────────────────────────────────────────────────────────
COVER_PROMPT = """
A full-page vertical 2026 Chinese tabloid-zine cover, 2:3 portrait, 1080x1620,
beige off-white paper background with halftone print texture, ink stipple shading,
modern Chinese self-publishing zine aesthetic — like a scrappy, hand-printed
financial diary spread (mix of crisp serif Chinese typography + visible halftone
red ink accent).

TOP MASTHEAD STRIP (thin black border, sans-serif Chinese + English):
"AI 小系统日报 · THE AGENT TIMES · 2026.07.02 · 测水特刊 · 免费"

MAIN HEADLINE (huge black serif Chinese characters, two lines, ~96pt, bold):
Line 1: "4 周做 AI 内容"
Line 2: "涨粉几乎为 0"

SUB-HEADLINE (smaller italic Chinese, ~36pt, below the headline):
"但今早 3 个老板私信问我:多少钱包一套?"

RED LEAD QUOTE BOX (red background, white Chinese text, mid-left position):
"📍 本期不卖课,也不教学,只是测水。"

CENTER ILLUSTRATION area (large, sketchy 1990s newspaper-style line drawing):
A weary mid-aged Chinese man sitting at a cluttered desk in a small home office,
hunched over a laptop. On the laptop screen: a clearly visible analytics
dashboard with a flat-line chart in red. To the right of the laptop: a stack
of 14 small printed papers labeled "扑了" (failed), and one paper on top labeled
"待发". To the left: a smartphone showing three new chat messages icons.
The man holds a small calculator showing "¥2.87". Coffee cup, scattered notes,
single desk lamp. Ink-stipple shading style.

SIDE PROPS (around the illustration):
- A red oval newspaper stamp top-right reading '测水' tilted ~-10 degrees
- A small "示意" yellow paper tag near the smartphone messages
- A tiny circular badge bottom-right reading '99/299/599'

BODY TEXT block (lower third, 2-column Chinese newspaper serif body font):
"【本报讯】2026 年 7 月,一名长期 AI 内容创作者公开承认自己 4 周抖音/小红书内容
全数扑街,但同时收到三条实体店老板询价私信。其推出三档测水定价 99/299/599 元/月,
14 条交付不行可退款。"
(rest as authentic Chinese tabloid filler)

BOTTOM RIGHT CORNER: a circular red wax stamp with bold Chinese characters
"测水首发" rotated about -12 degrees, slightly faded ink texture.

Overall: modern Chinese zine/tabloid hybrid, ink stipple halftone print, raw and
honest tone — like an indie financial diary you'd find at a coffee shop in 上海.
Mobile-readable typography, vertical aspect ratio for mobile carousel.
DO NOT include any English watermark, signature, or fictional brand logos.
""".strip()


def _gen_page_01_api() -> Image.Image | None:
    load_dotenv(ROOT / ".env")
    api_key = os.environ.get("GPT_IMAGE_API_KEY")
    base_url = os.environ.get("GPT_IMAGE_BASE_URL")
    model = os.environ.get("GPT_IMAGE_MODEL", "gpt-image-2")
    if not api_key or not base_url:
        log.warning("GPT_IMAGE_API_KEY 或 BASE_URL 未设置,跳过封面")
        return None
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url, timeout=300.0, max_retries=2)
    for attempt in range(1, 5):
        try:
            t0 = time.time()
            resp = client.images.generate(
                model=model, prompt=COVER_PROMPT, size="1024x1536", n=1,
            )
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
            log.info("  ✓ P01 cover (%.1fs, %d KB) attempt=%d",
                     dt, len(raw_bytes) // 1024, attempt)
            return final
        except Exception as exc:  # noqa: BLE001 — API exceptions vary; retry all
            log.warning("  ✗ P01 attempt=%d: %s", attempt, exc)
            time.sleep(5 * attempt)
    log.error("P01 封面生成失败,全部重试用尽")
    return None


LOCAL_PAGES = {
    2: _gen_page_02,
    3: _gen_page_03,
    4: _gen_page_04,
    5: _gen_page_05,
    6: _gen_page_06,
    7: _gen_page_07,
    8: _gen_page_08,
}


def main() -> int:
    ap = argparse.ArgumentParser(description="W27D04 小红书 8 张轮播图生成")
    ap.add_argument("--skip-cover", action="store_true", help="跳过 P01 API 调用")
    ap.add_argument("--only", type=int, nargs="*", help="只生成指定页 (1-8)")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pages_to_gen = set(args.only) if args.only else set(range(1, 9))

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
