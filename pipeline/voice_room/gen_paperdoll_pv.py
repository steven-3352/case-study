#!/usr/bin/env python3
"""语音厅《明月天涯》· 4 主角纸片人卡点 MV —— 薄片脚本（引擎见 paperdoll_engine.py）.

本文件只声明该片一次性的创意产物：素材路径（PVPaths）+ 分镜（build_shots）。
所有渲染原语/FX/立体三件套/运镜/艺术字/多人合成/背景动效/歌词卡拉OK/冻结门都在
公共引擎里，import 调 render()。分镜是本片专属，禁 clone 到下一条（template-clone 铁律）。

**分镜数据来源（非臆想）**：`pv/lyric_timing.json` —— 由 whisper 词级时间戳把 docx
《明月天涯》歌词 14 句 127 字 1:1 对齐到导唱真实演唱时点，逐字带时点。build_shots()
读它，按 docx 标注的**演唱者出场顺序**（轩珩→中里毅→合→诺兰→Cy→…）排布：
每句配对应演唱者立绘（solo / 2 人 / 4 人合体）+ 底部逐字点亮国风歌词美术字（真卡点）。

全曲 明月天涯 导唱(1).WAV · 53.08s · 129BPM。开场艺术字标题(0–4.14)→14 句演唱段
→结尾定版艺术字(48.14–52.92)。R1 立绘像素零改动。背景：现代立体感 plate + 逐帧真下雨
+ 花枝摆动（背景非静态）。全暖色（palette 铁律 · 禁蓝紫）。

调用：python3 gen_paperdoll_pv.py [start] [end]   默认 0 52.92
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

ROOT = Path(__file__).resolve().parents[2]
VOICE = ROOT / "publish" / "语音厅"
PATHS = PVPaths(
    assets_dir=VOICE / "script_v2_assets",
    wav=VOICE / "明月天涯 导唱(1).WAV",
    out_dir=VOICE / "script_v2_assets" / "pv",
    bg_plate="bg_mingyue_modern.png",
    slug="mingyue_full",
)

# 演唱者代号 → 立绘名（= {name}_cutout.png）
NAME = {"CY": "cy", "NL": "诺兰", "XH": "轩珩", "ZL": "中里毅2"}

# 段落调色（全暖 · 情绪弧轮替）
GOLD_SOFT = (240, 200, 160)
GOLD_BRIGHT = (250, 210, 165)
GRADES = [AMBER, ROSE, GOLD_SOFT, PEACH, ORANGE]

# 近景裁切（保头顶，切上半身/大半身）
UP = (0.10, 0.00, 0.90, 0.34)      # 上半身
HALF = (0.05, 0.00, 0.95, 0.58)    # 大半身

# solo 运镜序列：(cam, enter, crop, hfrac) —— 覆盖全部复杂运镜类型（≥9 种，禁连续3镜同cam）
SOLO_SEQ = [
    ("push_in",    "slam_up", None, 0.96),  # 推入·全身登场
    ("low_angle",  "",        None, 0.94),  # 仰拍·高耸压迫感
    ("orbit_fast", "",        None, 0.92),  # 快环绕·大弧戏剧
    ("dutch",      "",        UP,   0.84),  # 荷兰角·近景偏斜
    ("pan",        "",        UP,   0.86),  # 摇镜·视差横移
    ("spin",       "pop",     None, 0.90),  # 旋转·爆发式定位
    ("whip_right", "",        HALF, 0.88),  # 甩镜·残影横扫
    ("track",      "",        HALF, 0.86),  # 跟拍·弧线随焦
    ("bird_eye",   "",        None, 0.80),  # 俯视·轻度俯压
    ("pull_out",   "",        HALF, 0.82),  # 拉远·收尾透气
]
# 合体运镜序列：(cam, enter) —— 多人组镜同样多样
GRP_SEQ = [
    ("push_in",    "cascade"),  # 推进·错落入场
    ("orbit_fast", ""),         # 快环绕
    ("pan",        ""),         # 摇镜
    ("sway",       ""),         # 摆动·呼吸感
    ("pull_out",   ""),         # 拉远
]

TITLE_END = 4.14      # 开场标题结束 = 第 1 句起唱
OUTRO_START = 48.14   # 结尾定版起点（末句唱毕 + 尾韵）
SONG_END = 52.92

MAX_SUB = 1.86        # 单子镜上限（<2s → 任意 2s 窗口必跨切点，过 R9 冻结门）


def _load_lines():
    lt = PATHS.out_dir / "lyric_timing.json"
    if not lt.exists():
        sys.exit(f"[err] 歌词时间轴缺失: {lt}\n      先跑 whisper 对齐生成 lyric_timing.json")
    return json.loads(lt.read_text(encoding="utf-8"))


def _subshots(line, seg_end, gidx):
    """把一句歌词的可视窗口 [首字, 下句起] 拆成 ≤1.86s 的子镜，配演唱者立绘 + 歌词层。"""
    cast = [NAME[c] for c in line["cast"]]
    n = len(cast)
    disp0 = line["start"]
    lyric = {"singer": line["singer"], "text": line["text"],
             "chars": line["chars"], "disp0": disp0, "disp1": seg_end}
    dur = seg_end - disp0
    nsub = max(1, math.ceil(dur / MAX_SUB))
    step = dur / nsub
    out = []
    for k in range(nsub):
        a = disp0 + k * step
        b = seg_end if k == nsub - 1 else disp0 + (k + 1) * step
        grade = GRADES[gidx % len(GRADES)]
        fx = (["branch_sway", "spark", "shafts", "rays"] if gidx % 2 == 0
              else ["rain", "spark", "petal"])
        trans = ["flash", "zoomblur", "swipe_l", "swipe_r"][gidx % 4]
        if n == 1:                                   # 个人 solo 展示
            cam, enter, crop, hf = SOLO_SEQ[k % len(SOLO_SEQ)]
            if k > 0:
                enter = ""                           # 只首子镜入场，其余靠运镜+切点
            out.append(Shot(a, b, cast[0], crop, hf, cam, enter, grade,
                            fx=fx, trans=trans, lyric=lyric, singer=line["singer"]))
        else:                                        # 2 人 / 4 人合体
            cam, enter = GRP_SEQ[k % len(GRP_SEQ)]
            if k > 0:
                enter = ""
            hf = 0.90 if n == 2 else 0.86
            out.append(Shot(a, b, "", None, hf, cam, enter, grade,
                            fx=fx, group=cast, trans=trans,
                            lyric=lyric, singer=line["singer"]))
        gidx += 1
    return out, gidx


def build_shots():
    lines = _load_lines()
    shots = [
        # 开场艺术字标题（0–4.14 · 无立绘 · 花枝摆动 · 逐字弹显）
        Shot(0.00, TITLE_END, "", None, 0.0, "static", "flash", CREAM,
             fx=["shafts", "spark", "streak_radial", "branch_sway"],
             title_mode="opening", text="明月天涯", trans="flash"),
    ]
    gidx = 0
    for i, line in enumerate(lines):
        seg_end = lines[i + 1]["start"] if i + 1 < len(lines) else OUTRO_START
        subs, gidx = _subshots(line, seg_end, gidx)
        shots += subs
    # 结尾艺术字定版（无立绘 · 花枝摆动 + 双印）
    shots.append(
        Shot(OUTRO_START, SONG_END, "", None, 0.0, "static", "flash", GOLD_BRIGHT,
             fx=["branch_sway", "shafts", "spark", "bokeh_far"],
             title_mode="ending", text="明月天涯", trans="flash"))
    return shots


if __name__ == "__main__":
    start = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
    end = float(sys.argv[2]) if len(sys.argv) > 2 else SONG_END
    sys.exit(render(PATHS, build_shots(), start, end))
