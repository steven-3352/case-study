"""流水线定义：六步声明式契约。

调整/增删步骤只改这里，不动控制器。
每步除输入输出外，还声明 tool_name / purpose / outputs_desc，
供 CLI 与 Codex 统一渲染「执行透明化」提示。
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
        tool_name="intake_validate",
        purpose="收下用户素材并校验格式，确认音乐/歌词/人物/意图齐全可用",
        outputs_desc={
            "manifest.yaml":        "物料清单（每个文件的路径与类型）",
            "validation_report.md": "校验报告（哪些通过、哪些要补）",
            "intent.md":            "创作意图（用户想表达什么）",
        },
    ),
    StepSpec(
        step_id="01_analysis",
        title="LLM 分析 → 导演规划 + 故事框架",
        input_from=["00_intake"],
        prompts=["analysis.director.md", "analysis.lyrics_segment.md",
                 "analysis.character.md"],
        tool=tools.llm_analyze,
        outputs=["beats.json", "lyrics_semantic.json", "music_map.yaml",
                 "character_map.yaml", "story.md", "title_card.yaml"],
        approval=True,
        unit_kind="step",
        tool_name="llm_analyze",
        purpose="把歌词/音乐/人物/意图交给 LLM，产出导演规划与故事框架",
        outputs_desc={
            "story.md":             "故事框架（人可读总览）",
            "beats.json":           "音乐节拍与段落数据",
            "lyrics_semantic.json": "歌词逐行语义分段",
            "music_map.yaml":       "音乐结构地图（时长/段落）",
            "character_map.yaml":   "人物关系与导演功能",
            "title_card.yaml":      "标题卡/美术字数据契约（开场/结尾大标题+印章+样式）",
        },
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
        tool_name="llm_storyboard",
        purpose="按故事框架拆出逐镜分镜脚本，并规划背景场景组",
        outputs_desc={
            "storyboard.md":     "分镜脚本（人可读，逐镜说明）",
            "shots.yaml":         "镜头列表（编号/时长/动作数据）",
            "scene_groups.yaml":  "场景组（哪些镜头共用背景）",
        },
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
        tool_name="gen_keyframe",
        purpose="先生成背景底图，再合成人物，产出每镜首帧图",
        outputs_desc={
            "keyframes_index.yaml": "首帧图索引（每镜对应哪张图 + 生成参数）",
        },
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
        tool_name="gen_video",
        purpose="用首帧图跑 Seedance i2v，逐镜生成视频片段（9:16 / 720p）",
        outputs_desc={
            "shots_index.yaml": "视频片段索引（每镜对应哪段视频 + 时长）",
        },
    ),
    StepSpec(
        step_id="05_delivery",
        title="合成 + 字幕 + 美术字 + 剪辑",
        input_from=["04_shots", "00_intake", "01_analysis"],
        prompts=[],
        tool=tools.compose,
        outputs=["final.mp4", "subtitle.ass", "title_cards.json", "delivery_report.md"],
        approval=True,
        unit_kind="step",
        tool_name="compose",
        purpose="把所有片段按时间码拼接，对齐音乐、嵌字幕、叠大标题艺术字，产出成片",
        outputs_desc={
            "final.mp4":           "最终成片",
            "subtitle.ass":        "字幕文件（已嵌入成片）",
            "title_cards.json":    "大标题艺术字 spec（读 title_card.yaml，交 paperdoll 引擎渲染）",
            "delivery_report.md":  "交付报告（时长/规格/清单）",
        },
    ),
]

STEP_ORDER: list[str] = [s.step_id for s in STEPS]
STEP_BY_ID: dict[str, StepSpec] = {s.step_id: s for s in STEPS}
