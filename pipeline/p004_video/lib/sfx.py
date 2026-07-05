"""SFX 音效层混音 · VO + sfx.events → vo_with_sfx.mp3.

依赖 assets/sfx/catalog.yaml + audio_plan.yaml.sfx.events。
memory：
    - feedback_sfx-layer-required（4 类必覆盖 · BGM off 但 sfx 不 off）
    - feedback_no-synth-bgm（禁 aevalsrc/sine 合成 · 缺 wav → 跳过不合成）
    - feedback_dense-vo-no-dead-air（VO -16dB · sfx -8~-22dB 层级）

流程：
    1. 载 audio_plan.sfx.events + catalog · resolve 每个 event 的实际 wav
    2. 展开 t_start_seq 到多个单发 event
    3. resolve 优先级：event.src_rel → event.src_backup → catalog[kind].candidates
    4. 缺 wav 的 event 记入 GAP_REPORT · 跳过
    5. ffmpeg -filter_complex amix · ambient loop 到全片长度

单元测试见 pipeline/p004_video/lib/tests/test_sfx.py（P2 补）。
"""
from __future__ import annotations

import pathlib
import shutil
from dataclasses import dataclass
from typing import Any

import yaml

from .ffmpeg import FFMPEG, dur, run


@dataclass(frozen=True)
class ResolvedEvent:
    """展开后的单发 event · 已 resolve 到实际 wav 路径."""
    sid: str
    kind: str
    t_start: float
    duration: float | None      # None → ambient/loop 到全片
    gain_db: float
    src: pathlib.Path


@dataclass(frozen=True)
class GapEvent:
    """无法 resolve 的 event · 记入 GAP_REPORT."""
    sid: str
    kind: str
    t_start: float
    tried_paths: tuple[str, ...]
    fetch_hint: str


@dataclass(frozen=True)
class MixReport:
    output_path: pathlib.Path
    gap_report_path: pathlib.Path | None
    used_events: int
    gap_events: int
    total_events: int
    enabled: bool

    def format(self) -> str:
        if not self.enabled:
            return "· sfx disabled · vo mp3 copied through"
        if self.total_events == 0:
            return "· sfx enabled but no events · vo mp3 copied through"
        return (
            f"· sfx mix · {self.used_events}/{self.total_events} events applied · "
            f"{self.gap_events} gap"
        )


# ─────────────────────────────────────
# 载 catalog + audio_plan
# ─────────────────────────────────────

def _resolve_family(catalog: dict, kind: str) -> dict | None:
    """kind → family dict · 处理 alias_of."""
    fam = catalog.get("sfx_families", {}).get(kind)
    if not fam:
        return None
    if alias := fam.get("alias_of"):
        return catalog.get("sfx_families", {}).get(alias)
    return fam


def _resolve_event_src(
    event: dict[str, Any],
    catalog: dict,
    project_root: pathlib.Path,
) -> tuple[pathlib.Path | None, tuple[str, ...]]:
    """按优先级 resolve wav 路径 · 返回 (path or None, tried_paths)."""
    tried: list[str] = []
    for key in ("src_rel", "src_backup"):
        if src := event.get(key):
            p = project_root / src
            tried.append(str(src))
            if p.exists():
                return p, tuple(tried)
    fam = _resolve_family(catalog, event["kind"])
    if fam:
        for cand in fam.get("candidates", []):
            p = project_root / cand["path"]
            tried.append(cand["path"])
            if p.exists():
                return p, tuple(tried)
    return None, tuple(tried)


def _expand_seq_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """t_start_seq[] + duration_each → N 个单发 event（sid 加 _i 后缀）."""
    out: list[dict[str, Any]] = []
    for e in events:
        if "t_start_seq" in e:
            duration_each = float(e.get("duration_each", 0.15))
            for i, t in enumerate(e["t_start_seq"]):
                out.append({
                    **{k: v for k, v in e.items() if k not in ("t_start_seq", "duration_each")},
                    "sid": f"{e['sid']}_{i}",
                    "t_start": float(t),
                    "duration": duration_each,
                })
        else:
            out.append(e)
    return out


def _classify_events(
    events: list[dict[str, Any]],
    catalog: dict,
    project_root: pathlib.Path,
) -> tuple[list[ResolvedEvent], list[GapEvent]]:
    resolved: list[ResolvedEvent] = []
    gaps: list[GapEvent] = []
    for e in events:
        src, tried = _resolve_event_src(e, catalog, project_root)
        if src is None:
            gaps.append(GapEvent(
                sid=str(e["sid"]),
                kind=str(e["kind"]),
                t_start=float(e["t_start"]),
                tried_paths=tried,
                fetch_hint=str(e.get("fetch_hint", "")),
            ))
            continue
        resolved.append(ResolvedEvent(
            sid=str(e["sid"]),
            kind=str(e["kind"]),
            t_start=float(e["t_start"]),
            duration=float(e["duration"]) if "duration" in e else None,
            gain_db=float(e.get("gain_db", -12)),
            src=src,
        ))
    return resolved, gaps


