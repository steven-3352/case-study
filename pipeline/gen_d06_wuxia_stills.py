#!/usr/bin/env python3
"""D06 武侠MV《一弦入江湖》· 全 34 镜 GPT-image-2 静图生成.

用户 (2026-07-18) 确认:
  1. 画幅 9:16 竖版 (1024x1536 native)
  2. BGM 用 5cb1ed3798646bfe3638707510040f0d.mp4 音轨
  3. 全 AI (用文本锚定三视图角色)
  4. S03 字幕 "风来了。" (不烧进图,后期加)
  5. 先全出静图,用户逐张确认后再进 i2v
  6. 短片轻量模式

隐含约束 (脚本没直说但必须遵守,写进每个 prompt):
  - 现代 (S01-S04): 波波头齐刘海 + 白 T 家居;江湖 (S05-S34): 高马尾 + 完整武侠套装
  - 江湖套装全片一致: 月白长衫 + 青灰短外袍 + 深青腰带 + 玉佩 + 酒葫芦 + 二胡
  - 二胡作为叙事线索必须出现或被引用
  - 场景锁死江南水乡黄昏微雨,不飘走
  - 低武侠红线: 无金光/法阵/发光音波/夸张飞檐,火花极短
  - 气质: 松弛不羁带笑意,非仙气/黑衣杀手/复仇脸
  - 字幕不烧进图 (S03/S32/S34 后期 drawtext)
  - 极特写 (S02/S14/S17/S18) 只露局部,不搞出全身错版

跳过已存在文件,只跑缺失的 (省 API 费).
"""
from __future__ import annotations

import base64
import logging
import mimetypes
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tmp" / "d06_wuxia" / "stills"
# 三视图作参考图锁脸,每张调用都传
REF_IMAGE = ROOT / "publish" / "2026-W30" / "D06" / "三视图.png"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("d06.wuxia.still")


# 面部结构锚 (不含发型,由 HAIR_* 分别注入)
FACE = """
Young East Asian woman in her early twenties, delicate oval face, fair
natural complexion (warm undertone, not overly pale), large soft dark
brown eyes with double eyelids, small straight nose, natural gentle mouth.
Slim petite build. Photorealistic cinematic film look, NOT anime, NOT
illustration, NOT CG doll — real human photo aesthetic.
""".strip()

HAIR_MODERN = """
Short chin-length wavy black bob haircut with straight blunt bangs (齐刘海)
just above the eyebrows, casual tousled texture.
""".strip()

HAIR_WUXIA = """
Black hair pulled up into a high loose ponytail secured with a plain wooden
hair-stick, a few casual loose strands framing the face and at the nape,
natural unfussy tie-up — NOT tightly styled, NOT court-formal, just a clean
wanderer's ponytail. Ponytail sways naturally.
""".strip()

LOOK_MODERN = """
Wearing a loose off-white cotton t-shirt with slightly falling shoulder,
casual at-home style. Modern quiet Chinese apartment interior: soft daylight
through window, minimal warm-neutral palette, wood floor, plain linen
curtain drifting.
""".strip()

# 江湖服装 (S05-S34 全片一套,严禁换装)
LOOK_WUXIA = """
Wearing a flowing moon-white long inner robe (月白长衫) with a blue-gray
short outer robe (青灰短外袍) over it, thin dark teal fabric sash tied at
waist (深青腰带), a small pale green jade pendant hanging at collar, a
small slim wine gourd tied at the belt. Cloth boots (布靴).
""".strip()

# 二胡 (中式,不是小提琴)
ERHU = """
A Chinese erhu — a two-string bowed instrument with a dark rosewood
hexagonal soundbox covered in python-skin front, a long slender wooden
neck, two tuning pegs at the top, and a curved horsehair bow.
""".strip()

# 江南水乡设定 (黄昏/微雨/灯笼/酒旗,不飘走)
SETTING = """
Ancient Chinese Jiangnan water town: gray cobblestone streets, wooden
low-eaved buildings with tile roofs, red hanging paper lanterns, red-cloth
wine flags fluttering, wooden inn signs. Dusk warm-golden light on the
foreground, cool blue mist in the deeper background, light drizzle in the
air, atmospheric humidity.
""".strip()

# 低武侠硬边界
NEG_LOWFANTASY = """
Low-fantasy realistic wuxia — NO magic effects, NO golden light, NO glowing
runes, NO glowing sound waves, NO exaggerated flying leaps between roofs,
NO neon colors. Any spark from blade contact is extremely small and brief.
""".strip()

