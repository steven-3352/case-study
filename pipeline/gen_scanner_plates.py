#!/usr/bin/env python3
"""语音厅《明月天涯》· 创意 A(扫描仪)的机器本体与叠加底板.

原方案是买一台二手平板扫描仪拍实物,2026-07-26 改判走生成。

**风格 = 与四张立绘同一套画风**(2026-07-26 用户指定)。立绘是国乙半写实
厚涂:干净细线稿 + 柔和喷枪渐变上色 + 低饱和克制配色 + 布料哑光/金属玻璃
一点点高光,没有照片颗粒也没有笔触噪点。扫描仪必须画成**同一套资产里的一件
道具立绘**,不是实拍微距 —— 照片机器配插画人物会两层皮。

两类产出:
- **本体**(`scanner_*`): 机器作为道具,有形有轮廓,合成时当主体摆
- **叠加底板**(其余): 满幅无主体,渲染时 screen/multiply 叠在合成帧上

用法:
    .venv/bin/python pipeline/gen_scanner_plates.py
    .venv/bin/python pipeline/gen_scanner_plates.py --only scanner_body glass_platen

已存在的文件跳过,想重出先删。
"""
from __future__ import annotations

import argparse
import base64
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "publish" / "语音厅" / "assets" / "textures" / "scanner_gen"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("scanner.plates")

# design_language.md §0: A = 2000 年代家用平板扫描仪,放在有日光的房间里。
# 色板与明暗基调由该实物决定 —— 亮底,暗只作为局部瞬间。
# 画风必须与四张立绘一致(用户 2026-07-26 指定): 国乙半写实厚涂道具立绘。
#
# ⚠️ 第一版只写"illustration / not a photograph"是不够的 —— 模型给的是柔和
# 三维产品渲染(无线稿、无块面),跟立绘放一起还是两层皮。立绘的**识别特征是
# 线稿**: 清晰的深色描边 + 块面式上色。所以 STYLE_PROP 必须把线稿写成主诉求,
# 并把"3D 渲染 / 矢量渐变 / 产品摄影"明确列进否定项。
STYLE_PROP = """
Hand-drawn anime illustration of an inanimate prop, drawn as an item asset for a
high-end Japanese otome visual novel — the exact same art style as that game's
full-body character portraits. MOST IMPORTANT: clean crisp dark ink LINE ART
defines every edge, seam and contour, drawn with confident varying-weight
strokes, exactly like anime lineart. Colour is laid in underneath the lines as
soft cel shading: flat base tones with a few clear shadow shapes and a few crisp
highlight shapes, blended with a gentle airbrush. Semi-realistic proportions,
elegant and restrained.
This is 2D hand-painted anime art. It is NOT a 3D render, NOT a product
render, NOT product photography, NOT a photograph, NOT a soft vector gradient
illustration, NOT flat minimal vector art.
""".strip()

# 叠加底板是光/瑕疵层,画线稿没有意义 —— 这一档只要求"手绘感的干净渐变"。
STYLE_PLATE = """
Hand-painted 2D anime-style overlay texture for a visual-novel scene: soft clean
painted gradients and delicate hand-drawn detail, the kind an anime background
artist paints. It is NOT a photograph, NOT a 3D render, and has NO photographic
film grain, NO lens bokeh.
""".strip()

PALETTE = """
Color: ivory and warm beige ABS plastic, pale off-white, brushed aluminium grey,
and the faint green edge of float glass. Desaturated, restrained, elegant.
NO neon purple, NO neon pink, NO cyan glow, NO saturated blue, NO teal-and-orange
grade, NO dark moody cyberpunk grade, NO RGB LED lighting.
""".strip()

NEG = """
Absolutely NO: people, hands, faces, text, letters, numbers, logos, brand marks,
watermarks, UI overlays, HUD, borders, vignette frames, any recognizable object
placed on the glass. NO dark canvas aesthetic. NO photographic realism, NO photo
grain, NO lens bokeh, NO depth-of-field blur, NO 3D-render specular.
""".strip()


