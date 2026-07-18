#!/usr/bin/env python3
"""D06 武侠MV《一弦入江湖》· 全 34 段 Grok image-to-video 动效.

用户 (2026-07-18) 确认:
  - 34 张静图已过审,全部走 grok-imagine-video
  - 9:16 竖版 · duration=3s/段 (后期 ffmpeg 各裁 1s 快切)
  - reference_images 不传 (与 image 二选一,静图已锁角色)
  - 5 线程并发 (predicted 15-20 min 挂钟)

隐含约束继承 stills:
  - 现代 (S01-S04): 短波波头; 江湖 (S05-S34): 高马尾
  - 二胡贯穿, 无金光/法阵/发光音波
  - 火花极短一闪, 屋檐轻跑不飞起来

跳过已存在 mp4, 5 线程并发.
"""
from __future__ import annotations

import base64
import json
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
STILLS_DIR = ROOT / "tmp" / "d06_wuxia" / "stills"
VIDEOS_DIR = ROOT / "tmp" / "d06_wuxia" / "videos"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("d06.wuxia.video")


MOTION_QA = "Photorealistic cinematic film look, natural human motion, no morphing, no face distortion, no ghosting, no extra limbs, no melting fabric."


@dataclass(frozen=True)
class VideoScene:
    slug: str
    motion_prompt: str
    first_frame: Path
    duration: int
    label: str