TAIL = "9:16 vertical portrait cinematic frame, film grain, shallow depth of field, no text, no watermark, no subtitles burned in."


def modern_prompt(scene: str) -> str:
    return f"{FACE}\n\n{HAIR_MODERN}\n\n{LOOK_MODERN}\n\n{scene}\n\n{TAIL}"


def wuxia_prompt(scene: str, include_setting: bool = True) -> str:
    parts = [FACE, HAIR_WUXIA, LOOK_WUXIA, ERHU]
    if include_setting:
        parts.append(SETTING)
    parts += [scene, NEG_LOWFANTASY, TAIL]
    return "\n\n".join(parts)


@dataclass(frozen=True)
class Shot:
    slug: str
    covers_s: str
    label: str
    prompt: str


SHOTS: tuple[Shot, ...] = (
    # ========= 段 1 · 0-6s 现代唤醒 =========
    Shot("S01_modern_window", "0.0-2.0s", "S01 现代窗边侧脸",
        modern_prompt("""Composition: side profile close-up. She sits by a large
window, gazing softly out with unfocused eyes, calm daydreaming expression,
lips gently closed. An erhu (Chinese two-string instrument) leans against a
chair beside her, wooden body warmly catching side light. Very soft warm
daylight from the left rim-lights her hair and cheekbone. Dust motes drift
in the light beam. Rule of thirds, face right third, quiet negative space
on the left.""")),

    Shot("S02_finger_string", "2.0-4.0s", "S02 手指拨弦极特写",
        modern_prompt(f"""Composition: extreme macro close-up of her right hand
fingers plucking the strings of an erhu. Focus tight on fingertips and two
vibrating metal strings, polished dark rosewood soundbox and python-skin
front visible behind, wood grain sharply detailed. Slender fingers,
unpolished natural nails. Warm soft daylight rimming the strings. Extremely
shallow DOF. Only fingers and instrument visible — NO face, NO full body.

{ERHU}""")),

    Shot("S03_lift_eyes", "4.0-6.0s", "S03 抬眼看镜头",
        modern_prompt("""Composition: straight-on close-up portrait, face fills
frame vertically. She has just lifted her eyes toward camera, gaze direct
and clear, expression transitioning from dreamy blank to quietly awake
with a faint knowing smile at corner of mouth — as if she just heard
something only she can hear. Soft warm sidelight. Sharp focus on eyes.
Modern quiet apartment blurred in background.""")),

    Shot("S04_bow_sweep", "6.0-8.0s", "S04 琴弓横扫水墨转场",
        modern_prompt(f"""Composition: medium shot. She has just picked up the
erhu and drawn the horsehair bow horizontally across in a sweeping motion,
bow arcs across frame at eye level, motion-blurred. Where the bow passes,
the modern apartment background dissolves into flowing traditional Chinese
ink-wash (水墨) — gray-black brush strokes bleeding outward, walls and
window softening into abstract ink washes. Dissolve is halfway: half the
frame still modern room, half becoming ink-wash abstraction. NO golden
light, NO glowing runes, NO crack-of-light portal — only ink and mist.

{ERHU}""")),

    # ========= 段 2 · 6-10s 拉弦穿越 (S04→S05 世界切换) =========
    Shot("S05_town_arrival", "8.0-10.0s", "S05 古镇街口江湖初现",
        wuxia_prompt("""Composition: medium-full establishing shot. She stands
centered at the mouth of a Jiangnan cobblestone street at dusk, having
just completed the continued bow-drawing motion — erhu now held across her
body, bow arm still slightly extended, weight on one leg, relaxed easy
stance. Red paper lanterns hang from wooden eaves behind, a red wine flag
flutters. Warm-golden dusk light on her face, cool blue mist deeper in the
street, distant townsfolk silhouettes blurred. Expression: calm with amused
recognition — as if she has returned home. Slight motion in ponytail and
robe hem from the breeze.""")),

    # ========= 段 3 · 10-22s 江湖闪回 (12 镜快切) =========
    Shot("S06_street_gate", "10-11s", "S06 街口二胡搭肩",
        wuxia_prompt("""Composition: medium-wide shot. She stands at the mouth
of the old town street, erhu carried on her shoulder by a simple fabric
strap, weight relaxed on one leg, head tilted slightly. Behind her, a
large red wine flag whips in the breeze. Expression: like an old friend
of the jianghu returning home, quiet amused calm at the corner of her
mouth. Loose ponytail strands drift.""")),

    Shot("S07_tea_stall", "11-12s", "S07 茶摊边轻笑",
        wuxia_prompt("""Composition: medium shot from a slight side angle. She
sits at a rough wooden outdoor tea stand, an erhu leaning against the
bench beside her, a small ceramic tea bowl steaming in front of her, wisps
of steam rising. She looks slightly downward at the tea, a quiet unforced
smile — NOT looking at camera. Behind her, a bamboo teahouse curtain
sways lightly. Warm dusk light.""")),

    Shot("S08_eave_rain", "12-13s", "S08 屋檐听雨接雨",
        wuxia_prompt("""Composition: medium shot. She sits under a wooden eaved
porch, back against the wooden post, erhu laid horizontally across her
lap. Light drizzle visible as slanting silver lines just past the eave.
She extends her right hand palm-up beyond the eave to catch a few drops.
Expression: quietly attentive, waiting like before a storm. Behind her,
dim warm inn interior.""")),

    Shot("S09_market_walk", "13-14s", "S09 市集穿行",
        wuxia_prompt("""Composition: side-view tracking medium shot. She walks
briskly through a crowded Jiangnan market at dusk. Crowd around her is
deliberately motion-blurred and out of focus; only she is sharp. Jade
pendant and wine gourd swing at her waist with her stride. Erhu on
shoulder strap. Focused expression, slight forward lean. Background stall
lanterns and wooden signs streak past.""")),

    Shot("S10_carriage_pass", "14-15s", "S10 马车擦肩",
        wuxia_prompt("""Composition: medium shot from her side. A wooden
horse-drawn cart rushes past close behind her, motion-blurred, spraying up
mist from cobblestone puddles. She does NOT turn her head — just casually
reaches back with one hand to steady the erhu strap on her shoulder.
Expression: unbothered, seasoned. Dusk street with lanterns behind.""")),

    Shot("S11_bridge_glance", "15-16s", "S11 石桥半回眸",
        wuxia_prompt("""Composition: medium shot. She stands on the crest of an
arched gray-stone bridge over a canal at dusk in light drizzle. Two or
three townsfolk with oiled paper umbrellas walk past behind her. She has
just half-turned her head over her shoulder — hair strands sweeping across
her cheek, one sharp knowing look flashing in her eye. Wet stone bridge
reflects lantern light.""")),

    Shot("S12_inn_door", "16-17s", "S12 推开客栈门",
        wuxia_prompt("""Composition: interior POV shot — camera is INSIDE the
inn looking out through a narrow vertical crack of a just-opened heavy
wooden door. Her face and eyes are framed by this vertical door crack from
outside, sharp and alert, lit from behind by the outside blue dusk light.
Warm amber inn lantern light in the foreground silhouettes the door
edge. She is peering in, eyes visible through the crack. Emphasize the
door-crack framing effect — most of the image is the dark inn interior
and door edge, only a narrow strip shows her face outside. Rain patters
outside on the stone step.""")),

    Shot("S13_wineflag_gaze", "17-18s", "S13 酒旗下抬眸",
        wuxia_prompt("""Composition: medium-close shot. She stands in the
shadow of a huge red-cloth wine flag hanging from an inn corner, the flag
partially draping over the top of the frame, rippling in wind. She has
just tipped her chin up to look at something far off-frame — gaze
narrowed, focused. Robe hem lifts in the wind. Dusk warm-orange rim light
filtering through the wine flag's translucency.""")),

    Shot("S14_bow_string_macro", "18-19s", "S14 琴弓划弦特写",
        wuxia_prompt(f"""Composition: extreme close-up. Horsehair bow sweeps
swiftly across the two erhu strings, hair fibers slightly loose and
springing, strings vibrate in motion blur. Warm rim light catches the
varnished wood grain. Very tight and dark background. Only fragments of
her hand and outer sleeve visible — NO face, NO full body.

{ERHU}""", include_setting=False)),

    Shot("S15_alley_bamboo_hat", "19-20s", "S15 巷口斗笠客擦肩",
        wuxia_prompt("""Composition: medium two-shot at a narrow alley entrance
in dusk drizzle. She and a taller figure in a wide bamboo rain hat (斗笠)
and gray traveling cloak pass each other going opposite directions, both
walking, both eyes forward, NEITHER turning to look. Just a knife-edge of
tension crossing between them. Wet stone alley walls, dim.""")),

    Shot("S16_sleeve_sweep", "20-21s", "S16 抬手整袖袖扫镜头",
        wuxia_prompt("""Composition: dynamic action moment — she has just
raised her right arm across her body to straighten the wide sleeve cuff
of her outer robe, and IN THE ACT of that motion the sleeve fabric is
sweeping horizontally directly ACROSS the lens with strong motion blur —
a soft blue-gray fabric streak fills more than a third of the frame
diagonally, partially covering the top-right corner. Her face is calm,
eyes lowered to her sleeve, visible in the lower-left of the frame not
covered by the sleeve. Sense of an action about to be launched.
Background wet dim alley streaked from the motion.""")),

    Shot("S17_boot_splash", "21-22s", "S17 布靴踩水",
        wuxia_prompt("""Composition: extreme close-up of her cloth boots (布靴)
stepping onto a wet cobblestone. Moment of impact splashes a small crown
of water outward. Robe hem just visible at top of frame. Wet stones catch
warm lantern reflections. Only feet and immediate ground visible — NO
face, NO body.""", include_setting=False)),

    # ========= 段 4 · 22-32s 低武动作 (10 镜) =========
    Shot("S18_blade_tip_in", "22-23s", "S18 短刀入画眼神不变",
        wuxia_prompt("""Composition: shallow-focus close-up. A short curved
dagger's polished blade tip has ENTERED the frame from screen-left, aimed
at her throat area, held steady in a mid-thrust, tip clearly visible mid-
air about halfway across the frame — the blade has NOT touched anything,
NO spark, NO contact yet, blade is in pure clean transit. On the right
side of frame, her face and eyes remain calmly forward — expression
completely unchanged, NO shock, NO fear, NO reaction motion — she has
NOT moved to block. Focus is racked between the blade tip and her eye.
Dim wet alley behind. Absolutely NO sparks, NO impact flash in this
image.""", include_setting=False)),

    Shot("S19_bow_deflect", "23-24s", "S19 琴弓拨刀火花",
        wuxia_prompt("""Composition: medium shot. She holds the erhu bow
horizontally across her body and with a small effortless flick has just
pushed the incoming dagger sideways off its line — a tiny bright spark
flashes at the point of contact, sparks fine and extremely brief. Her
expression barely changes, corner of mouth slightly lifted. Loose
ponytail strands drift.""")),

    Shot("S20_side_dodge", "24-25s", "S20 侧身闪避",
        wuxia_prompt("""Composition: dynamic side shot, medium. She twists
mid-body sideways to let an implied blade pass in front of her chest —
the wide outer-robe hem sweeps past the lens in a dark blue-gray blur.
Ponytail whips with the motion. Her expression: calm, unhurried, precise
(NOT strained). Background wet alley streaked in motion.""")),

    Shot("S21_erhu_wrist_tap", "25-26s", "S21 二胡点腕落刀轻笑",
        wuxia_prompt("""Composition: dynamic freeze-frame moment of contact.
The wooden hexagonal soundbox end of her erhu has JUST STRUCK an
opponent's wrist visible on the right side of the frame — his wrist is
bent sharply from the impact, his fingers splayed open, and his short
sword is falling out of his grip mid-air just below the wrist. The erhu
soundbox is pressed AGAINST his wrist — CLEAR PHYSICAL CONTACT with the
wrist skin, not just extended-toward. Her face partially visible in the
frame with a quiet playful smile at the corner of her mouth. High
motion-frozen feeling.""")),

    Shot("S22_rooftop_run", "26-27s", "S22 屋檐轻跑",
        wuxia_prompt("""Composition: side tracking medium shot. She runs
lightly along the edge of a wooden tile rooftop at dusk, silhouetted
against a warm-orange sunset sky. Robe hem and long ponytail streaming
horizontally behind her from the run. Feet make quick soft contact with
the tiles — NO exaggerated flying, NO leaping between rooftops, just fast
light running along an ordinary sloped roof edge. Distant tile roofs of
the town in background.""")),

    Shot("S23_long_street_backlight", "27-28s", "S23 长街逆光",
        wuxia_prompt("""Composition: medium shot. She walks down the center of
a long stone street directly toward the camera. Warm-golden dusk sun
directly behind her, rimming her silhouette in a brilliant halo, her face
partially in shadow but features still readable. Ahead of her, blurred
townsfolk figures instinctively part to let her through. Wine flags and
red lanterns line the street. Confident easy stride.""")),

    Shot("S24_gourd_toss", "28-29s", "S24 酒葫芦抛接",
        wuxia_prompt("""Composition: medium-close shot. She has just tossed her
small wine gourd up into the air with a lazy flick of her wrist — the
gourd is captured mid-air just above her head, its cord dangling in a soft
arc. Her other hand is opening to receive it. Corner of mouth lifted in
casual amusement. Behind her: dim inn interior with amber lanterns.""")),

    Shot("S25_erhu_wind", "29-30s", "S25 拉响二胡气场压场",
        wuxia_prompt("""Composition: medium wide shot. She draws the erhu bow
across the strings full length, right arm fully extended. NO visible
glowing sound waves, NO magical effect, NO light halo. Instead: the wind
visibly picks up sharply — the red wine flag behind her whips and snaps
hard, ponytail streams sideways, robe hem billows. Ambient physical
effect only, NO glow, NO rune, NO spirit.""")),

    Shot("S26_opponents_retreat", "30-31s", "S26 对手后退让路",
        wuxia_prompt("""Composition: medium wide from her back-quarter view. She
stands facing several out-of-focus dark-clothed figures who instinctively
step backward, giving her a clear path forward. She does NOT chase — she
simply walks forward at a measured calm pace. Erhu carried on her
shoulder. Wet dusk street with lanterns.""")),

    Shot("S27_scabbard_tap", "31-32s", "S27 擦肩琴弓敲刀鞘",
        wuxia_prompt("""Composition: side view moment-of-contact freeze-frame.
She is mid-stride walking past a defeated opponent on the right side of
the frame. The tip of her horsehair erhu bow is IN THE ACT of striking
his sheathed sword scabbard at his hip — clear physical contact of bow
tip against wooden lacquered scabbard, tiny bright ting-flash at the
contact point, wisp of vibration on the bow hair. She does NOT look at
him, gaze forward. The opponent is a rough JIANGHU commoner traveler in
plain dust-brown short jacket and travel trousers — NOT a black-clad
assassin, NOT a court warrior, just a jianghu roughneck who lost. He
freezes mid-standing, stunned. Cool dusk stone street.""")),

    # ========= 段 5 · 32-38s 高光混剪 (6 镜) =========
    Shot("S28_dusk_rooftop_wide", "32-33s", "S28 黄昏屋檐远景",
        wuxia_prompt("""Composition: wide long shot. She sits on the tile edge
of a wooden eaved rooftop, small figure in the frame, erhu resting
horizontally beside her. In front of and below her, the ancient Jiangnan
town glows with warm lantern-lit windows against the deepening dusk sky.
Her silhouette small, human, contemplative. Solitary jianghu feeling.""")),

    Shot("S29_wind_smile_closeup", "33-34s", "S29 近景轻笑",
        wuxia_prompt("""Composition: tight close-up portrait. Loose ponytail
strands blow across her face in a breeze. Her eyes shift toward camera,
and the corner of her mouth pulls into a quiet dry weary-amused smile —
NOT sweet, more like ‘the jianghu can't rush me.' Warm-golden dusk
sidelight rim-lighting her cheekbone.""")),

    Shot("S30_street_dash", "34-35s", "S30 长街奔跑",
        wuxia_prompt("""Composition: handheld side tracking shot, medium, of
her IN THE MIDDLE of a full RUNNING stride — one leg pushed off the
ground, the other leg stretched forward, entire body clearly leaning
forward with the run. The erhu is CLEARLY VISIBLE strapped diagonally on
her back with its wooden neck rising above her right shoulder — she is
NOT holding it, it's on her back where the shoulder strap secures it.
Robe hem, outer robe, wine gourd, jade pendant, and long ponytail all
whip HORIZONTALLY behind her from the running speed. STRONG horizontal
motion blur streaks on the background walls and lanterns. Dusk warm
lantern light. Expression composed but urgent. Sense of fast running,
NOT walking.""")),

    Shot("S31_bow_block_sword", "35-36s", "S31 琴弓横挡刀",
        wuxia_prompt("""Composition: medium shot frozen at the moment of
impact. She holds her erhu bow horizontally in front of her chest with
both hands, and a curved short sword blade has just been stopped by the
bow — a very small bright spark flashes at the contact point, brief.
Expression: cool, direct eye contact with attacker off-frame right. Robe
caught mid-motion.""")),

    Shot("S32_bridge_lanterns_glance", "36-37s", "S32 回眸灯笼亮起",
        wuxia_prompt("""Composition: medium shot. She stands mid-bridge or at
an alley mouth, half-turned to look back over her shoulder toward camera.
Behind her, a long row of red paper lanterns has just been lit — glowing
warmly and evenly along the deep background. Expression: quietly knowing,
a hint of a smile. Dusk. Absolutely NO burned-in subtitle text in image
— text will be added later in post.""")),

    Shot("S33_wave_farewell", "37-38s", "S33 抬手告别",
        wuxia_prompt("""Composition: medium shot. She has just casually shifted
her erhu up onto her shoulder with one hand and raised her other hand in
a small easy wave — NOT looking directly at camera, more toward
off-screen. Half-smile at corner of mouth. Behind her the town glows
softly with lantern light. Dusk.""")),

    # ========= 段 6 · 38-40s 收尾 =========
    Shot("S34_back_walkaway", "38-40s", "S34 背影入江湖",
        wuxia_prompt("""Composition: full-body wide back shot. Her back walks
away from camera down the deepening cobblestone street of the town,
ponytail swaying, outer robe and hem moving with her stride, erhu on her
back. Ahead of her, the town street stretches on, lit with strings of
red lanterns and moving townsfolk silhouettes. Cold-warm mixed light
(dusk sky above + warm lantern below). Absolutely NO subtitle text in
image — will be added later in post.""")),
)


