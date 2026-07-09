#!/usr/bin/env python3
"""成片媒体体检门 · ①确定性闸(fail-closed).

抄 OpenMontage 的 ffprobe/黑帧/静音那套——只抓"技术上坏",不判创意。
机械兜底本项目已有但靠人肉的硬门：VO 前 6s 无死区、无 3s+ 沉默钉子、时长达标。

用法:
  python3 pipeline/gate_check_media.py <video.mp4>
  python3 pipeline/gate_check_media.py <video.mp4> --min 40 --max 60

检查项(任一 FAIL → 退出码 1，fail-closed):
  - 可解析 + 时长 > 0（在 --min/--max 内，若给）
  - 无 ≥1.0s 纯黑帧（blackdetect；黑底白字不算纯黑，不误伤 CTA）
  - 无 ≥3.0s 静音死区（silencedetect）
  - 前 6s mean_volume ≥ -25dB（音画硬门：禁前段死区）
  - 无爆音削波（max_volume ≥ -0.1dB → 疑似 clipping）

字幕存在性：本项目字幕走 HTML 帧 overlay（烧进画面，非独立轨），无法从流检测，跳过。
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys

BLACK_MIN_S = 1.0      # 纯黑帧 ≥ 此值 → FAIL
SILENCE_MIN_S = 3.0    # 静音死区 ≥ 此值 → FAIL
HEAD_WINDOW_S = 6.0    # 前 N 秒
HEAD_RMS_MIN_DB = -25.0
CLIP_MAX_DB = -0.1     # max_volume ≥ 此值 → 疑似爆音


def _run(cmd: list[str]) -> str:
    """跑 ffmpeg/ffprobe，返回合并的 stdout+stderr 文本。"""
    p = subprocess.run(cmd, capture_output=True, text=True)
    return (p.stdout or "") + (p.stderr or "")


def probe_duration(path: str) -> float | None:
    out = _run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", path,
    ]).strip()
    try:
        return float(out.splitlines()[0])
    except (ValueError, IndexError):
        return None


def detect_black(path: str) -> list[float]:
    out = _run([
        "ffmpeg", "-hide_banner", "-i", path,
        "-vf", "blackdetect=d=0.3:pic_th=0.98", "-an", "-f", "null", "-",
    ])
    return [float(m) for m in re.findall(r"black_duration:(\d+\.?\d*)", out)]


def detect_silence(path: str) -> list[float]:
    out = _run([
        "ffmpeg", "-hide_banner", "-i", path,
        "-af", "silencedetect=n=-30dB:d=2.0", "-f", "null", "-",
    ])
    return [float(m) for m in re.findall(r"silence_duration:\s*(\d+\.?\d*)", out)]


def _volumedetect(path: str, *, ss: float | None = None, t: float | None = None) -> dict[str, float]:
    cmd = ["ffmpeg", "-hide_banner"]
    if ss is not None:
        cmd += ["-ss", str(ss)]
    if t is not None:
        cmd += ["-t", str(t)]
    cmd += ["-i", path, "-af", "volumedetect", "-f", "null", "-"]
    out = _run(cmd)
    res: dict[str, float] = {}
    for key in ("mean_volume", "max_volume"):
        m = re.search(rf"{key}:\s*(-?\d+\.?\d*)\s*dB", out)
        if m:
            res[key] = float(m.group(1))
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--min", type=float, default=None, help="最短时长(s)")
    ap.add_argument("--max", type=float, default=None, help="最长时长(s)")
    args = ap.parse_args()

    if not shutil.which("ffprobe") or not shutil.which("ffmpeg"):
        print("FAIL · ffprobe/ffmpeg 未安装", file=sys.stderr)
        return 1

    errors: list[str] = []
    warns: list[str] = []

    dur = probe_duration(args.video)
    if dur is None or dur <= 0:
        print(f"FAIL · 无法解析或时长为 0：{args.video}", file=sys.stderr)
        return 1
    print(f"时长 · {dur:.1f}s")
    if args.min and dur < args.min:
        errors.append(f"时长 {dur:.1f}s < 下限 {args.min}s")
    if args.max and dur > args.max:
        errors.append(f"时长 {dur:.1f}s > 上限 {args.max}s")

    blacks = detect_black(args.video)
    bad_black = [b for b in blacks if b >= BLACK_MIN_S]
    print(f"黑帧 · 检出 {len(blacks)} 段，其中 ≥{BLACK_MIN_S}s：{len(bad_black)}")
    if bad_black:
        errors.append(f"纯黑帧 ≥{BLACK_MIN_S}s ×{len(bad_black)}（最长 {max(bad_black):.1f}s）")

    sils = detect_silence(args.video)
    bad_sil = [s for s in sils if s >= SILENCE_MIN_S]
    print(f"静音 · 检出 {len(sils)} 段，其中 ≥{SILENCE_MIN_S}s 死区：{len(bad_sil)}")
    if bad_sil:
        errors.append(f"沉默钉子 ≥{SILENCE_MIN_S}s ×{len(bad_sil)}（最长 {max(bad_sil):.1f}s）")

    head = _volumedetect(args.video, ss=0, t=HEAD_WINDOW_S)
    mv = head.get("mean_volume")
    if mv is None:
        warns.append("前 6s 无音频流或无法测响度")
    else:
        print(f"前{HEAD_WINDOW_S:.0f}s mean_volume · {mv:.1f}dB (门 ≥{HEAD_RMS_MIN_DB})")
        if mv < HEAD_RMS_MIN_DB:
            errors.append(f"前 6s 死区：mean_volume {mv:.1f}dB < {HEAD_RMS_MIN_DB}dB")

    full = _volumedetect(args.video)
    xv = full.get("max_volume")
    if xv is not None:
        print(f"全片 max_volume · {xv:.1f}dB (爆音门 <{CLIP_MAX_DB})")
        if xv >= CLIP_MAX_DB:
            warns.append(f"疑似爆音削波：max_volume {xv:.1f}dB")

    print("字幕 · HTML 帧 overlay（烧进画面），跳过轨检测")

    print("—" * 20)
    for w in warns:
        print(f"WARN · {w}")
    if errors:
        for e in errors:
            print(f"FAIL · {e}", file=sys.stderr)
        print(f"\n❌ 成片体检 FAIL（{len(errors)} 项）· fail-closed", file=sys.stderr)
        return 1
    print("✅ 成片体检 PASS" + (f"（{len(warns)} WARN）" if warns else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
