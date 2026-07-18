#!/usr/bin/env python3
"""D06 测试项目 · Grok image-to-video 给3张日式动漫静图加Live2D式动效.

头发/树枝/衣袍随风飘动 + 花瓣飘落 + 灯笼光晃动,静图升级成动态短片,
覆盖原片前15.1s(3镜)。首帧用 gen_d06_anime_test.py 出的图裁到16:9。

用法:
  python3 pipeline/gen_d06_video_motion.py                # 全跑3段
  python3 pipeline/gen_d06_video_motion.py 01_moon_portrait # 单段
"""
from __future__ import annotations

import base64
import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
FRAMES_DIR = ROOT / "tmp" / "d06_anime_test" / "images_16x9"
VIDEOS_DIR = ROOT / "tmp" / "d06_anime_test" / "videos"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("d06.video")


MOTION_01 = """
The bishounen anime character with long silver-lavender hair holds a serene
close-up bust pose under the huge glowing moon. His long hair sways and
drifts gently as if in a soft breeze, loose strands lifting slightly. Cherry
blossom petals drift slowly across the frame in soft bokeh, some passing in
front of his face. His eyes blink softly once, a faint calm smile. The moon's
glow behind him pulses with a very slow gentle bloom. Robe fabric at his
shoulders shifts subtly with the breeze. Camera holds mostly still with a
very slow, barely perceptible push-in. Japanese theatrical cel-shaded anime
motion style, smooth 2D animation feel, NOT 3D, NOT realistic photo motion.
No text, no watermark.
""".strip()

MOTION_02 = """
The same bishounen character, medium shot, is swept by a sudden gust of wind.
A dense flurry of cherry blossom petals blows rapidly across the frame,
motion-blurred. His long silver-lavender hair whips and streams sideways in
the wind, robe sleeves and sash flutter and billow. The moon fragment at the
frame edge flickers softly. Fast, energetic petal and hair motion suggesting
a strong gust, then his hair settles slightly as the gust passes. Japanese
theatrical cel-shaded anime motion style, smooth 2D animation feel, NOT 3D,
NOT realistic photo motion. No text, no watermark.
""".strip()

MOTION_03 = """
The same bishounen character stands full-body in the night courtyard. His
long hair and flowing robe sway continuously in a gentle breeze, the hanfu
sash drifting. The cherry blossom tree beside him sheds petals that drift and
fall slowly to the ground. The paper lanterns hanging from the pavilion sway
slightly and their glow flickers warmly. The large moon overhead holds
steady. Camera holds mostly still with a very slow, barely perceptible
push-in. Japanese theatrical cel-shaded anime motion style, smooth 2D
animation feel, NOT 3D, NOT realistic photo motion. No text, no watermark.
""".strip()


@dataclass(frozen=True)
class VideoScene:
    slug: str
    motion_prompt: str
    first_frame: Path
    duration: int  # seconds, grok 支持的整数档位
    label: str


SCENES: tuple[VideoScene, ...] = (
    VideoScene(
        slug="01_moon_portrait",
        motion_prompt=MOTION_01,
        first_frame=FRAMES_DIR / "01_moon_portrait.png",
        duration=8,
        label="01 月下人像 · 发丝花瓣飘",
    ),
    VideoScene(
        slug="02_petal_transition",
        motion_prompt=MOTION_02,
        first_frame=FRAMES_DIR / "02_petal_transition.png",
        duration=3,
        label="02 花瓣过渡 · 疾风扫发",
    ),
    VideoScene(
        slug="03_courtyard_wide",
        motion_prompt=MOTION_03,
        first_frame=FRAMES_DIR / "03_courtyard_wide.png",
        duration=5,
        label="03 庭院全身 · 衣袍树枝灯笼",
    ),
)


def png_to_data_url(path: Path) -> str:
    raw = path.read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:image/png;base64,{b64}"


