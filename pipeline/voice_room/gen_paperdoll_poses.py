#!/usr/bin/env python3
"""语音厅 V4 · 4 主角额外姿态立绘生成（gpt-image-2 公共客户端）.

以每人正面 _cutout.png 为参考图，通过 images/edits 生成：
  three_quarter → 约 45° 转身
  side          → 侧面约 90°

输出：publish/语音厅/pv_v4/poses/{name}_{pose}.png
      4 人 × 2 姿态 = 8 张

调用：python3 gen_paperdoll_poses.py
"""
from __future__ import annotations

import logging
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT   = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.gpt_image_client import GPTImageClient  # noqa: E402
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


def _gen_one(client: GPTImageClient, job: PoseJob) -> bool:
    log.info("生图: %s · %s → %s", job.name, job.pose, job.out.name)
    try:
        result = client.edit(
            prompt=POSE_PROMPTS[job.pose],
            images=[job.ref],
            size="1024x1536",
        )
        job.out.write_bytes(result)
    except Exception as exc:  # noqa: BLE001
        log.error("放弃 %s %s: %s", job.name, job.pose, exc)
        return False

    log.info("✓ %s (%d KB)", job.out.name, job.out.stat().st_size // 1024)
    return True


def main() -> int:
    load_dotenv(ROOT / ".env")
    api_key  = os.environ.get("GPT_IMAGE_API_KEY")
    base_url = os.environ.get("GPT_IMAGE_BASE_URL", "")
    model    = os.environ.get("GPT_IMAGE_MODEL", "gpt-image-2")
    if not api_key or not base_url:
        log.error("缺 GPT_IMAGE_API_KEY 或 GPT_IMAGE_BASE_URL")
        return 1

    client = GPTImageClient(
        api_key=api_key,
        base_url=base_url,
        model=model,
        timeout=180.0,
        attempts=4,
    )

    OUT.mkdir(parents=True, exist_ok=True)
    jobs = _make_jobs()

    if not jobs:
        log.info("全部已生成，无需重跑")
        return 0

    log.info("共 %d 张待生成 · model=%s · api=%s", len(jobs), model, client.base_url)
    ok = 0
    for job in jobs:
        if _gen_one(client, job):
            ok += 1
        else:
            time.sleep(3)

    log.info("完成: %d/%d", ok, len(jobs))
    return 0 if ok == len(jobs) else 1


if __name__ == "__main__":
    sys.exit(main())
