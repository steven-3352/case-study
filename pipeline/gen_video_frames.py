#!/usr/bin/env python3
"""S01 冬夜卧室 · 4 段 Grok video 生成 · yunwu.ai 中转.

策略：
  - 每段用对应的 GPT-image-2 静图作首帧（image.url 传 base64 data URL）
  - 每段 motion prompt 描述"这一段的动作变化"，不重复描述画面
  - 单段 duration 5-10s；aspect_ratio 9:16；resolution 720p
  - 提交返回可能同步（含 video url）或异步（含 task_id 需轮询）
  - 双策略兼容：先解析同步响应，无则轮询

用法：
  python3 pipeline/gen_video_frames.py                # 全跑 4 段
  python3 pipeline/gen_video_frames.py S01_fake_angry # 单段
"""
from __future__ import annotations

import base64
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
PROJ_DIR = ROOT / "tmp" / "shortfilm_memory"
FRAMES_DIR = PROJ_DIR / "scenes" / "S01_winter_bedroom" / "frames"
VIDEOS_DIR = PROJ_DIR / "scenes" / "S01_winter_bedroom" / "videos"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("shortfilm.video")


# 4 段 motion prompt（描述动作变化，不重复画面）
S01_MOTION = """
The 40-year-old woman with long black hair, oval face, in cream pajamas standing
at the side of the bed slowly plants her hands firmly on her hips in a
mock-angry pose. She tilts her chin up slightly, her eyebrows softly furrow,
and her mouth opens as she speaks with playful frustration. Her long hair
sways gently. In the foreground, the top of the man's buzz-cut head remains
barely visible under the dark-orange quilt. The bedside amber lamp glow stays
warm and still. Camera very slowly pushes in by about 3 percent. Total
duration around 5 seconds. Photorealistic, Kodak Portra 400 film look, warm
cozy quiet indoor mood.

IMPORTANT NEGATIVES: NO visible breath puff from her mouth, NO white vapor,
NO steam or fog around her lips, NO cigarette smoke, NO exhale mist, NO cold
blue tint on skin. Her mouth just opens and closes naturally as she speaks —
nothing coming out of it. No morphing, no face distortion, no ghosting.
""".strip()

S02_MOTION = """
The 40-year-old man with a buzz cut, thick eyebrows, weathered face, in a
soft charcoal-grey thermal undershirt is lying on his side in bed. He slowly
lifts the corner of the heavy dark-orange padded quilt with one hand,
opening a warm amber pocket of the bed. He looks toward the off-camera-right
with a wide affectionate grin, then pats the mattress beside him twice with
his free hand as a gentle invitation. His body stays in one relaxed, natural
side-lying human pose throughout — arms stay their natural length, limbs
never stretch or elongate. The bedside amber lamp glow holds steady. Camera
holds still. Total duration around 5 seconds. Photorealistic, Kodak Portra
400 film look, warm cozy quiet indoor mood.

IMPORTANT NEGATIVES: NO visible breath puff from mouth, NO white vapor,
NO steam or fog around lips, NO cigarette smoke, NO exhale mist, NO cold
blue tint. NO body stretching, NO limb elongation, NO rubber-band arms,
NO elastic morphing, NO warping, NO face distortion, NO ghosting.
Realistic human anatomy and proportions at all times.
""".strip()

S03_MOTION = """
The couple lies in bed together, both matching the reference faces. The
woman's back is against the man's chest in a spooning embrace, both facing
camera-left. The woman's eyelids gently close as she settles into sleep, her
chest rising and falling with slow breathing. The man's arm softly tightens
around her waist over the quilt, his hand giving hers a small squeeze before
relaxing. Both faces relax into peaceful sleep. The bedside amber lamp
flickers once softly. The AC unit red power light glows warm-red in the
background. Camera very slowly drifts downward by about 2 percent. Total
duration around 8 seconds. Photorealistic, film grain, no face morphing.
""".strip()

S04_MOTION = """
The 40-year-old man, buzz cut damp from a fresh wash, in a dark charcoal
wool sweater is leaning down over the sleeping woman. His lips make gentle
contact with her forehead in a careful goodbye kiss. He holds the kiss for
about one and a half seconds, then very slowly pulls his head back, careful
not to wake her. He straightens up half a step. The sleeping woman does not
stir — her eyes remain closed, her breathing steady, her hand still tucked
under her cheek. Soft morning light slants gently through the window,
warm cream tone with a hint of pale gold. A faint wisp of steam from a
bedside mug rises slowly. Camera very slowly pushes in on her sleeping face
by about 2 percent. Total duration around 6 seconds. Photorealistic,
Kodak Portra 400 film grain, no morphing, no face distortion.
""".strip()


@dataclass(frozen=True)
class VideoScene:
    slug: str
    motion_prompt: str
    first_frame: Path
    duration: int  # seconds
    label: str
    ref_frames: tuple[Path, ...] = field(default_factory=tuple)