def generate_one(base_url: str, api_key: str, model: str, shot: Shot, out_dir: Path) -> Path | None:
    """走 /v1/images/edits 多参考图 multipart,三视图作 ref 锁脸."""
    out = out_dir / f"{shot.slug}.png"
    if out.exists():
        log.info("skip 已存在: %s", out.name)
        return out

    log.info("生图: %s (%s) → %s", shot.label, shot.covers_s, out.name)
    url = base_url.rstrip("/") + "/v1/images/edits"
    ref_bytes = REF_IMAGE.read_bytes()
    ref_mime = mimetypes.guess_type(str(REF_IMAGE))[0] or "image/png"

    max_retries = 4
    for attempt in range(1, max_retries + 1):
        try:
            files = [("image", (REF_IMAGE.name, ref_bytes, ref_mime))]
            data = {
                "prompt": shot.prompt,
                "model": model,
                "n": "1",
                "size": "1024x1536",
            }
            headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
            resp = requests.post(url, files=files, data=data, headers=headers, timeout=300)
            resp.raise_for_status()
            payload = resp.json()
        except Exception as exc:
            log.warning("尝试 %d/%d 失败: %s", attempt, max_retries, exc)
            if attempt < max_retries:
                time.sleep(5)
                continue
            log.error("放弃 %s (%d 次全败)", shot.label, max_retries)
            return None

        if not payload.get("data"):
            log.error("返回 data 为空: %s", payload)
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

    return None


