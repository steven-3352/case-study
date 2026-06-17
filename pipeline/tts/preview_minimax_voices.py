#!/usr/bin/env python3
"""批量试听 MiniMax speech-2.8-turbo 音色（t2a_async_v2）.

凭证见仓库根目录 `.env`（MINIMAX_API_KEY + MINIMAX_BASE_URL 中转根地址）

  python3 pipeline/tts/preview_minimax_voices.py
  python3 pipeline/tts/preview_minimax_voices.py --voice "Chinese (Mandarin)_Gentleman"
"""
from __future__ import annotations

import argparse
import copy
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import pipeline.env_loader  # noqa: F401 — 加载 .env
from pipeline.env_loader import api_base

from pipeline.tts.gen_speech import load_config, CFG_PATH
from pipeline.tts.minimax_client import create_async_task, download_file, poll_async_task

OUT = ROOT / "pipeline" / "tts" / "_previews"

# P001 口播风格：中年男、第一人称复盘、口语，避免播音腔/青涩/霸道
CANDIDATES = [
    ("01_radio_host", "Chinese (Mandarin)_Radio_Host", "电台男主播"),
    ("02_gentleman", "Chinese (Mandarin)_Gentleman", "温润男声"),
    ("03_sincere_adult", "Chinese (Mandarin)_Sincere_Adult", "真诚青年"),
    ("04_southern_man", "Chinese (Mandarin)_Southern_Young_Man", "南方小哥"),
    ("05_reliable_exec", "Chinese (Mandarin)_Reliable_Executive", "沉稳高管"),
    ("06_jingying_jp", "male-qn-jingying-jingpin", "精英青年-beta"),
]

SAMPLE = (
    "第五天一看数据，我傻眼了。"
    "做了二十年互联网，还是会翻车。"
    "曝光有了，留资寥寥无几。"
    "复盘下来，问题不在系统，在内容太机器。"
)


def synth_one(cfg: dict, voice_id: str, label: str, out: pathlib.Path) -> None:
    key = os.environ["MINIMAX_API_KEY"]
    group_id = os.getenv("MINIMAX_GROUP_ID") or cfg.get("minimax", {}).get("group_id")
    one = copy.deepcopy(cfg)
    one.setdefault("minimax", {})["voice_id"] = voice_id
    print(f"  → {label} ({voice_id}) …", flush=True)
    task_id, _ = create_async_task(SAMPLE, one, key=key, group_id=group_id)
    file_id = poll_async_task(task_id, one, key=key, group_id=group_id)
    out.write_bytes(download_file(file_id, one, key=key, group_id=group_id))
    print(f"    OK {out.name}")


def main() -> None:
    ap = argparse.ArgumentParser(description="MiniMax 音色试听")
    ap.add_argument("--config", type=pathlib.Path, default=CFG_PATH)
    ap.add_argument("--voice", help="只测单个 voice_id")
    ap.add_argument("-o", "--output-dir", type=pathlib.Path, default=OUT)
    args = ap.parse_args()

    if not os.getenv("MINIMAX_API_KEY"):
        sys.exit("请在仓库根目录 .env 中设置 MINIMAX_API_KEY")

    cfg = load_config(args.config.resolve())
    host = api_base("MINIMAX_BASE_URL", cfg=cfg["minimax"].get("api_host"), default="https://api.minimaxi.com")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    items = CANDIDATES
    if args.voice:
        items = [("custom", args.voice, args.voice)]

    print(f"model: {cfg['minimax']['model']} · api: {host}")
    print(f"样本文案 {len(SAMPLE)} 字 · 输出 → {args.output_dir}\n")

    for slug, vid, label in items:
        out = args.output_dir / f"{slug}.mp3"
        try:
            synth_one(cfg, vid, label, out)
        except Exception as e:
            print(f"    ✗ {label}: {e}")

    print("\n试听建议（P001 复盘口播）：")
    print("  优先：电台男主播 / 温润男声 / 沉稳高管")
    print("  备选：真诚青年 / 南方小哥（更口语）")
    print("  慎选：精英青年（偏广告）、青涩/霸道系列（不像真人复盘）")


if __name__ == "__main__":
    main()
