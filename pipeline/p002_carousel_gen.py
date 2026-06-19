#!/usr/bin/env python3
"""P002 三版报纸风轮播图批量生成.

输入：v0 / vA / vB 三版脚本的页面文本（内联在本文件，单源真值）
调用：GPT-image-2（gpt-image-2 @ tonbirds）
输出：publish/P002/xhs/{v0,vA,vB}/page_{01..06}.png
     先按 1024x1536（模型原生）生成，再 Pillow 升采样到 1080x1620（保持 2:3，无裁切）

并发：默认串行（API 限流安全），可 --workers N 改并发
重试：每张最多 2 次，失败的记入 failures.log 继续
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import logging
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "publish" / "P002" / "xhs"
RAW_SIZE = "1024x1536"
FINAL_W, FINAL_H = 1080, 1620

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("p002.gen")


# ────────────────────────────────────────────────────────────────────────────
# 每页固定视觉结构（与版本无关）
# ────────────────────────────────────────────────────────────────────────────

PAGE_VISUALS: dict[int, dict[str, str]] = {
    1: {
        "illustration": (
            "central group illustration: five characters lined up like a police lineup "
            "against a height chart wall, each holding a numbered placard 1 to 5. "
            "Left to right: (1) shy nerdy young asian man in white shirt and round glasses, "
            "(2) sophisticated career woman in black tailored suit holding americano, "
            "(3) mysterious tall man in black hoodie with face hidden in shadow, "
            "(4) young woman in cheap knockoff black suit looking embarrassed, "
            "(5) silicon valley tech bro in grey hoodie and white airpods. "
            "Wide group shot, police mugshot lighting from above."
        ),
        "props": "three red oval newspaper stamps in top corners reading '独家' '头版' '号外'",
        "cebar_color": "no 栏目条 (this is the cover)",
    },
    2: {
        "illustration": (
            "tabloid illustration of a shy young asian man, age 22, "
            "white button-up shirt slightly oversized, round wire-rimmed glasses, "
            "soft sad puppy eyes, slight stoop posture, standing slightly behind "
            "looking down at a laptop keyboard. Short black hair side-parted."
        ),
        "props": (
            "RIGHT 1/3: fake VSCode editor screenshot, dark gray #1E1E1E background, "
            "monospace code visible: 'function getUserName() { return user.|  name }', "
            "the gray 'name' word is autocomplete suggestion. "
            "ABOVE CHARACTER: yellow speech bubble with black Chinese text '你是不是想写...这个？'"
        ),
        "cebar_color": "black bar with white Chinese text",
    },
    3: {
        "illustration": (
            "tabloid illustration of a sophisticated career woman, age 28, "
            "black tailored business suit, designer luxury handbag draped on arm, "
            "holding americano coffee cup, confident smirk, sleek bob haircut, "
            "gold earrings, expensive watch, red lipstick. Full body 3/4 view."
        ),
        "props": (
            "RIGHT 1/2: a wall of 6 stacked fake subscription bills with red 'PAID' stamps, "
            "amounts increasing $20 → $40 → $60 → $100 → $150 → $200, "
            "header on each bill reads 'Pro Subscription · 顾氏家族会所'."
        ),
        "cebar_color": "red bar with white Chinese text",
    },
    4: {
        "illustration": (
            "tabloid illustration of a mysterious man, age 30s, "
            "dark hoodie and black baseball cap pulled low, only side silhouette visible, "
            "face completely hidden in deep shadow, muscular forearms exposed, "
            "hands typing on a mechanical keyboard. Single warm desk lamp casts dramatic side shadow. "
            "Noir film aesthetic, paparazzi candid from behind."
        ),
        "props": (
            "RIGHT 1/2: a large dark terminal screenshot, black background #0A0A0A, "
            "green monospace text reads: '$ claude' new line '> Analyzing your codebase...' "
            "new line '> Found 47 issues' new line '> 让我想想... (thinking 47s)' "
            "new line '$ ▌' with blinking cursor."
        ),
        "cebar_color": "black bar with white Chinese text",
    },
    5: {
        "illustration": (
            "tabloid illustration of two women standing awkwardly side by side, "
            "both wearing nearly identical black business suits but one is visibly cheaper. "
            "LEFT (sister 顾): elegant original with designer accessories, confident posture. "
            "RIGHT (sister 温): cheap knockoff with plastic handbag, embarrassed sideways glance. "
            "Side by side comparison, paparazzi caught moment."
        ),
        "props": (
            "BOTTOM HALF: a wall of 5-6 fake weibo comment screenshots stacked at slight angles, "
            "Chinese comments visible like: '姐妹？分明是高仿包啊' / '撞脸不可怕，撞性格还便宜🤣' / "
            "'前 7 天免费，第 8 天破防'."
        ),
        "cebar_color": "pink bar with white Chinese text",
    },
    6: {
        "illustration": (
            "tabloid illustration of a young silicon valley tech bro in grey zip hoodie "
            "and white airpods pro, holding hands with a tired exhausted programmer "
            "in faded company hoodie. The tech bro smiles proudly facing camera; "
            "the programmer's tired eyes wander to the distance with conflicted longing look. "
            "Awkward couple, paparazzi candid."
        ),
        "props": (
            "BELOW THE COUPLE: four old-west style WANTED posters lined up, "
            "each with header 'WANTED · 下一任候选人', a black silhouette, "
            "and a red wax stamp 'NEXT?' overlaid at an angle. "
            "Silhouettes labelled (left to right): G 公子 / 崔少 / 灵码姐 / K 小哥."
        ),
        "cebar_color": "red bar with white Chinese text",
    },
}


# ────────────────────────────────────────────────────────────────────────────
# 三版页面文本（单源真值 · 与 script*.md 对齐）
# ────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PageText:
    page: int
    masthead: str        # 顶部报头一行
    cebar_text: str      # 栏目条文字（P1 留空）
    headline: str        # 主标题（黑色衬线大字）
    subheading: str      # 副标题
    body_lead: str       # 第一段正文（视觉里看得清的那段）
    sidebar_title: str   # 侧栏标题
    sidebar_items: tuple[str, ...]  # 3-4 条
    stamp_text: str      # 右下角红章文字
    extra_note: str = ""  # P1 用作"导语红字"


def _v0() -> tuple[PageText, ...]:
    return (
        PageText(
            page=1,
            masthead="THE OVERTIME TIMES · 打工人日报 · 2026.06.18 星期四 · 第 4748 期 · ¥3.5",
            cebar_text="",
            headline="惊！打工人深夜痛诉",
            subheading="换了 5 个对象，钱包和心都碎了",
            body_lead="【本报讯】记者今晨蹲守某互联网大厂楼下，独家撞见 35 岁码农“小 C”瘫坐马路牙子。据其哭诉，五年内交往 5 任对象，皆为代号神秘的极客圈人物。",
            sidebar_title="本报独家",
            sidebar_items=("码农情感档案", "第 3 任最抓马", "建议从头看"),
            stamp_text="号外",
            extra_note="📍 警告：本文含大量真实暴击，请勿对号入座",
        ),
        PageText(
            page=2,
            masthead="THE OVERTIME TIMES · 2026.06.18",
            cebar_text="情感专栏 · 第 1 任前任 · 2021.10 - 2023.03",
            headline='我的初恋是个"复读机"',
            subheading="暧昧三年，他没主动说过一句完整的话",
            body_lead="【本报追踪】时间拨回 2021 年深秋，多名 VSCode 后巷目击者向本报反映：常有一名白衬衫无框眼镜男子，紧贴某码农小 C 身后半步，从不出声。",
            sidebar_title="分手原因",
            sidebar_items=("只会接话，不会主动", "没有灵魂只有补全", "永远活在我的影子里"),
            stamp_text="已分手",
        ),
        PageText(
            page=3,
            masthead="THE OVERTIME TIMES · 2026.06.18",
            cebar_text="金融版 · 第 2 任前任 · 2023.03 - 2025.02",
            headline="她能让我月入百万",
            subheading="也能让我月光",
            body_lead='【本报金融版】2023 年春，顾氏千金以"$20 包月，全身心都给你"的甜蜜誓言横扫硅谷码农圈，22 个月豪掷 $4,840，相当于一辆二手五菱宏光。',
            sidebar_title="分手原因",
            sidebar_items=("越用越贵", "限额比前任管的还严", "出轨已成为生理需求"),
            stamp_text="钱包警告",
        ),
        PageText(
            page=4,
            masthead="THE OVERTIME TIMES · 2026.06.18",
            cebar_text="社会版 · 第 3 任（出轨对象） · 2025.02 至今 · 仍在交往",
            headline="47 秒沉默之后",
            subheading="这个不露脸的男人，让我尖叫了",
            body_lead="【本报突发 · 凌晨 3:47】K 先生 47 秒后重构小 C 半年烂代码，补齐 12 个测试用例，丢下一句“请确认是否提交”。",
            sidebar_title="恋爱亮点",
            sidebar_items=("不靠界面靠实力", "47 秒重构半年烂代码", "按 token 收费但不杀熟"),
            stamp_text="深夜密会",
        ),
        PageText(
            page=5,
            masthead="THE OVERTIME TIMES · 2026.06.18",
            cebar_text="娱乐版 · 第 4 任前任 · 2025.03 - 2025.04",
            headline='"我是顾小姐的妹妹"',
            subheading="温小妹认亲风波始末",
            body_lead="【本报娱乐快讯】一位自称“顾小姐失散多年妹妹”的女子温小妹携“平价高定”人设强势出道：姐姐能做的，我便宜一半也能做。",
            sidebar_title="分手原因",
            sidebar_items=("复刻款穿搭引尴尬", "免费 7 天后画风突变", "灵魂含量不足 20%"),
            stamp_text="山寨预警",
        ),
        PageText(
            page=6,
            masthead="THE OVERTIME TIMES · 2026.06.18",
            cebar_text="头版连载 · 最新进展 · 2025.04 至今 · 关系待定",
            headline="硅谷归来的 C 少爷",
            subheading="他刚牵我的手，我已在想下一个",
            body_lead='【本报独家 · 昨夜 23:50】C 少爷身着灰连帽衫 + AirPods Pro，开口必带"Let me check..."。下一波相亲对象已排队到 2027 年。',
            sidebar_title="待相亲名单",
            sidebar_items=("G 公子 蹲点小区门口", "字节崔少 微信已加", "阿里灵码姐 主动短信"),
            stamp_text="海王无敌",
        ),
    )


def _vA() -> tuple[PageText, ...]:
    base = list(_v0())
    base[0] = PageText(
        page=1,
        masthead="THE OVERTIME TIMES · 打工人日报 · 2026.06.18 星期四 · 第 4748 期 · ¥3.5",
        cebar_text="",
        headline="5 年谈了 5 个对象",
        subheading="没一个撑过 8 个月",
        body_lead="【本报讯】记者今晨蹲守某互联网大厂楼下，独家撞见 35 岁码农“小 C”瘫坐马路牙子。据其交代，五年内交往 5 任对象，从初恋柯学长到现任 C 少爷。",
        sidebar_title="本报独家",
        sidebar_items=("码农情感档案", "第 3 任最抓马", "建议从头看"),
        stamp_text="号外",
        extra_note="📍 警告：本文含大量真实暴击，请勿对号入座",
    )
    base[2] = PageText(
        page=3,
        masthead="THE OVERTIME TIMES · 2026.06.18",
        cebar_text="金融版 · 第 2 任前任 · 2023.03 - 2025.02",
        headline="她每天给我倒一杯美式",
        subheading="月底给我寄账单",
        body_lead='【本报金融版】2023 年春，顾氏千金以"$20 包月，全身心都给你"横扫硅谷。22 个月豪掷 $4,840，折合一辆二手五菱宏光。',
        sidebar_title="分手原因",
        sidebar_items=("越用越贵", "限额比前任管得还严", "出轨已成为生理需求"),
        stamp_text="钱包警告",
    )
    base[3] = PageText(
        page=4,
        masthead="THE OVERTIME TIMES · 2026.06.18",
        cebar_text="社会版 · 第 3 任（出轨对象） · 2025.02 至今 · 仍在交往",
        headline="47 秒的沉默之后",
        subheading="这个不露脸的男人，让我闭嘴了",
        body_lead="【本报突发 · 凌晨 3:47】K 先生 47 秒后一口气重构小 C 半年的烂摊子代码，补齐 12 个测试用例，丢下一句“请确认是否提交”。",
        sidebar_title="恋爱亮点",
        sidebar_items=("不靠界面靠实力", "47 秒重构半年烂代码", "按 token 收费但不杀熟"),
        stamp_text="深夜密会",
    )
    return tuple(base)


def _vB() -> tuple[PageText, ...]:
    base = list(_v0())
    base[0] = PageText(
        page=1,
        masthead="THE OVERTIME TIMES · 打工人日报 · 2026.06.18 星期四 · 第 4748 期 · ¥3.5",
        cebar_text="",
        headline="惊！打工人深夜痛诉",
        subheading="换了 5 个对象，钱包和心都碎了",
        body_lead="【本报讯】记者蹲守某大厂楼下撞见 35 岁码农小 C 瘫坐马路牙子，怀里抱着没喝完的瑞幸生椰拿铁。五任前任今日同框曝光——其中一位至今未露过脸。",
        sidebar_title="本报独家",
        sidebar_items=("第 3 任最抓马", "第 5 任最不要脸", "建议备好速效救心丸"),
        stamp_text="号外",
        extra_note="📍 警告：35 岁以上码农建议备好速效救心丸",
    )
    base[1] = PageText(
        page=2,
        masthead="THE OVERTIME TIMES · 2026.06.18",
        cebar_text="情感专栏 · 第 1 任前任 · 2021.10 - 2023.03",
        headline='我的初恋是个"复读机"',
        subheading="暧昧三年，他没主动说过一句完整的话",
        body_lead='【本报追踪】2021 年深秋，多名 VSCode 后巷目击者反映：常有一名白衬衫无框眼镜男子，紧贴码农小 C 身后半步，从不出声，只飘出半句话："你是不是想写...这个？"',
        sidebar_title="分手原因",
        sidebar_items=("只会接话，从不主动", "三年没说完一句话", "月供 $10，靠脸吃饭", "永远活在我的影子里"),
        stamp_text="已分手",
    )
    base[2] = PageText(
        page=3,
        masthead="THE OVERTIME TIMES · 2026.06.18",
        cebar_text="金融版 · 本报金融版资深记者 钱多多 报道 · 2023.03 - 2025.02",
        headline="她能让我月入百万",
        subheading="也能让我月光",
        body_lead='【本报金融版】顾氏千金以"$20 包月"横扫硅谷。22 个月豪掷 $4,840，折合一辆二手五菱宏光，或 484 杯瑞幸生椰拿铁，或 161 次理发——而小 C 这两年只理过 3 次头。',
        sidebar_title="分手原因",
        sidebar_items=("月费 $20 起，Ultra $200 封顶", "限额比前任管钱还严", "22 个月烧掉一辆五菱", "出轨已成生理需求"),
        stamp_text="钱包警告",
    )
    base[3] = PageText(
        page=4,
        masthead="THE OVERTIME TIMES · 2026.06.18",
        cebar_text="号外 · 凌晨突发 · 本报情感版主笔 老 K 现场连线",
        headline="47 秒沉默之后",
        subheading="这个不露脸的男人，让我尖叫了",
        body_lead="【本报突发 · 凌晨 3:47】K 先生 47 秒后重构小 C 半年烂代码，顺手关掉了柯学长那条挂了三年的 // TODO: 你是不是想分... 附注一句：楼上想说的应该是分手。",
        sidebar_title="恋爱亮点",
        sidebar_items=("47 秒重构半年烂代码", "顺手关掉前任挂三年的 TODO", "不靠 npm，他就是 npm", "按 token 收费但不杀熟"),
        stamp_text="深夜密会",
    )
    base[4] = PageText(
        page=5,
        masthead="THE OVERTIME TIMES · 2026.06.18",
        cebar_text="娱乐版 · 本报记者已蹲守该女子家门 47 小时未眨眼 · 2025.03 - 2025.04",
        headline='"我是顾小姐的妹妹"',
        subheading="温小妹认亲风波，DNA 都对不上",
        body_lead='【本报娱乐】温小妹自称顾家失散多年妹妹："姐姐 $20 我只要 $9.9，前 7 天还免费。"本报金融版会计师吐槽：姓氏都不一样，DNA 也对不上——唯一一致的是月费打了 5 折。',
        sidebar_title="分手原因",
        sidebar_items=("复刻款穿搭引尴尬", "前 7 天免费，第 8 天连弹 14 次", "灵魂含量仅顾小姐的 40%", "但价格 50%，性价比尚可"),
        stamp_text="山寨预警",
    )
    base[5] = PageText(
        page=6,
        masthead="THE OVERTIME TIMES · 2026.06.19 凌晨 · 第 4749 期 · ¥7.0（被迫提价）",
        cebar_text="头版连载 · 凌晨值班记者（已无意识）发回最新进展",
        headline="硅谷归来的 C 少爷",
        subheading="他刚牵我的手，已在替我投简历",
        body_lead='【本报独家 · 昨夜 23:50】C 少爷开口必带"Let me check..."，紧接着炫家世三连："我爹是 GPT，大哥是 ChatGPT，表姐是 Sora。"狗仔抓拍到他左手已擅自把小 C 简历改成英文版投了 5 家硅谷大厂。',
        sidebar_title="待相亲名单",
        sidebar_items=("G 公子 蹲点小区门口", "字节崔少 微信已加", "阿里灵码姐 主动短信"),
        stamp_text="海王无敌",
    )
    return tuple(base)


VERSIONS: dict[str, tuple[PageText, ...]] = {
    "vA": _vA(),
    "v0": _v0(),
    "vB": _vB(),
}


# ────────────────────────────────────────────────────────────────────────────
# Prompt 组装
# ────────────────────────────────────────────────────────────────────────────

PROMPT_TEMPLATE = """
A full-page vertical 1990s Chinese tabloid newspaper layout, 2:3 portrait,
beige off-white paper background with halftone print texture, ink stipple shading,
slightly desaturated sepia tone, vintage 1990s gossip magazine aesthetic.