def main() -> int:
    load_dotenv(ROOT / ".env")
    api_key = os.environ.get("GPT_IMAGE_API_KEY") or os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("GPT_IMAGE_BASE_URL") or os.environ.get("OPENAI_BASE_URL")
    # tonbirds 实际模型名是 gpt-image-2-1k
    model = os.environ.get("GPT_IMAGE_MODEL", "gpt-image-2-1k")
    if not api_key or not base_url:
        log.error("缺 GPT_IMAGE_API_KEY 或 GPT_IMAGE_BASE_URL (查 .env)")
        return 1
    if not REF_IMAGE.exists():
        log.error("参考图缺失: %s", REF_IMAGE)
        return 2

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    args = sys.argv[1:]
    if args:
        target = set(args)
        shots = tuple(s for s in SHOTS if s.slug in target)
        if not shots:
            log.error("slug 不匹配: %s · 可用: %s", args, [s.slug for s in SHOTS])
            return 3
    else:
        shots = SHOTS

    log.info(
        "model=%s · ref=%s · out=%s · 待检 %d 张 (跳过已存在) · 5 线程并发",
        model, REF_IMAGE.name, OUT_DIR, len(shots),
    )

    ok = 0
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = {
            ex.submit(generate_one, base_url, api_key, model, s, OUT_DIR): s
            for s in shots
        }
        for fut in as_completed(futures):
            shot = futures[fut]
            try:
                result = fut.result()
            except Exception as exc:
                log.error("worker 异常 %s: %s", shot.slug, exc)
                result = None
            if result is not None:
                ok += 1
    log.info("完成: %d/%d 成功", ok, len(shots))
    return 0 if ok == len(shots) else 5


if __name__ == "__main__":
    sys.exit(main())