def submit_video(base_url: str, api_key: str, model: str, scene: VideoScene) -> dict:
    url = base_url.rstrip("/") + "/v1/videos/generations"
    if not scene.first_frame.exists():
        raise FileNotFoundError(f"首帧图缺失: {scene.first_frame}")

    payload = {
        "model": model,
        "prompt": scene.motion_prompt,
        "resolution": "720p",
        "aspect_ratio": "16:9",
        "duration": scene.duration,
        "image": {"url": png_to_data_url(scene.first_frame)},
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    log.info(
        "POST %s · model=%s · duration=%ds · payload≈%d KB",
        url, model, scene.duration, len(json.dumps(payload)) // 1024,
    )
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    log.info("HTTP %d · body_head: %s", resp.status_code, resp.text[:400])
    resp.raise_for_status()
    return resp.json()


def extract_video_url(resp: dict) -> str | None:
    if "video" in resp and isinstance(resp["video"], dict):
        if isinstance(resp["video"].get("url"), str):
            return resp["video"]["url"]
    for key in ("video_url", "url", "output_url", "result_url"):
        if key in resp and isinstance(resp[key], str):
            return resp[key]
    if "data" in resp and isinstance(resp["data"], list) and resp["data"]:
        item = resp["data"][0]
        for key in ("url", "video_url", "output_url"):
            if key in item and isinstance(item[key], str):
                return item[key]
    if "output" in resp and isinstance(resp["output"], dict):
        for key in ("url", "video_url"):
            if key in resp["output"]:
                return resp["output"][key]
    return None


def extract_task_id(resp: dict) -> str | None:
    for key in ("task_id", "job_id", "id", "request_id"):
        if key in resp and isinstance(resp[key], str):
            return resp[key]
    return None


def poll_task(base_url: str, api_key: str, task_id: str, max_wait: int = 600) -> str | None:
    poll_url_candidates = [
        base_url.rstrip("/") + f"/v1/videos/generations/{task_id}",
        base_url.rstrip("/") + f"/v1/videos/{task_id}",
        base_url.rstrip("/") + f"/v1/tasks/{task_id}",
    ]
    headers = {"Authorization": f"Bearer {api_key}"}
    start = time.time()
    delay = 5

    poll_url = None
    for cand in poll_url_candidates:
        try:
            r = requests.get(cand, headers=headers, timeout=15)
            if r.status_code == 200:
                poll_url = cand
                log.info("轮询 endpoint: %s", cand)
                break
        except Exception as exc:
            log.debug("探测 %s 失败: %s", cand, exc)

    if not poll_url:
        log.warning("找不到有效 poll endpoint · 候选：%s", poll_url_candidates)
        return None

    while time.time() - start < max_wait:
        try:
            r = requests.get(poll_url, headers=headers, timeout=15)
            if r.status_code != 200:
                log.warning("轮询 HTTP %d · %s", r.status_code, r.text[:200])
                time.sleep(delay)
                continue
            data = r.json()
            log.info("轮询 %ds · status=%s", int(time.time() - start), data.get("status", "?"))
            video_url = extract_video_url(data)
            if video_url:
                return video_url
            status = str(data.get("status", "")).lower()
            if status in {"failed", "error"}:
                log.error("任务失败: %s", data)
                return None
            time.sleep(delay)
            delay = min(delay + 2, 15)
        except Exception as exc:
            log.warning("轮询异常: %s", exc)
            time.sleep(delay)

    log.error("轮询超时 (%ds)", max_wait)
    return None


def download_video(url: str, out: Path) -> bool:
    try:
        log.info("下载 %s → %s", url[:80], out.name)
        r = requests.get(url, timeout=180, stream=True)
        r.raise_for_status()
        out.write_bytes(r.content)
        log.info("✓ %s (%d KB)", out, out.stat().st_size // 1024)
        return True
    except Exception as exc:
        log.error("下载失败: %s", exc)
        return False


def generate_scene_video(base_url: str, api_key: str, model: str, scene: VideoScene, out_dir: Path) -> Path | None:
    out = out_dir / f"{scene.slug}.mp4"
    log.info("=== %s ===", scene.label)
    try:
        resp = submit_video(base_url, api_key, model, scene)
    except Exception as exc:
        log.error("提交失败: %s", exc)
        return None

    video_url = extract_video_url(resp)
    if video_url:
        log.info("同步返回 video URL")
        return out if download_video(video_url, out) else None

    task_id = extract_task_id(resp)
    if not task_id:
        log.error("响应既无 video_url 也无 task_id: %s", resp)
        return None

    log.info("异步任务 id=%s · 开始轮询", task_id)
    video_url = poll_task(base_url, api_key, task_id)
    if not video_url:
        return None
    return out if download_video(video_url, out) else None


def main() -> int:
    load_dotenv(ROOT / ".env")
    api_key = os.environ.get("GROK_API_KEY")
    base_url = os.environ.get("GROK_BASE_URL")
    model = os.environ.get("GROK_MODEL", "grok-imagine-video")
    if not api_key or not base_url:
        log.error("缺 GROK_API_KEY 或 GROK_BASE_URL（查 .env）")
        return 1

    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    args = sys.argv[1:]
    if args:
        target = set(args)
        scenes = tuple(s for s in SCENES if s.slug in target)
        if not scenes:
            log.error("slug 不匹配: %s · 可用: %s", args, [s.slug for s in SCENES])
            return 3
    else:
        scenes = SCENES

    log.info("model=%s · base=%s · 待生成 %d 段 (%s)", model, base_url, len(scenes), [s.slug for s in scenes])
    results = [generate_scene_video(base_url, api_key, model, s, VIDEOS_DIR) for s in scenes]
    ok = sum(1 for r in results if r is not None)
    log.info("完成: %d/%d 成功", ok, len(scenes))
    return 0 if ok == len(scenes) else 5


if __name__ == "__main__":
    sys.exit(main())
