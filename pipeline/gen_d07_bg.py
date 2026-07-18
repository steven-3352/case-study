#!/usr/bin/env python3
"""D07 · 男厅《明月天涯》立绘卡点 MV · 4 张纯背景板 (无角色).

客户借用能力单,与项目主旨分线(见 publish/2026-W30/D07/production_plan.md §4.1)。

对应 production_plan.md §5 交付清单「背景 4 张」:
  山夜 / 断桥雨 / 长街酒肆 / 山顶月,各 1 张,1920x1080,不含任何角色,
  给剪映做转场/空镜/视差底层用。

复用 gen_d07_stills.py 的水墨风格锚 + 调色板锁,但走纯文生图
(/v1/images/generations),不挂角色参考图。
"""
from __future__ import annotations

import base64
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tmp" / "d07_moon" / "bg"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("d07.moon.bg")


STYLE = """
Style: Chinese ink-wash (水墨) wuxia landscape illustration, empty scene,
NO people, NO characters, NO figures anywhere in frame. Painterly rice-paper
texture, calligraphy brush strokes, soft cyan-gray (青灰) tonal wash, black
ink deep shadows, negative-space composition typical of Song-Dynasty ink
painting. Cinematic wide landscape framing suitable as a static background
plate / parallax layer.
""".strip()

PALETTE = """
Color palette: monochrome black and white with restrained celadon-cyan (青灰)
accents only. Ink black #000, paper white #F5F1E8, celadon gray-cyan
#5F7A7A / #8FA5A5. NO neon, NO saturated pink or purple, NO golden glow,
NO orange sunset, NO cyberpunk RGB. Moonlight highlights allowed.
""".strip()

NEG = """
Absolutely NO: any human figure, any silhouette of a person, NO burned-in
Chinese text or subtitles, NO large kinetic typography, NO DV/REC viewfinder
UI frame, NO recording HUD overlays, NO watermark, NO signature. NO neon
purple, NO neon pink, NO saturated red, NO golden divine light, NO magical
circles, NO glowing runes, NO cyberpunk tech.
""".strip()


def build_prompt(scene: str) -> str:
    return f"""{STYLE}

{PALETTE}

SCENE:
{scene}

CONSTRAINTS:
{NEG}
""".strip()


@dataclass(frozen=True)
class BgShot:
    slug: str
    label: str
    scene: str

    @property
    def prompt(self) -> str:
        return build_prompt(self.scene)


BG_SHOTS: tuple[BgShot, ...] = (
    BgShot("bg_mountain_night", "山夜",
           """Empty wide landscape at night. Layered ink-wash mountain silhouettes
receding into thick mist, fading from dark foreground ridges to pale distant
peaks. A large full moon hangs low near the horizon, partially veiled by
drifting cloud wisps. Deep negative white space in the sky. No figures, no
structures, no text. Cool celadon-tinted moonlight."""),

    BgShot("bg_bridge_rain", "断桥雨",
           """Empty wide shot of a broken arched stone bridge spanning a misty
gorge, heavy diagonal ink-brush rain streaking across the whole frame. A gap
is visible where the bridge has crumbled in the middle. Dark stormy
ink-wash sky above, turbulent water below. No figures anywhere on the
bridge. Cold, dramatic, painterly rain texture."""),

    BgShot("bg_tavern_street", "长街酒肆",
           """Empty long straight ancient-town stone street stretching into deep
one-point perspective, rows of paper lanterns hanging along both sides
rendered as soft ink-wash white/gray blurs (restrained monochrome light,
NOT glowing red). A rustic wooden tavern with lattice windows sits along
the street, warm ink-tone lamplight glowing faintly from within. No people
walking, no figures in windows or doorways. Quiet nocturnal ambience."""),

    BgShot("bg_summit_moon", "山顶月",
           """Empty sweeping wide shot along the top of a mountain ridge. A
massive sea of turbulent ink-wash clouds churns below, spilling toward
camera. Distant layered mountain peaks fade into a hazy horizon. A huge
low-hanging full moon dominates the upper frame, casting cool celadon
moonlight across the cloud sea. No human figures on the ridge. Epic,
solitary, negative-space heavy composition."""),
)


def _post_once(base_url: str, api_key: str, model: str, shot: BgShot,
               timeout: int = 300) -> dict | None:
    url = base_url.rstrip("/") + "/v1/images/generations"
    payload = {
        "prompt": shot.prompt,
        "model": model,
        "n": 1,
        "size": "1536x1024",
    }
    headers = {"Authorization": f"Bearer {api_key}",
               "Accept": "application/json",
               "Content-Type": "application/json"}
    resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
    if not resp.ok:
        body_snip = (resp.text or "")[:500]
        raise requests.HTTPError(
            f"{resp.status_code} · body={body_snip}", response=resp)
    return resp.json()


def generate_one(base_url: str, api_key: str, model: str, shot: BgShot,
                 out_dir: Path, max_retries: int = 3) -> Path | None:
    out = out_dir / f"{shot.slug}.png"
    if out.exists():
        log.info("skip 已存在: %s", out.name)
        return out

    log.info("生图: %s → %s", shot.label, out.name)

    payload = None
    for attempt in range(1, max_retries + 1):
        try:
            payload = _post_once(base_url, api_key, model, shot)
            break
        except Exception as exc:
            log.warning("尝试 %s/%d %s 失败: %s",
                        attempt, max_retries, shot.slug, exc)
            if attempt < max_retries:
                time.sleep(5)

    if payload is None:
        log.error("放弃 %s (全部重试失败)", shot.label)
        return None

    if not payload.get("data"):
        log.error("返回 data 为空 %s: %s", shot.slug, payload)
        return None

    first = payload["data"][0]
    if first.get("b64_json"):
        out.write_bytes(base64.b64decode(first["b64_json"]))
    elif first.get("url"):
        img_bytes = requests.get(first["url"], timeout=180).content
        out.write_bytes(img_bytes)
    else:
        log.error("无 b64_json 也无 url: %s", first)
        return None

    log.info("✓ %s (%s bytes)", out, out.stat().st_size)
    return out


def main() -> int:
    load_dotenv(ROOT / ".env")
    api_key = os.environ.get("GPT_IMAGE_API_KEY") or os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("GPT_IMAGE_BASE_URL") or os.environ.get("OPENAI_BASE_URL")
    model = os.environ.get("GPT_IMAGE_MODEL", "gpt-image-2")
    max_workers = int(os.environ.get("GPT_IMAGE_WORKERS", "2"))
    if not api_key or not base_url:
        log.error("缺 GPT_IMAGE_API_KEY 或 GPT_IMAGE_BASE_URL (查 .env)")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    args = sys.argv[1:]
    if args:
        target = set(args)
        shots = tuple(s for s in BG_SHOTS if s.slug in target)
        if not shots:
            log.error("slug 不匹配: %s · 可用: %s",
                      args, [s.slug for s in BG_SHOTS])
            return 3
    else:
        shots = BG_SHOTS

    log.info("model=%s · out=%s · 待检 %d 张 · %d 线程并发",
             model, OUT_DIR, len(shots), max_workers)

    done = 0
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(generate_one, base_url, api_key, model, s, OUT_DIR): s
            for s in shots
        }
        for fut in as_completed(futures):
            shot = futures[fut]
            try:
                result = fut.result()
            except Exception as exc:
                log.error("线程异常 %s: %s", shot.slug, exc)
                continue
            if result:
                done += 1
                log.info("进度 %d/%d", done, len(shots))

    log.info("完成 %d/%d 张", done, len(shots))
    return 0 if done == len(shots) else 4


if __name__ == "__main__":
    sys.exit(main())
