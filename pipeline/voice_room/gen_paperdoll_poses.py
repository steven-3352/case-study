#!/usr/bin/env python3
"""语音厅 V4 · 4 主角额外姿态立绘生成（gpt-image-2 images/edits · http.client multipart）.

以每人正面 _cutout.png 为参考图，通过 images/edits 生成：
  three_quarter → 约 45° 转身
  side          → 侧面约 90°

输出：publish/语音厅/pv_v4/poses/{name}_{pose}.png
      4 人 × 2 姿态 = 8 张

调用：python3 gen_paperdoll_poses.py
"""
from __future__ import annotations

import base64
import http.client
import json
import logging
import mimetypes
import os
import sys
import time
import urllib.parse
from codecs import encode
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT   = Path(__file__).resolve().parents[2]
VOICE  = ROOT / "publish" / "语音厅"
ASSETS = VOICE / "script_v2_assets"
OUT    = VOICE / "pv_v4" / "poses"

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

NAMES = ["cy", "诺兰", "轩珩", "中里毅2"]

POSE_PROMPTS = {
    "three_quarter": (
        "Same anime character in the reference image, same outfit and hairstyle, "
        "three-quarter view (roughly 45 degrees turned to the right), full body standing pose, "
        "clean white background, anime illustration style, high quality line art, "
        "sharp edges, transparent-ready white background"
    ),
    "side": (
        "Same anime character in the reference image, same outfit and hairstyle, "
        "side view (90 degrees profile, facing left), full body standing pose, "
        "clean white background, anime illustration style, high quality line art, "
        "sharp edges, transparent-ready white background"
    ),
}


@dataclass
class PoseJob:
    name: str
    pose: str
    ref: Path
    out: Path


def _make_jobs() -> list[PoseJob]:
    jobs = []
    for name in NAMES:
        ref = ASSETS / f"{name}_cutout.png"
        if not ref.exists():
            log.warning("参考图缺失，跳过: %s", ref)
            continue
        for pose in POSE_PROMPTS:
            out = OUT / f"{name}_{pose}.png"
            if out.exists():
                log.info("已存在，跳过: %s", out.name)
                continue
            jobs.append(PoseJob(name=name, pose=pose, ref=ref, out=out))
    return jobs


def _build_multipart(job: PoseJob, model: str, boundary: str) -> bytes:
    """按 http.client 手动 multipart 格式构造请求体（参照用户示例）."""
    prompt = POSE_PROMPTS[job.pose]
    file_type = mimetypes.guess_type(str(job.ref))[0] or "application/octet-stream"
    parts: list[bytes] = []

    # --- image 字段 ---
    parts.append(encode("--" + boundary))
    parts.append(encode(
        "Content-Disposition: form-data; name=image; filename=ref.png"
    ))
    parts.append(encode(f"Content-Type: {file_type}"))
    parts.append(encode(""))
    parts.append(job.ref.read_bytes())

    # --- prompt 字段 ---
    parts.append(encode("--" + boundary))
    parts.append(encode("Content-Disposition: form-data; name=prompt;"))
    parts.append(encode("Content-Type: text/plain"))
    parts.append(encode(""))
    parts.append(encode(prompt))

    # --- model 字段 ---
    parts.append(encode("--" + boundary))
    parts.append(encode("Content-Disposition: form-data; name=model;"))
    parts.append(encode("Content-Type: text/plain"))
    parts.append(encode(""))
    parts.append(encode(model))

    # --- n 字段 ---
    parts.append(encode("--" + boundary))
    parts.append(encode("Content-Disposition: form-data; name=n;"))
    parts.append(encode("Content-Type: text/plain"))
    parts.append(encode(""))
    parts.append(encode("1"))

    # --- size 字段 ---
    parts.append(encode("--" + boundary))
    parts.append(encode("Content-Disposition: form-data; name=size;"))
    parts.append(encode("Content-Type: text/plain"))
    parts.append(encode(""))
    parts.append(encode("1024x1536"))

    # --- 结束 boundary ---
    parts.append(encode("--" + boundary + "--"))
    parts.append(encode(""))

    return b"\r\n".join(parts)


def _gen_one(host: str, api_key: str, model: str, job: PoseJob) -> bool:
    boundary = "wL36Yn8afVp8Ag7AmP8qZ0SA4n1v9T"
    log.info("生图: %s · %s → %s  [%s/v1/images/edits]", job.name, job.pose, job.out.name, host)

    for attempt in range(1, 5):
        try:
            payload = _build_multipart(job, model, boundary)
            conn = http.client.HTTPSConnection(host, timeout=180)
            headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {api_key}",
                "Content-type": f"multipart/form-data; boundary={boundary}",
            }
            conn.request("POST", "/v1/images/edits", payload, headers)
            res  = conn.getresponse()
            body = res.read()
        except Exception as exc:
            log.warning("尝试 %d/4 失败: %s", attempt, exc)
            if attempt < 4:
                time.sleep(5 * attempt)
            continue
        finally:
            try:
                conn.close()
            except Exception:
                pass

        log.info("尝试 %d/4 → HTTP %d, body_len=%d", attempt, res.status, len(body))
        if res.status != 200:
            log.warning("  body: %s", body[:300].decode("utf-8", errors="replace"))
            if attempt < 4:
                time.sleep(5 * attempt)
            continue

        try:
            data = json.loads(body)
        except Exception:
            log.warning("  非 JSON body: %s", body[:300].decode("utf-8", errors="replace"))
            if attempt < 4:
                time.sleep(5 * attempt)
            continue

        items = data.get("data") or []
        if not items:
            log.warning("  data 为空, keys=%s", list(data.keys()))
            if attempt < 4:
                time.sleep(5 * attempt)
            continue

        first = items[0]
        if first.get("b64_json"):
            job.out.write_bytes(base64.b64decode(first["b64_json"]))
        elif first.get("url"):
            import urllib.request
            with urllib.request.urlopen(first["url"]) as r:  # noqa: S310
                job.out.write_bytes(r.read())
        else:
            log.error("无 b64_json 也无 url: %s", list(first.keys()))
            return False

        log.info("✓ %s (%d KB)", job.out.name, job.out.stat().st_size // 1024)
        return True

    log.error("放弃 %s %s（4 次全败）", job.name, job.pose)
    return False


def main() -> int:
    load_dotenv(ROOT / ".env")
    api_key  = os.environ.get("GPT_IMAGE_API_KEY")
    base_url = os.environ.get("GPT_IMAGE_BASE_URL", "")
    model    = os.environ.get("GPT_IMAGE_MODEL", "gpt-image-2")
    if not api_key or not base_url:
        log.error("缺 GPT_IMAGE_API_KEY 或 GPT_IMAGE_BASE_URL")
        return 1

    # 从 base_url 提取主机名（如 https://yunwu.ai/v1 → yunwu.ai）
    host = urllib.parse.urlparse(base_url).netloc

    OUT.mkdir(parents=True, exist_ok=True)
    jobs = _make_jobs()

    if not jobs:
        log.info("全部已生成，无需重跑")
        return 0

    log.info("共 %d 张待生成 · model=%s · host=%s", len(jobs), model, host)
    ok = 0
    for job in jobs:
        if _gen_one(host, api_key, model, job):
            ok += 1
        else:
            time.sleep(3)

    log.info("完成: %d/%d", ok, len(jobs))
    return 0 if ok == len(jobs) else 1


if __name__ == "__main__":
    sys.exit(main())
