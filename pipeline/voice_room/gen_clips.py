#!/usr/bin/env python3
"""语音厅 MV · grok-imagine-video i2v 出 S1/S2/S3 视频（16:9）.

- 起始帧来自 gen_startframes.py（frames/S{NN}_startframe.png）
- motion prompt 摘自 script_v2.md（i2v-video-prompt skill 铁律格式）
- 中转 yunwu.ai（GROK_BASE_URL）· aspect_ratio=16:9 · 720p
- 存 publish/语音厅/script_v2_assets/clips/S{NN}.mp4

生成后必逐帧 QA（memory feedback_camera-motion-vs-i2v-ceiling）。
"""
from __future__ import annotations

import base64
import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "publish" / "语音厅" / "script_v2_assets"
FRAMES = ASSETS / "frames"
OUT_DIR = ASSETS / "clips"
OUT_DIR.mkdir(parents=True, exist_ok=True)

S1_MOTION = """[intent] Serve completion_3s hook: establish POV and mystery within 4 seconds.
[hook 0-2s] Phone screen slowly brightens from dim to full glow (1.5s ease-out). At 2.0s, ink-wash moon on screen becomes crisp. Golden calligraphy softly fades in from transparent to full (0.8s), letter by letter.
[main action 2s-4s] Woman's fingertips subtly shift 2mm (breathing, not gesture). Warm dawn ambient light on bedsheet slowly intensifies 10%.
[camera] Camera dolly forward at constant 0.4 ft/s. Slight lens breathing. Total push-in 3-4%. No handheld shake in this shot — locked contemplative.
[lighting] Practical dawn window light 5500K from upper-left, 15% intensity ramp across 4s. No overhead artificial lights on.
[anchor] A young woman's right hand only — slender fingers, cream silk pajama cuff, natural manicure, no rings. No face visible.
[look] Kodak Portra 400 film grain, warm cream-and-gold palette, documentary intimacy.
[NEGATIVES] NO face morphing, NO extra fingers, NO body stretching, NO warping, NO ghosting. NO breath puff, NO cold blue tint, NO neon purple/pink/cyan, NO Dracula palette, NO dark developer canvas, NO on-camera speaking, NO people in background."""

S2_MOTION = """[intent] Serve completion_3s: establish the location (this same living room appears in all shots).
[hook 0-1s] Foreground pillow edge slightly shifts as camera begins to rise (POV waking). Dawn light on wooden floor visibly warms 15% over 1s.
[main action 1-2s] Camera continues rising, revealing the full living room in one continuous motion. Sheer curtain on left billows gently. Distant mountain mist very subtly shifts. A tiny bird silhouette crosses distant sky (1 second).
[camera] Camera tilt up at 8 deg/s, total tilt 15 deg over 2s. Simultaneous rise of 6 inches (POV sitting up). Smooth handheld micro-vibration 0.5mm at 2Hz.
[lighting] Dawn 5500K window light intensifies 20% over 2s. Warm floor bounce grows. No artificial lights.
[anchor] No people. Foreground: cream pillow edge (blurred). Wooden herringbone floor. Cream linen sofa (right frame). Wooden dining table (center). Empty white ceramic coffee cup on saucer.
[look] Kodak Portra 400 film, morning warmth, documentary POV.
[NEGATIVES] NO people appearing, NO neon, NO cold blue tint on floor or walls, NO warping, NO ghosting, NO Dracula palette, NO dark canvas."""

S3_MOTION = """[intent] Serve completion_rate + emotional peak: the "he looks at me" beat.
[hook 0-1.5s] Man in profile carefully places pour-over carafe onto table (0.8s smooth motion). Steam from coffee cup gently rises in visible curls.
[main action 1.5-3.5s] Man slowly turns head toward camera (90 deg rotation over 2s, ease-in-out, natural neck movement — not mechanical). As his gaze locks with camera, a soft closed-mouth micro-smile forms at the corner of his mouth (0.4s natural muscle movement).
[hold 3.5-4s] Gaze holds camera. Steam continues rising. Curtain sways 2mm.
[camera] Static handheld, 0.5mm micro-vibration at 2Hz. No dolly, no pan. Camera is "the woman on the sofa" — anchored.
[lighting] Practical dawn window light 5500K, ~30% intensity. Warm bounce off wooden floor. Rim light on his silver hair from window (upper-left backlight).
[anchor] Young man, 25-year-old East Asian features, silver-white hair swept back mid-length, pale skin, sharp jawline, cool aloof but softening expression. White oxford shirt sleeves rolled to forearm, black tailored trousers. Keep the exact face from the first frame.
[look] Kodak Portra 400 film grain, warm morning intimacy, handheld documentary. Natural micro-expression, not staged smile.
[NEGATIVES] NO face morphing, NO teeth showing (smile is closed-mouth), NO exaggerated cinematic smile, NO breath puff, NO cold blue tint, NO neon, NO Dracula palette, NO dark canvas, NO body stretching, NO warping, NO extra fingers, NO black cape, NO arms-crossed standing pose."""

