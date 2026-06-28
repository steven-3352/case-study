#!/usr/bin/env python3
"""W27D05 小红书 8 张轮播 · P003 hybrid 模式.

P01 封面: GPT-image-2 报纸风(API)
P02-P08: Pillow 本地渲染(招聘卡 / 导出步骤 / 柱图 / 群截屏 / 内核 / Excel / CTA)

输出: publish/2026-W27/D05-招人前先数群/xhs/page_{01..08}.png · 1080×1620 · 2:3

用法:
    python3 pipeline/p004_video/gen_xhs_d05.py              # 全部
    python3 pipeline/p004_video/gen_xhs_d05.py --skip-cover # 只本地图(调试)
    python3 pipeline/p004_video/gen_xhs_d05.py --only 1 4   # 指定页
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
OUT_DIR = ROOT / "publish" / "2026-W27" / "D05-招人前先数群" / "xhs"
W, H = 1080, 1620

FONT_REG = "/System/Library/Fonts/PingFang.ttc"
FONT_BOLD = "/System/Library/Fonts/PingFang.ttc"
FONT_SONG = "/System/Library/Fonts/STSong.ttf"
FONT_MONO = "/System/Library/Fonts/Menlo.ttc"

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
WECHAT = (149, 236, 105)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("d05xhs")


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


def _fallback_font(size: int) -> ImageFont.FreeTypeFont:
    """PingFang index=2 含扩展汉字(迟/远 等),作 _font(bold) 缺字回退."""
    try:
        return ImageFont.truetype(FONT_REG, size, index=2)
    except Exception:
        return _font(size)


def _draw_safe(draw: ImageDraw.ImageDraw, xy: tuple, text: str, fill,
               font: ImageFont.FreeTypeFont) -> None:
    """逐字渲染,缺字自动回退 PingFang idx=2,避免 迟/远 这类字符渲成空白."""
    fb = _fallback_font(font.size)
    x, y = xy
    for ch in text:
        bbox = font.getbbox(ch)
        if (bbox[3] - bbox[1]) <= 1 and ch.strip():
            draw.text((x, y), ch, fill=fill, font=fb)
            fbb = fb.getbbox(ch)
            x += fbb[2] - fbb[0]
        else:
            draw.text((x, y), ch, fill=fill, font=font)
            x += bbox[2] - bbox[0]


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
# P02: 招聘需求(老板原话 + 招聘 APP 截屏示意)
# ───────────────────────────────────────────────────────────────────────
def _gen_page_02() -> Image.Image:
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    draw.text((80, 110), "一个母婴店老板", fill=INK, font=_font(56, bold=True))
    draw.text((80, 200), "上个月跟我说 ——", fill=INK_SOFT, font=_song(50))

    # 老板原话引用框
    y = 320
    _draw_rounded_rect(draw, (80, y, W - 80, y + 360), 24, (255, 245, 240),
                       outline=ORANGE, width=4)
    draw.text((110, y + 30), "📞 店主 L · 微信语音 02:48", fill=ORANGE, font=_font(28, bold=True))
    draw.text((110, y + 90), '"客户消息太多回不过来"', fill=INK, font=_font(46, bold=True))
    draw.text((110, y + 170), '"我得招个人专门回微信"', fill=INK, font=_font(46, bold=True))
    draw.text((110, y + 260), '"BOSS 直聘都挂了 3 天了"', fill=INK_SOFT, font=_song(36))

    # 招聘示意卡
    y = 760
    _draw_rounded_rect(draw, (80, y, W - 80, y + 380), 24, (245, 245, 240),
                       outline=LINE_DARK, width=2)
    draw.text((110, y + 30), "🔍 BOSS 直聘 · 老板搜过", fill=INK_SOFT, font=_font(30, bold=True))
    draw.line([(110, y + 80), (W - 110, y + 80)], fill=LINE, width=2)

    # 招聘卡
    _draw_rounded_rect(draw, (110, y + 110, W - 110, y + 350), 16, PAPER,
                       outline=RED, width=4)
    draw.text((140, y + 130), "客服专员 · 微信回复", fill=INK, font=_font(40, bold=True))
    draw.text((W - 360, y + 130), "¥4500-6000", fill=RED, font=_font(40, bold=True))
    draw.text((140, y + 200), "经验不限  学历不限  五险一金  餐补",
              fill=INK_SOFT, font=_font(28))
    draw.text((140, y + 260), "某母婴连锁 · 门店运营部", fill=INK_SOFT, font=_song(30))

    # 红色印章
    _draw_stamp(draw, W - 280, y + 250, "已挂 3 天", color=RED)

    draw.text((80, H - 60), "招聘 APP 示意 · 不指代真实门店 · 已脱敏",
              fill=GRAY, font=_font(22))
    return img


# ───────────────────────────────────────────────────────────────────────
# P03: 我说,先别招 + 微信导出步骤
# ───────────────────────────────────────────────────────────────────────
def _gen_page_03() -> Image.Image:
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    # 反转开头
    draw.text((80, 100), "我说 ——", fill=GREEN, font=_song(50))
    draw.text((80, 200), "先别招", fill=RED, font=_font(150, bold=True))

    draw.text((80, 400), "我让她先做一件事:", fill=INK, font=_font(40, bold=True))

    # 三步教学卡
    steps = [
        ("1", "微信 PC 端", "设置 → 聊天 → 备份与迁移"),
        ("2", "选「门店客户群」", "范围:近 90 天 · 导出 .txt"),
        ("3", "全文贴给 AI", "让它「归类 + 统计 + 出表」"),
    ]
    y = 520
    for num, title, desc in steps:
        _draw_rounded_rect(draw, (80, y, W - 80, y + 220), 24, (255, 250, 245),
                           outline=LINE_DARK, width=2)
        # 圆形序号
        _draw_rounded_rect(draw, (110, y + 30, 200, y + 120), 45, RED)
        bbox = _font(64, bold=True).getbbox(num)
        nw, nh = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((155 - nw // 2, y + 75 - nh // 2 - 4), num, fill="white",
                  font=_font(64, bold=True))
        # 标题
        draw.text((240, y + 36), title, fill=INK, font=_font(42, bold=True))
        # 描述
        draw.text((240, y + 110), desc, fill=INK_SOFT, font=_font(32))
        y += 250

    draw.text((80, H - 60), "微信 PC 端真实路径 · 15 分钟可完成",
              fill=GRAY, font=_font(22))
    return img


# ───────────────────────────────────────────────────────────────────────
# P04: 数完才知道 · 柱图主战场
# ───────────────────────────────────────────────────────────────────────
def _gen_page_04() -> Image.Image:
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    draw.text((80, 100), "90 天 · 全部归类", fill=INK_SOFT, font=_font(36, bold=True))

    # 大数字
    draw.text((80, 170), "1247", fill=RED, font=_font(220, bold=True))
    draw.text((80, 410), "条客户问题", fill=INK, font=_font(48, bold=True))

    # 反差句
    draw.text((80, 500), "真不一样的 ——", fill=INK_SOFT, font=_song(40))
    draw.text((80, 570), "只有 10 来类", fill=ORANGE, font=_font(80, bold=True))

    # 柱图
    y = 740
    _draw_rounded_rect(draw, (80, y, W - 80, y + 720), 24, (255, 250, 245),
                       outline=LINE_DARK, width=2)
    draw.text((110, y + 30), "头部 5 类 · 占 7 成多", fill=RED, font=_font(34, bold=True))
    draw.line([(110, y + 90), (W - 110, y + 90)], fill=LINE, width=2)

    bars = [
        ("营业时间", 22, RED),
        ("价格 / 团购", 18, RED),
        ("改约 / 预约", 14, RED),
        ("产品适用", 11, RED),
        ("退换货", 8, RED),
        ("其他 6 类合计", 27, GRAY),
    ]
    by = y + 130
    max_w = W - 110 - 280 - 100  # name=210, pct=80
    for name, pct, color in bars:
        draw.text((130, by + 6), name, fill=INK, font=_font(30))
        track_x0 = 350
        track_x1 = W - 200
        draw.rounded_rectangle((track_x0, by, track_x1, by + 48), radius=8,
                               fill=(235, 230, 220))
        fill_w = int((track_x1 - track_x0) * pct / 30)
        draw.rounded_rectangle((track_x0, by, track_x0 + fill_w, by + 48),
                               radius=8, fill=color)
        draw.text((W - 180, by + 4), f"{pct}%", fill=color, font=_mono(36))
        by += 88

    draw.text((80, H - 60), "某母婴店 90 天群消息归类(示意 · 已脱敏)",
              fill=GRAY, font=_font(22))
    return img


# ───────────────────────────────────────────────────────────────────────
# P05: 老板反应 · 沉默三秒 + 群截屏
# ───────────────────────────────────────────────────────────────────────
def _gen_page_05() -> Image.Image:
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    draw.text((80, 100), "她看完柱图 ——", fill=INK, font=_font(50, bold=True))
    draw.text((80, 180), "沉默了三秒", fill=RED, font=_font(80, bold=True))

    # 当晚发群仿真截屏
    y = 340
    _draw_rounded_rect(draw, (80, y, W - 80, y + 1050), 24, (237, 237, 237),
                       outline=LINE_DARK, width=2)

    # 群头部
    _draw_rounded_rect(draw, (110, y + 30, 195, y + 115), 18, WECHAT)
    draw.text((130, y + 50), "💬", fill="white", font=_font(56))
    draw.text((220, y + 38), "店务总群(8)", fill=INK, font=_font(36, bold=True))
    draw.text((220, y + 86), "今天 22:14", fill=INK_SOFT, font=_font(24))

    # 红色示意水印
    _draw_rounded_rect(draw, (W - 230, y + 40, W - 110, y + 84), 8, RED)
    draw.text((W - 218, y + 46), "示意 · 已脱敏", fill="white", font=_font(20, bold=True))

    draw.line([(110, y + 145), (W - 110, y + 145)], fill=(208, 208, 208), width=2)

    # 时间分隔
    draw.text((W // 2 - 60, y + 170), "今天 22:14", fill="white", font=_font(22, bold=True))
    _draw_rounded_rect(draw, (W // 2 - 90, y + 162, W // 2 + 90, y + 200), 12, (200, 200, 200))
    draw.text((W // 2 - 60, y + 170), "今天 22:14", fill="white", font=_font(22, bold=True))

    # 员工提问(左侧)
    _draw_rounded_rect(draw, (130, y + 240, 200, y + 310), 14, (168, 237, 234))
    draw.text((150, y + 256), "👨", fill="white", font=_font(40))
    _draw_rounded_rect(draw, (220, y + 245, 760, y + 320), 16, "white")
    draw.text((240, y + 263), "姐 那客服明天发招聘?", fill=INK, font=_font(32))

    # 老板回复(右侧 + 绿色气泡 + 红框)
    _draw_rounded_rect(draw, (W - 200, y + 380, W - 130, y + 460), 14, (255, 154, 139))
    draw.text((W - 180, y + 396), "👩", fill="white", font=_font(40))
    _draw_rounded_rect(draw, (260, y + 380, W - 220, y + 510), 18, WECHAT,
                       outline=RED, width=4)
    draw.text((290, y + 405), "店主 L", fill=(90, 140, 64), font=_font(24, bold=True))
    _draw_safe(draw, (290, y + 440), "招人推迟 · 先做个表", INK, _font(46, bold=True))

    # 员工回应
    _draw_rounded_rect(draw, (130, y + 580, 200, y + 650), 14, (168, 237, 234))
    draw.text((150, y + 596), "👩", fill="white", font=_font(40))
    _draw_rounded_rect(draw, (220, y + 585, 700, y + 655), 16, "white")
    draw.text((240, y + 603), "啊?什么表?", fill=INK, font=_font(32))

    # 老板回复 2
    _draw_rounded_rect(draw, (W - 200, y + 720, W - 130, y + 790), 14, (255, 154, 139))
    draw.text((W - 180, y + 736), "👩", fill="white", font=_font(40))
    _draw_rounded_rect(draw, (350, y + 725, W - 220, y + 795), 18, WECHAT)
    draw.text((370, y + 743), "客户问的问题表 · 明早讲", fill=INK, font=_font(32))

    # 引用大字
    draw.text((80, H - 200), '当晚她发了一句:', fill=INK_SOFT, font=_song(36))
    _draw_safe(draw, (80, H - 130), '"招人推迟,先做个表"', RED, _font(48, bold=True))

    return img


# ───────────────────────────────────────────────────────────────────────
# P06: 内核句 · 你不是缺人,你是缺数据
# ───────────────────────────────────────────────────────────────────────
def _gen_page_06() -> Image.Image:
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    draw.text((80, 140), "她那一刻明白了 ——", fill=GRAY, font=_song(46))

    # 大字内核
    y = 360
    draw.text((80, y), "你不是缺", fill=INK, font=_font(140, bold=True))
    # "人" 上画红 ✗ 删除标记(双对角线,避免水平线把"人"变"大")
    ren_x, ren_y = 720, y
    draw.text((ren_x, ren_y), "人", fill=INK, font=_font(140, bold=True))
    cx1, cy1, cx2, cy2 = ren_x - 8, ren_y + 18, ren_x + 138, ren_y + 162
    draw.line([(cx1, cy1), (cx2, cy2)], fill=RED, width=22)
    draw.line([(cx2, cy1), (cx1, cy2)], fill=RED, width=22)

    y += 220
    draw.text((80, y), "你是缺数据", fill=RED, font=_font(140, bold=True))

    # 副解释
    y += 280
    _draw_rounded_rect(draw, (80, y, W - 80, y + 320), 24, (245, 245, 240),
                       outline=LINE_DARK, width=2)
    draw.text((110, y + 30), "招人 ≠ 解决重复问题", fill=ORANGE, font=_font(40, bold=True))
    points = [
        "▸ 人会累 · 数据不累",
        "▸ 人会走 · 数据沉淀下来",
        "▸ 人凭感觉 · 数据看占比",
        "▸ 80% 的问题 · 做 SOP 就能解决",
    ]
    py = y + 100
    for p in points:
        draw.text((130, py), p, fill=INK, font=_font(32))
        py += 56

    draw.text((80, H - 50), "W27D05 · 数据让老板自醒", fill=GRAY, font=_font(22))
    return img


# ───────────────────────────────────────────────────────────────────────
# P07: Excel 模板预览
# ───────────────────────────────────────────────────────────────────────
def _gen_page_07() -> Image.Image:
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    draw.text((80, 100), "我把数法 ——", fill=INK_SOFT, font=_song(46))
    draw.text((80, 180), "做成了 Excel 模板", fill=INK, font=_font(64, bold=True))

    # Excel 仿真
    y = 340
    _draw_rounded_rect(draw, (80, y, W - 80, y + 920), 18, "white",
                       outline=LINE_DARK, width=3)
    # Excel 顶栏(绿色)
    _draw_rounded_rect(draw, (80, y, W - 80, y + 70), 18, (16, 124, 65))
    # 把下半截盖白
    draw.rectangle((80, y + 35, W - 80, y + 70), fill=(16, 124, 65))
    draw.text((110, y + 18), "📊 客户问题归类模板 · 90 天.xlsx",
              fill="white", font=_font(28, bold=True))

    # 表头
    headers = ["日期", "客户原话", "类型", "头部", "占比"]
    col_x = [110, 230, 600, 800, 920]
    col_w = [120, 370, 200, 120, 130]
    by = y + 95
    # 表头背景
    draw.rectangle((100, by, W - 100, by + 60), fill=(232, 244, 236))
    for i, h in enumerate(headers):
        draw.text((col_x[i], by + 16), h, fill=INK, font=_font(28, bold=True))
    by += 64
    rows = [
        ("06-01", "几点关门?", "营业时间", "是", "22%"),
        ("06-02", "团购券能用?", "价格/团购", "是", "18%"),
        ("06-03", "3 点改 4 点?", "改约", "是", "14%"),
        ("06-04", "我家娃能用?", "产品适用", "是", "11%"),
        ("06-05", "上次有问题退?", "退换货", "是", "8%"),
        ("06-06", "你们做团购?", "价格/团购", "是", "18%"),
        ("06-07", "今晚营业吗?", "营业时间", "是", "22%"),
        ("06-08", "停车在哪?", "其他(长尾)", "—", "—"),
    ]
    for r in rows:
        for i, v in enumerate(r):
            is_hi = (i == 3 and v == "是") or (i == 4 and "%" in v)
            color = RED if is_hi else INK
            font = _font(26, bold=is_hi)
            draw.text((col_x[i], by + 12), v, fill=color, font=font)
        draw.line([(100, by + 60), (W - 100, by + 60)], fill=(235, 235, 235), width=1)
        by += 60

    # 底部小字
    draw.text((80, H - 110), "5 列 / 5 分钟一条 / 90 天约 1200+ 行",
              fill=INK, font=_font(36, bold=True))
    draw.text((80, H - 60), "数完头部 5 类占多少,招人的决定就改了",
              fill=GRAY, font=_song(28))
    return img


# ───────────────────────────────────────────────────────────────────────
# P08: CTA · 评论扣"也想数" + 凑 10 个发模板
# ───────────────────────────────────────────────────────────────────────
def _gen_page_08() -> Image.Image:
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    draw.text((80, 100), "你也是 ——", fill=INK_SOFT, font=_song(46))
    draw.text((80, 170), "实体店老板?", fill=INK, font=_font(72, bold=True))

    # 测水方式
    y = 320
    _draw_rounded_rect(draw, (80, y, W - 80, y + 460), 24, (255, 245, 240),
                       outline=ORANGE, width=4)
    draw.text((110, y + 30), "📍 测水 · 3 字门槛", fill=ORANGE, font=_font(36, bold=True))

    # 大字 CTA
    draw.text((110, y + 100), "评论扣", fill=INK, font=_font(56, bold=True))
    draw.text((360, y + 90), '"也想数"', fill=RED, font=_font(72, bold=True))

    # 兑现
    items = [
        "▸ 我把数法发你(微信导出 + AI 归类提示词)",
        "▸ Excel 模板送你(5 列 · 已脱敏)",
        "▸ 凑 10 个发模板 · 不凑齐我自己用",
        "▸ 数完发现头部 5 类不到 6 成 = 你真该招人",
    ]
    iy = y + 220
    for it in items:
        draw.text((130, iy), it, fill=INK, font=_font(32))
        iy += 56

    # 测水统计板
    y = 820
    _draw_rounded_rect(draw, (80, y, W - 80, y + 380), 24, (28, 28, 28))
    draw.text((110, y + 30), "今天测水 · 你算哪一边?", fill=ORANGE, font=_font(36, bold=True))

    # 两栏对照
    draw.text((110, y + 110), "数完头部 ≥ 7 成", fill="white", font=_font(36, bold=True))
    draw.text((110, y + 160), "= 不缺人 · 缺数据", fill=GREEN, font=_font(36, bold=True))

    draw.line([(110, y + 220), (W - 190, y + 220)], fill=(80, 80, 80), width=2)

    draw.text((110, y + 240), "数完头部 < 6 成", fill="white", font=_font(36, bold=True))
    draw.text((110, y + 290), "= 真该招人 · 不是话术能解决",
              fill=RED, font=_font(36, bold=True))

    # 内核 reprise
    draw.text((80, H - 180), '别先招人 ——', fill=INK_SOFT, font=_song(36))
    draw.text((80, H - 110), '先看 90 天群记录', fill=INK, font=_font(46, bold=True))
    draw.text((80, H - 50), "W27D05 · 测水 · 不卖 AI 客服",
              fill=GRAY, font=_font(22))
    return img


# ───────────────────────────────────────────────────────────────────────
# P01: 封面(GPT-image-2 报纸风)
# ───────────────────────────────────────────────────────────────────────
COVER_PROMPT = """
A full-page vertical 2026 Chinese tabloid-zine cover, 2:3 portrait, 1080x1620,
beige off-white paper background with halftone print texture, ink stipple shading,
modern Chinese self-publishing zine aesthetic — like a scrappy, hand-printed
small-business advisory column (mix of crisp serif Chinese typography + visible
halftone red ink accent).

