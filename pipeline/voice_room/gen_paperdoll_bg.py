#!/usr/bin/env python3
"""纸片人卡点 MV · 通用背景 plate 生成器（gpt-image-2 出插画级最终背景，16:9 · 1920×1080）.

为什么存在：PIL 现搓渐变+blur 多边形背景一眼廉价，与插画级立绘材质不匹配
（见 memory feedback_no-cheap-procedural-background）。改为直接用 gpt-image-2 生成
插画级背景当最终底，立绘 + 卡点动效叠其上——省事、省时、效果与立绘同级。

这是**通用工具**：提示词是片专属素材（放各片 prompts/ 目录），传参调用即可复用。
- 纯文本 generate（背景无人物，立绘是后叠层）
- 中转 tonbirds · 原生 1536x1024 → 升采样 1920x1080
- prompt 须全暖 · 禁蓝紫 · 禁冷 · 禁深色画布 · 中下部留空给立绘站位

用法：
    python3 gen_paperdoll_bg.py --prompt-file prompts/bg_mingyue.txt \\
        --out publish/语音厅/script_v2_assets/pv/bg_mingyue.png
    python3 gen_paperdoll_bg.py --prompt "warm ink-wash night ..." --out /tmp/bg.png
"""
from __future__ import annotations

import argparse
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

RAW_SIZE = "1536x1024"          # gpt-image-2 原生 16:9
FINAL_W, FINAL_H = 1920, 1080


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


def gen_bg(client: OpenAI, model: str, out: Path, prompt: str, retries: int = 4) -> bool:
    out.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(1, retries + 2):
        try:
            t0 = time.time()
            resp = client.images.generate(model=model, prompt=prompt, size=RAW_SIZE, n=1)
            out.write_bytes(_upscale(_decode(resp.data[0])))
            print(f"[ok] {out.name} ({time.time() - t0:.0f}s, {out.stat().st_size // 1024} KB)")
            return True
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] attempt {attempt} 失败: {type(exc).__name__}: {exc}")
            time.sleep(5 * attempt)
    print(f"[err] {out.name} 全部重试失败")
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description="gpt-image-2 背景 plate 生成器")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--prompt-file", type=Path, help="提示词文本文件路径")
    src.add_argument("--prompt", type=str, help="提示词内联文本")
    ap.add_argument("--out", type=Path, required=True, help="输出 png 路径")
    args = ap.parse_args()

    prompt = (args.prompt_file.read_text().strip() if args.prompt_file else args.prompt)
    if not prompt:
        sys.exit("[err] 提示词为空")

    load_dotenv(ROOT / ".env")
    api_key = os.environ["GPT_IMAGE_API_KEY"]
    base_url = os.environ["GPT_IMAGE_BASE_URL"].rstrip("/")
    if not base_url.endswith("/v1"):
        base_url += "/v1"
    model = os.environ.get("GPT_IMAGE_MODEL", "gpt-image-2")
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=300.0, max_retries=2)
    print(f"[info] model={model} base_url={base_url} out={args.out}")

    return 0 if gen_bg(client, model, args.out, prompt) else 1


if __name__ == "__main__":
    sys.exit(main())
