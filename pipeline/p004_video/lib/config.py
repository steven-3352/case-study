"""pipeline_config.yaml 载入 · 每条内容一份，声明所有分镜/VO/字幕/平台参数.

结构示例（W29+ 每条内容 pipeline_config.yaml）:
    content_id: W29D01
    paths:
      root_rel: publish/2026-W29/D01-XXX
    ffmpeg:
      crf: 20
    tts:
      voice_id: male-qn-jingying-jingpin
      base_speed: 0.95
      segments:
        - sid: s1_silence
          target_start: 0.0
          target_dur: 3.0
          emotion: silence
          speed: 0.0
          text: "(0-3s 沉默钉子)"
          tail_pad: 0.0
        - sid: s2
          target_start: 3.0
          target_dur: 5.0
          emotion: neutral
          speed: 0.95
          text: "..."
          tail_pad: 0.15
    scenes:
      - name: M1_night_desk
        total_dur: 3.0
        clips:
          - src_type: broll
            src_rel: assets/broll/raw/office_desk_dusk_evening_empty__26609644.mp4
            duration: 2.0
          - src_type: img
            src_rel: build/assets_ui/01_lockscreen_2312.png
            duration: 1.0
    platforms:
      douyin: {subs_size: 42, margin_v: 200, max_cue_chars: 32, max_line_chars: 17}
      xhs:    {subs_size: 50, margin_v: 220, max_cue_chars: 26, max_line_chars: 14}
      weixin: {subs_size: 42, margin_v: 200, max_cue_chars: 32, max_line_chars: 17}
    overlays:
      - text: "23:12 · 又一次决心学英语"
        t_start: 2.0
        t_end: 3.0
        fontsize: 64
        y_expr: h-500
"""
from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from typing import Any

import yaml

from .platforms import DEFAULT_PLATFORMS, DrawTextOverlay, PlatformSpec
from .render import ClipSpec, SceneSpec
from .tts import VOSegment


@dataclass(frozen=True)
class PipelineConfig:
    content_id: str
    root: pathlib.Path            # 项目根（含 pipeline/ publish/ 等）
    content_root: pathlib.Path    # 本条 publish/ 目录
    crf: int
    tts_voice_id: str
    tts_base_speed: float
    vo_segments: tuple[VOSegment, ...]
    scenes: tuple[SceneSpec, ...]
    platforms: tuple[PlatformSpec, ...]
    overlays: tuple[DrawTextOverlay, ...]

    @property
    def build_dir(self) -> pathlib.Path:
        return self.content_root / "build"

    @property
    def audio_dir(self) -> pathlib.Path:
        return self.build_dir / "audio"

    @property
    def clips_dir(self) -> pathlib.Path:
        return self.build_dir / "clips"

    @property
    def final_dir(self) -> pathlib.Path:
        return self.build_dir / "final"

    @property
    def ui_dir(self) -> pathlib.Path:
        return self.build_dir / "assets_ui"

    @property
    def timing_json(self) -> pathlib.Path:
        return self.audio_dir / f"seg_timing_{self.content_id.lower()}.json"

    @property
    def vo_mp3(self) -> pathlib.Path:
        return self.audio_dir / f"vo_{self.content_id.lower()}.mp3"

    @property
    def preview_mp4(self) -> pathlib.Path:
        return self.final_dir / f"preview_no_bgm_{self.content_id.lower()}.mp4"

    @property
    def video_only_mp4(self) -> pathlib.Path:
        return self.final_dir / f"preview_video_only_{self.content_id.lower()}.mp4"


def _resolve(root: pathlib.Path, rel: str) -> pathlib.Path:
    p = pathlib.Path(rel)
    return p if p.is_absolute() else (root / p)


def _parse_segments(raw: list[dict[str, Any]]) -> tuple[VOSegment, ...]:
    return tuple(
        VOSegment(
            sid=s["sid"],
            target_start=float(s["target_start"]),
            target_dur=float(s["target_dur"]),
            emotion=s.get("emotion", "neutral"),
            speed=float(s.get("speed", 1.0)),
            text=s.get("text", ""),
            tail_pad=float(s.get("tail_pad", 0.3)),
        )
        for s in raw
    )


def _parse_scenes(raw: list[dict[str, Any]], root: pathlib.Path, content_root: pathlib.Path) -> tuple[SceneSpec, ...]:
    scenes: list[SceneSpec] = []
    for sc in raw:
        clips: list[ClipSpec] = []
        for c in sc["clips"]:
            src_rel = c["src_rel"]
            # 相对项目根优先；找不到再试相对 content_root（如 build/assets_ui/*）
            src_root = _resolve(root, src_rel)
            src_content = _resolve(content_root, src_rel)
            src = src_root if src_root.exists() or not src_content.exists() else src_content
            clips.append(ClipSpec(
                src_type=c["src_type"],
                src=src,
                duration=float(c["duration"]),
            ))
        scenes.append(SceneSpec(
            name=sc["name"],
            clips=tuple(clips),
            total_dur=float(sc["total_dur"]),
        ))
    return tuple(scenes)


def _parse_platforms(raw: dict[str, Any] | None) -> tuple[PlatformSpec, ...]:
    if not raw:
        return DEFAULT_PLATFORMS
    specs: list[PlatformSpec] = []
    for name, cfg in raw.items():
        specs.append(PlatformSpec(
            name=name,
            subs_size=int(cfg["subs_size"]),
            margin_v=int(cfg["margin_v"]),
            max_cue_chars=int(cfg["max_cue_chars"]),
            max_line_chars=int(cfg["max_line_chars"]),
        ))
    return tuple(specs)


def _parse_overlays(raw: list[dict[str, Any]] | None) -> tuple[DrawTextOverlay, ...]:
    if not raw:
        return ()
    return tuple(
        DrawTextOverlay(
            text=o["text"],
            t_start=float(o["t_start"]),
            t_end=float(o["t_end"]),
            fontsize=int(o.get("fontsize", 64)),
            color=o.get("color", "white"),
            border_w=int(o.get("border_w", 4)),
            border_color=o.get("border_color", "black"),
            y_expr=o.get("y_expr", "h-500"),
            x_expr=o.get("x_expr", "(w-text_w)/2"),
        )
        for o in raw
    )


def load(config_path: pathlib.Path, project_root: pathlib.Path) -> PipelineConfig:
    """载入 pipeline_config.yaml → PipelineConfig."""
    data: dict[str, Any] = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    content_id = data["content_id"]
    content_root = _resolve(project_root, data["paths"]["root_rel"])

    return PipelineConfig(
        content_id=content_id,
        root=project_root,
        content_root=content_root,
        crf=int(data.get("ffmpeg", {}).get("crf", 20)),
        tts_voice_id=data.get("tts", {}).get("voice_id", ""),
        tts_base_speed=float(data.get("tts", {}).get("base_speed", 0.95)),
        vo_segments=_parse_segments(data["tts"]["segments"]),
        scenes=_parse_scenes(data["scenes"], project_root, content_root),
        platforms=_parse_platforms(data.get("platforms")),
        overlays=_parse_overlays(data.get("overlays")),
    )