# ─────────────────────────────────────
# ffmpeg 混音
# ─────────────────────────────────────

def _build_filter_complex(
    resolved: list[ResolvedEvent],
    total_duration_s: float,
) -> str:
    """构建 -filter_complex 字符串 · VO 是 [0] · sfx 从 [1] 起."""
    parts: list[str] = []
    mix_labels: list[str] = ["[0:a]"]
    for i, ev in enumerate(resolved, start=1):
        adelay_ms = max(0, int(ev.t_start * 1000))
        # ambient / 长 duration → loop 到 total_duration
        is_ambient = ev.kind == "ambient" or (ev.duration is not None and ev.duration >= 5.0)
        if is_ambient:
            target = ev.duration if ev.duration else total_duration_s
            parts.append(
                f"[{i}:a]aloop=loop=-1:size=2e+09,"
                f"atrim=duration={target},"
                f"adelay={adelay_ms}|{adelay_ms},"
                f"volume={ev.gain_db}dB[a{i}]"
            )
        else:
            duration = ev.duration if ev.duration else 0.5
            parts.append(
                f"[{i}:a]atrim=duration={duration},"
                f"adelay={adelay_ms}|{adelay_ms},"
                f"volume={ev.gain_db}dB[a{i}]"
            )
        mix_labels.append(f"[a{i}]")
    filter_str = ";".join(parts)
    # amix(normalize=0) 保 VO 满电平 · sfx 叠加后瞬态可能过 0 dBFS。
    # 尾接 alimiter 限到 ~-1 dBFS 防 hit 瞬态硬削（memory feedback_sfx-layer-required · D05 +0.3dB 教训）。
    filter_str += (";" + "".join(mix_labels)
                   + f"amix=inputs={len(mix_labels)}:normalize=0:duration=first[mx];"
                   + "[mx]alimiter=limit=0.9:attack=5:release=50[out]")
    return filter_str


def _write_gap_report(gaps: list[GapEvent], path: pathlib.Path) -> None:
    lines = [
        "# SFX GAP Report",
        "",
        "> 以下 event 在 catalog 与 event.src_rel/src_backup 中均未找到 wav · 已跳过混音（禁合成 · memory feedback_no-synth-bgm）",
        "",
        "补齐方法：走 Freesound.org 拉 CC0 wav → 落到 event.src_rel 或 catalog[kind].candidates[].path",
        "",
        f"| sid | kind | t_start | 尝试路径 | Freesound 关键词 |",
        f"|-----|------|---------|---------|---------|",
    ]
    for g in gaps:
        tried = " · ".join(g.tried_paths) if g.tried_paths else "（无）"
        lines.append(f"| {g.sid} | {g.kind} | {g.t_start:.2f}s | {tried} | {g.fetch_hint} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def mix_sfx_with_vo(
    vo_mp3: pathlib.Path,
    audio_plan_yaml: pathlib.Path,
    catalog_yaml: pathlib.Path,
    out_mp3: pathlib.Path,
    project_root: pathlib.Path,
) -> MixReport:
    """VO + sfx.events → out_mp3.

    行为：
        - audio_plan 不存在 / sfx.enabled=false → copy vo 到 out（enabled=false 报告）
        - 全部 event 无 wav → copy vo · 写 GAP · MixReport gap_events=N
        - 部分有 wav → ffmpeg amix · 写 GAP report
    """
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    if not audio_plan_yaml.exists():
        shutil.copy(vo_mp3, out_mp3)
        return MixReport(out_mp3, None, 0, 0, 0, enabled=False)

    plan = yaml.safe_load(audio_plan_yaml.read_text(encoding="utf-8"))
    sfx_cfg = plan.get("sfx") or {}
    if not sfx_cfg.get("enabled"):
        shutil.copy(vo_mp3, out_mp3)
        return MixReport(out_mp3, None, 0, 0, 0, enabled=False)

    catalog = yaml.safe_load(catalog_yaml.read_text(encoding="utf-8")) if catalog_yaml.exists() else {}
    raw_events = sfx_cfg.get("events") or []
    events = _expand_seq_events(raw_events)
    resolved, gaps = _classify_events(events, catalog, project_root)

    gap_report_path = out_mp3.with_suffix(".gap.md") if gaps else None
    if gap_report_path:
        _write_gap_report(gaps, gap_report_path)

    if not resolved:
        shutil.copy(vo_mp3, out_mp3)
        return MixReport(out_mp3, gap_report_path, 0, len(gaps), len(events), enabled=True)

    total_dur = dur(vo_mp3)
    cmd: list[str] = [FFMPEG, "-y", "-i", str(vo_mp3)]
    for ev in resolved:
        cmd += ["-i", str(ev.src)]
    filter_str = _build_filter_complex(resolved, total_dur)
    cmd += [
        "-filter_complex", filter_str,
        "-map", "[out]",
        "-c:a", "libmp3lame", "-b:a", "192k",
        "-ar", "48000",
        str(out_mp3),
    ]
    run(cmd)
    return MixReport(out_mp3, gap_report_path, len(resolved), len(gaps), len(events), enabled=True)
