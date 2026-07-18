#!/usr/bin/env python3
"""D07 · 4 张背景板过 grok-imagine-video 加大气层动效(云雾/雨丝/灯笼摇曳).

客户借用能力单,与项目主旨分线(见 publish/2026-W30/D07/production_plan.md §7)。
只给 4 张纯背景板(无角色)生成动效,15 张角色立绘维持纯 FFmpeg 运镜——
用户 2026-07-18 明确拍板"只给4张背景加i2v,人物仍纯运镜"。

API 契约抄 pipeline/gen_d06_wuxia_motion.py(同一个 grok-imagine-video 中转),
只改了 aspect_ratio(D07 是 16:9 横版,D06 是 9:16 竖版)和 prompt 内容。

用法:
  python3 pipeline/client_projects/d07_moon/gen_bg_motion.py            # 全跑4段
  python3 pipeline/client_projects/d07_moon/gen_bg_motion.py bg_mountain_night  # 单段
"""
from __future__ import annotations

import base64
import json
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[3]
STILLS_DIR = ROOT / "tmp" / "d07_moon" / "bg"
VIDEOS_DIR = ROOT / "tmp" / "d07_moon" / "bg_motion"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("d07.moon.bg_motion")

MOTION_QA = (
    "Chinese ink-wash wuxia landscape motion, painterly 2D animation feel, "
    "NOT photoreal, NOT 3D CG. No people, no figures, no text, no watermark. "
    "Camera holds still, no push-in, no pan. Subtle, minimal, understated motion only — "
    "do not invent new cloud shapes, puffs, bubbles, or circular blobs that are not in "
    "the original image; do not deform or cartoonify existing brushwork; preserve the "
    "exact original composition and silhouettes throughout."
)


@dataclass(frozen=True)
class BgMotionScene:
    slug: str
    label: str
    motion_prompt: str
    duration: int


SCENES: tuple[BgMotionScene, ...] = (
    BgMotionScene(
        "bg_mountain_night", "山夜 · 云雾漂移+月晕呼吸",
        f"The existing thin mist layer drifts very slightly and slowly sideways, "
        f"like a faint breeze passing through — a subtle parallax shift only, "
        f"not new cloud formations. The large moon's halo pulses with a very "
        f"slow, faint glow breathing in and out. Distant peaks and all rock "
        f"silhouettes stay perfectly fixed. {MOTION_QA}",
        duration=4,
    ),
    BgMotionScene(
        "bg_bridge_rain", "断桥雨 · 雨丝连续落下+水面涟漪",
        f"Thin diagonal ink-brush rain streaks fall continuously and steadily "
        f"through the frame, same density and thickness as the still image. "
        f"The river water surface has only faint, small, natural ripples — no "
        f"new round shapes. Bridge stones and rock silhouettes stay perfectly "
        f"fixed. {MOTION_QA}",
        duration=4,
    ),
    BgMotionScene(
        "bg_tavern_street", "长街酒肆 · 灯笼摇曳+雾气浮动",
        f"The paper lanterns hanging along both sides of the street sway "
        f"gently side to side, their soft ink-tone glow flickering subtly. "
        f"Thin mist drifts low along the stone street. Tavern lattice windows "
        f"stay fixed. {MOTION_QA}",
        duration=4,
    ),
    BgMotionScene(
        "bg_summit_moon", "山顶月 · 云海翻涌",
        f"The vast sea of ink-wash clouds below the ridge churns and rolls "
        f"slowly and continuously, spilling toward camera in soft undulating "
        f"waves. The huge moon's glow breathes very faintly. Ridge and distant "
        f"peaks stay fixed. {MOTION_QA}",
        duration=6,
    ),
)


def png_to_data_url(path: Path) -> str:
    raw = path.read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:image/png;base64,{b64}"


