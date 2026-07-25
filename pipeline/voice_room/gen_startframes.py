#!/usr/bin/env python3
"""语音厅 MV · gpt-image-2 出 S1/S2/S3 起始帧（16:9 · 1920×1080）.

- S1/S2 无角色 → images.generate（纯文本）
- S3 需 cy 一致性 → images.edit 传 cy_cutout.png 作参考
- 中转：tonbirds（GPT_IMAGE_BASE_URL）· 原生 1536×1024 → 升采样 1920×1080
- 存 publish/语音厅/script_v2_assets/frames/S{01,02,03}_startframe.png

prompt 摘自 script_v2.md，去掉 [attach ...] 元注（参考图走 image 参数）。
"""
from __future__ import annotations

import base64
import io
import os
import sys
import time
import urllib.request
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "publish" / "语音厅" / "script_v2_assets"
CUTOUT_DIR = ASSETS
OUT_DIR = ASSETS / "frames"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RAW_SIZE = "1536x1024"  # gpt-image-2 原生 16:9
FINAL_W, FINAL_H = 1920, 1080

S1_PROMPT = """Cinematic 16:9, extreme close-up of a horizontal smartphone screen held by \
a woman's slender right hand (only fingertips visible in lower-right quadrant, \
cream silk pajama sleeve), her hand emerging from a soft cream duvet edge. \
The phone screen shows an elegant ink-wash moon on cream paper background, \
with delicate golden vertical calligraphy characters. Early dawn window light \
from upper-left, 5500K, very soft. Background: blurred bedside — cream linen sheets, \
wooden bedframe edge, dawn light bloom from window. Warm cream (#f8f4ea) and \
pale gold (#d4af37) palette. Shot on Kodak Portra 400 film, natural window light, \
handheld documentary. Shallow depth of field f/1.4, 85mm lens. \
NO neon purple, NO dark canvas, NO cold blue tint, NO cyberpunk lighting."""

S2_PROMPT = """Cinematic 16:9, POV waking shot from bed pillow height. Foreground blurry cream \
pillow edge lower 1/5. Wide floor-to-ceiling window dominates upper 2/3, \
warm dawn light streaming in 5500K. Modern minimalist Chinese apartment interior: \
wooden herringbone floor, cream linen sofa on right, wooden dining table center \
with empty ceramic coffee cup on saucer, a small vase with 3 white peonies. \
Window overlooks a distant misty mountain and river skyline at dawn (soft haze). \
Sheer white linen curtain half-drawn on left, gently billowing. \
Palette: cream #f8f4ea, warm wood #c9a878, pale gold #d4af37, sky pale blue-green \
#b8d4e3 (only in distant sky, not saturated). Shot on Kodak Portra 400. \
Handheld documentary intimacy. 35mm equiv, f/2.8. \
NO dark room, NO neon, NO overhead artificial lights on, NO cyberpunk, \
NO cold blue tint anywhere except distant sky haze."""

S3_PROMPT = """Cinematic 16:9, modern Chinese apartment kitchen island in warm morning light. \
Right foreground: the young man from the reference image (silver-white hair swept back, \
sharp features, pale skin) — KEEP his exact face and hair from the reference — \
wearing a crisp white oxford shirt tucked into black tailored trousers, \
sleeves rolled to forearm, standing at a wooden kitchen island. His body angled \
3/4 away from camera (facing island), his right hand carefully placing a glass \
pour-over carafe onto a wooden dining table just in front of him. Steam rising \
from a ceramic coffee cup already on the table. His face in profile, calm expression. \
Background: modern living room — floor-to-ceiling window with dawn light, \
sheer curtain, wooden herringbone floor, cream sofa (blurred in background). \
Left foreground: soft-focused blur of a cream throw blanket edge draped over sofa arm. \
Palette cream #f8f4ea, wood #c9a878, subtle gold reflections on carafe. \
Shot on Kodak Portra 400, natural window light 5500K, handheld intimacy. \
50mm lens, f/2.0, shallow DOF on foreground blanket. \
NO dark room, NO black cape, NO black vest, NO neon, NO cold blue tint, \
NO purple, NO Dracula palette, NO arms-crossed pose (he must be reaching to the table)."""

# (slug, prompt, reference cutout filename or None)
SHOTS = [
    ("S1", S1_PROMPT, None),
    ("S2", S2_PROMPT, None),
    ("S3", S3_PROMPT, "cy_ref.png"),
]


def _decode(first) -> bytes:
    b64 = getattr(first, "b64_json", None)
    if b64:
        return base64.b64decode(b64)
    url = getattr(first, "url", None)
    if url:
        with urllib.request.urlopen(url) as r:  # noqa: S310
            return r.read()
    raise RuntimeError(f"无 b64_json/url: {first!r}")


def _upscale(png_bytes: bytes) -> bytes:
    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    final = img.resize((FINAL_W, FINAL_H), Image.LANCZOS)
    buf = io.BytesIO()
    final.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def gen_shot(client: OpenAI, model: str, slug: str, prompt: str,
             ref: str | None, retries: int = 4) -> bool:
    out = OUT_DIR / f"{slug}_startframe.png"
    ref_path = CUTOUT_DIR / ref if ref else None
    if ref_path and not ref_path.exists():
        print(f"[err] {slug} 参考图缺失: {ref_path}")
        return False

    for attempt in range(1, retries + 2):
        handle = None
        try:
            t0 = time.time()
            if ref_path:
                handle = open(ref_path, "rb")
                resp = client.images.edit(
                    model=model, image=handle, prompt=prompt,
                    size=RAW_SIZE, n=1,
                )
            else:
                resp = client.images.generate(
                    model=model, prompt=prompt, size=RAW_SIZE, n=1,
                )
            raw = _decode(resp.data[0])
            out.write_bytes(_upscale(raw))
            dt = time.time() - t0
            print(f"[ok] {slug}_startframe.png ({dt:.0f}s, {out.stat().st_size // 1024} KB)"
                  f"{' [ref=' + ref + ']' if ref else ''}")
            return True
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] {slug} attempt {attempt} 失败: {type(exc).__name__}: {exc}")
            time.sleep(5 * attempt)
        finally:
            if handle:
                handle.close()
    print(f"[err] {slug} 全部重试失败")
    return False


def main() -> int:
    load_dotenv(ROOT / ".env")
    api_key = os.environ["GPT_IMAGE_API_KEY"]
    base_url = os.environ["GPT_IMAGE_BASE_URL"].rstrip("/")
    if not base_url.endswith("/v1"):
        base_url += "/v1"
    model = os.environ.get("GPT_IMAGE_MODEL", "gpt-image-2")
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=300.0, max_retries=2)
    print(f"[info] model={model} base_url={base_url} out={OUT_DIR}")

    only = sys.argv[1:] or None
    ok = 0
    todo = [s for s in SHOTS if not only or s[0] in only]
    for slug, prompt, ref in todo:
        if gen_shot(client, model, slug, prompt, ref):
            ok += 1
    print(f"[done] {ok}/{len(todo)} 起始帧完成 → {OUT_DIR}")
    return 0 if ok == len(todo) else 1


if __name__ == "__main__":
    sys.exit(main())
