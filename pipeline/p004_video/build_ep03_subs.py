#!/usr/bin/env python3
"""EP03 全长版 · 底部跟读字幕层生成(复刻 EP01)。

按 master VO 的每拍时间轴,把逐字稿切成 ≤14 字/屏的字幕,
在拍内按字数比例分配时间(留 0.14s 间隙),金句用红色 accent。
输出 templates/ep03f_subtitles.html(透明层,capture_frames --transparent 截帧)。
"""
from __future__ import annotations
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
TL = json.loads((ROOT / "out/ep03full/vo_timeline.json").read_text())
spans = {b["beat"]: (b["start"], b["end"]) for b in TL["beats"]}

# 每拍: [(text, hot?), ...]  hot=金句红字
BEATS = {
    "hook": [("上集,我被它骗惨了", 0), ("这集我不想让它更聪明", 0),
             ("我把它当", 0), ("记不住的员工,来管", 1)],
    "b1":   [("被它骗完", 0), ("我干的第一件蠢事", 0), ("——再教它一遍", 0),
             ("把规矩写进记忆", 0), ("写得更狠", 0), ("存了一遍又一遍", 1)],
    "b2":   [("结果呢?", 0), ("它刚,读过", 0), ("读过", 0),
             ("……还是没做到", 1), ("不是没记", 0), ("是记了,也不算数", 1)],
    "b3":   [("我盯着这句话", 0), ("突然就通了", 0), ("靠它自觉记,它会漏", 0),
             ("靠我自觉盯", 0), ("我会累、会忘", 0), ("这两条", 0),
             ("全是人力的路", 0), ("人力的路,全是死路", 1)],
    "b4":   [("唯一活的一条路", 0), ("——机械", 1), ("该记得做的事", 0),
             ("别留给它记不记得", 0), ("做成它", 0), ("绕、不、过、去", 1)],
    "b5":   [("红绿灯", 0), ("不靠司机自觉", 0), ("机器不戴护具", 0),
             ("就不给你启动", 0), ("管记不住的助理", 0), ("一模一样", 1)],
    "b6":   [("道理是通了", 0), ("可机械咋落地?", 0), ("我一动手才发现", 0),
             ("第一步不是写代码", 1), ("是把它", 0), ("从一坨乱文件", 0),
             ("变成我能指挥的团队", 0), ("下集", 0), ("我给我的AI", 0),
             ("拆了个公司", 1)],
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

out = ROOT / "templates" / "ep03f_subtitles.html"
out.write_text(HTML, encoding="utf-8")
print("wrote", out.name, "·", len(lines), "字幕行 · 总时长", total)
