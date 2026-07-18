#!/usr/bin/env python3
"""D06 测试项目 · GPT-image-2 出日式动漫风格人物,替换原古风MV前15秒画面.

原片 publish/2026-W30/D06/5cb1ed3798646bfe3638707510040f0d.mp4 是古风翻唱MV
(640x368≈16:9)。本脚本只出前15.1s对应的3张关键帧图(4个卡点分段共用),
角色贯穿同一人设,风格改为日系赛璐璐动漫,画幅16:9。

出图规格:1536x1024(gpt-image-2 landscape 原生尺寸,后续用 ffmpeg crop 到 640x368 比例对齐原片)。
"""
from __future__ import annotations

import base64
import logging
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tmp" / "d06_anime_test" / "images"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("d06.anime")


# 人设锚点(全片共用,保证3张图是同一个角色)
CHARACTER_ANCHOR = """
A young bishounen male anime character, appears in his early 20s.
Long flowing silver-lavender hair past his shoulders with a few loose
strands framing his face, sharp gentle eyes with warm amber-gold irises,
fair pale skin, elegant androgynous features. Wearing a pale blue-and-white
flowing hanfu-inspired robe with subtle floral embroidery along the collar
and sleeves, a thin dark sash at the waist.

Art style: high-budget Japanese theatrical anime film style (like Kyoto
Animation / Ufotable key visual quality), clean bold cel-shaded linework,
soft cinematic rim lighting, painterly backgrounds, NOT 3D render, NOT
Chinese guochuang illustration style — distinctly Japanese anime look.
""".strip()


@dataclass(frozen=True)
class Shot:
    slug: str
    covers_s: str  # 覆盖的原片时间段,注释用
    prompt: str
    label: str


SHOTS: tuple[Shot, ...] = (
    Shot(
        slug="01_moon_portrait",
        covers_s="0.0-8.0s",
        label="月下樱花人像特写",
        prompt=f"""
{CHARACTER_ANCHOR}

Composition: close-up bust portrait, centered, looking down gently with
a serene calm expression, eyes half-closed. Behind him a huge glowing
full moon fills the frame like a soft halo. Cherry blossom branches
frame both edges of the frame, pink petals drifting through the air in
soft bokeh. Dreamy heavy bloom/glow diffusion over the whole image,
pastel pink and white palette, romantic nostalgic mood. 16:9 landscape
cinematic frame, no text, no watermark.
""".strip(),
    ),
    Shot(
        slug="02_petal_transition",
        covers_s="8.0-10.7s",
        label="花瓣飞舞过渡镜",
        prompt=f"""
{CHARACTER_ANCHOR}

Composition: same character, medium shot, partially obscured by a dense
flurry of wind-blown cherry blossom petals sweeping across the frame,
motion blur on the petals suggesting a gust of wind. A fragment of the
moon glows softly at the edge of frame. Warmer pink-orange tones mixed
with the cool moonlight, dynamic diagonal composition suggesting movement.
16:9 landscape cinematic frame, no text, no watermark.
""".strip(),
    ),
    Shot(
        slug="03_courtyard_wide",
        covers_s="10.7-15.1s",
        label="夜色庭院全身建立镜",
        prompt=f"""
{CHARACTER_ANCHOR}

Composition: full-body wide establishing shot, character standing
gracefully in a traditional East-Asian palace courtyard at night. Dark
wooden pavilion silhouettes with glowing paper lanterns in the
background, a cherry blossom tree beside him dropping petals, a large
moon in the night sky above the rooftops. His robe and long hair caught
mid-flow by a gentle breeze, elegant confident standing pose, weight on
one leg, looking off into the distance. Cool night blues contrasted with
warm lantern light and pink blossoms. 16:9 landscape cinematic frame,
no text, no watermark.
""".strip(),
    ),
)


def generate_one(client: OpenAI, model: str, shot: Shot, out_dir: Path) -> Path | None:
    out = out_dir / f"{shot.slug}.png"
    log.info("生图: %s (%s) → %s", shot.label, shot.covers_s, out.name)

    max_retries = 4
    for attempt in range(1, max_retries + 1):
        try:
            resp = client.images.generate(
                model=model,
                prompt=shot.prompt,
                size="1536x1024",
                n=1,
            )
        except Exception as exc:
            log.warning("尝试 %d/%d 失败: %s", attempt, max_retries, exc)
            if attempt < max_retries:
                time.sleep(5)
                continue
            log.error("放弃 %s（%d 次全败）", shot.label, max_retries)
            return None

        if not resp.data:
            log.error("返回 data 为空: %s", resp)
            return None

        first = resp.data[0]
        if getattr(first, "b64_json", None):
            out.write_bytes(base64.b64decode(first.b64_json))
        elif getattr(first, "url", None):
            import urllib.request

            with urllib.request.urlopen(first.url) as r:  # noqa: S310
                out.write_bytes(r.read())
        else:
            log.error("无 b64_json 也无 url: %s", first)
            return None

        log.info("✓ %s (%s bytes)", out, out.stat().st_size)
        return out

    return None


def main() -> int:
    load_dotenv(ROOT / ".env")
    api_key = os.environ.get("GPT_IMAGE_API_KEY") or os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("GPT_IMAGE_BASE_URL") or os.environ.get("OPENAI_BASE_URL")
    model = os.environ.get("GPT_IMAGE_MODEL") or os.environ.get(
        "OPENAI_IMAGE_MODEL", "gpt-image-2"
    )
    if not api_key or not base_url:
        log.error("缺 GPT_IMAGE_API_KEY 或 GPT_IMAGE_BASE_URL（查 .env）")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    client = OpenAI(api_key=api_key, base_url=base_url)

    log.info("model=%s · out=%s · 共 %d 张", model, OUT_DIR, len(SHOTS))
    results: list[Path | None] = [generate_one(client, model, s, OUT_DIR) for s in SHOTS]

    ok = sum(1 for r in results if r is not None)
    log.info("完成: %d/%d 成功", ok, len(SHOTS))
    return 0 if ok == len(SHOTS) else 5


if __name__ == "__main__":
    sys.exit(main())
