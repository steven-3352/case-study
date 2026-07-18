#!/usr/bin/env python3
"""短片《回忆·思念》· S01 南方冬夜卧室片段 · 4 张关键帧.

场景片段（用户原话，2026-07-12）：
  冬天南方卧室没暖气只有空调，女主穿睡衣叉腰假装生气：
  "不开空调你要冻死熊熊（女主给男主起的爱称）吗"。
  男主掀开被子让女主赶紧钻进来，男主抱着女主亲密入睡。
  早上男主起得早，亲吻还在入睡的女主。

技术要点：
  1. 走 client.images.edit + 人设参考图（锁面孔一致性）
  2. 单人镜头传 1 张 reference；双人镜头传 2 张
  3. 场景基调：冷调房间 vs 暖调被窝的双色反差
  4. 尺寸 1024x1536，画风延续人设图的 Kodak Portra 400 胶片写实
"""
from __future__ import annotations

import base64
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
PROJ_DIR = ROOT / "tmp" / "shortfilm_memory"
CHAR_DIR = PROJ_DIR / "character_design"
OUT_DIR = PROJ_DIR / "scenes" / "S01_winter_bedroom" / "frames"

MALE_REF = CHAR_DIR / "male_v1_front.png"
FEMALE_REF = CHAR_DIR / "female_v1_front.png"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("shortfilm.S01")


# 场景共同锚（4 张关键帧共用，确保同一片段视觉统一）· 2026-07-12 v2 去冷刻意化
SCENE_ANCHOR = """
Setting: an old-style southern-Chinese apartment bedroom in winter, no
central heating (typical for south China), with a wall-mounted white split
air-conditioner unit high on the background wall. Plain white walls, warm
wooden floor, lived-in and slightly cluttered: a wooden bedside table with
a warm-yellow tungsten lamp, a folded worn quilt, a paperback book, a used
glass of water. The mood is quiet and cozy, not exaggeratedly cold — a
normal winter night at home with a couple who love each other.

Cinematography: shot on Kodak Portra 400 film, 35mm lens, natural indoor
low-light, subtle film grain, slight lens breathing. Photorealistic,
documentary intimate style. NO airbrushing, NO plastic AI skin, visible skin
pores, subtle skin blemishes, real body proportions, un-glamorised.

Color grading: warm indoor amber (3000K tungsten glow from bedside lamp)
gently balanced with cooler neutral wall tones. The whole frame is warm and
lived-in, with subtle contrast — nothing exaggerated. NO visible breath
puffs, NO shivering, NO overly cold blue tones. Just a quiet, real, tender
winter night.
""".strip()


S01_PROMPT = f"""
FRAME S01 · The Fake-Angry Complaint.

Foreground: the 40-year-old northern Chinese woman from the reference image
(long straight black hair falling to her shoulders, oval face, slim ~50kg
build, southern delicate features softened by northern warmth — SAME FACE AS
REFERENCE), wearing an old soft cotton pajama set in muted dusty rose or pale
cream color, slightly oversized, the pants slightly wrinkled. Barefoot on the
cold wooden floor, one foot slightly lifted onto the other ankle instinctively
(cold reflex).

Pose: standing at the side of the bed, hands on her hips in a mock-angry
gesture, chin lifted slightly, eyebrows softly furrowed but the corner of her
mouth about to break into a smile — she is pretending to be mad but her eyes
are warm and playful. Mouth slightly open mid-speech. A faint white puff of
breath visible in the cold air near her lips (crucial detail — proves how
cold the room is).

Composition: medium shot from the perspective of someone lying in bed looking
up at her, slight low angle. She occupies the right two-thirds of frame. On
the left third: the edge of a rumpled dark-orange quilt, the top of a man's
buzz-cut head barely visible under the quilt (do NOT show his full face here).
In the far background upper-left: the white wall-mounted air-conditioner unit,
red power light OFF.

Mood: intimate, tender, the small domestic fight of a couple who love each
other. Cold-room-warm-heart contrast.

{SCENE_ANCHOR}
""".strip()


