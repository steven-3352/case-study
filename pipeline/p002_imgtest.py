#!/usr/bin/env python3
"""P002 角色生图 · 接口连通性测试.

跑 1 张柯学长肖像，验证 GPT-image API 能通。
成功后输出到 publish/P002/xhs/assets/test_keshu.png。
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
log = logging.getLogger("p002.imgtest")


KESHU_PROMPT = (
    "tabloid newspaper illustration of a shy young asian man, age 22, "
    "white button-up shirt slightly oversized, round wire-rimmed glasses, "
    "soft sad puppy eyes, gentle smile, slight stoop posture, "
    "standing slightly behind a desk looking down at a laptop keyboard, "
    "short black hair side-parted neatly, no confidence in his eyes, "
    "vintage halftone print, ink stipple shading, slightly desaturated, "
    "1990s gossip magazine portrait, full body 3/4 view, white background"
)


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
    out = ASSETS_DIR / "test_keshu.png"

    log.info("model=%s base_url=%s", model, base_url)
    log.info("生成测试图：柯学长（cheapest 试通）...")
    try:
        resp = client.images.generate(
            model=model,
            prompt=KESHU_PROMPT,
            size="1024x1024",
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

    log.info("✓ 测试图已写入 %s (%s bytes)", out, out.stat().st_size)
    return 0


if __name__ == "__main__":
    sys.exit(main())
