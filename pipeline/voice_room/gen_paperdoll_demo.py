#!/usr/bin/env python3
"""语音厅 · V4 新手法测试小样（四手法 × 四人物 · 一条 demo reel 供目视）。

用途：验证 V3 完全没有的四个新手法，每个落在不同人物上，让用户一次看到更多东西。
不是正片分镜（正片见 gen_paperdoll_pv_v4.py）；本文件是纯技术小样，可随时改。

四手法 × 四人物（每段 ~4.5s · 每 2s 内必有可见变化 + 段间硬切转场）：
  0.0–4.5   轩珩    split          分屏切割（面部/半身/全身三格错位滑入）
  4.5–9.0   中里毅2  kaleido        节奏分身（5 副本沿弧线逐拍 pop）
  9.0–13.5  cy      speed_impact   漫画冲击框（推入 + 重拍放射线/冲击环）
  13.5–18.0 诺兰    silhouette     剪影点亮登场（暗剪影被金光扫亮）

调用：python3 gen_paperdoll_demo.py [start] [end]   默认 0 18
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paperdoll_engine import (  # noqa: E402
    AMBER, ORANGE, PEACH, ROSE, PVPaths, Shot, render,
)

ROOT  = Path(__file__).resolve().parents[2]
VOICE = ROOT / "publish" / "语音厅"
V4DIR = VOICE / "pv_v4"

PATHS = PVPaths(
    assets_dir=VOICE / "script_v2_assets",
    wav=VOICE / "明月天涯 导唱(1).WAV",
    out_dir=V4DIR,
    bg_plate="bg_v4.png",
    slug="mingyue_demo",
)

BG = {
    "garden":   str(V4DIR / "bg_v4d.png"),
    "terrace":  str(V4DIR / "bg_v4.png"),
    "overlook": str(V4DIR / "bg_v4b.png"),
    "arch":     str(V4DIR / "bg_v4c.png"),
}

END = 18.0


def build_shots() -> list:
    return [
        # ① 分屏切割 · 轩珩 · 花园景（每格不同景别 → 2s 内画面结构持续变化）
        Shot(0.0, 4.5, "轩珩", None, 0.90, "split", "flash", AMBER,
             fx=["spark", "bokeh_far"], trans="flash",
             singer="轩珩", name="轩珩", epithet="分屏", bg=BG["garden"]),
        # ② 节奏分身 · 中里毅2 · 石拱门（5 副本逐拍 pop → bbox 持续扩张）
        Shot(4.5, 9.0, "中里毅2", None, 0.92, "kaleido", "flash", ROSE,
             fx=["spark", "bokeh_far"],
             trans="zoomblur", singer="中里毅2", name="中里毅2",
             epithet="分身", bg=BG["arch"]),
        # ③ 漫画冲击框 · cy · 主露台（推入 + 重拍放射线/冲击环）
        Shot(9.0, 13.5, "cy", None, 0.64, "push_in", "pop", PEACH,
             fx=["speed_impact", "spark"], trans="swipe_l",
             singer="cy", name="cy", epithet="冲击", bg=BG["terrace"]),
        # ④ 剪影点亮登场 · 诺兰 · 露台全景（暗剪影被金光从左扫亮）
        Shot(13.5, END, "诺兰", None, 0.66, "low_angle", "silhouette", ORANGE,
             fx=["spark", "bokeh_far"], trans="flash",
             singer="诺兰", name="诺兰", epithet="点亮", bg=BG["overlook"]),
    ]


if __name__ == "__main__":
    start = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
    end   = float(sys.argv[2]) if len(sys.argv) > 2 else END
    sys.exit(render(PATHS, build_shots(), start, end))