S02_PROMPT = f"""
FRAME S02 · The Quilt Invitation.

Central subject: the 40-year-old northern Chinese man from the reference image
(buzz cut, thick eyebrows, warm honest weathered face, slightly stocky ~170cm
build — SAME FACE AS REFERENCE). He is lying on his side in bed, propped up
on one elbow, wearing a soft charcoal-grey thermal undershirt (long sleeves,
slightly stretched collar). His other hand is holding up the corner of a
heavy dark-orange padded quilt, opening a warm pocket of the bed for someone
to climb in. He is looking directly at his partner (off-camera to the right)
with a wide affectionate grin, a gentle "come here, hurry up" expression.
His breath is visible as a faint white puff — he too is cold.

Composition: medium wide shot from the woman's approaching perspective, the
quilt-lifted-open triangle of golden lamplight is the visual anchor at
center-frame — the WARM POCKET in the cold room. Behind him: rumpled sheets,
a warm bedside tungsten lamp casting deep amber glow only on the bed area.
Background: the cold blue-tinted room, the AC unit on the wall still shows
OFF (red power light off — the running joke).

Mood: warmth, invitation, tenderness, the small everyday act of love that
becomes a lifetime memory.

{SCENE_ANCHOR}
""".strip()


S03_PROMPT = f"""
FRAME S03 · Sleeping in Each Other's Arms.

Two subjects sharing bed, both faces matching the two reference images (the
man: buzz cut, thick brows, weathered face; the woman: long black hair, oval
face, delicate features). They are lying on their sides, the woman's back
against the man's chest in a big-spoon little-spoon embrace, both facing
camera-left. The man's arm is wrapped around her waist over the quilt, his
hand holding hers softly. Both are asleep — soft closed eyes, relaxed
peaceful faces, slightly parted lips. The woman's long black hair is spread
softly across the pillow and partly across the man's chin. The heavy
dark-orange quilt pulled up to her shoulder, up to the man's collarbone.

Composition: horizontal medium close-up, camera at bed level, roughly eye
level with the sleepers, both faces clearly visible and in soft focus.
Bedside lamp warm tungsten (3000K amber) as the only light source, the AC
unit red power light NOW ON (small warm-red glow in the dark background —
he finally turned it on for her).

Mood: quiet, safe, deep intimacy, the visual definition of "coming home".
Warm-amber engulfs the entire frame; the cold room has finally warmed.

{SCENE_ANCHOR}
""".strip()


S04_PROMPT = f"""
FRAME S04 · The Morning Kiss Before He Leaves.

The 40-year-old man (buzz cut, thick brows, weathered face — MATCHING MALE
REFERENCE) is already dressed for going out: a dark charcoal wool sweater,
slightly damp buzz-cut hair (freshly washed). He is leaning down over the
bed, one hand gently supporting himself on the mattress next to the sleeping
woman's pillow, the other hand not touching her (careful not to wake her).
His face is close to hers, his lips just barely touching her forehead in a
soft, careful goodbye kiss. His eyes are closed, expression tender and
slightly reluctant to leave.

The woman (long black hair spread on the pillow, oval face, delicate features
— MATCHING FEMALE REFERENCE) is still deeply asleep, lying on her side,
the quilt pulled up to just below her ear, mouth slightly parted, one hand
tucked under her cheek. Peaceful, unaware.

Composition: side view close-up, both faces framed together, camera at
pillow-level. Behind them: soft morning light spilling gently through a
window (warm cream and pale gold tones), casting a soft rectangular pool of
daylight on the wall behind. The bedside lamp still on but softer against
the morning light. A faint wisp of steam from a mug of tea he placed
silently on the bedside table.

Mood: quiet devotion, the small unseen tenderness of a partner leaving early
while the other still sleeps. Bittersweet — the emotional beat of the whole
memory-piece.

{SCENE_ANCHOR}
""".strip()


@dataclass(frozen=True)
class Scene:
    slug: str
    prompt: str
    label: str
    refs: tuple[Path, ...] = field(default_factory=tuple)


SCENES: tuple[Scene, ...] = (
    Scene(
        slug="S01_fake_angry",
        prompt=S01_PROMPT,
        label="S01 女主叉腰假生气",
        refs=(FEMALE_REF,),
    ),
    Scene(
        slug="S02_quilt_invite",
        prompt=S02_PROMPT,
        label="S02 男主掀被招手",
        refs=(MALE_REF,),
    ),
    Scene(
        slug="S03_sleep_hug",
        prompt=S03_PROMPT,
        label="S03 相拥入睡",
        refs=(MALE_REF, FEMALE_REF),
    ),
    Scene(
        slug="S04_morning_kiss",
        prompt=S04_PROMPT,
        label="S04 清晨亲吻",
        refs=(MALE_REF, FEMALE_REF),
    ),
)


