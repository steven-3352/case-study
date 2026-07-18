#!/usr/bin/env python3
"""D07 · 男厅《明月天涯》立绘卡点 MV · 15 张主视觉生成.

客户借用能力单,与项目主旨分线(见 publish/2026-W30/D07/live2d_beat_sync_playbook.md).

配置:
  - 版式: 横版 16:9 → 1536x1024 (native gpt-image-2-1k 支持)
  - 风格: 水墨风·武侠风,黑白+青灰调
  - 角色: 4 人 · 3 换装 + 1 保留
      轩珩(轩珩.png)   → 已是青灰道袍执箫,免换,只补姿势
      Cy(cy.png)       → 保脸型,换成武侠黑披氅暗纹长衫
      中里毅(中里毅2.png) → 保脸型,换成武侠青灰长袍执剑
      诺兰(诺兰.png)   → 保脸型,换成武侠黑劲装腕甲发带

隐含约束(prompt 硬写):
  - 水墨渲染质感(NOT anime, NOT CG,像宣纸+焦墨+青色淡染)
  - 黑白+青(NEG: 霓虹紫/粉,饱和红,金色发光,赛博)
  - NO 大字歌词烧进图(后期剪映加)
  - NO DV UI 边框烧进图(后期剪映加)
  - NO watermark
  - 4 角色任何组合出现都要与客户脸型一致

15 shots (与 production_plan.md §3 对齐):
"""
from __future__ import annotations

import base64
import logging
import mimetypes
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tmp" / "d07_moon" / "stills"
# 客户原图 5120px 单张 20MB+,多角色 shot 一次传 4 张会超请求上限
# 用 tmp/d07_moon/refs/ 的 1024px 降采样版 (每张 300-400KB)
REF_DIR = ROOT / "tmp" / "d07_moon" / "refs"