def submit_video(base_url: str, api_key: str, model: str, scene: BgMotionScene,
                  first_frame: Path) -> dict:
    url = base_url.rstrip("/") + "/v1/videos/generations"
    if not first_frame.exists():
        raise FileNotFoundError(f"首帧图缺失: {first_frame}")

    payload = {
        "model": model,
        "prompt": scene.motion_prompt,
        "resolution": "720p",
        "aspect_ratio": "16:9",
        "duration": scene.duration,
        "image": {"url": png_to_data_url(first_frame)},
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    log.info("POST %s · duration=%ds · payload≈%d KB",
              scene.slug, scene.duration, len(json.dumps(payload)) // 1024)
    resp = requests.post(url, headers=headers, json=payload, timeout=180)
    log.info("HTTP %d · %s · body_head: %s", resp.status_code, scene.slug, resp.text[:200])
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


def poll_task(base_url: str, api_key: str, task_id: str, slug: str,
              max_wait: int = 600) -> str | None:
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
                break
        except Exception:
            pass

    if not poll_url:
        log.warning("[%s] 找不到有效 poll endpoint", slug)
        return None

    while time.time() - start < max_wait:
        try:
            r = requests.get(poll_url, headers=headers, timeout=15)
            if r.status_code != 200:
                time.sleep(delay)
                continue
            data = r.json()
            elapsed = int(time.time() - start)
            log.info("[%s] 轮询 %ds · status=%s", slug, elapsed, data.get("status", "?"))
            video_url = extract_video_url(data)
            if video_url:
                return video_url
            status = str(data.get("status", "")).lower()
            if status in {"failed", "error"}:
                log.error("[%s] 任务失败: %s", slug, data)
                return None
            time.sleep(delay)
            delay = min(delay + 2, 15)
        except Exception:
            time.sleep(delay)

    log.error("[%s] 轮询超时", slug)
    return None


def download_video(url: str, out: Path, slug: str) -> bool:
    """先直连;失败(常见于结果 CDN 需科学上网)再退化走本地代理(抄自 gen_d06_wuxia_motion.py)。"""
    proxies = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
    for attempt_proxies in (None, proxies):
        try:
            r = requests.get(url, timeout=180, stream=True, proxies=attempt_proxies)
            r.raise_for_status()
            out.write_bytes(r.content)
            log.info("[%s] ✓ %s (%d KB)%s", slug, out.name, out.stat().st_size // 1024,
                      " [via proxy]" if attempt_proxies else "")
            return True
        except Exception as exc:
            log.warning("[%s] 下载失败(%s): %s", slug,
                        "直连" if attempt_proxies is None else "代理", exc)
    return False


def generate_scene_video(base_url: str, api_key: str, model: str,
                          scene: BgMotionScene, out_dir: Path) -> Path | None:
    out = out_dir / f"{scene.slug}.mp4"
    if out.exists():
        log.info("skip 已存在: %s", out.name)
        return out

    first_frame = STILLS_DIR / f"{scene.slug}.png"
    log.info("=== [%s] %s 提交 ===", scene.slug, scene.label)
    try:
        resp = submit_video(base_url, api_key, model, scene, first_frame)
    except Exception as exc:
        log.error("[%s] 提交失败: %s", scene.slug, exc)
        return None

    video_url = extract_video_url(resp)
    if video_url:
        return out if download_video(video_url, out, scene.slug) else None

    task_id = extract_task_id(resp)
    if not task_id:
        log.error("[%s] 无 video_url 也无 task_id", scene.slug)
        return None

    log.info("[%s] 异步任务 id=%s · 开始轮询", scene.slug, task_id)
    video_url = poll_task(base_url, api_key, task_id, scene.slug)
    if not video_url:
        return None
    return out if download_video(video_url, out, scene.slug) else None


def main() -> int:
    load_dotenv(ROOT / ".env")
    api_key = os.environ.get("GROK_API_KEY")
    base_url = os.environ.get("GROK_BASE_URL")
    model = os.environ.get("GROK_MODEL", "grok-imagine-video")
    if not api_key or not base_url:
        log.error("缺 GROK_API_KEY 或 GROK_BASE_URL (查 .env)")
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

    log.info("model=%s · base=%s · 待生成 %d 段 · 4 线程并发",
              model, base_url, len(scenes))

    ok = 0
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {
            ex.submit(generate_scene_video, base_url, api_key, model, s, VIDEOS_DIR): s
            for s in scenes
        }
        for fut in as_completed(futures):
            scene = futures[fut]
            try:
                r = fut.result()
            except Exception as exc:
                log.error("worker 异常 %s: %s", scene.slug, exc)
                r = None
            if r is not None:
                ok += 1
    log.info("完成: %d/%d 成功", ok, len(scenes))
    return 0 if ok == len(scenes) else 5


if __name__ == "__main__":
    sys.exit(main())
