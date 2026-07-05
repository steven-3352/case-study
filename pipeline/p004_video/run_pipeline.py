#!/usr/bin/env python3
"""P004 视频编排 · lib 版 · 从 pipeline_config.yaml 驱动.

用法：
    # 新内容首渲推荐顺序（VO 先锁 · 避免整片重合成返工）：
    #   1) --step vo         合成并锁定 VO → seg_timing.json（打印 scene realign 建议）
    #   2) 据实测 seg_timing 调 pipeline_config.yaml 的 scenes/overlays（不再按估算值）
    #   3) --step preview     ship gate + 底片（复用已锁 VO · 不重掷 MiniMax 时长）
    #   4) --step platforms   三平台字幕 + overlay
    # --step all 也可，但 VO 已锁后重跑 all 会复用 VO（不再重合成），改稿即时生效。
    python3 pipeline/p004_video/run_pipeline.py --config <yaml> --step all

    # 只跑其中一步（tts 崩了修完不想重跑其他）
    python3 pipeline/p004_video/run_pipeline.py --config <yaml> --step vo
    python3 pipeline/p004_video/run_pipeline.py --config <yaml> --step preview
    python3 pipeline/p004_video/run_pipeline.py --config <yaml> --step platforms
    # VO 确需重合成（换 voice_id / 改 text）才加 --force-vo

步骤：
    ui        : 生成 UI PNG（本 orchestrator 不承担 HTML 渲染 · 由 gen_ui_<content>.py 独立跑）
    vo        : 合成 VO 分段 → concat → loudnorm → seg_timing.json
    preview   : 底片 · UI/B-roll → clip → concat → 挂 VO
    platforms : 三平台差异化字幕烧录 + drawtext overlay → <platform>/video_no_bgm.mp4
    all       : vo → preview → platforms（ui 独立跑，因为设计上是 HTML 渲染）

W28D01-D06 golden reference 走 build_wXXdYY_preview.py + gen_vo_wXXdYY.py（不动）。
W29+ 每条新内容写 pipeline_config.yaml 走本 orchestrator。
"""
from __future__ import annotations

import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import yaml  # noqa: E402

from pipeline.p004_video.lib import config as cfg_mod  # noqa: E402
from pipeline.p004_video.lib import render, tts as tts_lib  # noqa: E402
from pipeline.p004_video.lib.ffmpeg import dur  # noqa: E402
from pipeline.p004_video.lib.platforms import render_platform  # noqa: E402
from pipeline.p004_video.lib.sfx import mix_sfx_with_vo  # noqa: E402
from pipeline.tts.gen_speech import synthesize_text  # noqa: E402

STEPS = ("ui", "vo", "preview", "platforms", "all")
SFX_CATALOG_PATH = PROJECT_ROOT / "assets" / "sfx" / "catalog.yaml"


def _write_tts_config_override(cfg: cfg_mod.PipelineConfig) -> pathlib.Path:
    """按 cfg.tts_voice_id / base_speed 覆盖默认 config.yaml · 写到 p004_video/_<id>_tts_config.yaml."""
    base_path = PROJECT_ROOT / "pipeline" / "tts" / "config.yaml"
    base = yaml.safe_load(base_path.read_text(encoding="utf-8"))
    if cfg.tts_voice_id:
        base.setdefault("minimax", {})["voice_id"] = cfg.tts_voice_id
    base.setdefault("minimax", {})["speed"] = cfg.tts_base_speed
    out = ROOT / f"_{cfg.content_id.lower()}_tts_config.yaml"
    out.write_text(yaml.safe_dump(base, allow_unicode=True), encoding="utf-8")
    return out


def step_vo(cfg: cfg_mod.PipelineConfig, force: bool = False) -> None:
    """VO 合成 · segments → padded → concat → loudnorm.

    VO 先锁（idempotent）：已有 vo_<id>.mp3 + seg_timing.json 时默认复用，不重掷
    MiniMax 时长骰子。改稿后据实测 seg_timing 调 scenes/overlays，再跑 preview/platforms
    即可——不会因 --step all 又重合成把时间线换掉。要强制重合成传 --force-vo。
    """
    if not force and cfg.vo_mp3.exists() and cfg.timing_json.exists():
        total = dur(cfg.vo_mp3)
        print(f"♻ VO 复用 · 已锁 {total:.2f}s · {cfg.vo_mp3}（--force-vo 强制重合成）")
        suggestions = render.suggest_scene_realign(list(cfg.scenes), cfg.timing_json)
        render.print_realign_report(suggestions)
        return

    cfg.audio_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"vo_{cfg.content_id.lower()}"
    tts_cfg_path = _write_tts_config_override(cfg)

    def _synth(text: str, out: pathlib.Path, emotion: str, speed: float) -> str:
        return synthesize_text(text, out, config_path=tts_cfg_path, emotion=emotion, speed=speed)

    listf, timing, engines = tts_lib.synthesize_segments(
        list(cfg.vo_segments),
        cfg.audio_dir,
        prefix=prefix,
        synthesize_text=_synth,
    )
    final_mp3 = tts_lib.concat_with_loudnorm(listf, cfg.audio_dir, prefix=prefix)
    total = dur(final_mp3)
    tts_lib.write_timing_json(timing, engines, total, cfg.timing_json)
    print(f"✓ VO 合成 · 总长 {total:.2f}s · {final_mp3}")
    print(f"  时间线：{cfg.timing_json}")

    # D04 教训：VO 合成后立即报告 scene realign 建议 · 防 preview/platforms 才发现 CTA 裁掉
    suggestions = render.suggest_scene_realign(list(cfg.scenes), cfg.timing_json)
    render.print_realign_report(suggestions)


