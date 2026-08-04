#!/usr/bin/env python3
"""下载本地 faster-whisper medium 模型（跨平台）。

- 目标目录用 Path.home()，Windows / macOS / Linux 一致：
    ~/.local/share/mvstudio/models/faster-whisper-medium/
- 该目录正是 mv_platform.control_plane.detect_local_whisper_model() 的扫描根之一，
  下完即被自动发现，用户无需在 .env 手填 whisper 路径。
- 幂等：已存在 model.bin 则跳过，不重复下载（medium 约 1.5GB）。

单独运行：python download_whisper.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# 与 mv_platform 扫描目录、size 关键字保持一致（名字里必须含 "medium"）
MODEL_SIZE = "medium"
TARGET_DIR = Path.home() / ".local" / "share" / "mvstudio" / "models" / "faster-whisper-medium"


def main() -> int:
    marker = TARGET_DIR / "model.bin"
    if marker.is_file():
        print(f"✅ 模型已存在，跳过下载：{TARGET_DIR}")
        return 0

    try:
        from faster_whisper import download_model
    except ImportError:
        print("❌ 未安装 faster-whisper。先跑：pip install -r requirements.txt")
        return 1

    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📥 下载 faster-whisper [{MODEL_SIZE}] 到：{TARGET_DIR}")
    print("   首次约 1.5GB，请耐心等待……")

    try:
        # output_dir 直接落地到目标目录（复制而非软链，Windows 友好）
        download_model(MODEL_SIZE, output_dir=str(TARGET_DIR))
    except Exception as exc:  # 网络/磁盘等失败，给出可操作提示
        print(f"❌ 下载失败：{exc}")
        print("   可重试；或设置国内镜像后再跑：")
        print("     export HF_ENDPOINT=https://hf-mirror.com   # Windows: set HF_ENDPOINT=...")
        return 1

    if marker.is_file():
        print(f"✅ 完成：{TARGET_DIR}")
        return 0
    print("❌ 下载结束但未找到 model.bin，请重试。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
