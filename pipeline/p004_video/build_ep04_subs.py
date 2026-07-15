#!/usr/bin/env python3
"""EP04 全长版 · 底部跟读字幕层生成(复刻 EP01/EP02)。

按 master VO 的每拍时间轴,把逐字稿切成 ≤14 字/屏的字幕,
在拍内按字数比例分配时间(留 0.14s 间隙),金句用红色 accent。
输出 templates/ep04f_subtitles.html(透明层,capture_frames --transparent 截帧)。
"""
from __future__ import annotations
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
TL = json.loads((ROOT / "out/ep04full/vo_timeline.json").read_text())
spans = {b["beat"]: (b["start"], b["end"]) for b in TL["beats"]}

# 每拍: [(text, hot?), ...]  hot=金句红字
BEATS = {
    "hook": [("管 AI 最大的坑", 0), ("别把它当一个人", 0), ("我把它当一整个团队", 1)],
    "b1":   [("上集说过", 0), ("落地第一步不是写代码", 0), ("我先撞上个更蠢的问题", 0),
             ("我的规矩", 0), ("散得到处都是", 1), ("我自己都找不着", 0), ("它更别提", 1)],
    "b2":   [("我一拍脑袋", 0), ("与其记哪个文件放啥", 0), ("不如立一条规矩", 0),
             ("我只对 3 个头儿说话", 1)],
    "b3":   [("参谋长", 1), ("管我是谁、往哪走", 0), ("前台", 1),
             ("指路 + 记录归档体检", 0), ("项目经理", 1), ("管在办项目、派活", 0),
             ("仨人,各带一队", 0)],
    "b4":   [("最爽的是", 0), ("我只跟这仨说话", 0), ("他们自动把活派下去", 1),
             ("研究员、史官、门卫", 0), ("我不用记谁管谁", 1)],
    "b5":   [("这不是我瞎画的", 0), ("它自己长出的关系图", 0), ("25 节点 · 72 条线", 0),
             ("枢纽是参谋长和前台", 0), ("没有一个孤立点", 1), ("乱文件夹", 0),
             ("真变成了一支队伍", 1)],
    "b6":   [("还有条边界我写死了", 0), ("每个项目平行独立", 0), ("不塞进大脑", 0),
             ("大脑只留个门牌", 1), ("记住这条", 0), ("它后面救了我一命", 1)],
    "b7":   [("团队,是搭好了", 0), ("可它还是嘴上答应", 0), ("背地敷衍", 1),
             ("组织能治乱", 0), ("治不了骗", 1), ("下集给它上 4 道锁", 1)],
}

GAP = 0.14
lines = []
for beat, items in BEATS.items():
    s, e = spans[beat]
    span = e - s
    weights = [max(2, len(t)) for t, _ in items]
    wsum = sum(weights)
    t = s
    for (txt, hot), w in zip(items, weights):
        seg = span * w / wsum
        start = t
        end = t + seg - GAP
        lines.append({"t": round(start, 2), "end": round(end, 2), "text": txt, "hot": hot})
        t += seg

total = TL["total"]
lines_js = ",\n      ".join(
    f'{{ t:{l["t"]}, end:{l["end"]}, text:"{l["text"]}", hot:{l["hot"]} }}' for l in lines
)

HTML = f"""<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="utf-8">
  <script src="../shared/gsap.min.js"></script>
  <script src="../shared/gsap_helpers.js"></script>
  <style>
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    html, body {{ width:1080px; height:1920px; background:transparent !important; overflow:hidden; }}
    .sub {{
      position:absolute; left:60px; right:60px; bottom:132px; text-align:center;
      font-family:"PingFang SC","Heiti SC",sans-serif; font-weight:900;
      font-size:58px; line-height:1.3; color:#fff; letter-spacing:1px; padding:0 20px;
      text-shadow:-4px -4px 0 #000,4px -4px 0 #000,-4px 4px 0 #000,4px 4px 0 #000,
        -4px 0 0 #000,4px 0 0 #000,0 -4px 0 #000,0 4px 0 #000,0 0 26px rgba(0,0,0,.95);
      opacity:0;
    }}
    .sub.hot {{ color:#ff5a5f; }}
  </style>
</head>
<body>
  <div class="sub" id="sub"></div>
  <script>
    const lines = [
      {lines_js}
    ];
    const sub = document.getElementById("sub");
    const tl = gsap.timeline();
    lines.forEach((line) => {{
      tl.call(() => {{ sub.textContent = line.text; sub.classList.toggle("hot", !!line.hot); }}, [], line.t);
      tl.fromTo(sub, {{ opacity:0, y:8 }}, {{ opacity:1, y:0, duration:0.16 }}, line.t);
      tl.to(sub, {{ opacity:0, duration:0.16 }}, line.end - 0.16);
    }});
    tl.to({{}}, {{ duration:0.05 }}, {total});
    registerTimeline(tl);
    window.__contentKey = function () {{
      const cs = getComputedStyle(sub);
      if (parseFloat(cs.opacity) <= 0.001) return "blank";
      return sub.textContent + "|" + cs.opacity + "|" + cs.transform;
    }};
  </script>
</body>
</html>
"""

out = ROOT / "templates" / "ep04f_subtitles.html"
out.write_text(HTML, encoding="utf-8")
print("wrote", out.name, "·", len(lines), "字幕行 · 总时长", total)