# 每段 motion prompt 简洁描述本镜的具体动作变化 (画面已由首帧锁定)
MOTIONS: dict[str, tuple[str, str]] = {
    # 段 1 现代唤醒
    "S01_modern_window": (
        "S01 现代窗边呼吸",
        f"She breathes softly, chest rising and falling gently. Lashes flutter, "
        f"she blinks slowly once. A few strands of her short bob hair drift "
        f"barely in the still air. Dust motes drift lazily in the sidelight. "
        f"Camera holds still. {MOTION_QA}"),
    "S02_finger_string": (
        "S02 手指拨弦震颤",
        f"Extreme macro. Her fingertip presses down, releases the erhu string, "
        f"the string vibrates rapidly with visible motion blur. Fine tremor "
        f"propagates. Camera holds tight and still. {MOTION_QA}"),
    "S03_lift_eyes": (
        "S03 抬眸淡笑",
        f"Her eyes slowly lift and meet the camera lens. Expression shifts from "
        f"dreamy blank to quiet awakening, the faintest knowing smile pulls at "
        f"the corner of her mouth. A single natural blink. Camera still. {MOTION_QA}"),
    "S04_bow_sweep": (
        "S04 琴弓横扫水墨",
        f"She continues drawing the erhu bow horizontally across frame. Where "
        f"the bow passes, the modern apartment background continues to dissolve "
        f"into flowing gray-black Chinese ink-wash strokes, ink bleeds outward. "
        f"NO golden light, NO glowing runes, NO portal. {MOTION_QA}"),
    "S05_town_arrival": (
        "S05 古镇初现风动",
        f"Gentle breeze catches her loose high ponytail and moon-white robe hem, "
        f"both drift and sway. Red wine flag behind her flutters. Red paper "
        f"lanterns sway. Distant townsfolk silhouettes shift subtly. Camera "
        f"holds still with very slow barely perceptible push-in. {MOTION_QA}"),

    # 段 3 江湖闪回 S06-S17
    "S06_street_gate": (
        "S06 街口二胡搭肩",
        f"She stands at street mouth with erhu on shoulder strap. Ponytail "
        f"sways lightly in the breeze, wine flag whips overhead, her head "
        f"tilts slightly, a small amused smile forms at corner of mouth. "
        f"Camera holds still. {MOTION_QA}"),
    "S07_tea_stall": (
        "S07 茶摊边轻笑",
        f"She sits at the tea stand. Steam wisps rise from the tea bowl. "
        f"Bamboo curtain behind her sways gently. She looks slightly down, "
        f"her quiet unforced smile deepens for a beat. Ponytail strands "
        f"drift. Camera still. {MOTION_QA}"),
    "S08_eave_rain": (
        "S08 屋檐听雨接雨",
        f"Slanting silver rain lines fall past the eave continuously. A few "
        f"drops land in her extended palm, water droplets form. She keeps "
        f"her hand still, expression quietly attentive. Ponytail strands "
        f"drift slightly. Camera still. {MOTION_QA}"),
    "S09_market_walk": (
        "S09 市集穿行",
        f"She walks briskly forward. Wine gourd and jade pendant swing at "
        f"her waist with each stride. Ponytail bounces subtly. The blurred "
        f"crowd around her continues to move and streak past. Camera tracks "
        f"her from the side at matching speed. {MOTION_QA}"),
    "S10_carriage_pass": (
        "S10 马车擦肩",
        f"The wooden horse-drawn cart continues rushing past behind her in "
        f"strong horizontal motion blur, spraying up puddle mist. She does "
        f"NOT turn her head — her hand steadies the erhu strap. Her ponytail "
        f"briefly disturbed by the cart's wind then settles. {MOTION_QA}"),
    "S11_bridge_glance": (
        "S11 石桥半回眸",
        f"She has just turned her head over her shoulder — hair strands "
        f"sweep across her cheek as they settle. Her sharp knowing look "
        f"holds for a beat, then a tiny smile forms. Umbrella townsfolk "
        f"behind continue walking. Light drizzle falls. {MOTION_QA}"),
    "S12_inn_door": (
        "S12 推开客栈门",
        f"The heavy wooden door creaks open slightly wider from her push, "
        f"the vertical crack expanding. Warm amber lantern light plays "
        f"across her face. Her sharp alert eyes hold steady, small blink. "
        f"Rain falls outside. Camera holds still from inside. {MOTION_QA}"),
    "S13_wineflag_gaze": (
        "S13 酒旗下抬眸",
        f"The large red wine flag ripples continuously above her. She keeps "
        f"her chin tipped up, gaze narrowed and focused far off-frame. Robe "
        f"hem lifts and drifts in the wind. Ponytail sways. Warm dusk light "
        f"through wine flag translucency shifts subtly. {MOTION_QA}"),
    "S14_bow_string_macro": (
        "S14 琴弓划弦特写",
        f"Extreme macro. Horsehair bow sweeps swiftly across the two erhu "
        f"strings, hair fibers spring and settle, strings vibrate strongly "
        f"with motion blur. Warm rim light catches wood grain shifts. "
        f"Camera tight and still. {MOTION_QA}"),
    "S15_alley_bamboo_hat": (
        "S15 巷口斗笠客擦肩",
        f"Both figures continue walking opposite directions past each other, "
        f"both robes and the bamboo hat sway with their steps, neither turns "
        f"their head. Rain falls between them. Tension crossing them holds. "
        f"Camera still, side view. {MOTION_QA}"),
    "S16_sleeve_sweep": (
        "S16 抬手整袖袖扫镜头",
        f"The wide blue-gray sleeve continues its horizontal arc across the "
        f"frame with strong motion blur, then begins to fall back and settle. "
        f"Her face becomes fully visible as sleeve clears. Hair strands "
        f"settle. Dim wet alley in background. {MOTION_QA}"),
    "S17_boot_splash": (
        "S17 布靴踩水",
        f"Extreme close-up on the cloth boots. The lifted foot completes "
        f"its rise, water droplets scatter and fall. Robe hem shifts. The "
        f"next foot begins to descend toward the next wet cobblestone. "
        f"Warm lantern reflections ripple on wet stones. {MOTION_QA}"),

    # 段 4 低武动作 S18-S27
    "S18_blade_tip_in": (
        "S18 短刀入画眼神不变",
        f"The short curved dagger blade tip holds its position in the frame, "
        f"absolutely no impact motion. Her expression stays completely still "
        f"— she does NOT flinch, does NOT react. A single very slow blink. "
        f"Ponytail sways barely. Camera holds. NO sparks. NO contact. {MOTION_QA}"),
    "S19_bow_deflect": (
        "S19 琴弓拨刀火花",
        f"The tiny spark at bow-blade contact fades quickly, dagger continues "
        f"deflected sideways off frame. Bow returns to horizontal position. "
        f"Her expression barely changes, small smile persists. Ponytail sways. "
        f"Camera holds still. {MOTION_QA}"),
    "S20_side_dodge": (
        "S20 侧身闪避",
        f"She completes her body twist, the sword blade passes through in "
        f"front of her chest and clears frame. Outer-robe hem trails behind "
        f"the motion then settles. Ponytail whips then settles. Her expression "
        f"stays calm. Background streaks with the motion. {MOTION_QA}"),
    "S21_erhu_wrist_tap": (
        "S21 二胡点腕落刀",
        f"The opponent's wrist stays bent from the strike, fingers splayed. "
        f"The falling short sword completes its drop and clatters to wet "
        f"cobblestone at their feet. Her quiet playful smile holds and "
        f"deepens slightly. {MOTION_QA}"),
    "S22_rooftop_run": (
        "S22 屋檐轻跑",
        f"She continues running lightly along the tile rooftop edge, feet "
        f"making quick soft contact. Long ponytail streams horizontally, "
        f"robe hem billows behind her. Warm dusk sky. NO exaggerated leap, "
        f"NO flying. Camera tracks laterally with her. {MOTION_QA}"),
    "S23_long_street_backlight": (
        "S23 长街逆光",
        f"She continues walking toward camera at a measured confident pace. "
        f"Blurred townsfolk ahead continue to part and step aside. Warm-"
        f"golden dusk backlight rims her silhouette. Wine flags flutter, "
        f"lanterns sway. {MOTION_QA}"),
    "S24_gourd_toss": (
        "S24 酒葫芦抛接",
        f"The tossed wine gourd reaches apex above her head, then falls "
        f"back down into her waiting open hand — she catches it cleanly. "
        f"Corner of mouth lifts more with amusement. Cord traces arc. "
        f"Camera still. {MOTION_QA}"),
    "S25_erhu_wind": (
        "S25 拉响二胡气场压场",
        f"She completes drawing the bow full length across strings. NO glow, "
        f"NO sound waves, NO magic. Instead: wind visibly picks up hard — "
        f"red wine flag whips violently, her long ponytail streams sideways, "
        f"robe hem billows dramatically. Physical wind only. {MOTION_QA}"),
    "S26_opponents_retreat": (
        "S26 对手后退让路",
        f"The blurred dark-clothed figures ahead continue backing away, "
        f"parting a clear path. She walks forward at a measured calm pace "
        f"toward them, erhu swaying on her shoulder with her stride. "
        f"Ponytail sways. Wet dusk street. {MOTION_QA}"),
    "S27_scabbard_tap": (
        "S27 擦肩琴弓敲刀鞘",
        f"The tiny bright spark at the bow-tip contact with scabbard fades. "
        f"The opponent commoner stays frozen mid-standing, stunned. She "
        f"continues walking past him without looking, gaze forward. Her "
        f"ponytail sways with her stride. {MOTION_QA}"),

    # 段 5 高光混剪 S28-S33
    "S28_dusk_rooftop_wide": (
        "S28 黄昏屋檐远景",
        f"Wide shot. Distant lantern-lit windows flicker warm across the "
        f"town below. Her small figure sits still, breeze rustles her "
        f"ponytail. Sky continues to deepen slightly from dusk toward "
        f"night. Wisps of mist drift. Camera still. {MOTION_QA}"),
    "S29_wind_smile_closeup": (
        "S29 近景轻笑",
        f"Tight close-up. Loose ponytail strands blow across her face and "
        f"settle. Her eyes shift toward camera, corner of mouth pulls into "
        f"a quiet dry weary-amused smile that lingers for a beat then "
        f"softens. Single blink. Warm sidelight shifts. {MOTION_QA}"),
    "S30_street_dash": (
        "S30 长街奔跑",
        f"She continues her full running stride, robe hem, wine gourd, jade "
        f"pendant, and long ponytail all whip HORIZONTALLY behind her from "
        f"speed. Strong horizontal motion blur streaks on background walls "
        f"and lanterns. Handheld shake. Expression composed but urgent. {MOTION_QA}"),
    "S31_bow_block_sword": (
        "S31 琴弓横挡刀",
        f"The curved short sword vibrates against her horizontal erhu bow, "
        f"tiny bright spark at contact fades quickly. She holds the bow "
        f"firmly with both hands, eyes locked forward on attacker off-frame. "
        f"Her ponytail sways from the impact absorption. {MOTION_QA}"),
    "S32_bridge_lanterns_glance": (
        "S32 回眸灯笼亮起",
        f"The long row of red paper lanterns finishes lighting up one after "
        f"another along the deep background — sequential warm glow ripple. "
        f"She half-turns her head fully to look back at camera, small "
        f"knowing smile forms. Ponytail sways. {MOTION_QA}"),
    "S33_wave_farewell": (
        "S33 抬手告别",
        f"Her raised hand continues in a small casual wave, hand moves side "
        f"to side once. Half-smile at corner of mouth lingers. Ponytail "
        f"sways. Behind her the town lantern light glows softly. Breeze "
        f"catches robe hem. Camera still. {MOTION_QA}"),

    # 段 6 收尾
    "S34_back_walkaway": (
        "S34 背影入江湖",
        f"Her back walks steadily away from camera down the deepening "
        f"cobblestone street. Ponytail sways with each stride, outer robe "
        f"and hem move naturally with her walk. String of red lanterns "
        f"twinkle warmly along the receding street. Townsfolk silhouettes "
        f"shift subtly. Camera very slowly pulls back. {MOTION_QA}"),
}