TOP MASTHEAD STRIP (thin black border, sans-serif Chinese + English):
"AI 小系统日报 · THE AGENT TIMES · 2026.07.03 · 老板自醒特刊 · 免费"

MAIN HEADLINE (huge black serif Chinese characters, two lines, ~92pt, bold):
Line 1: "招人这件事"
Line 2: "我建议你先别招"

SUB-HEADLINE (smaller italic Chinese, ~36pt, below the headline):
"母婴店老板让我帮她招客服,我让她先看 3 个月群记录,数完那天她说不用招了"

RED LEAD QUOTE BOX (red background, white Chinese text, mid-left position):
"📍 1247 条客户问题 · 头部 5 类占 7 成多"

CENTER ILLUSTRATION area (large, sketchy 1990s newspaper-style line drawing):
A mid-aged Chinese female shop owner sitting at a small office desk in a baby
goods store backroom, looking down at a laptop screen showing a colorful bar
chart with 5 prominent red bars labeled "营业时间" "价格" "改约" "产品适用"
"退换". Her phone on the desk shows a WeChat group with many unread message
icons. Her notebook beside her has a crossed-out "招人" (recruit) written in red
ink and below it "先做个表" (make a table first) circled in red. Coffee cup,
shelves of baby products behind her. Ink-stipple shading style, 1990s editorial
illustration aesthetic.

