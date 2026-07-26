#!/usr/bin/env python3
"""语音厅《明月天涯》· V4 纸片人卡点 MV —— Tuscan 日落背景 + §13 运动感技法.

本文件是该片专属一次性分镜产物（template-clone 铁律）。引擎见 paperdoll_engine.py。

V4 技法组合（§13.9）：
  0–4.14s   胶片走带 film_strip · 花园景 bg_v4d
  登场段     碎片聚合 shatter · bg 循环 4 景（逐人不同角）
  solo 段    残影 echo + 多运镜 · bg 轮换
  2人段      place_group · 石拱门 bg_v4c
  4人合体    echo+flash · 主露台 bg_v4
  尾段特写   经典 · 露台全景 bg_v4b
  结尾定版   title_mode=ending · bg_v4b

调用：python3 gen_paperdoll_pv_v4.py [start] [end]   默认 0 52.92
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paperdoll_engine import (  # noqa: E402
    AMBER, CREAM, ORANGE, PEACH, ROSE, PVPaths, Shot, render,
)

ROOT  = Path(__file__).resolve().parents[2]
VOICE = ROOT / "publish" / "语音厅"
V4DIR = VOICE / "pv_v4"

PATHS = PVPaths(
    assets_dir=VOICE / "script_v2_assets",
    wav=VOICE / "明月天涯 导唱(1).WAV",
    out_dir=V4DIR,
    bg_plate="bg_v4.png",   # 主露台作 numpy 底图
    slug="mingyue_v4",
)

NAME  = {"CY": "cy", "NL": "诺兰", "XH": "轩珩", "ZL": "中里毅2"}

GOLD_SOFT  = (240, 200, 160)
GOLD_WARM  = (248, 208, 158)
GRADES     = [AMBER, ROSE, GOLD_SOFT, PEACH, ORANGE]

# V4 背景绝对路径
BG = {
    "garden":   str(V4DIR / "bg_v4d.png"),   # 花园角 · 开场
    "terrace":  str(V4DIR / "bg_v4.png"),    # 主露台 · 4 人合体
    "overlook": str(V4DIR / "bg_v4b.png"),   # 露台全景 · 尾/solo
    "arch":     str(V4DIR / "bg_v4c.png"),   # 石拱门 · 2 人
}
BG_SOLO = [BG["garden"], BG["overlook"], BG["terrace"], BG["arch"]]

UP   = (0.10, 0.00, 0.90, 0.34)
HALF = (0.05, 0.00, 0.95, 0.58)

# hfrac = 人物"静止"高度占比。刻意压小（全身镜 0.60-0.66）→ 头顶留足空气(不砍头)
# 且给缩放运镜"生长空间"。SOLO_SEQ 以「新手法为主」（split 分屏/kaleido 分身/silhouette
# 剪影/speed_impact 冲击框，V3 全无）打底，相机运动只做衔接过桥 · 禁连续 3 镜同一 cam。
SOLO_SEQ = [
    ("split",      "flash",      None, 0.90),   # 新①分屏切割（3 格不同景别错位滑入）
    ("push_in",    "silhouette", None, 0.64),   # 新②剪影点亮登场 + 推入
    ("kaleido",    "flash",      None, 0.92),   # 新③节奏分身（5 副本弧线逐拍 pop）
    ("low_angle",  "pop",        None, 0.60),   # 相机 + ④漫画冲击框
    ("split",      "flash",      None, 0.90),   # 新①再现（换人/换景/换景别组合）
    ("whip_right", "",           HALF, 0.76),   # 甩镜半身 + ④冲击框 + 残影
    ("kaleido",    "flash",      None, 0.92),   # 新③
    ("orbit_fast", "pop",        None, 0.64),   # 快环绕 + ④冲击框 + 残影
]
GRP_SEQ = [
    ("push_in",    "cascade"),
    ("orbit_fast", ""),
    ("pan",        ""),
    ("sway",       ""),
    ("pull_out",   ""),
]
# 相机过桥镜（加冲击框/残影，让"运镜"也不 PPT）
CAM_IMPACT = {"low_angle", "whip_right", "orbit_fast", "dutch", "spin", "pan", "track"}
CAM_ECHO   = {"whip_right", "orbit_fast", "spin", "dutch"}

TITLE_END   = 4.14
OUTRO_START = 48.14
SONG_END    = 52.92
MAX_SUB     = 1.86


def _load_lines() -> list:
    lt = VOICE / "script_v2_assets" / "pv" / "lyric_timing.json"
    if not lt.exists():
        sys.exit(f"[err] 歌词时间轴缺失: {lt}")
    return json.loads(lt.read_text(encoding="utf-8"))


def _subshots_v4(line: dict, seg_end: float, gidx: int) -> tuple:
    """把一句歌词拆成 ≤1.86s 子镜，V4 版：solo 加 echo/shatter，多人加 bg 切换。"""
    cast  = [NAME[c] for c in line["cast"]]
    n     = len(cast)
    disp0 = line["start"]
    lyric = {"singer": line["singer"], "text": line["text"],
             "chars": line["chars"], "disp0": disp0, "disp1": seg_end}
    dur   = seg_end - disp0
    nsub  = max(1, math.ceil(dur / MAX_SUB))
    step  = dur / nsub
    out   = []

    for k in range(nsub):
        a     = disp0 + k * step
        b     = seg_end if k == nsub - 1 else disp0 + (k + 1) * step
        grade = GRADES[gidx % len(GRADES)]
        trans = ["flash", "zoomblur", "swipe_l", "swipe_r"][gidx % 4]
        base_fx = ["spark", "bokeh_far"] if gidx % 3 == 0 else ["rain", "spark"]

        if n == 1:
            cam, enter, crop, hf = SOLO_SEQ[k % len(SOLO_SEQ)]
            # fx：新手法镜（split/kaleido/silhouette）自带奇观，不叠 shatter/echo（会抢占
            # place_doll 分支）；相机过桥镜叠漫画冲击框 + 快镜叠残影，让运镜也不 PPT。
            fx = list(base_fx)
            if cam in CAM_IMPACT and enter != "silhouette":
                fx.append("speed_impact")
            if cam in CAM_ECHO:
                fx.append("echo")
            bg = BG_SOLO[gidx % len(BG_SOLO)]
            out.append(Shot(a, b, cast[0], crop, hf, cam, enter, grade,
                            fx=fx, trans=trans, lyric=lyric,
                            singer=line["singer"], bg=bg))
        elif n == 2:
            cam, enter = GRP_SEQ[k % len(GRP_SEQ)]
            if k > 0:
                enter = ""
            out.append(Shot(a, b, "", None, 0.72, cam, enter, grade,
                            fx=base_fx + ["branch_sway", "speed_impact"], group=cast,
                            trans=trans, lyric=lyric,
                            singer=line["singer"], bg=BG["arch"]))
        else:
            # 4人合体 — 露台主景 + 冲击框重拍 + flash
            cam, enter = GRP_SEQ[k % len(GRP_SEQ)]
            if k > 0:
                enter = ""
            out.append(Shot(a, b, "", None, 0.66, cam, enter, grade,
                            fx=base_fx + ["echo", "flare", "speed_impact"], group=cast,
                            trans="flash", lyric=lyric,
                            singer=line["singer"], bg=BG["terrace"]))
        gidx += 1
    return out, gidx


def build_shots() -> list:
    lines = _load_lines()
    shots = [
        # 开场胶片走带：4人同框 · 花园景 · film_strip fx
        Shot(0.00, TITLE_END, "", None, 0.0, "static", "flash", CREAM,
             fx=["film_strip", "shafts", "spark"],
             group=["cy", "诺兰", "轩珩", "中里毅2"],
             title_mode="opening", text="明月天涯",
             trans="flash", bg=BG["garden"]),
    ]
    gidx = 0
    for i, line in enumerate(lines):
        seg_end = lines[i + 1]["start"] if i + 1 < len(lines) else OUTRO_START
        subs, gidx = _subshots_v4(line, seg_end, gidx)
        shots += subs

    # 结尾定版：露台全景 · 艺术字 + 印章
    shots.append(
        Shot(OUTRO_START, SONG_END, "", None, 0.0, "static", "flash",
             (248, 210, 160),
             fx=["branch_sway", "shafts", "spark", "bokeh_far"],
             title_mode="ending", text="明月天涯",
             trans="flash", bg=BG["overlook"]))
    return shots


if __name__ == "__main__":
    start = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
    end   = float(sys.argv[2]) if len(sys.argv) > 2 else SONG_END
    sys.exit(render(PATHS, build_shots(), start, end))