TOP MASTHEAD STRIP (thin black border, sans-serif Chinese + English):
{masthead}

{cebar_block}

MAIN HEADLINE (large black serif Chinese characters, bold, ~80pt):
"{headline}"

SUB-HEADLINE (smaller italic Chinese, ~36pt):
"{subheading}"

{extra_note_block}

CENTER ILLUSTRATION area:
{illustration}

SIDE PROPS:
{props}

BODY TEXT block (Chinese newspaper serif body 报宋 font, 2-column lower half):
"{body_lead}"
(rest of paragraph should appear as authentic-looking Chinese tabloid filler text)

RIGHT SIDEBAR (red box with white Chinese title, bullet items with ▸):
title: "{sidebar_title}"
items:
{sidebar_items}

BOTTOM RIGHT CORNER: a circular red wax stamp 印章 with bold Chinese characters
"{stamp_text}" rotated about -12 degrees, slightly faded ink texture.

Overall: authentic Chinese 1990s gossip tabloid, ink stipple halftone print,
mobile-readable typography, vertical aspect ratio for mobile carousel.
DO NOT include any English watermarks or signature.
""".strip()


def _build_prompt(page_text: PageText) -> str:
    visuals = PAGE_VISUALS[page_text.page]
    cebar_block = ""
    if page_text.cebar_text:
        cebar_block = (
            f"COLUMN BAR (栏目条, {visuals['cebar_color']}, full-width):\n"
            f'"{page_text.cebar_text}"\n'
        )
    extra_note_block = ""
    if page_text.extra_note:
        extra_note_block = (
            f"\nRED LEAD QUOTE BOX (red background, white Chinese text):\n"
            f'"{page_text.extra_note}"\n'
        )
    items_text = "\n".join(f"  ▸ {it}" for it in page_text.sidebar_items)
    return PROMPT_TEMPLATE.format(
        masthead=page_text.masthead,
        cebar_block=cebar_block,
        headline=page_text.headline,
        subheading=page_text.subheading,
        extra_note_block=extra_note_block,
        illustration=visuals["illustration"],
        props=visuals["props"],
        body_lead=page_text.body_lead,
        sidebar_title=page_text.sidebar_title,
        sidebar_items=items_text,
        stamp_text=page_text.stamp_text,
    )


# ────────────────────────────────────────────────────────────────────────────
# 调 API + 写盘
# ────────────────────────────────────────────────────────────────────────────

def _client() -> OpenAI:
    load_dotenv(ROOT / ".env")
    api_key = os.environ["GPT_IMAGE_API_KEY"]
    base_url = os.environ["GPT_IMAGE_BASE_URL"]
    return OpenAI(api_key=api_key, base_url=base_url, timeout=300.0, max_retries=2)


def _decode(resp_data) -> bytes:
    first = resp_data[0]
    b64 = getattr(first, "b64_json", None)
    if b64:
        return base64.b64decode(b64)
    url = getattr(first, "url", None)
    if url:
        with urllib.request.urlopen(url) as r:
            return r.read()
    raise RuntimeError(f"无 b64_json/url：{first!r}")


def _upscale_to_final(png_bytes: bytes) -> bytes:
    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    final = img.resize((FINAL_W, FINAL_H), Image.LANCZOS)
    buf = io.BytesIO()
    final.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def gen_one(client: OpenAI, model: str, version: str, page_text: PageText, retries: int = 4) -> tuple[str, int, bool, str]:
    out = OUT_DIR / version / f"page_{page_text.page:02d}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    prompt = _build_prompt(page_text)
    last_err = ""
    for attempt in range(1, retries + 2):
        try:
            t0 = time.time()
            resp = client.images.generate(
                model=model,
                prompt=prompt,
                size=RAW_SIZE,
                n=1,
            )
            raw = _decode(resp.data)
            png = _upscale_to_final(raw)
            out.write_bytes(png)
            dt = time.time() - t0
            log.info("  ✓ %s/P%d (%.1fs, %d KB) attempt=%d", version, page_text.page, dt, len(png) // 1024, attempt)
            return version, page_text.page, True, ""
        except Exception as exc:  # noqa: BLE001 - 重试任何异常
            last_err = f"{type(exc).__name__}: {exc}"
            log.warning("  ✗ %s/P%d attempt=%d failed: %s", version, page_text.page, attempt, last_err)
            time.sleep(5 * attempt)
    return version, page_text.page, False, last_err


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=1, help="并发数（默认 1 = 串行）")
    ap.add_argument("--only", nargs="*", default=None,
                    help="只生成指定 version 或 version:page，如 vA 或 vA:1")
    args = ap.parse_args()

    client = _client()
    model = os.environ.get("GPT_IMAGE_MODEL", "gpt-image-1")
    log.info("model=%s base_url=%s out=%s", model, os.environ["GPT_IMAGE_BASE_URL"], OUT_DIR)

    tasks: list[tuple[str, PageText]] = []
    only_versions: set[str] = set()
    only_pages: set[tuple[str, int]] = set()
    if args.only:
        for tok in args.only:
            if ":" in tok:
                v, p = tok.split(":", 1)
                only_pages.add((v, int(p)))
            else:
                only_versions.add(tok)
    for v, pages in VERSIONS.items():
        for pt in pages:
            if args.only:
                if v in only_versions or (v, pt.page) in only_pages:
                    tasks.append((v, pt))
            else:
                tasks.append((v, pt))

    log.info("准备生成 %d 张图，并发=%d", len(tasks), args.workers)

    results: list[tuple[str, int, bool, str]] = []
    if args.workers == 1:
        for v, pt in tasks:
            results.append(gen_one(client, model, v, pt))
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = [ex.submit(gen_one, client, model, v, pt) for v, pt in tasks]
            for f in as_completed(futs):
                results.append(f.result())

    ok = sum(1 for _, _, s, _ in results if s)
    fail = [(v, p, e) for v, p, s, e in results if not s]
    log.info("完成 %d/%d", ok, len(results))
    if fail:
        fail_log = OUT_DIR / "failures.log"
        with fail_log.open("w") as f:
            for v, p, e in fail:
                f.write(f"{v}\tP{p}\t{e}\n")
        log.warning("失败 %d 张，详情：%s", len(fail), fail_log)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