SCENES: tuple[VideoScene, ...] = tuple(
    VideoScene(
        slug=slug,
        motion_prompt=motion,
        first_frame=STILLS_DIR / f"{slug}.png",
        duration=3,
        label=label,
    )
    for slug, (label, motion) in MOTIONS.items()
)


def png_to_data_url(path: Path) -> str:
    raw = path.read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:image/png;base64,{b64}"


def submit_video(base_url: str, api_key: str, model: str, scene: VideoScene) -> dict:
    url = base_url.rstrip("/") + "/v1/videos/generations"
    if not scene.first_frame.exists():
        raise FileNotFoundError(f"首帧图缺失: {scene.first_frame}")

    # Grok 二选一: image (i2v) OR reference_images (r2v),不能同时传.
    # 静图已锁角色,走 i2v 更强.
    payload = {
        "model": model,
        "prompt": scene.motion_prompt,
        "resolution": "720p",
        "aspect_ratio": "9:16",
        "duration": scene.duration,
        "image": {"url": png_to_data_url(scene.first_frame)},
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    log.info(
        "POST %s · duration=%ds · payload≈%d KB",
        scene.slug, scene.duration, len(json.dumps(payload)) // 1024,
    )
    resp = requests.post(url, headers=headers, json=payload, timeout=180)
    log.info("HTTP %d · %s · body_head: %s", resp.status_code, scene.slug, resp.text[:200])
    resp.raise_for_status()
    return resp.json()


def extract_video_url(resp: dict) -> str | None:
    if "video" in resp and isinstance(resp["video"], dict):
        if isinstance(resp["video"].get("url"), str):
            return resp["video"]["url"]
    for key in ("video_url", "url", "output_url", "result_url"):
        if key in resp and isinstance(resp[key], str):
            return resp[key]
    if "data" in resp and isinstance(resp["data"], list) and resp["data"]:
        item = resp["data"][0]
        for key in ("url", "video_url", "output_url"):
            if key in item and isinstance(item[key], str):
                return item[key]
    if "output" in resp and isinstance(resp["output"], dict):
        for key in ("url", "video_url"):
            if key in resp["output"]:
                return resp["output"][key]
    return None


def extract_task_id(resp: dict) -> str | None:
    for key in ("task_id", "job_id", "id", "request_id"):
        if key in resp and isinstance(resp[key], str):
            return resp[key]
    return None


def poll_task(base_url: str, api_key: str, task_id: str, slug: str, max_wait: int = 600) -> str | None:
    poll_url_candidates = [
        base_url.rstrip("/") + f"/v1/videos/generations/{task_id}",
        base_url.rstrip("/") + f"/v1/videos/{task_id}",
        base_url.rstrip("/") + f"/v1/tasks/{task_id}",
    ]
    headers = {"Authorization": f"Bearer {api_key}"}
    start = time.time()
    delay = 5

    poll_url = None
    for cand in poll_url_candidates:
        try:
            r = requests.get(cand, headers=headers, timeout=15)
            if r.status_code == 200:
                poll_url = cand
                break
        except Exception:
            pass

    if not poll_url:
        log.warning("[%s] 找不到有效 poll endpoint", slug)
        return None

    while time.time() - start < max_wait:
        try:
            r = requests.get(poll_url, headers=headers, timeout=15)
            if r.status_code != 200:
                time.sleep(delay)
                continue
            data = r.json()
            elapsed = int(time.time() - start)
            log.info("[%s] 轮询 %ds · status=%s", slug, elapsed, data.get("status", "?"))
            video_url = extract_video_url(data)
            if video_url:
                return video_url
            status = str(data.get("status", "")).lower()
            if status in {"failed", "error"}:
                log.error("[%s] 任务失败: %s", slug, data)
                return None
            time.sleep(delay)
            delay = min(delay + 2, 15)
        except Exception:
            time.sleep(delay)

    log.error("[%s] 轮询超时", slug)
    return None


def download_video(url: str, out: Path, slug: str) -> bool:
    proxies = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
    try:
        r = requests.get(url, timeout=180, stream=True, proxies=proxies)
        r.raise_for_status()
        out.write_bytes(r.content)
        log.info("[%s] ✓ %s (%d KB)", slug, out.name, out.stat().st_size // 1024)
        return True
    except Exception as exc:
        log.error("[%s] 下载失败: %s", slug, exc)
        return False


def generate_scene_video(base_url: str, api_key: str, model: str, scene: VideoScene, out_dir: Path) -> Path | None:
    out = out_dir / f"{scene.slug}.mp4"
    if out.exists():
        log.info("skip 已存在: %s", out.name)
        return out

    log.info("=== [%s] %s 提交 ===", scene.slug, scene.label)
    try:
        resp = submit_video(base_url, api_key, model, scene)
    except Exception as exc:
        log.error("[%s] 提交失败: %s", scene.slug, exc)
        return None

    video_url = extract_video_url(resp)
    if video_url:
        return out if download_video(video_url, out, scene.slug) else None

    task_id = extract_task_id(resp)
    if not task_id:
        log.error("[%s] 无 video_url 也无 task_id", scene.slug)
        return None

    log.info("[%s] 异步任务 id=%s · 开始轮询", scene.slug, task_id)
    video_url = poll_task(base_url, api_key, task_id, scene.slug)
    if not video_url:
        return None
    return out if download_video(video_url, out, scene.slug) else None


def main() -> int:
    load_dotenv(ROOT / ".env")
    api_key = os.environ.get("GROK_API_KEY")
    base_url = os.environ.get("GROK_BASE_URL")
    model = os.environ.get("GROK_MODEL", "grok-imagine-video")
    if not api_key or not base_url:
        log.error("缺 GROK_API_KEY 或 GROK_BASE_URL (查 .env)")
        return 1

    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    args = sys.argv[1:]
    if args:
        target = set(args)
        scenes = tuple(s for s in SCENES if s.slug in target)
        if not scenes:
            log.error("slug 不匹配: %s · 可用: %s", args, [s.slug for s in SCENES])
            return 3
    else:
        scenes = SCENES

    log.info("model=%s · base=%s · 待生成 %d 段 · 5 线程并发", model, base_url, len(scenes))

    ok = 0
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = {
            ex.submit(generate_scene_video, base_url, api_key, model, s, VIDEOS_DIR): s
            for s in scenes
        }
        for fut in as_completed(futures):
            scene = futures[fut]
            try:
                r = fut.result()
            except Exception as exc:
                log.error("worker 异常 %s: %s", scene.slug, exc)
                r = None
            if r is not None:
                ok += 1
    log.info("完成: %d/%d 成功", ok, len(scenes))
    return 0 if ok == len(scenes) else 5


if __name__ == "__main__":
    sys.exit(main())