# (slug, motion_prompt, duration_seconds)
SHOTS = [
    ("S1", S1_MOTION, 4),
    ("S2", S2_MOTION, 2),
    ("S3", S3_MOTION, 4),
]


def png_to_data_url(path: Path) -> str:
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def submit(base_url: str, api_key: str, model: str, frame: Path,
           prompt: str, duration: int) -> dict:
    url = base_url.rstrip("/") + "/v1/videos/generations"
    payload = {
        "model": model,
        "prompt": prompt,
        "resolution": "720p",
        "aspect_ratio": "16:9",
        "duration": duration,
        "image": {"url": png_to_data_url(frame)},
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    print(f"[post] {frame.name} · dur={duration}s · payload≈{len(json.dumps(payload)) // 1024}KB")
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    print(f"[http] {r.status_code} · {r.text[:300]}")
    r.raise_for_status()
    return r.json()


def extract_url(resp: dict) -> str | None:
    if isinstance(resp.get("video"), dict) and isinstance(resp["video"].get("url"), str):
        return resp["video"]["url"]
    for k in ("video_url", "url", "output_url", "result_url"):
        if isinstance(resp.get(k), str):
            return resp[k]
    if isinstance(resp.get("data"), list) and resp["data"]:
        it = resp["data"][0]
        for k in ("url", "video_url", "output_url"):
            if isinstance(it.get(k), str):
                return it[k]
    if isinstance(resp.get("output"), dict):
        for k in ("url", "video_url"):
            if isinstance(resp["output"].get(k), str):
                return resp["output"][k]
    return None


def extract_task_id(resp: dict) -> str | None:
    for k in ("task_id", "job_id", "id", "request_id"):
        if isinstance(resp.get(k), str):
            return resp[k]
    return None


def poll(base_url: str, api_key: str, task_id: str, max_wait: int = 600) -> str | None:
    cands = [
        base_url.rstrip("/") + f"/v1/videos/generations/{task_id}",
        base_url.rstrip("/") + f"/v1/videos/{task_id}",
        base_url.rstrip("/") + f"/v1/tasks/{task_id}",
    ]
    headers = {"Authorization": f"Bearer {api_key}"}
    start = time.time()
    poll_url = None
    for c in cands:
        try:
            r = requests.get(c, headers=headers, timeout=15)
            if r.status_code == 200:
                poll_url = c
                print(f"[poll] endpoint={c}")
                break
        except Exception:
            pass
    if not poll_url:
        print(f"[warn] 无有效 poll endpoint · {cands}")
        return None
    delay = 5
    while time.time() - start < max_wait:
        try:
            r = requests.get(poll_url, headers=headers, timeout=15)
            if r.status_code != 200:
                time.sleep(delay)
                continue
            data = r.json()
            print(f"[poll] {int(time.time() - start)}s · status={data.get('status', '?')}")
            u = extract_url(data)
            if u:
                return u
            if str(data.get("status", "")).lower() in {"failed", "error"}:
                print(f"[err] 任务失败: {data}")
                return None
            time.sleep(delay)
            delay = min(delay + 2, 15)
        except Exception as exc:
            print(f"[warn] 轮询异常: {exc}")
            time.sleep(delay)
    print(f"[err] 轮询超时 {max_wait}s")
    return None


def download(url: str, out: Path) -> bool:
    try:
        r = requests.get(url, timeout=180)
        r.raise_for_status()
        out.write_bytes(r.content)
        print(f"[ok] {out.name} ({out.stat().st_size // 1024} KB)")
        return True
    except Exception as exc:
        print(f"[err] 下载失败: {exc}")
        return False


def gen_one(base_url: str, api_key: str, model: str, slug: str,
            prompt: str, duration: int) -> bool:
    frame = FRAMES / f"{slug}_startframe.png"
    if not frame.exists():
        print(f"[err] {slug} 起始帧缺失: {frame}（先跑 gen_startframes.py）")
        return False
    out = OUT_DIR / f"{slug}.mp4"
    try:
        resp = submit(base_url, api_key, model, frame, prompt, duration)
    except Exception as exc:
        print(f"[err] {slug} 提交失败: {exc}")
        return False
    url = extract_url(resp)
    if not url:
        tid = extract_task_id(resp)
        if tid:
            url = poll(base_url, api_key, tid)
    if not url:
        print(f"[err] {slug} 无 video url · resp={json.dumps(resp)[:300]}")
        return False
    return download(url, out)


def main() -> int:
    load_dotenv(ROOT / ".env")
    api_key = os.environ["GROK_API_KEY"]
    base_url = os.environ["GROK_BASE_URL"]
    model = os.environ.get("GROK_MODEL", "grok-imagine-video")
    print(f"[info] model={model} base_url={base_url} out={OUT_DIR}")

    only = sys.argv[1:] or None
    todo = [s for s in SHOTS if not only or s[0] in only]
    ok = 0
    for slug, prompt, dur in todo:
        if gen_one(base_url, api_key, model, slug, prompt, dur):
            ok += 1
    print(f"[done] {ok}/{len(todo)} 视频完成 → {OUT_DIR}")
    return 0 if ok == len(todo) else 1


if __name__ == "__main__":
    sys.exit(main())
