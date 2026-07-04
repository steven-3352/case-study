"""TTS 时长前置估算 · 合成前预测每段 mp3 时长，捕获 target_dur 溢出.

背景（D03 教训）：
    s2 计划 5s → 实测 8.55s（多 71%）· s6 计划 12s → 实测 12.3s
    → 把 M7 (计划 6s) 挤到 1.7s，视觉节奏被打崩
    如果合成前能预测「s2 会 8.4s，与你写的 5s target 相差 3.4s」，
    就可以在 storyboard/audio_plan 阶段调整，不用等 30 min TTS 跑完才发现。

模型（MiniMax 男声·精英精品 · 中文密语料 · D03 实测拟合）:
    baseline_char_rate = 5.0 字/秒 at speed 1.0 (纯中文含标点)
    英文单词按音节数计（约 word_len / 2.5，min 1）
    情绪倍率：neutral 1.0 · sad 0.85 · gentle 0.95 · happy 1.05
    实际速率 = 5.0 * speed * emotion_mult
    duration ≈ char_units / 实际速率

D03 8 段实测拟合结果（±15% target）:
    s2 Δ 0.2%   s3 Δ 1.9%   s4 Δ 11.6%   s5 Δ 7.8% (短段加 0.3s head/tail)
    s6 Δ 1.7%   s8 Δ 5.3%   s9 Δ 18.9%   s10 Δ 3.8%

用法:
    python3 pipeline/tts/estimate_duration.py --text "…" --speed 0.95 --emotion neutral
    python3 pipeline/tts/estimate_duration.py --config publish/2026-WXX/DYY-*/pipeline_config.yaml
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys
from dataclasses import dataclass

import yaml

BASELINE_CHAR_RATE: float = 5.0    # 字/秒 at speed 1.0 (D03 s2/s6 拟合)
SHORT_SEGMENT_HEAD_TAIL: float = 0.3  # 短段（<3s）加常量 head/tail overhead
SHORT_SEGMENT_THRESHOLD: float = 3.0

EMOTION_MULT: dict[str, float] = {
    "neutral": 1.0,
    "sad": 0.85,
    "gentle": 0.95,
    "happy": 1.05,
    "silence": 0.0,   # 不合成
    "gap": 0.0,       # 不合成
}

# 溢出容差 · 超过就 warn
WARN_DELTA_RATIO = 0.15   # 预测 vs target 差 ≥ 15% 报警
FAIL_DELTA_RATIO = 0.30   # 差 ≥ 30% 建议改稿


def _is_chinese_or_punct(ch: str) -> bool:
    """中文字符 + 常见中文标点（TTS 中都占正常字宽）."""
    if "一" <= ch <= "鿿":
        return True
    return ch in "。！？，、：；「」『』（）《》——…"


def _syllable_count(word: str) -> int:
    """英文单词音节估算 · 极简 · 每 2-3 字母算 1 syl · min 1."""
    return max(1, round(len(word) / 2.5))


def _clean_text(text: str) -> str:
    """gen_speech 内部会 re.sub(r'\\s+', '', text) 除去所有空白."""
    return re.sub(r"\s+", "", text)


@dataclass(frozen=True)
class Estimate:
    text: str
    speed: float
    emotion: str
    zh_count: int
    en_syllables: int
    digit_count: int
    char_units: float           # zh + en_syl + digits
    est_duration: float         # 秒


def estimate(text: str, speed: float = 1.0, emotion: str = "neutral") -> Estimate:
    """预测一段 VO 合成后的时长（秒）· ±15% 目标."""
    cleaned = _clean_text(text)
    zh_count = sum(1 for c in cleaned if _is_chinese_or_punct(c))
    en_words = re.findall(r"[A-Za-z]+", cleaned)
    en_syllables = sum(_syllable_count(w) for w in en_words)
    digit_count = sum(1 for c in cleaned if c.isdigit())
    char_units = zh_count + en_syllables + digit_count

    mult = EMOTION_MULT.get(emotion, 1.0)
    if mult <= 0:
        return Estimate(
            text=text, speed=speed, emotion=emotion,
            zh_count=zh_count, en_syllables=en_syllables, digit_count=digit_count,
            char_units=char_units, est_duration=0.0,
        )

    rate = BASELINE_CHAR_RATE * speed * mult
    est_dur = char_units / rate
    if est_dur < SHORT_SEGMENT_THRESHOLD:
        est_dur += SHORT_SEGMENT_HEAD_TAIL

    return Estimate(
        text=text, speed=speed, emotion=emotion,
        zh_count=zh_count, en_syllables=en_syllables, digit_count=digit_count,
        char_units=char_units, est_duration=round(est_dur, 2),
    )


@dataclass(frozen=True)
class SegmentReport:
    sid: str
    target_dur: float
    estimate: Estimate
    delta_s: float                # est - target
    delta_ratio: float            # abs(delta) / target
    verdict: str                  # ok / warn / fail

    def format(self) -> str:
        icon = {"ok": "✓", "warn": "⚠", "fail": "❌"}[self.verdict]
        direction = "溢出" if self.delta_s > 0 else "留空(tail_pad 补)"
        return (
            f"{icon} {self.sid:<10} target {self.target_dur:5.2f}s · "
            f"est {self.estimate.est_duration:5.2f}s · "
            f"Δ{self.delta_s:+.2f}s ({self.delta_ratio*100:+.1f}%) {direction} · "
            f"字={self.estimate.zh_count} en_syl={self.estimate.en_syllables} "
            f"数={self.estimate.digit_count} · emo={self.estimate.emotion} spd={self.estimate.speed}"
        )


def check_segment(sid: str, target_dur: float, text: str, speed: float, emotion: str) -> SegmentReport:
    """一段 vs target 预算差距 · silence/gap 跳过.

    OVER（est > target）是关键风险：VO 会挤压后续段（D03 s2/s6 教训）。
    UNDER（est < target）通常由 tail_pad 填充静音，正常。
    """
    est = estimate(text, speed, emotion)
    if emotion in ("silence", "gap"):
        return SegmentReport(sid=sid, target_dur=target_dur, estimate=est,
                             delta_s=0.0, delta_ratio=0.0, verdict="ok")
    delta = est.est_duration - target_dur
    ratio = delta / target_dur if target_dur > 0 else 0.0
    # 只对 OVER 做 warn/fail · UNDER 归 ok（tail_pad 填充）
    if ratio >= FAIL_DELTA_RATIO:
        verdict = "fail"
    elif ratio >= WARN_DELTA_RATIO:
        verdict = "warn"
    else:
        verdict = "ok"
    return SegmentReport(sid=sid, target_dur=target_dur, estimate=est,
                         delta_s=round(delta, 2), delta_ratio=round(ratio, 3),
                         verdict=verdict)


def check_config(config_path: pathlib.Path) -> list[SegmentReport]:
    """从 pipeline_config.yaml 读 tts.segments 逐段检查."""
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    reports: list[SegmentReport] = []
    for seg in data["tts"]["segments"]:
        reports.append(check_segment(
            sid=seg["sid"],
            target_dur=float(seg["target_dur"]),
            text=seg.get("text", ""),
            speed=float(seg.get("speed", 1.0)),
            emotion=seg.get("emotion", "neutral"),
        ))
    return reports


def _print_summary(reports: list[SegmentReport], target_total: float | None = None) -> int:
    for r in reports:
        print(r.format())
    warns = [r for r in reports if r.verdict == "warn"]
    fails = [r for r in reports if r.verdict == "fail"]
    est_total = sum(r.estimate.est_duration if r.estimate.est_duration > 0 else r.target_dur
                    for r in reports)
    print()
    print(f"─ 汇总 ─")
    print(f"  段数: {len(reports)} · warn: {len(warns)} · fail: {len(fails)}")
    print(f"  预测总长: {est_total:.2f}s")
    if target_total is not None:
        print(f"  计划总长: {target_total:.2f}s · Δ={est_total-target_total:+.2f}s")
    if fails:
        print(f"  ❌ 建议改稿：{', '.join(r.sid for r in fails)}")
        return 2
    if warns:
        print(f"  ⚠ 关注：{', '.join(r.sid for r in warns)}")
        return 1
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="TTS 时长前置估算")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--text", help="单条文本 · 与 --speed / --emotion / --target 配合")
    src.add_argument("--config", type=pathlib.Path, help="pipeline_config.yaml 路径")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--emotion", default="neutral")
    ap.add_argument("--target", type=float, default=0.0, help="单条模式下声明目标窗口")
    args = ap.parse_args()

    if args.text:
        est = estimate(args.text, args.speed, args.emotion)
        print(f"text ({len(args.text)} chars, 字={est.zh_count} en_syl={est.en_syllables} "
              f"数={est.digit_count})")
        print(f"  emotion={est.emotion} speed={est.speed}")
        print(f"  预测时长: {est.est_duration:.2f}s")
        if args.target > 0:
            report = check_segment("adhoc", args.target, args.text, args.speed, args.emotion)
            print(f"  {report.format()}")
            sys.exit({"ok": 0, "warn": 1, "fail": 2}[report.verdict])
        sys.exit(0)

    reports = check_config(args.config)
    total = sum(float(s["target_dur"])
                for s in yaml.safe_load(args.config.read_text(encoding="utf-8"))["tts"]["segments"])
    code = _print_summary(reports, target_total=total)
    sys.exit(code)


if __name__ == "__main__":
    main()