def step_preview(cfg: cfg_mod.PipelineConfig) -> None:
    """底片 · scenes → clips → concat → attach VO."""
    if not cfg.vo_mp3.exists():
        raise FileNotFoundError(f"VO 未生成: {cfg.vo_mp3} · 先跑 --step vo")

    # D04 教训 · CTA 完整性 fail-closed 门（preview 前拦）
    passed, reason = render.check_ship_gate(list(cfg.scenes), cfg.timing_json)
    if not passed:
        print(f"❌ CTA ship gate FAIL: {reason}", file=sys.stderr)
        print(f"   见 memory tts-estimate-duration-pre-synth · 修 pipeline_config.yaml.scenes 后重跑 --step preview",
              file=sys.stderr)
        sys.exit(2)
    print(f"✓ {reason}")

    render.concat_video_only(list(cfg.scenes), cfg.clips_dir, cfg.video_only_mp4)
    print(f"✓ 视频轨拼接 · {cfg.video_only_mp4}")

    vo_normalized = cfg.audio_dir / f"{cfg.vo_mp3.stem}_loudnorm.mp3"
    render.normalize_vo(cfg.vo_mp3, vo_normalized)

    # sfx 音效层 · memory feedback_sfx-layer-required
    # audio_plan 缺失 / sfx.enabled=false / 全 gap → 透传 VO；有 wav → amix
    audio_plan_path = cfg.content_root / "audio_plan.yaml"
    vo_with_sfx = cfg.audio_dir / f"{cfg.vo_mp3.stem}_with_sfx.mp3"
    sfx_report = mix_sfx_with_vo(
        vo_mp3=vo_normalized,
        audio_plan_yaml=audio_plan_path,
        catalog_yaml=SFX_CATALOG_PATH,
        out_mp3=vo_with_sfx,
        project_root=PROJECT_ROOT,
    )
    print(f"[sfx] {sfx_report.format()}")
    if sfx_report.gap_report_path:
        print(f"      gap 报告 · {sfx_report.gap_report_path}")

    render.attach_vo(cfg.video_only_mp4, vo_with_sfx, cfg.preview_mp4)
    total = dur(cfg.preview_mp4)
    print(f"✓ 底片合成 · 总长 {total:.2f}s · {cfg.preview_mp4}")

    seg_total, plan_total, delta = render.sanity_check_timing(list(cfg.scenes), cfg.timing_json)
    warn = "⚠" if delta > 1.0 else "✓"
    print(f"[timing sanity] seg {seg_total:.2f}s vs plan {plan_total:.2f}s · Δ={delta:.2f}s {warn}")


def step_platforms(cfg: cfg_mod.PipelineConfig) -> None:
    """三平台差异化 · ass + drawtext + 一次 ffmpeg."""
    if not cfg.preview_mp4.exists():
        raise FileNotFoundError(f"底片未生成: {cfg.preview_mp4} · 先跑 --step preview")
    if not cfg.timing_json.exists():
        raise FileNotFoundError(f"seg_timing 未生成: {cfg.timing_json} · 先跑 --step vo")

    for spec in cfg.platforms:
        out_dir = cfg.content_root / spec.name
        r = render_platform(
            spec,
            src_mp4=cfg.preview_mp4,
            timing_json=cfg.timing_json,
            out_dir=out_dir,
            overlays=list(cfg.overlays),
            crf=cfg.crf,
        )
        print(f"✓ {spec.name:<7} · {r.duration_s:5.2f}s · {r.size_mb:5.1f} MB · {r.out_mp4}")


def main() -> None:
    ap = argparse.ArgumentParser(description="P004 pipeline orchestrator")
    ap.add_argument("--config", required=True, type=pathlib.Path,
                    help="pipeline_config.yaml 相对项目根或绝对路径")
    ap.add_argument("--step", choices=STEPS, default="all")
    ap.add_argument("--force-vo", action="store_true",
                    help="强制重合成 VO（默认复用已锁的 vo_<id>.mp3 · 防 MiniMax 时长重掷）")
    args = ap.parse_args()

    config_path = args.config
    if not config_path.is_absolute():
        config_path = (PROJECT_ROOT / config_path).resolve()
    if not config_path.exists():
        print(f"❌ config 不存在: {config_path}", file=sys.stderr)
        sys.exit(1)

    cfg = cfg_mod.load(config_path, PROJECT_ROOT)
    print(f"→ pipeline · {cfg.content_id} · step={args.step}")
    print(f"  content_root: {cfg.content_root}")

    if args.step in ("vo", "all"):
        step_vo(cfg, force=args.force_vo)
    if args.step in ("preview", "all"):
        step_preview(cfg)
    if args.step in ("platforms", "all"):
        step_platforms(cfg)
    if args.step == "ui":
        print("ⓘ ui step 不由本 orchestrator 承担 · 请跑对应 gen_ui_<content>.py（HTML → PNG）")


if __name__ == "__main__":
    main()
