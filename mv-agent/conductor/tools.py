"""工具层 — 调用 mv_platform 公共工具库的实际实现。

调用链：conductor → tools.py → mv_platform.*

每个工具签名统一：
    run(inputs, out_dir, params, prompt_file=None) -> ToolResult

M1：占位产物 + 真实提示词加载（从 mv_platform.prompt_catalog）
M2：逐个替换为真实 API 调用（LLM / 图像 / 视频）
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

# ── 加载 .env（mv-agent/.env）
try:
    from dotenv import load_dotenv
    _env_file = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(_env_file, override=False)
except ImportError:
    pass  # python-dotenv 可选；用户可在 shell 里直接 export

# ── 复用项目公共工具库 mv_platform
# 把项目根目录（mv-agent 的上两级）加入路径，让 mv_platform 可以 import
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    from mv_platform.application.prompt_catalog import (
        DEFAULT_SYSTEM_PROMPTS,
        DEFAULT_PROMPTS,
    )
    from mv_platform.application.control_plane import (
        ENV_MAP,
        detect_local_whisper_model,
    )
    _MV_PLATFORM_OK = True
except ImportError:
    # 独立运行（mv_platform 不在路径）时回退到空字典
    DEFAULT_SYSTEM_PROMPTS = {}
    DEFAULT_PROMPTS = {}
    ENV_MAP = {}
    _MV_PLATFORM_OK = False

from .contracts import ToolResult


# ──────────────────────────────────────────────────────────────────────────────
# 配置辅助
# ──────────────────────────────────────────────────────────────────────────────

def _load_provider_config() -> dict:
    """从环境变量读取 provider 配置，变量名遵循 mv_platform.control_plane.ENV_MAP。"""
    cfg: dict = {}
    for dotted, env_key in ENV_MAP.items():
        section, key = dotted.split(".", 1)
        val = os.environ.get(env_key, "")
        if val:
            cfg.setdefault(section, {})[key] = val
    return cfg


def _get_system_prompt(catalog_key: str, prompt_file: Optional[Path] = None) -> str:
    """提示词读取策略：
      1. 用户提供的 prompt_file（可覆盖）
      2. mv_platform.prompt_catalog 里的默认值
      3. 占位文字
    """
    if prompt_file and Path(prompt_file).is_file():
        return Path(prompt_file).read_text(encoding="utf-8").strip()
    txt = DEFAULT_SYSTEM_PROMPTS.get(catalog_key, "")
    if txt:
        return txt
    return f"# 提示词占位 [{catalog_key}]\n请在 prompts/ 目录下添加对应文件。"


def _write(out_dir: Path, name: str, body: str) -> str:
    p = Path(out_dir) / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return name


# ──────────────────────────────────────────────────────────────────────────────
# 六步工具实现（M1 占位 · M2 接真实 API）
# ──────────────────────────────────────────────────────────────────────────────

def intake_validate(inputs, out_dir, params, prompt_file=None) -> ToolResult:
    """00_intake — 物料进来 + 校验。

    M2 接入：调用 mv_platform 物料校验 + faster-whisper 对齐。
    """
    out_dir = Path(out_dir)
    file_list = [str(f) for f in (inputs or [])]

    _write(out_dir, "manifest.yaml",
           "# 物料清单（M2 由校验工具填充）\nversion: 1\nfiles:\n" +
           "".join(f"  - {f}\n" for f in file_list))

    _write(out_dir, "validation_report.md",
           "# 物料校验报告\n\n"
           "> M2 接入后由校验工具自动填充。\n\n"
           "## 检查项\n- [ ] 音频文件格式\n- [ ] 歌词时间码\n"
           "- [ ] 人物图片分辨率\n- [ ] 创作意图文本\n")

    _write(out_dir, "intent.md",
           "# 创作意图\n\n> 待用户填写 / LLM 提炼。\n")

    return ToolResult(
        ok=True,
        outputs=["manifest.yaml", "validation_report.md", "intent.md"],
        meta={"step": "00_intake", "mv_platform": _MV_PLATFORM_OK},
    )


def llm_analyze(inputs, out_dir, params, prompt_file=None) -> ToolResult:
    """01_analysis — LLM 分析 → 导演规划 + 故事框架。

    M2 接入：
      - DEFAULT_SYSTEM_PROMPTS["lyrics.semantic_segment.requested"] → 歌词分段
      - DEFAULT_SYSTEM_PROMPTS["relationship_map.draft_requested"]  → 人物关系
      - _load_provider_config() 取 LLM API key / model
    """
    out_dir = Path(out_dir)
    sys_prompt = _get_system_prompt("lyrics.semantic_segment.requested", prompt_file)

    _write(out_dir, "beats.json",
           '{\n  "_note": "M2 由 LLM 填充",\n  "segments": []\n}\n')
    _write(out_dir, "lyrics_semantic.json",
           '{\n  "_note": "M2 由 LLM 填充",\n  "lines": []\n}\n')
    _write(out_dir, "music_map.yaml",
           "# 音乐结构地图（M2 填充）\ntotal_duration: 0\nsections: []\n")
    _write(out_dir, "character_map.yaml",
           "# 人物关系地图（M2 填充）\ncharacters: []\n")
    _write(out_dir, "story.md",
           "# 故事框架\n\n> M2 接入后由 LLM 生成。\n\n"
           f"**使用提示词**：{getattr(prompt_file, 'name', str(prompt_file))}\n\n"
           f"**提示词预览**：\n```\n{sys_prompt[:200]}...\n```\n")

    return ToolResult(
        ok=True,
        outputs=["beats.json", "lyrics_semantic.json", "music_map.yaml",
                 "character_map.yaml", "story.md"],
        meta={"step": "01_analysis", "mv_platform": _MV_PLATFORM_OK,
              "prompt_key": "lyrics.semantic_segment.requested"},
    )


def llm_storyboard(inputs, out_dir, params, prompt_file=None) -> ToolResult:
    """02_storyboard — 故事框架 → 分镜脚本 + 背景规划。

    M2 接入：
      - DEFAULT_SYSTEM_PROMPTS["visual_score.creative_draft_requested"] → 创意分镜
      - DEFAULT_SYSTEM_PROMPTS["visual_score.quality_review_requested"] → 质量审查
    """
    out_dir = Path(out_dir)
    sys_prompt = _get_system_prompt("visual_score.creative_draft_requested", prompt_file)

    _write(out_dir, "shots.yaml",
           "# 分镜列表（M2 由 LLM 填充）\nshots:\n"
           "  - id: SH001\n    duration: 5\n    description: 占位镜头\n")
    _write(out_dir, "storyboard.md",
           "# 分镜脚本\n\n> M2 接入后由 LLM 生成。\n\n"
           f"**提示词预览**：\n```\n{sys_prompt[:200]}...\n```\n")
    _write(out_dir, "scene_groups.yaml",
           "# 场景组（M2 填充）\ngroups: []\n")

    return ToolResult(
        ok=True,
        outputs=["shots.yaml", "storyboard.md", "scene_groups.yaml"],
        meta={"step": "02_storyboard", "mv_platform": _MV_PLATFORM_OK},
    )


def gen_keyframe(inputs, out_dir, params, prompt_file=None) -> ToolResult:
    """03_keyframes — 首帧图（背景 + 人物合成）。

    M2 接入：
      - DEFAULT_SYSTEM_PROMPTS["image.background.generate_requested"] → 背景
      - DEFAULT_SYSTEM_PROMPTS["image.keyframe.generate_requested"]   → 首帧
      - _load_provider_config()["image"] 取图像 API
    """
    out_dir = Path(out_dir)
    cfg = _load_provider_config()
    image_cfg = cfg.get("image", {})

    _write(out_dir, "keyframes_index.yaml",
           "# 关键帧索引（M2 由图像生成工具填充）\n"
           f"# 当前配置：model={image_cfg.get('model', '未配置')}\n"
           "keyframes: []\n")

    return ToolResult(
        ok=True,
        outputs=["keyframes_index.yaml"],
        meta={"step": "03_keyframes", "mv_platform": _MV_PLATFORM_OK,
              "image_model": image_cfg.get("model", "")},
    )


def gen_video(inputs, out_dir, params, prompt_file=None) -> ToolResult:
    """04_shots — 逐镜视频（Seedance i2v）。

    M2 接入：
      - DEFAULT_SYSTEM_PROMPTS["video.shot.generate_requested"] → 视频提示词
      - _load_provider_config()["video"] 取 Seedance API（SEEDANCE_API_KEY）
      - 规格锁定：9:16 / 720p（同 mv_platform 服务端）
    """
    out_dir = Path(out_dir)
    cfg = _load_provider_config()
    video_cfg = cfg.get("video", {})

    _write(out_dir, "shots_index.yaml",
           "# 视频片段索引（M2 由 Seedance i2v 填充）\n"
           f"# 当前配置：model={video_cfg.get('model', '未配置')}\n"
           "# 规格：9:16 / 720p（固定）\n"
           "shots: []\n")

    return ToolResult(
        ok=True,
        outputs=["shots_index.yaml"],
        meta={"step": "04_shots", "mv_platform": _MV_PLATFORM_OK,
              "video_model": video_cfg.get("model", "")},
    )


def compose(inputs, out_dir, params, prompt_file=None) -> ToolResult:
    """05_delivery — 合成 + 字幕 + 美术字 + 剪辑。

    M2 接入：调用 ffmpeg 合成所有片段 + 嵌字幕。
    路径工具：_load_provider_config()["paths"]["ffmpeg_path"]
    """
    out_dir = Path(out_dir)
    cfg = _load_provider_config()
    ffmpeg = cfg.get("paths", {}).get("ffmpeg_path", "") or "ffmpeg"

    _write(out_dir, "final.mp4",
           f"# 占位（M2 由 ffmpeg 合成）\n# ffmpeg 路径：{ffmpeg}\n")
    _write(out_dir, "subtitle.ass",
           "[Script Info]\nTitle: MV 字幕占位\n\n[Events]\n")
    _write(out_dir, "delivery_report.md",
           "# 交付报告\n\n> M2 接入后由合成工具填充。\n\n"
           f"- ffmpeg: `{ffmpeg}`\n- 状态：占位\n")

    return ToolResult(
        ok=True,
        outputs=["final.mp4", "subtitle.ass", "delivery_report.md"],
        meta={"step": "05_delivery", "mv_platform": _MV_PLATFORM_OK,
              "ffmpeg": ffmpeg},
    )