SCENES: tuple[VideoScene, ...] = (
    VideoScene(
        slug="S01_fake_angry",
        motion_prompt=S01_MOTION,
        first_frame=FRAMES_DIR / "S01_fake_angry.png",
        duration=5,
        label="S01 女主叉腰假生气",
    ),
    VideoScene(
        slug="S02_quilt_invite",
        motion_prompt=S02_MOTION,
        first_frame=FRAMES_DIR / "S02_quilt_invite.png",
        duration=5,
        label="S02 男主掀被招手",
    ),
    VideoScene(
        slug="S03_sleep_hug",
        motion_prompt=S03_MOTION,
        first_frame=FRAMES_DIR / "S03_sleep_hug.png",
        duration=8,
        label="S03 相拥入睡",
    ),
    VideoScene(
        slug="S04_morning_kiss",
        motion_prompt=S04_MOTION,
        first_frame=FRAMES_DIR / "S04_morning_kiss.png",
        duration=6,
        label="S04 清晨亲吻",
    ),
)


def png_to_data_url(path: Path) -> str:
    """本地 png → data:image/png;base64,... URL."""
    raw = path.read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:image/png;base64,{b64}"


def submit_video(
    base_url: str,
    api_key: str,
    model: str,
    scene: VideoScene,
) -> dict:
    """POST /v1/videos/generations · 返回 response json."""
    url = base_url.rstrip("/") + "/v1/videos/generations"

    if not scene.first_frame.exists():
        raise FileNotFoundError(f"首帧图缺失: {scene.first_frame}")

    payload: dict = {
        "model": model,
        "prompt": scene.motion_prompt,
        "resolution": "720p",
        "aspect_ratio": "9:16",
        "duration": scene.duration,
        "image": {"url": png_to_data_url(scene.first_frame)},
    }
    if scene.ref_frames:
        payload["reference_images"] = [
            {"url": png_to_data_url(r)} for r in scene.ref_frames if r.exists()
        ]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    log.info(
        "POST %s · model=%s · duration=%ds · payload≈%d KB",
        url,
        model,
        scene.duration,
        len(json.dumps(payload)) // 1024,
    )
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    log.info("HTTP %d · body_head: %s", resp.status_code, resp.text[:400])
    resp.raise_for_status()
    return resp.json()


def extract_video_url(resp: dict) -> str | None:
    """从各种可能的响应结构里挖 video URL."""
    # yunwu.ai/grok-imagine-video 实际结构：{"video": {"url": "..."}, "status": "done"}
    if "video" in resp and isinstance(resp["video"], dict):
        if isinstance(resp["video"].get("url"), str):
            return resp["video"]["url"]
    # 其他常见字段路径尝试
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
    """异步响应挖 task_id / job_id."""
    for key in ("task_id", "job_id", "id", "request_id"):
        if key in resp and isinstance(resp[key], str):
            return resp[key]
    return None


def poll_task(
    base_url: str, api_key: str, task_id: str, max_wait: int = 600
) -> str | None:
    """轮询任务直到有 video URL 或超时."""
    poll_url_candidates = [
        base_url.rstrip("/") + f"/v1/videos/generations/{task_id}",
        base_url.rstrip("/") + f"/v1/videos/{task_id}",
        base_url.rstrip("/") + f"/v1/tasks/{task_id}",
    ]
    headers = {"Authorization": f"Bearer {api_key}"}
    start = time.time()
    delay = 5

    # 先探测哪个 poll endpoint 有效
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
            log.info(
                "轮询 %ds · status=%s",
                int(time.time() - start),
                data.get("status", "?"),
            )
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
    """下载视频到本地."""
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


def generate_scene_video(
    base_url: str, api_key: str, model: str, scene: VideoScene, out_dir: Path
) -> Path | None:
    """生成单段视频，返回本地路径或 None."""
    out = out_dir / f"{scene.slug}.mp4"
    log.info("=== %s ===", scene.label)
    try:
        resp = submit_video(base_url, api_key, model, scene)
    except Exception as exc:
        log.error("提交失败: %s", exc)
        return None

    # 同步响应？
    video_url = extract_video_url(resp)
    if video_url:
        log.info("同步返回 video URL")
        return out if download_video(video_url, out) else None

    # 异步 task id？
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

    log.info(
        "model=%s · base=%s · 待生成 %d 段 (%s)",
        model,
        base_url,
        len(scenes),
        [s.slug for s in scenes],
    )
    results = [
        generate_scene_video(base_url, api_key, model, s, VIDEOS_DIR) for s in scenes
    ]
    ok = sum(1 for r in results if r is not None)
    log.info("完成: %d/%d 成功", ok, len(scenes))
    return 0 if ok == len(scenes) else 5


if __name__ == "__main__":
    sys.exit(main())
