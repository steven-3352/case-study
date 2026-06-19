#!/usr/bin/env python3
"""P002 中文渲染测试 · P2 柯学长报纸版面.

用 v0 基线里的真实中文标题/正文跑一张 1024x1536（接近 9:16）整版图，
评估 gpt-image-2 对中文的渲染质量。
"""
from __future__ import annotations

import base64
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = ROOT / "publish" / "P002" / "xhs" / "assets"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("p002.cn_test")


P2_PROMPT = """
A full-page 1990s Chinese tabloid newspaper layout, vertical 9:16 portrait,
beige off-white paper background with halftone print texture, ink stipple shading.

TOP STRIP (red bar, white Chinese text):
"情感专栏 · 第 1 任前任 · 2021.10 - 2023.03"

HEADLINE (large black serif Chinese characters, 思源宋体 Heavy):
"我的初恋是个"复读机""
subheading (smaller, italic Chinese):
"暧昧三年，他没主动说过一句完整的话"

CENTER ILLUSTRATION (left 2/3):
tabloid illustration of a shy young asian man, age 22,
white button-up shirt slightly oversized, round wire-rimmed glasses,
soft sad puppy eyes, gentle smile, slight stoop posture,
standing slightly behind a desk looking down at a laptop keyboard,
short black hair side-parted, vintage halftone ink stipple shading,
1990s gossip magazine portrait style.

DIALOGUE BUBBLE above his head (yellow background, black Chinese text):
"你是不是想写...这个？"

RIGHT 1/3: fake VSCode code editor screenshot, dark gray #1E1E1E background,
gray line numbers, monospace text showing:
"function getUserName() {
  return user.|
            name
}"
the gray "name" being autocomplete suggestion.

BODY TEXT (Chinese newspaper body 报宋 font, two-column):
"【本报追踪】时间拨回 2021 年深秋，多名 VSCode 后巷目击者向本报反映：
常有一名白衬衫无框眼镜男子，紧贴某码农小 C 身后半步，从不出声..."

RIGHT SIDEBAR (red box, white Chinese text, "分手原因"):
▸ 只会接话，不会主动
▸ 没有灵魂只有补全
▸ 永远活在我的影子里

BOTTOM RIGHT: red round stamp 印章 with Chinese characters "已分手"
rotated -12 degrees, slightly faded ink texture.

NEWSPAPER MASTHEAD at top: "THE OVERTIME TIMES · 打工人日报 · 2026.06.18"

Style: authentic 1990s Chinese gossip tabloid, slightly desaturated, sepia tone,
ink stipple halftone print texture, vertical aspect ratio for mobile carousel.
""".strip()


def main() -> int:
    load_dotenv(ROOT / ".env")
    api_key = os.environ.get("GPT_IMAGE_API_KEY")
    base_url = os.environ.get("GPT_IMAGE_BASE_URL")
    model = os.environ.get("GPT_IMAGE_MODEL", "gpt-image-1")
    if not api_key or not base_url:
        log.error("缺 GPT_IMAGE_API_KEY 或 GPT_IMAGE_BASE_URL")
        return 1

    client = OpenAI(api_key=api_key, base_url=base_url)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    out = ASSETS_DIR / "test_p2_chinese.png"

    log.info("model=%s 测试中文渲染（P2 柯学长整版）...", model)
    try:
        resp = client.images.generate(
            model=model,
            prompt=P2_PROMPT,
            size="1024x1536",
            n=1,
        )
    except Exception as exc:
        log.exception("生图失败：%s", exc)
        return 2

    if not resp.data:
        log.error("返回 data 为空：%s", resp)
        return 3

    first = resp.data[0]
    if getattr(first, "b64_json", None):
        out.write_bytes(base64.b64decode(first.b64_json))
    elif getattr(first, "url", None):
        import urllib.request
        with urllib.request.urlopen(first.url) as r:
            out.write_bytes(r.read())
    else:
        log.error("既无 b64_json 也无 url：%s", first)
        return 4

    log.info("✓ 中文测试图已写入 %s (%s bytes)", out, out.stat().st_size)
    return 0


if __name__ == "__main__":
    sys.exit(main())
