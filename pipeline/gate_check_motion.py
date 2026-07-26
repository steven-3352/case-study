#!/usr/bin/env python3
"""冻结自检门 · R9「构图动 > 特效动」的机器判据（2s 硬线，fail-closed）.

治的病：帧内特效满天飞（描边光/雨/雾/粒子/闪电/字幕浮现）但主体（立绘）位置和
景别 2 秒不变 —— 观众判定「人/画面不动」= PPT。叠再多特效也救不回来。

判据（唯一 pass 依据，见 SKILL.md §10.2 故障5 / §2.5 / R9）：
  滑窗扫全片，任取一个 <window>s 窗口。若窗口内发生「切镜」（shot 边界）→ 直接过
  （切镜本身就是翻篇）。否则窗口落在同一连续镜内，比对主体（立绘 alpha bbox）：
    · 中心位移峰值  < 画面宽 <disp>%  且
    · 面积变化峰值  < <area>%
  两条同时成立 = 冻结 = fail。运镜 / 转场 / 切镜任一手段让主体在 <window>s 内
  跨过阈值都算过，不强制必须是硬切。

  用「窗口内相对首帧的峰值位移」而非「首末帧差」——orbit 一类正弦运镜 2s 内可能
  荡回起点，首末帧几乎一样但观众明明看到在动，峰值判据不会误伤。

  辅助诊断（不单独判 fail，仅定位病因）：全片硬切数、主体缺席（纯字卡）窗口数。

数据来源：渲染器随片吐的 *.motion.json 侧车（每帧记录立绘 bbox + 所属 shot）。
不在扁平化 mp4 上猜运动 —— mp4 无 alpha，特效在动会污染整帧差分，恰好放过
「特效在动、主体不动」这个要抓的正例。

用法：
    python3 pipeline/gate_check_motion.py path/to/pv.motion.json
    python3 pipeline/gate_check_motion.py track.json --window 2.0 --disp 4 --area 8
退出码 0=过 1=冻结（fail-closed）2=输入错误。
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

WINDOW_S = 2.0        # 硬线窗口：任意连续 2s 主体必须可感前进
DISP_FRAC = 0.04      # 中心位移阈值 = 画面宽 4%
AREA_FRAC = 0.08      # 面积变化阈值 = 8%
STEP_S = 0.25         # 滑窗步长


def _center_area(bbox):
    """bbox = [cx, cy, w, h] → (cx, cy, area)；None → None."""
    if not bbox:
        return None
    cx, cy, w, h = bbox
    return (cx, cy, max(1.0, w * h))


def _merge_ranges(times, gap):
    """把命中的时间点并成 [起, 止] 连续段，便于人读。"""
    if not times:
        return []
    times = sorted(times)
    out = [[times[0], times[0]]]
    for t in times[1:]:
        if t - out[-1][1] <= gap * 1.5:
            out[-1][1] = t
        else:
            out.append([t, t])
    return out


def check_track(path, window=WINDOW_S, disp_frac=DISP_FRAC,
                area_frac=AREA_FRAC, step=STEP_S):
    """校验一条 motion track。返回 (ok: bool, report: str)。"""
    path = Path(path)
    if not path.exists():
        return False, f"[motion] 找不到 track: {path}"
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        return False, f"[motion] track 读取失败: {e}"

    W = float(data.get("w") or 0)
    fps = float(data.get("fps") or 0)
    samples = data.get("track") or []
    if not W or not fps or len(samples) < 2:
        return True, f"[motion] track 太短或缺 w/fps（{len(samples)} 帧），跳过冻结自检"

    ts = [float(s["t"]) for s in samples]
    shots = [s.get("shot") for s in samples]
    cas = [_center_area(s.get("bbox")) for s in samples]
    span = ts[-1] - ts[0]
    if span < window:
        return True, (f"[motion] 片段仅 {span:.2f}s < {window}s 窗口，"
                      f"无法做冻结自检（正常，segment 太短）")

    disp_thr = disp_frac * W

    def sample_idx(tt):
        # 最近样本索引（帧近似）
        j = int(round((tt - ts[0]) * fps))
        return max(0, min(len(samples) - 1, j))

    frozen_starts = []      # fail：连续镜内主体冻结的窗口起点
    absent_starts = []      # 诊断：主体缺席（纯字卡）窗口
    worst = None            # (归一化位移峰值, 窗口起点) 用于报告最差点

    t = ts[0]
    while t + window <= ts[-1] + 1e-6:
        i0 = sample_idx(t)
        i1 = sample_idx(t + window)
        seg = range(i0, i1 + 1)

        # 窗口内切镜 = 翻篇，直接过
        if len({shots[k] for k in seg}) > 1:
            t += step
            continue

        a = cas[i0]
        # 主体缺席（字卡/转场）：不属立绘冻结范畴，诊断即可
        present = [cas[k] for k in seg if cas[k] is not None]
        if a is None or len(present) < 2:
            absent_starts.append(round(t, 2))
            t += step
            continue

        acx, acy, a_area = a
        peak_disp = 0.0
        peak_area = 0.0
        for k in seg:
            c = cas[k]
            if c is None:
                continue
            cx, cy, area = c
            peak_disp = max(peak_disp, math.hypot(cx - acx, cy - acy))
            peak_area = max(peak_area, abs(area - a_area) / a_area)

        moved = peak_disp >= disp_thr or peak_area >= area_frac
        if not moved:
            frozen_starts.append(round(t, 2))
            norm = peak_disp / disp_thr if disp_thr else 0.0
            if worst is None or norm < worst[0]:
                worst = (norm, round(t, 2), peak_disp / W, peak_area)
        t += step

    # 诊断：硬切数
    cuts = sum(1 for k in range(1, len(shots)) if shots[k] != shots[k - 1])
    cut_rate = cuts / span if span else 0.0

    lines = []
    ok = not frozen_starts
    tag = "OK" if ok else "FAIL"
    lines.append(f"[motion] {tag} · {span:.1f}s · {cuts} 切 "
                 f"({cut_rate:.2f}/s) · 阈值 位移≥{disp_frac*100:.0f}%宽 "
                 f"或 面积≥{area_frac*100:.0f}% / {window:.0f}s")

    if frozen_starts:
        ranges = _merge_ranges(frozen_starts, step)
        segs = ", ".join(f"{a:.2f}~{b + window:.2f}s" for a, b in ranges)
        lines.append(f"[motion] ✗ 冻结（连续镜内主体 {window:.0f}s 无可感推进）: {segs}")
        if worst:
            _, wt, wd, wa = worst
            lines.append(f"[motion]   最死窗口 @{wt:.2f}s：位移峰值 {wd*100:.1f}%宽 "
                         f"(需≥{disp_frac*100:.0f}%)，面积峰值 {wa*100:.1f}% "
                         f"(需≥{area_frac*100:.0f}%)")
        lines.append("[motion]   修法（任选其一让画面往前走）：加一刀切镜换景别 / "
                     "上运镜(推拉摇移) / 用转场把画面翻篇。详见 R9 · §2.5")
    if absent_starts:
        rr = _merge_ranges(absent_starts, step)
        segs = ", ".join(f"{a:.2f}~{b + window:.2f}s" for a, b in rr)
        lines.append(f"[motion] · 诊断：主体缺席窗口（纯字卡/转场，不判 fail）: {segs}")

    return ok, "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="纸片人 MV 冻结自检门（2s 硬线）")
    ap.add_argument("track", help="渲染器吐的 *.motion.json 侧车")
    ap.add_argument("--window", type=float, default=WINDOW_S, help="窗口秒数（默认 2.0）")
    ap.add_argument("--disp", type=float, default=DISP_FRAC * 100,
                    help="中心位移阈值（画面宽百分比，默认 4）")
    ap.add_argument("--area", type=float, default=AREA_FRAC * 100,
                    help="面积变化阈值（百分比，默认 8）")
    ap.add_argument("--step", type=float, default=STEP_S, help="滑窗步长秒（默认 0.25）")
    args = ap.parse_args()

    ok, report = check_track(args.track, window=args.window,
                             disp_frac=args.disp / 100, area_frac=args.area / 100,
                             step=args.step)
    print(report)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
