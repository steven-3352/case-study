"""流水线定义：六步声明式契约（ad-agent · 广告/视频创作）。

调整/增删步骤只改这里，不动控制器。step_id 沿用 mv-agent 命名（00_intake…05_delivery），
让 cli.py 的逐镜 shot 逻辑（仅 03_keyframes/04_shots）无缝复用。

保真主线：产品原图有两个身份——
  · 展示帧（display）：原图像素锁死 + AI 生成背景铺满画幅，100% 保真兜底
  · 生成镜（generated）：AI 首帧 → i2v，负责动感/氛围，允许漂移
02 分镜给每镜标 type(generated/display) 与 motion(static/ken_burns/i2v)。
"""
from __future__ import annotations

from . import tools
from .contracts import StepSpec

STEPS: list[StepSpec] = [
    StepSpec(
        step_id="00_intake",
        title="物料进来 + 校验",
        input_from=[],
        prompts=[],
        tool=tools.intake_validate,
        outputs=["manifest.yaml", "validation_report.md", "brief.md"],
        approval=True,
        unit_kind="step",
        tool_name="intake_validate",
        purpose="收下产品图/人物图 + 广告文本 + 画幅，校验格式齐不齐，读图片尺寸",
        outputs_desc={
            "manifest.yaml":        "物料清单（图片路径+尺寸+摘要 / 广告文本 / 画幅 / 用途）",
            "validation_report.md": "校验报告（哪些通过、哪些要补）",
            "brief.md":             "广告文本原文（人可读）",
        },
    ),
    StepSpec(
        step_id="01_analysis",
        title="LLM 分析需求 → 需求理解书",
        input_from=["00_intake"],
        prompts=["analysis.requirements.md"],
        tool=tools.llm_analyze,
        outputs=["requirements.md", "requirements.yaml"],
        approval=True,
        unit_kind="step",
        tool_name="llm_analyze",
        purpose="把广告文本+图片清单交给 LLM，提炼用途/卖点/人群/基调/CTA，产需求理解书",
        outputs_desc={
            "requirements.md":   "需求理解书（人可读 · 等你确认方向对不对）",
            "requirements.yaml": "结构化需求（用途/卖点/人群/基调/CTA/建议时长）",
        },
    ),
    StepSpec(
        step_id="02_storyboard",
        title="需求 → 视频故事 + 逐镜分镜",
        input_from=["01_analysis", "00_intake"],
        prompts=["storyboard.creative.md"],
        tool=tools.llm_storyboard,
        outputs=["shots.yaml", "storyboard.md", "story.md"],
        approval=True,
        unit_kind="shot",
        tool_name="llm_storyboard",
        purpose="按需求写视频故事，拆逐镜脚本，每镜标 generated(i2v) 或 display(产品展示帧)",
        outputs_desc={
            "story.md":      "视频故事线（人可读总览）",
            "storyboard.md": "分镜脚本（人可读逐镜表：类型/动作/画面）",
            "shots.yaml":    "镜头列表（id/type/motion/duration/product_ref/image_prompt/...）",
        },
    ),
    StepSpec(
        step_id="03_keyframes",
        title="关键帧：生成镜首帧 + 产品展示帧",
        input_from=["02_storyboard", "00_intake"],
        prompts=["image.background.md", "image.keyframe.md"],
        tool=tools.gen_keyframe,
        outputs=["keyframes_index.yaml"],
        approval=True,
        unit_kind="shot",
        tool_name="gen_keyframe",
        purpose="generated 镜→AI 画首帧；display 镜→产品原图贴到 AI 生成的背景上（像素不动）",
        outputs_desc={
            "keyframes_index.yaml": "首帧图索引（每镜对应哪张图 + 类型/动作 + 生成参数）",
        },
    ),
    StepSpec(
        step_id="04_shots",
        title="每镜视频（生成镜 i2v · 展示镜静态/推拉）",
        input_from=["03_keyframes"],
        prompts=["video.motion.md"],
        tool=tools.gen_video,
        outputs=["shots_index.yaml"],
        approval=True,
        unit_kind="shot",
        tool_name="gen_video",
        purpose="generated/i2v 镜→Seedance 出片；static/ken_burns 展示镜→ffmpeg 本地出片(免费)",
        outputs_desc={
            "shots_index.yaml": "视频片段索引（每镜对应哪段视频 + 时长 + 来源）",
        },
    ),
    StepSpec(
        step_id="05_delivery",
        title="合成 + 文字叠加 + 交付",
        input_from=["04_shots", "00_intake", "01_analysis"],
        prompts=[],
        tool=tools.compose,
        outputs=["final.mp4", "overlay.ass", "delivery_report.md"],
        approval=True,
        unit_kind="step",
        tool_name="compose",
        purpose="把所有片段按分镜顺序拼接，叠卖点/CTA 文字，产出成片（用户指定画幅）",
        outputs_desc={
            "final.mp4":          "最终成片（用户指定画幅）",
            "overlay.ass":        "文字叠加（卖点/CTA，已烧入成片）",
            "delivery_report.md": "交付报告（时长/画幅/镜头清单）",
        },
    ),
]

STEP_ORDER: list[str] = [s.step_id for s in STEPS]
STEP_BY_ID: dict[str, StepSpec] = {s.step_id: s for s in STEPS}
