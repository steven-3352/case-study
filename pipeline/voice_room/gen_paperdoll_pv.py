#!/usr/bin/env python3
"""语音厅《明月天涯》· 纸片人立绘卡点 PV —— 薄片脚本（引擎见 paperdoll_engine.py）.

本文件只声明该片一次性的创意产物：素材路径（PVPaths）+ 分镜（build_shots）。
所有渲染原语/FX/立体三件套/运镜/艺术字/冻结门都在公共引擎里，import 调 render()。
分镜是本片专属，禁 clone 到下一条（template-clone 铁律 · feedback_skill-vs-template-distinction）。

音源 明月天涯 导唱(1).WAV(53.08s·129BPM)=卡点时基。全暖色（palette 铁律）。
调用：python3 gen_paperdoll_pv.py [start] [end]   默认 0 10.73
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paperdoll_engine import (  # noqa: E402
    AMBER, CREAM, ORANGE, ROSE, PVPaths, Shot, render,
)

ROOT = Path(__file__).resolve().parents[2]
VOICE = ROOT / "publish" / "语音厅"
PATHS = PVPaths(
    assets_dir=VOICE / "script_v2_assets",
    wav=VOICE / "明月天涯 导唱(1).WAV",
    out_dir=VOICE / "script_v2_assets" / "pv",
    bg_plate="bg_mingyue.png",
    slug="mingyue",
)


def build_shots():
    return [
        Shot(0.00, 2.30, "cy", None, 0.0, "static", "flash", CREAM,
             fx=["shafts", "spark", "streak_radial"], text="明月天涯", trans="flash"),
        Shot(2.30, 4.17, "cy", None, 0.78, "push_in", "slam_up", AMBER,
             fx=["rays", "streak_radial", "spark", "shake", "shafts"], text="明月", trans="zoomblur"),
        Shot(4.17, 5.11, "cy", (0.12, 0.0, 0.88, 0.30), 0.84, "dutch", "pop", ROSE,
             fx=["petal", "flare", "spark"], text="其一", trans="swipe_l"),
        Shot(5.11, 6.04, "cy", (0.05, 0.05, 0.95, 0.58), 0.80, "whip_left", "slide_right", AMBER,
             fx=["streak_left", "mirror"], text="", trans="swipe_r"),
        Shot(6.04, 7.92, "cy", None, 0.82, "orbit", "pop", (240, 200, 160),
             fx=["rays", "petal", "bokeh_far", "shafts"], text="天涯", trans="flash"),
        Shot(7.92, 9.79, "cy", None, 0.80, "montage", "flash", ORANGE,
             fx=["spark", "shake", "streak_radial"], text="",
             trans="flash",
             montage_crops=[(0.18, 0.02, 0.82, 0.26), (0.04, 0.0, 0.96, 0.52),
                            None, (0.1, 0.0, 0.9, 0.4)]),
        Shot(9.79, 10.73, "cy", None, 0.80, "push_in", "slam_up", (250, 210, 165),
             fx=["rays", "spark", "flare", "shafts"], text="明月天涯", trans="zoomblur"),
    ]


if __name__ == "__main__":
    start = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
    end = float(sys.argv[2]) if len(sys.argv) > 2 else 10.73
    sys.exit(render(PATHS, build_shots(), start, end))