def _open_refs(refs: tuple[Path, ...]) -> list:
    """打开参考图 file handle 列表（单张或多张）。"""
    if not refs:
        return []
    for r in refs:
        if not r.exists():
            raise FileNotFoundError(f"参考图缺失: {r}")
    return [open(r, "rb") for r in refs]


def _close_refs(handles: list) -> None:
    for h in handles:
        try:
            h.close()
        except Exception:
            pass


def generate_one(
    client: OpenAI, model: str, scene: Scene, out_dir: Path
) -> Path | None:
    """出单张场景关键帧，走 image.edit 传参考图。失败返回 None。"""
    out = out_dir / f"{scene.slug}.png"
    log.info(
        "生图: %s → %s (refs=%d)",
        scene.label,
        out.name,
        len(scene.refs),
    )

    max_retries = 4
    for attempt in range(1, max_retries + 1):
        handles = _open_refs(scene.refs)
        try:
            # gpt-image-2 image.edit 支持多参考图（list of file）
            image_arg = handles if len(handles) > 1 else handles[0]
            resp = client.images.edit(
                model=model,
                image=image_arg,
                prompt=scene.prompt,
                size="1024x1536",
                n=1,
            )
        except Exception as exc:
            log.warning("尝试 %d/%d 失败: %s", attempt, max_retries, exc)
            _close_refs(handles)
            if attempt < max_retries:
                time.sleep(5)
                continue
            log.error("放弃 %s（%d 次全败）", scene.label, max_retries)
            return None
        finally:
            _close_refs(handles)

        if not resp.data:
            log.error("返回 data 为空: %s", resp)
            return None

        first = resp.data[0]
        if getattr(first, "b64_json", None):
            out.write_bytes(base64.b64decode(first.b64_json))
        elif getattr(first, "url", None):
            import urllib.request

            with urllib.request.urlopen(first.url) as r:  # noqa: S310
                out.write_bytes(r.read())
        else:
            log.error("无 b64_json 也无 url: %s", first)
            return None

        log.info("✓ %s (%s bytes)", out, out.stat().st_size)
        return out

    return None


def main() -> int:
    load_dotenv(ROOT / ".env")
    api_key = os.environ.get("GPT_IMAGE_API_KEY") or os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("GPT_IMAGE_BASE_URL") or os.environ.get("OPENAI_BASE_URL")
    model = os.environ.get("GPT_IMAGE_MODEL") or os.environ.get(
        "OPENAI_IMAGE_MODEL", "gpt-image-2"
    )
    if not api_key or not base_url:
        log.error("缺 GPT_IMAGE_API_KEY 或 GPT_IMAGE_BASE_URL（查 .env）")
        return 1

    if not MALE_REF.exists() or not FEMALE_REF.exists():
        log.error(
            "人设参考图缺失: 请先跑 pipeline/gen_character_portrait.py 生成 "
            "%s 和 %s",
            MALE_REF,
            FEMALE_REF,
        )
        return 2

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    client = OpenAI(api_key=api_key, base_url=base_url)

    # 命令行支持：只跑指定 scene（如 python gen_scene_frames.py S01_fake_angry）
    args = sys.argv[1:]
    if args:
        target_slugs = set(args)
        scenes = tuple(s for s in SCENES if s.slug in target_slugs)
        if not scenes:
            log.error(
                "指定 slug 不匹配任何 scene: %s。可用: %s",
                args,
                [s.slug for s in SCENES],
            )
            return 3
    else:
        scenes = SCENES

    log.info(
        "model=%s · out=%s · 待跑 %d 张 (%s)",
        model,
        OUT_DIR,
        len(scenes),
        [s.slug for s in scenes],
    )
    results: list[Path | None] = [generate_one(client, model, s, OUT_DIR) for s in scenes]

    ok = sum(1 for r in results if r is not None)
    log.info("完成: %d/%d 成功", ok, len(scenes))
    return 0 if ok == len(scenes) else 5


if __name__ == "__main__":
    sys.exit(main())