REF_PNG = {
    "轩珩": REF_DIR / "轩珩.png",
    "cy": REF_DIR / "cy.png",
    "中里毅": REF_DIR / "中里毅2.png",
    "诺兰": REF_DIR / "诺兰.png",
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("d07.moon.still")


# ============ Prompt Fragments · 复用锚点 ============

STYLE = """
Style: Chinese ink-wash (水墨) wuxia illustration, adult character portrait,
painterly rice-paper texture, focused calligraphy brush strokes for outlines,
soft cyan-gray (青灰) tonal wash, black ink deep shadows, negative-space
composition typical of Song-Dynasty ink painting. Cinematic key light with
gentle rim. Detailed anime-realism face rendering (fine skin gradation,
delicate eyes), NOT chibi, NOT flat cel, NOT modern CG toon.
""".strip()

PALETTE = """
Color palette: monochrome black and white with restrained celadon-cyan (青灰)
accents only. Ink black #000, paper white #F5F1E8, celadon gray-cyan
#5F7A7A / #8FA5A5. NO neon, NO saturated pink or purple, NO golden glow,
NO orange sunset, NO cyberpunk RGB. Moonlight highlights allowed.
""".strip()

NEG = """
Absolutely NO: burned-in Chinese text or subtitles, NO large kinetic
typography, NO DV/REC viewfinder UI frame, NO recording HUD overlays, NO
watermark, NO signature. NO neon purple, NO neon pink, NO saturated red,
NO golden divine light, NO magical circles, NO glowing runes, NO cyberpunk
tech. NO extra fingers, NO melting faces, NO duplicated limbs.
""".strip()

# 单角色描述 · 面部锚 + 服装 override
CHAR_XUANHENG = """
轩珩 (Xuanheng): Adult East Asian male, calm elegant scholar-warrior in his
mid-20s, sharp handsome face with defined jawline, thick straight dark
hair pulled up in a high topknot secured by a jade crown, wearing loose
flowing pale silver-gray wuxia scholar robes (道袍) with dark celadon-gray
inner robe and sash, holding a black polished bamboo flute (长箫). Face
matches the reference image exactly — same jawline, same eye shape, same
mouth. Composed poised bearing.
""".strip()

CHAR_CY = """
Cy (silver-haired swordsman): Adult East Asian male, silver-white long hair
falling loosely down his back with a small side braid, striking pale
narrow eyes, sharp aristocratic face with subtle dark neck tattoo just
visible at the collar. WARDROBE OVERRIDE — he must wear a WUXIA-STYLE
black long robe (深黑长袍) with muted dragon-scale ink-brush pattern in
dark gray, celadon inner collar, silver waist chain — NOT modern suit,
NOT modern cape, NOT vest, NOT tie. Face matches the reference image
exactly — same silver hair, same face structure, same pale eyes. Cool
detached bearing.
""".strip()

CHAR_ZLY = """
中里毅 (Nakazato Tsuyoshi): Adult East Asian male, soft pale-lavender hair
(shorter, tousled), delicate refined face with slight melancholy. WARDROBE
OVERRIDE — he must wear WUXIA celadon-gray inner tunic with layered
pale-silver outer robe (青灰长袍), narrow dark sash, carrying a slim
straight sword (直剑) at his hip — NOT modern purple silk shirt, NOT
holding a bouquet, NOT modern trousers. Face matches the reference
image exactly — same soft features, same pale hair color kept, same eye
shape. Poet-swordsman bearing, quiet.
""".strip()

CHAR_NL = """
诺兰 (Nolan): Adult East Asian male, silver-white shoulder-length loose hair
with front strands falling over one eye, striking pale eyes, subtle arm
tattoo. WARDROBE OVERRIDE — he must wear WUXIA-STYLE black fitted
close-cut fighting robe (黑劲装) with leather bracers on both wrists, dark
gray waist wrap, dark hair band across forehead — NOT modern black tank
top, NOT ripped modern trousers, NOT cross necklace. Face matches the
reference image exactly — same silver hair, same pale eyes, same jawline.
Sharp lithe bearing, ready for combat.
""".strip()

CHAR_DESC = {
    "轩珩": CHAR_XUANHENG,
    "cy": CHAR_CY,
    "中里毅": CHAR_ZLY,
    "诺兰": CHAR_NL,
}


def build_prompt(scene: str, characters: list[str]) -> str:
    """把风格 + 角色描述 + 场景 + 反面拼成完整 prompt."""
    char_blocks = "\n\n".join(f"{c.upper()}:\n{CHAR_DESC[c]}" for c in characters)
    return f"""{STYLE}

{PALETTE}

CHARACTERS IN THIS FRAME:

{char_blocks}

SCENE:
{scene}

CONSTRAINTS:
{NEG}
""".strip()


@dataclass(frozen=True)
class Shot:
    slug: str
    covers_s: str
    label: str
    characters: tuple[str, ...]
    scene: str

    @property
    def prompt(self) -> str:
        return build_prompt(self.scene, list(self.characters))


# ============ 15 Shots ============

SHOTS: tuple[Shot, ...] = (
    Shot("S01_xuanheng_flute_distant", "0.0-3.5s", "S01 轩珩执箫远景山影",
         ("轩珩",),
         """Wide landscape shot. Xuanheng stands alone on a distant rocky
outcrop overlooking layered ink-wash mountain silhouettes fading into
mist. He holds the flute vertically in his right hand at his side.
Composition: rule-of-thirds, character on the right third, mountains
receding into negative white space on the left. Faint moon low behind
distant peaks. Cool celadon dawn tone."""),

    Shot("S02_xuanheng_side_moon", "3.5-7.0s", "S02 轩珩侧脸近景 + 明月",
         ("轩珩",),
         """Tight profile close-up of Xuanheng's face from the side, eyes
closed lightly, moonlight rimming his silhouette. Behind him, a large full
moon hangs in a cloudy ink-wash night sky, low on the horizon. Wisps of
his loose topknot strands lift gently in the wind. Frame right shows just
the top of the flute held near his chest. Cinematic 16:9, breathing
stillness."""),

    Shot("S03_zly_sword_back", "7.0-9.8s", "S03 中里毅执剑背影",
         ("中里毅",),
         """Medium-wide back shot of Nakazato Tsuyoshi standing facing away
from camera, straight sword sheathed at his hip, one hand resting on the
hilt. He looks off into a bamboo grove receding into mist. Ink-wash
bamboo leaves scattered as calligraphy strokes across the composition.
Cool celadon light. His outer robe hem catches a slight breeze."""),

    Shot("S04_zly_face_sword", "9.8-12.3s", "S04 中里毅正脸 + 剑",
         ("中里毅",),
         """Medium close-up frontal shot of Nakazato Tsuyoshi. He has just
half-drawn his straight sword — the blade visible about 30% out of the
scabbard held horizontally across his lower chest, blade edge catching a
sharp specular highlight. His eyes are lowered to the blade, expression
quiet and resolute. Neutral ink-wash background with soft cyan
directional light from the left."""),

    Shot("S05_xh_zly_bridge_rain", "12.3-15.8s", "S05 双人对峙雨中断桥",
         ("轩珩", "中里毅"),
         """Wide two-shot: Xuanheng and Nakazato Tsuyoshi face each other on a
broken arched stone bridge in heavy diagonal ink-brush rain. Xuanheng on
frame left holding his flute horizontally in a defensive grip; Nakazato
Tsuyoshi on frame right, sword fully drawn pointed downward. Between them,
a gap in the broken bridge. Their robes and hair fly in the storm wind.
Ink-wash dark stormy sky. Rain rendered as diagonal calligraphy strokes
across the whole frame."""),

    Shot("S06_flute_sword_clash", "15.8-18.8s", "S06 剑与箫击点 → 白光",
         ("轩珩", "中里毅"),
         """WIDE HORIZONTAL 16:9 landscape composition (both men side by side
across the frame, NOT a vertical portrait crop). Action close-up of the
moment Xuanheng's flute (held horizontal) meets Nakazato Tsuyoshi's
straight sword edge at a sharp crossing angle in the center of the frame.
Small burst of pure white ink-splatter at the contact point (NOT sparks,
NOT electricity — just white paper burst effect). Both men's hands and
forearms visible framing the impact, positioned left-of-center and
right-of-center so the frame reads wide, not stacked vertically. Motion
blur radiating outward. Behind them, storm rain streaks and shattered
bridge fragments floating, filling the wide negative space on both
sides."""),

    Shot("S07_four_toast_silhouette", "18.8-22.0s", "S07 4 人举杯剪影",
         ("轩珩", "cy", "中里毅", "诺兰"),
         """Wide four-figure silhouette shot in a moonlit courtyard. All four
men stand in a loose horizontal line, each raising a wine cup in one hand
in a toast gesture. Xuanheng (leftmost, topknot silhouette holding flute
in other hand), Nakazato Tsuyoshi (center-left, straight sword at hip),
Cy (center-right, tall black robe silhouette), Nolan (rightmost, fitted
black robe silhouette). Behind them, a huge full moon over ink-wash
mountains. Long shadows cast forward. High-contrast ink silhouettes."""),

    Shot("S08_nolan_turn_back", "22.0-25.0s", "S08 诺兰回头长发扬起",
         ("诺兰",),
         """Medium shot. Nolan is caught mid-turn — his upper body pivoting
sharply back over his left shoulder toward camera, his loose silver hair
whipping in a wide arc across the frame in strong horizontal motion,
one pale eye visible through a gap in the flying hair. His right hand is
half-raised as if he just heard something. Behind him, an ink-wash
grassland with distant wind ripples in tall grass. Cyan-tinted twilight."""),

    Shot("S09_nolan_distant_moon", "25.0-28.0s", "S09 诺兰远景 + 月满山",
         ("诺兰",),
         """Wide landscape shot. Nolan stands alone on a hilltop as a small
silhouette on the right third of the frame, facing left toward a massive
low-hanging full moon that dominates the horizon. Layered ink-wash
mountain ranges recede into misty distance. His black wuxia robes and
long silver hair are picked up in the moonlight rim. Deep negative
space in the sky. Solitary contemplative jianghu feeling."""),

    Shot("S10_cy_mountain_top", "28.0-31.0s", "S10 Cy 立于山顶远眺",
         ("cy",),
         """Wide medium shot. Cy stands at the edge of a rocky mountain
outcrop, black robes rippling in the wind, silver hair streaming behind
him, gaze fixed on the horizon far off-frame. Below and behind him, a
sea of ink-wash cloud mist rolls between peaks. He is turned slightly
three-quarters away from camera. Cold celadon dawn light hits his
profile. Sweeping epic composition."""),

    Shot("S11_cy_side_walk_street", "31.0-34.0s", "S11 Cy 侧脸行进 + 长街",
         ("cy",),
         """Medium side tracking shot of Cy walking along a long straight
ancient-town stone street lit by rows of paper lanterns (rendered as
soft ink-wash white blurs, NOT glowing red — restrained monochrome
lantern light). Behind him the street stretches deep into the frame in
one-point perspective. Silver hair falling to his shoulder blade. His
gaze forward, cool. Robe hem catches the walk motion."""),

    Shot("S12_nolan_cy_tavern", "34.0-37.0s", "S12 诺兰+Cy 酒肆对坐",
         ("cy", "诺兰"),
         """Medium two-shot inside a rustic wooden tavern. Cy sits on the
left of a low wooden table, one arm resting casually, a small wine cup
in his hand. Nolan sits on the right, half-leaning forward with his cup
raised slightly toward Cy in a subtle toast. A ceramic wine bottle sits
between them. Behind them, wooden lattice windows opening onto ink-wash
night mountains. Warm ink-tone lamplight on their faces — desaturated
warm, not golden."""),

    Shot("S13_four_tavern_wide", "37.0-40.0s", "S13 全景酒肆 4 人",
         ("轩珩", "cy", "中里毅", "诺兰"),
         """Wide four-shot inside the tavern common room. All four men are
gathered around a large square wooden table. Xuanheng leaning back on
his chair, flute laid across the table; Nakazato Tsuyoshi upright, cup
half-raised; Cy on the far side facing partly toward camera; Nolan
leaning forward laughing quietly. Bowls, cups, and a wine jar clutter
the table. Behind them, the tavern lattice and hanging paper lanterns.
Ink-wash monochrome with subtle warm tint, painterly."""),

    Shot("S14_four_summit_clouds", "40.0-46.0s", "S14 4 人齐立山顶 + 云翻",
         ("轩珩", "cy", "中里毅", "诺兰"),
         """Sweeping wide shot. All four men stand along the top of a
mountain ridge, evenly spaced across the frame, all facing outward
looking off into the distance. Left to right: Xuanheng, Nakazato
Tsuyoshi, Cy, Nolan. A massive sea of turbulent ink-wash clouds churns
below their feet, spilling out toward camera. Behind them, distant
mountain peaks fade into the sky. Their robes and hair all lift in the
wind. Epic jianghu ensemble composition. Cool moonlit celadon."""),

    Shot("S15_four_back_farewell", "46.0-52.5s", "S15 4 人背影远眺 → 收尾",
         ("轩珩", "cy", "中里毅", "诺兰"),
         """Wide back-shot. The four men walk away from camera side by side
along a broad ridge path that leads deep into the layered ink-wash
mountains ahead. Left to right: Xuanheng, Nakazato Tsuyoshi, Cy, Nolan.
Each carries his own weapon — flute, sword, sheathed blade, bracers.
Ahead of them the mountain path stretches into infinite negative white
space, a distant faint moon visible high in the sky. Their silhouettes
gradually smaller against the vast landscape. Sense of jianghu
brotherhood receding into legend."""),
)


def _post_once(base_url: str, api_key: str, model: str, shot: Shot,
               files_payload: list, timeout: int = 300) -> dict | None:
    """一次 POST,返回 payload 或抛异常."""
    url = base_url.rstrip("/") + "/v1/images/edits"
    data = {
        "prompt": shot.prompt,
        "model": model,
        "n": "1",
        "size": "1536x1024",  # 横版 16:9
    }
    headers = {"Authorization": f"Bearer {api_key}",
               "Accept": "application/json"}
    resp = requests.post(url, files=files_payload, data=data,
                         headers=headers, timeout=timeout)
    if not resp.ok:
        body_snip = (resp.text or "")[:500]
        raise requests.HTTPError(
            f"{resp.status_code} · body={body_snip}", response=resp)
    return resp.json()


def generate_one(base_url: str, api_key: str, model: str, shot: Shot,
                 out_dir: Path, model_fallback: str | None = None) -> Path | None:
    """走 /v1/images/edits 多参考图 multipart.

    每个 shot 按 characters 挂对应参考图,gpt-image-2-1k 支持多 image field.

    Fallback: 主 model 4 次全败 (超时/400/500 都算),自动切 model_fallback 再 2 次.
    这是 tonbirds 中转多参考图的实测规律 — 1k 对 3+ 张 ref 常超时,count 更稳.
    """
    out = out_dir / f"{shot.slug}.png"
    if out.exists():
        log.info("skip 已存在: %s", out.name)
        return out

    log.info("生图: %s (%s) chars=%s → %s",
             shot.label, shot.covers_s, shot.characters, out.name)

    files_payload = []
    for name in shot.characters:
        ref_path = REF_PNG[name]
        ref_bytes = ref_path.read_bytes()
        ref_mime = mimetypes.guess_type(str(ref_path))[0] or "image/png"
        files_payload.append(("image", (ref_path.name, ref_bytes, ref_mime)))

    # ( model, attempts )
    plan: list[tuple[str, int]] = [(model, 3)]
    if model_fallback and model_fallback != model:
        plan.append((model_fallback, 3))

    payload = None
    for stage_model, max_retries in plan:
        log.info("→ 用模型 %s 试 %d 次 · %s",
                 stage_model, max_retries, shot.slug)
        for attempt in range(1, max_retries + 1):
            try:
                payload = _post_once(base_url, api_key, stage_model, shot,
                                     files_payload)
                break
            except Exception as exc:
                log.warning("尝试 %s/%d[%s] 失败 %s: %s",
                            attempt, max_retries, stage_model,
                            shot.slug, exc)
                if attempt < max_retries:
                    time.sleep(5)
        if payload is not None:
            log.info("✓ 模型 %s 打通 · %s", stage_model, shot.slug)
            break
        log.warning("模型 %s 全败,尝试下一模型", stage_model)

    if payload is None:
        log.error("放弃 %s (全部模型全败)", shot.label)
        return None

    if not payload.get("data"):
        log.error("返回 data 为空 %s: %s", shot.slug, payload)
        return None

    first = payload["data"][0]
    if first.get("b64_json"):
        out.write_bytes(base64.b64decode(first["b64_json"]))
    elif first.get("url"):
        img_bytes = requests.get(first["url"], timeout=180).content
        out.write_bytes(img_bytes)
    else:
        log.error("无 b64_json 也无 url: %s", first)
        return None

    log.info("✓ %s (%s bytes)", out, out.stat().st_size)
    return out


def main() -> int:
    load_dotenv(ROOT / ".env")
    api_key = os.environ.get("GPT_IMAGE_API_KEY") or os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("GPT_IMAGE_BASE_URL") or os.environ.get("OPENAI_BASE_URL")
    model = os.environ.get("GPT_IMAGE_MODEL", "gpt-image-2-1k")
    model_fallback = os.environ.get("GPT_IMAGE_MODEL2")
    max_workers = int(os.environ.get("GPT_IMAGE_WORKERS", "5"))
    if not api_key or not base_url:
        log.error("缺 GPT_IMAGE_API_KEY 或 GPT_IMAGE_BASE_URL (查 .env)")
        return 1

    missing_refs = [n for n, p in REF_PNG.items() if not p.exists()]
    if missing_refs:
        log.error("参考图缺失: %s", missing_refs)
        return 2

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    args = sys.argv[1:]
    if args:
        target = set(args)
        shots = tuple(s for s in SHOTS if s.slug in target)
        if not shots:
            log.error("slug 不匹配: %s · 可用: %s",
                      args, [s.slug for s in SHOTS])
            return 3
    else:
        shots = SHOTS

    log.info("model=%s · fallback=%s · out=%s · 待检 %d 张 · %d 线程并发",
             model, model_fallback or "无", OUT_DIR, len(shots), max_workers)

    done = 0
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(generate_one, base_url, api_key, model, s, OUT_DIR,
                        model_fallback): s
            for s in shots
        }
        for fut in as_completed(futures):
            shot = futures[fut]
            try:
                result = fut.result()
            except Exception as exc:
                log.error("线程异常 %s: %s", shot.slug, exc)
                continue
            if result:
                done += 1
                log.info("进度 %d/%d", done, len(shots))

    log.info("完成 %d/%d 张", done, len(shots))
    return 0 if done == len(shots) else 4


if __name__ == "__main__":
    sys.exit(main())