def build_prompt(scene: str, lineart: bool) -> str:
    style = STYLE_PROP if lineart else STYLE_PLATE
    return f"{style}\n\n{PALETTE}\n\nSUBJECT:\n{scene}\n\nCONSTRAINTS:\n{NEG}"


@dataclass(frozen=True)
class Plate:
    slug: str
    label: str
    scene: str
    lineart: bool = False    # True = 道具本体(要线稿) · False = 光/瑕疵叠加底板

    @property
    def prompt(self) -> str:
        return build_prompt(self.scene, self.lineart)


PLATES: tuple[Plate, ...] = (
    # ——— 本体:机器当道具立绘,合成时是主体 ———
    Plate("scanner_body", "扫描仪本体 · 掀盖 · 道具立绘",
          """A consumer flatbed scanner from the early 2000s with its lid lifted
open to about seventy degrees, drawn as a game prop illustration. Seen from a
high three-quarter angle so both the open glass bed and the underside of the lid
are visible. Ivory-beige moulded plastic body with soft rounded corners, a thin
brushed aluminium trim strip, a white foam backing pad on the inside of the lid,
and a clean sheet of glass with a faint green tint along its cut edge. Even soft
frontal lighting, gentle contact shadow beneath. Plain flat pale background, the
prop fully inside frame with clear silhouette.""", lineart=True),

    Plate("scanner_closed", "扫描仪本体 · 合盖 · 道具立绘",
          """The same early-2000s consumer flatbed scanner with the lid closed
flat, drawn as a game prop illustration. Seen from a high three-quarter angle.
Ivory-beige moulded plastic, soft rounded corners, a thin brushed aluminium trim
strip, a slim seam running along the front where lid meets body. Even soft
frontal lighting, gentle contact shadow beneath. Plain flat pale background, the
prop fully inside frame with clear silhouette.""", lineart=True),

    Plate("glass_platen", "玻璃台面 · 满幅底",
          """The bare glass bed of a flatbed scanner seen straight down from
directly above, painted as clean illustration. The glass is nearly transparent
over a pale off-white backing, with a faint cool-green tint concentrated along
the edges where the glass is cut. A soft even sheen across the surface. The
frame is filled edge to edge by the glass surface itself, no object resting on
it, no border.""", lineart=True),

    # ——— 叠加底板:满幅无主体,渲染时 screen/multiply ———
    Plate("glass_dust", "玻璃浮尘 · 指纹油膜",
          """Dust and smudges on scanner glass, painted as clean illustration
rather than photographed: scattered fine dust motes as small bright dots, a few
long thin hairs as single crisp curved strokes, oily fingerprint smudges as soft
translucent shapes with faint ridge lines, a broad circular wipe mark from a
cloth. All of it sits over a pale near-white ground. The frame is filled edge to
edge, no object resting on the glass, no border."""),

    Plate("ccd_banding", "CCD 行噪 · 传感器条纹",
          """Scanner sensor banding rendered as clean graphic illustration: very
fine horizontal bands running the full width of a pale near-white field, with a
gentle periodic ripple in brightness from line to line and a few slightly darker
streaks. The bands are delicate, smooth-edged and irregular in spacing. Overall
bright, near-white. The frame is filled edge to edge, no border."""),

    Plate("lamp_falloff", "灯管不匀 · 两端衰减",
          """A single long narrow horizontal bar of cold white light spanning the
frame, painted as clean illustration. The bar is brightest at its centre and
falls off smoothly toward both ends, with a soft warm-white core, one tight
crisp edge and one slightly diffused edge. The surrounding area is dim but never
black. The uneven falloff is the subject. The frame is filled edge to edge, no
border."""),

    Plate("lid_leak", "盖板漏光 · 边缝",
          """Daylight flooding through the wedge-shaped gap of a lifted scanner
lid, painted as clean illustration: a hard bright warm wedge of light entering
from one edge and falling off smoothly across the frame into soft shade, with a
faint warm colour fringe at its brightest. A sliver of ivory-beige plastic lid
edge and rubber gasket runs along the seam. The frame is filled edge to edge, no
border."""),

    Plate("jam_smear", "卡纸拖影 · 步进错位",
          """A scan where the stepper motor stuttered, painted as clean
illustration: a pale near-white field in which one horizontal band is stretched
and smeared vertically into long soft streaks while the rest stays crisp. The
boundary between the clean region and the smeared region is abrupt, a hard
horizontal line. Bright and washed out, the smear reads as elongated ghosting.
The frame is filled edge to edge, no border."""),

    Plate("chassis_plastic", "机身塑料 · 满幅底",
          """The moulded top surface of an ivory-beige ABS plastic scanner body,
seen straight down from directly above, painted as clean illustration: a fine
regular pebble moulding texture, a straight brushed aluminium trim strip, a
subtle mould seam line, and one slightly more yellowed patch from age. The frame
is filled edge to edge by the plastic surface itself, no buttons with symbols,
no labels, no border.""", lineart=True),
)