SIDE PROPS (around the illustration):
- A red oval newspaper stamp top-right reading '招人推迟' tilted ~-10 degrees
- A small "示意" yellow paper tag near the WeChat phone
- A tiny circular badge bottom-right reading 'W27D05'

BODY TEXT block (lower third, 2-column Chinese newspaper serif body font):
"【本报讯】2026 年 7 月,一名母婴店主原计划招聘专职客服,但在导出 90 天微信
群聊天记录后,AI 归类发现 1247 条客户问题中头部 5 类(营业时间、价格、改约、
产品适用、退换货)占了 7 成多。当晚她在店务群发出"招人推迟,先做个表"。"
(rest as authentic Chinese tabloid filler)

BOTTOM RIGHT CORNER: a circular red wax stamp with bold Chinese characters
"不缺人 缺数据" rotated about -12 degrees, slightly faded ink texture.

Overall: modern Chinese zine/tabloid hybrid, ink stipple halftone print, raw and
honest small-business advisory tone — like an indie business diary you'd find at
a coffee shop in 上海. Mobile-readable typography, vertical aspect ratio for
mobile carousel. DO NOT include any English watermark, signature, or fictional
brand logos. DO NOT use neon purple/pink/cyan colors anywhere — only paper
beige, ink black, red ink #c83030, occasional warm orange.
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
    ap = argparse.ArgumentParser(description="W27D05 小红书 8 张轮播图生成")
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
