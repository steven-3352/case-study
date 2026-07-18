#!/usr/bin/env python3
"""临时短片《回忆·思念》人物设计图 · GPT-image-2 中转.

场景锚点：居家、生活片段回忆、温馨。
出图规格：1024x1536（接近 9:16 竖版人像），半身正面参考图。
风格：写实电影感，Kodak Portra 400 胶片质感，反 AI 磨皮。
"""
from __future__ import annotations

import base64
import logging
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tmp" / "shortfilm_memory" / "character_design"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("shortfilm.character")


# 通用风格锚（两个角色共用，保证同一部片子的视觉一致性）
STYLE_ANCHOR = """
Photorealistic cinematic portrait, waist-up front view, subject centered,
shot on Kodak Portra 400 film, 50mm lens, shallow depth of field, natural
warm indoor light spilling from a west-facing window (late afternoon golden hour),
soft film grain, subtle skin texture with visible pores and fine lines,
NO airbrushing, NO plastic skin, NO glossy over-retouched AI look.

Setting: a cozy northern Chinese apartment interior in the background, softly
out of focus — warm beige wall, a slice of wooden bookshelf or windowsill with
a small potted plant, hint of a knitted throw or a mug on a side table. The
whole frame breathes a quiet, lived-in, nostalgic warmth. Muted earth tones,
mustard yellow, soft brown, cream, gentle amber highlights.

Mood: candid, unposed, a person paused mid-thought in their own home. Slight
melancholy behind the eyes but soft, warm. This is a memory-piece portrait,
not a fashion shoot.
""".strip()


MALE_PROMPT = f"""
A 40-year-old northern Chinese man, waist-up candid home portrait.

Physical: buzz cut hair (very short crew cut, showing scalp),
thick dark bold eyebrows, small warm eyes with faint crow's feet,
slightly stocky build (a soft belly, not obese — a lived-in body around 170 cm),
broad shoulders, weathered honest face with slight tan, faint stubble shadow,
a small mole or shaving nick allowed. Ethnicity: Han Chinese, northern (Beijing/
Hebei/Shandong type), rugged and warm, not model-handsome.

Wardrobe: soft charcoal-grey cotton crew-neck sweater or a dark navy henley,
slightly worn at the collar, sleeves pushed up to forearms showing thick wrists.
No accessories, no glasses.

Pose: standing or half-leaning against a kitchen counter or a doorframe, one
hand loosely holding a warm ceramic mug (steam rising), the other hand relaxed.
Looking slightly off-camera to the left, a small quiet smile, eyes carrying
the weight of remembering someone.

{STYLE_ANCHOR}
""".strip()


FEMALE_PROMPT = f"""
A 40-year-old Chinese woman, born in southern China (Jiangnan / Wu region)
but raised in the north from childhood — she carries southern delicate features
softened by northern warmth. Waist-up candid home portrait.

Physical: long straight black hair falling past the shoulders (slight natural
wave, no elaborate styling, a few strands loose around the face), fair skin
with a natural warm undertone, delicate OVAL face (egg-shaped, narrow gently
rounded chin, subtle cheekbones), calm almond eyes with a hint of tiredness,
soft eyebrows, small nose, no heavy makeup — bare lips with natural pink tone.
Slim build (about 167 cm, 50 kg / 100 jin), gentle collarbones visible.
Age visible around the eyes and a faint line at the corner of the mouth —
40 real, not 40 idealised.

Wardrobe: an oversized oatmeal-cream knitted sweater, sleeves swallowing part
of her hands, or a soft dusty-rose linen shirt with the top button undone.
No jewelry except perhaps a thin worn silver band on her right hand.

Pose: sitting on a wooden windowsill or curled up on a linen sofa, knees
slightly drawn up, one hand resting near her collarbone, the other holding
a small teacup. Head slightly tilted, looking out of the window into soft
afternoon light, a very faint melancholy smile — not sad, but remembering.

{STYLE_ANCHOR}
""".strip()


@dataclass(frozen=True)
class Character:
    slug: str
    prompt: str
    label: str


CHARACTERS: tuple[Character, ...] = (
    Character(slug="male_v1_front", prompt=MALE_PROMPT, label="男主·正面·家居"),
    Character(slug="female_v1_front", prompt=FEMALE_PROMPT, label="女主·正面·家居"),
)


def generate_one(
    client: OpenAI, model: str, character: Character, out_dir: Path
) -> Path | None:
    """出单张图，成功返回路径，失败 None（不 raise，让另一张继续）。"""
    out = out_dir / f"{character.slug}.png"
    log.info("生图: %s → %s", character.label, out.name)

    max_retries = 4
    for attempt in range(1, max_retries + 1):
        try:
            resp = client.images.generate(
                model=model,
                prompt=character.prompt,
                size="1024x1536",
                n=1,
            )
        except Exception as exc:
            log.warning("尝试 %d/%d 失败: %s", attempt, max_retries, exc)
            if attempt < max_retries:
                time.sleep(5)
                continue
            log.error("放弃 %s（%d 次全败）", character.label, max_retries)
            return None

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

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    client = OpenAI(api_key=api_key, base_url=base_url)

    log.info("model=%s · out=%s · 共 %d 张", model, OUT_DIR, len(CHARACTERS))
    results: list[Path | None] = [
        generate_one(client, model, c, OUT_DIR) for c in CHARACTERS
    ]

    ok = sum(1 for r in results if r is not None)
    log.info("完成: %d/%d 成功", ok, len(CHARACTERS))
    return 0 if ok == len(CHARACTERS) else 5


if __name__ == "__main__":
    sys.exit(main())
