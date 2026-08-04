"""流水线定义：六步声明式契约。

调整/增删步骤只改这里，不动控制器。
"""
from __future__ import annotations

from . import tools
from .contracts import StepSpec

# 六步：物料 → 分析 → 分镜 → 关键帧 → 视频 → 合成
STEPS: list[StepSpec] = [
    StepSpec(
        step_id="00_intake",
        title="物料进来 + 校验",
        input_from=[],
        prompts=[],
        tool=tools.intake_validate,
        outputs=["manifest.yaml", "validation_report.md", "intent.md"],
        approval=True,
        unit_kind="step",
    ),
    StepSpec(
        step_id="01_analysis",
        title="LLM 分析 → 导演规划 + 故事框架",
        input_from=["00_intake"],
        prompts=["analysis.director.md", "analysis.lyrics_segment.md",
                 "analysis.character.md"],
        tool=tools.llm_analyze,
        outputs=["beats.json", "lyrics_semantic.json", "music_map.yaml",
                 "character_map.yaml", "story.md"],
        approval=True,
        unit_kind="step",
    ),
    StepSpec(
        step_id="02_storyboard",
        title="故事框架 → 分镜脚本 + 背景规划",
        input_from=["01_analysis"],
        prompts=["storyboard.creative.md", "storyboard.quality_review.md"],
        tool=tools.llm_storyboard,
        outputs=["shots.yaml", "storyboard.md", "scene_groups.yaml"],
        approval=True,
        unit_kind="shot",
    ),
    StepSpec(
        step_id="03_keyframes",
        title="关键帧：人物 + 背景 → 首帧图",
        input_from=["02_storyboard", "00_intake"],
        prompts=["image.background.md", "image.keyframe.md", "translate.md"],
        tool=tools.gen_keyframe,
        outputs=["keyframes_index.yaml"],
        approval=True,
        unit_kind="shot",
    ),
    StepSpec(
        step_id="04_shots",
        title="每镜视频（i2v · 单路径 · 付费锁）",
        input_from=["03_keyframes"],
        prompts=["video.motion.md", "translate.md"],
        tool=tools.gen_video,
        outputs=["shots_index.yaml"],
        approval=True,
        unit_kind="shot",
    ),
    StepSpec(
        step_id="05_delivery",
        title="合成 + 字幕 + 美术字 + 剪辑",
        input_from=["04_shots", "00_intake", "01_analysis"],
        prompts=[],
        tool=tools.compose,
        outputs=["final.mp4", "subtitle.ass", "delivery_report.md"],
        approval=True,
        unit_kind="step",
    ),
]

STEP_ORDER: list[str] = [s.step_id for s in STEPS]
STEP_BY_ID: dict[str, StepSpec] = {s.step_id: s for s in STEPS}