def _post_once(base_url: str, api_key: str, model: str, plate: Plate,
               timeout: int = 300) -> dict:
    url = base_url.rstrip("/") + "/v1/images/generations"
    resp = requests.post(
        url,
        json={"prompt": plate.prompt, "model": model, "n": 1, "size": "1536x1024"},
        headers={"Authorization": f"Bearer {api_key}",
                 "Accept": "application/json",
                 "Content-Type": "application/json"},
        timeout=timeout,
    )
    if not resp.ok:
        raise requests.HTTPError(f"{resp.status_code} · body={(resp.text or '')[:500]}")
    return resp.json()


def generate_one(base_url: str, api_key: str, model: str, plate: Plate,
                 out_dir: Path, max_retries: int = 4) -> Path | None:
    out = out_dir / f"{plate.slug}.png"
    if out.exists():
        log.info("skip 已存在: %s", out.name)
        return out

    log.info("生图: %s → %s", plate.label, out.name)
    payload = None
    for attempt in range(1, max_retries + 1):
        try:
            payload = _post_once(base_url, api_key, model, plate)
            break
        except Exception as exc:
            log.warning("尝试 %d/%d %s 失败: %s", attempt, max_retries, plate.slug, exc)
            if attempt < max_retries:
                time.sleep(5)

    if payload is None or not payload.get("data"):
        log.error("放弃 %s", plate.label)
        return None

    first = payload["data"][0]
    if first.get("b64_json"):
        out.write_bytes(base64.b64decode(first["b64_json"]))
    elif first.get("url"):
        out.write_bytes(requests.get(first["url"], timeout=180).content)
    else:
        log.error("无 b64_json 也无 url: %s", plate.slug)
        return None

    log.info("✓ %s (%d KB)", out.name, out.stat().st_size // 1024)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="生成扫描仪质感底板")
    ap.add_argument("--only", nargs="*", default=None, help="只出指定 slug")
    args = ap.parse_args()

    load_dotenv(ROOT / ".env")
    base_url = os.environ["GPT_IMAGE_BASE_URL"]
    api_key = os.environ["GPT_IMAGE_API_KEY"]
    model = os.environ.get("GPT_IMAGE_MODEL", "gpt-image-2")
    # 503「无可用渠道」的根因是并发过高,不是模型名 —— 见 memory
    # feedback_gpt-image-model-fallback。默认压到 2。
    workers = int(os.environ.get("GPT_IMAGE_WORKERS", "2"))

    plates = PLATES
    if args.only:
        plates = tuple(p for p in PLATES if p.slug in set(args.only))
        if not plates:
            log.error("--only 没匹配到任何 slug,可选: %s",
                      ", ".join(p.slug for p in PLATES))
            return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log.info("共 %d 张 · 并发 %d · 输出 %s", len(plates), workers, OUT_DIR)

    ok = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(generate_one, base_url, api_key, model, p, OUT_DIR): p
                   for p in plates}
        for fut in as_completed(futures):
            if fut.result() is not None:
                ok += 1

    log.info("完成 %d/%d", ok, len(plates))
    return 0 if ok == len(plates) else 1


if __name__ == "__main__":
    sys.exit(main())
