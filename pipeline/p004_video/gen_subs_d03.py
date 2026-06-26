#!/usr/bin/env python3
"""W27D03 字幕层 · 从 seg_timing 生成底部跟读字幕 _subtitles.html + sub_va.srt.

底部跟读字幕（逐句跟 VO），与各镜大字钩子(subtitle_big，已烧在 scene 模板)分层互斥。
每段在其 VO 起止区间内按句切分、均匀铺时；末句留 0.15s 收尾。
"""
from __future__ import annotations
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
TIMING = ROOT / "out" / "audio" / "seg_timing_d03.json"
SUB_HTML = ROOT / "templates" / "_subtitles.html"
PROJECT = ROOT.parent.parent
SRT = PROJECT / "publish" / "2026-W27" / "D03-海外获客成长" / "design" / "sub_va.srt"

# 跟读字幕分句（每行≤约14字便于阅读，与口播句界对齐）。
# 用列表显式控制断句，避免一行过长遮主体。
LINES_BY_SEG = {
    "s1": ["一天搭完，第5天我傻眼了。"],
    "s2": ["一个人，做老外的英文市场。", "我用一天，从拉客、收邮箱、", "到自动跟进，全搭到上线。"],
    "s3": ["然后我就不管了。", "有人填邮箱，它立刻发欢迎信，", "往后每隔几天自己发一封养着。",
           "我人不在，它照样一封封地发，", "跟进这环，我盯的时间几乎是零。"],
    "s4": ["它一直在替我攒老外客户。", "可第5天我一看——曝光是涨了，", "留下来的却寥寥无几。"],
    "s5": ["扒下来根因是内容太机器，", "AI 一键出的图谁都刷过。", "改成 AI 只出背景、文字我自己排，",
           "才像活人发的，留资才开始动。", "整套基本没花钱，盯守也几乎是零。"],
    "s6": ["系统能跑，内容得先像人。", "你有没有「留了线索却总忘跟进」的活？", "评论说说，下条我把这套自动跟进拆给你。"],
}


def srt_ts(t: float) -> str:
    h = int(t // 3600); m = int((t % 3600) // 60); s = int(t % 60); ms = int(round((t - int(t)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main() -> None:
    data = json.loads(TIMING.read_text(encoding="utf-8"))
    total = data["total"]
    cues = []  # (start, end, text)
    for seg in data["segments"]:
        sid = seg["id"]
        seg_start = seg["start"]
        vo = seg["vo_dur"]
        lines = LINES_BY_SEG[sid]
        # 按句字数比例分配 VO 时长，留 0.15s 收尾静默
        weights = [len(re.sub(r"\s", "", ln)) for ln in lines]
        wsum = sum(weights)
        span = vo
        t = seg_start
        for ln, w in zip(lines, weights):
            d = span * (w / wsum)
            start = t
            end = t + max(0.5, d - 0.12)
            cues.append((round(start, 2), round(end, 2), ln))
            t += d
    # JS lines
    js_lines = ",\n".join(
        f'      {{ t: {s}, end: {e}, text: "{txt}" }}' for s, e, txt in cues
    )
    html = f'''<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="utf-8">
  <title>Subtitle Overlay · W27D03</title>
  <link rel="stylesheet" href="../shared/style.css">
  <script src="../shared/gsap.min.js"></script>
  <script src="../shared/gsap_helpers.js"></script>
  <style>
    html, body, .canvas {{ background: transparent !important; }}
    .sub-line {{
      position: absolute;
      left: 60px; right: 60px;
      bottom: 210px;                 /* 底部跟读，避开各镜中上大字钩子(subtitle_big)互斥不打架 */
      text-align: center;
      font-family: var(--sans);
      font-weight: 900;
      font-size: 50px;
      line-height: 1.3;
      color: #fff;
      letter-spacing: 1px;
      text-shadow:
        -4px -4px 0 #000, 4px -4px 0 #000,
        -4px 4px 0 #000, 4px 4px 0 #000,
        -4px 0 0 #000, 4px 0 0 #000,
        0 -4px 0 #000, 0 4px 0 #000,
        0 0 24px rgba(0,0,0,.95);
      opacity: 0;
      padding: 0 20px;
    }}
  </style>
</head>
<body>
  <div class="canvas">
    <div class="sub-line" id="sub"></div>
  </div>
  <script>
    // W27D03 底部跟读字幕 · 与 sub_va.srt 对齐 · 总时长 {total}s
    const lines = [
{js_lines}
    ];
    const sub = document.getElementById("sub");
    const tl = gsap.timeline();
    lines.forEach((line) => {{
      tl.call(() => {{ sub.textContent = line.text; }}, [], line.t);
      tl.fromTo(sub, {{ opacity: 0, y: 8 }}, {{ opacity: 1, y: 0, duration: 0.16 }}, line.t);
      tl.to(sub, {{ opacity: 0, duration: 0.16 }}, line.end - 0.16);
    }});
    tl.to({{}}, {{ duration: 0.05 }}, {total});
    registerTimeline(tl);
  </script>
</body>
</html>
'''
    SUB_HTML.write_text(html, encoding="utf-8")

    # SRT
    srt_parts = []
    for i, (s, e, txt) in enumerate(cues, 1):
        srt_parts.append(f"{i}\n{srt_ts(s)} --> {srt_ts(e)}\n{txt}\n")
    SRT.parent.mkdir(parents=True, exist_ok=True)
    SRT.write_text("\n".join(srt_parts), encoding="utf-8")
    print(f"✓ 字幕层: {SUB_HTML}  ({len(cues)} 句)")
    print(f"✓ SRT:   {SRT}")


if __name__ == "__main__":
    main()
