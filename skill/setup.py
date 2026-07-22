#!/usr/bin/env python3
"""
Tonbirds-Content-Engine-Plugin · Environment Health Check
第一次使用前运行，验证 Python 版本、依赖包、系统工具、API Key 是否就绪。

用法:
  python3 skill/setup.py              # 读当前目录 .env
  python3 skill/setup.py --env .env   # 指定 .env 文件路径
"""

import sys
import subprocess
import importlib.util
import argparse
import os
from pathlib import Path

# ── ANSI 颜色 ──────────────────────────────────────────────────────
GREEN  = "\033[32m"
RED    = "\033[31m"
YELLOW = "\033[33m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

def ok(label, detail=""):
    print(f"  {GREEN}✓{RESET} {label:<42} {DIM}{detail}{RESET}")

def fail(label, detail=""):
    print(f"  {RED}✗{RESET} {label:<42} {RED}{detail}{RESET}")

def warn(label, detail=""):
    print(f"  {YELLOW}⚠{RESET} {label:<42} {YELLOW}{detail}{RESET}")

def section(title):
    print(f"\n{BOLD}{title}{RESET}")
    print("─" * 54)

# ── 简易 .env 解析（不依赖 python-dotenv）────────────────────────────
def load_dotenv_simple(path: str) -> dict:
    env = {}
    p = Path(path)
    if not p.exists():
        return env
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
    return env


def main():
    parser = argparse.ArgumentParser(description="Tonbirds plugin env health check")
    parser.add_argument("--env", default=".env",
                        help="Path to .env file (default: .env in cwd)")
    args = parser.parse_args()

    errors   = 0
    warnings = 0

    # ── 1. Python 版本 ──────────────────────────────────────────────
    section("1 · Python 版本")
    major, minor = sys.version_info[:2]
    ver_str = f"{major}.{minor}.{sys.version_info[2]}"
    if (major, minor) >= (3, 9):
        ok("Python ≥ 3.9", ver_str)
    else:
        fail("Python ≥ 3.9 required", f"当前 {ver_str}，请升级")
        errors += 1

    # ── 2. pip 包 ───────────────────────────────────────────────────
    section("2 · pip 依赖包")

    REQUIRED_PKGS = [
        ("requests",     "cap-stock-footage / cap-video-i2v"),
        ("openai",       "cap-image-gen / cap-video-i2v"),
        ("yaml",         "cap-tts / cap-video-i2v  (pyyaml)"),
        ("dotenv",       "cap-tts / 可选              (python-dotenv)"),
        ("edge_tts",     "cap-tts edge provider 保底"),
        ("pydantic",     "schema 验证"),
    ]

    OPTIONAL_PKGS = [
        ("librosa",      "音乐卡点 beat 检测（漫画/音乐/MV 风格用）"),
        ("PIL",          "图像预处理               (Pillow)"),
        ("playwright",   "HTML 截帧渲染             (P001/P004)"),
    ]

    for mod, note in REQUIRED_PKGS:
        found = importlib.util.find_spec(mod) is not None
        if found:
            ok(mod, note)
        else:
            fail(mod, f"未安装 · {note}")
            errors += 1

    for mod, note in OPTIONAL_PKGS:
        found = importlib.util.find_spec(mod) is not None
        if found:
            ok(mod, f"(可选) {note}")
        else:
            warn(mod, f"(可选未装) {note}")
            warnings += 1

    # ── 3. 系统工具 ─────────────────────────────────────────────────
    section("3 · 系统工具")

    TOOLS = [
        ("ffmpeg",  "视频合成 / BGM 叠轨 / 字幕烧录",  True),
        ("ffprobe", "成片体检 gate_check_media",        True),
        ("git",     "版本控制",                          True),
    ]

    for tool, note, required in TOOLS:
        try:
            res = subprocess.run(
                [tool, "--version"],
                capture_output=True, text=True, timeout=5
            )
            # ffmpeg/ffprobe/git 都在第一行输出版本号
            ver = res.stdout.splitlines()[0] if res.stdout else res.stderr.splitlines()[0]
            ok(tool, ver[:60])
        except FileNotFoundError:
            if required:
                fail(tool, f"未找到 · {note}")
                errors += 1
            else:
                warn(tool, f"(可选未装) {note}")
                warnings += 1
        except Exception as e:
            warn(tool, str(e)[:60])
            warnings += 1

    # ── 4. API Key 存在性检查（只 warn，不 fail） ────────────────────
    section(f"4 · API Key 检查  ({args.env})")

    # 优先读指定 .env，再叠加系统环境变量
    file_env = load_dotenv_simple(args.env)

    KEY_GROUPS = [
        ("cap-stock-footage", ["PEXELS_API_KEY"]),
        ("cap-video-i2v",     ["SEEDANCE_API_KEY", "SEEDANCE_BASE_URL"]),
        ("cap-tts (minimax)", ["MINIMAX_API_KEY", "MINIMAX_BASE_URL"]),
        ("cap-tts (volc)",    ["VOLC_TTS_APPID", "VOLC_TTS_TOKEN"]),
        ("cap-image-gen",     ["GPT_IMAGE_API_KEY", "GPT_IMAGE_BASE_URL"]),
    ]

    all_keys = set(k for _, ks in KEY_GROUPS for k in ks)
    combined  = {**file_env, **{k: v for k, v in os.environ.items() if k in all_keys}}

    if not Path(args.env).exists():
        warn(f".env 文件不存在", f"{args.env}  →  参考 skill/.env.example 创建")
        warnings += 1

    for cap, keys in KEY_GROUPS:
        missing = [k for k in keys if not combined.get(k)]
        present = [k for k in keys if combined.get(k)]
        if not missing:
            ok(cap, f"key 齐全 ({', '.join(present)})")
        else:
            warn(cap, f"缺 {', '.join(missing)}  (不用此 cap 可忽略)")
            warnings += 1

    # ── 5. 汇总 ────────────────────────────────────────────────────
    section("汇总")
    if errors == 0 and warnings == 0:
        print(f"  {GREEN}{BOLD}✓ 全部通过，环境就绪。{RESET}")
    elif errors == 0:
        print(f"  {YELLOW}{BOLD}⚠ 必要项通过，{warnings} 个可选项需关注（见上方 ⚠）。{RESET}")
    else:
        print(f"  {RED}{BOLD}✗ {errors} 个必要项缺失，请按上方提示安装后重跑。{RESET}")
        if warnings:
            print(f"  {YELLOW}  另有 {warnings} 个可选项警告。{RESET}")

    print()
    if errors:
        print(f"  {DIM}安装缺失包: pip install requests openai pyyaml edge-tts python-dotenv{RESET}")
        print(f"  {DIM}ffmpeg macOS: brew install ffmpeg  |  Linux: sudo apt install ffmpeg{RESET}")
        print(f"  {DIM}key 配置: cp skill/.env.example .env  →  填入各 API Key{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
