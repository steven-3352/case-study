#!/usr/bin/env python3
"""S01 冬夜卧室 · 4 段对白 TTS · edge-tts.

男声：zh-CN-YunxiNeural（温柔低沉）
女声：zh-CN-XiaoyiNeural（清亮细腻）

每段单独 mp3，方便对齐视频段。
用法：
  python3 pipeline/gen_dialogue_vo.py            # 4 段全跑
  python3 pipeline/gen_dialogue_vo.py S01 S04    # 单段
"""
from __future__ import annotations

import asyncio
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tmp" / "shortfilm_memory" / "scenes" / "S01_winter_bedroom" / "audio"

FEMALE_VOICE = "zh-CN-XiaoyiNeural"
MALE_VOICE = "zh-CN-YunxiNeural"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("shortfilm.tts")


@dataclass(frozen=True)
class Line:
    slug: str
    voice: str
    text: str
    rate: str = "+0%"  # edge-tts rate 参数，负值放慢
    volume: str = "+0%"


@dataclass(frozen=True)
class DialogueSegment:
    slug: str
    label: str
    lines: tuple[Line, ...] = field(default_factory=tuple)


# 定 4 段对白。S03 是 2 行（女主先说，男主后说），其他单行。
SEGMENTS: tuple[DialogueSegment, ...] = (
    DialogueSegment(
        slug="S01",
        label="S01 女主叉腰假生气",
        lines=(
            Line(
                slug="S01_female",
                voice=FEMALE_VOICE,
                text="哎呀，你不开空调，是要冻死熊熊啊？",
                rate="-5%",  # 撒娇尾音略慢
            ),
        ),
    ),
    DialogueSegment(
        slug="S02",
        label="S02 男主掀被招手",
        lines=(
            Line(
                slug="S02_male",
                voice=MALE_VOICE,
                text="过来，我给你暖着。",
                rate="-10%",  # 低沉宠溺
                volume="-5%",
            ),
        ),
    ),
    DialogueSegment(
        slug="S03",
        label="S03 相拥入睡",
        lines=(
            Line(
                slug="S03a_female",
                voice=FEMALE_VOICE,
                text="真暖和……",
                rate="-15%",  # 睡意浓
                volume="-8%",
            ),
            Line(
                slug="S03b_male",
                voice=MALE_VOICE,
                text="睡吧。",
                rate="-20%",  # 耳语
                volume="-10%",
            ),
        ),
    ),
    DialogueSegment(
        slug="S04",
        label="S04 清晨亲吻",
        lines=(
            Line(
                slug="S04_male",
                voice=MALE_VOICE,
                text="我走了，再睡会儿。",
                rate="-15%",  # 气声不舍
                volume="-10%",
            ),
        ),
    ),
)


async def synth_one(line: Line, out_dir: Path) -> Path | None:
    """出单条 mp3，失败 None."""
    out = out_dir / f"{line.slug}.mp3"
    try:
        comm = edge_tts.Communicate(
            text=line.text,
            voice=line.voice,
            rate=line.rate,
            volume=line.volume,
        )
        await comm.save(str(out))
    except Exception as exc:
        log.error("合成失败 %s: %s", line.slug, exc)
        return None
    log.info(
        "✓ %s [%s] · %d 字 · %d KB",
        out.name,
        line.voice,
        len(line.text),
        out.stat().st_size // 1024,
    )
    return out


async def run(targets: set[str]) -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    segs = tuple(s for s in SEGMENTS if not targets or s.slug in targets)
    if not segs:
        log.error("slug 不匹配: %s", targets)
        return 3
    log.info("待合成 %d 段（%d 条 line）", len(segs), sum(len(s.lines) for s in segs))
    ok = 0
    total = 0
    for seg in segs:
        log.info("=== %s ===", seg.label)
        for line in seg.lines:
            total += 1
            if await synth_one(line, OUT_DIR):
                ok += 1
    log.info("完成: %d/%d 条", ok, total)
    return 0 if ok == total else 5


def main() -> int:
    targets = set(sys.argv[1:])
    return asyncio.run(run(targets))


if __name__ == "__main__":
    sys.exit(main())
