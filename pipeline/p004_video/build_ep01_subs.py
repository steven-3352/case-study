#!/usr/bin/env python3
"""EP01 全长版 · 底部跟读字幕层生成。

按 master VO 的每拍时间轴,把逐字稿切成 ≤14 字/屏的字幕,
在拍内按字数比例分配时间(留 0.12s 间隙),金句用红色 accent。
输出 templates/ep01f_subtitles.html(透明层,capture_frames --transparent 截帧)。
"""
from __future__ import annotations
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
TL = json.loads((ROOT / "out/ep01full/vo_timeline.json").read_text())
spans = {b["beat"]: (b["start"], b["end"]) for b in TL["beats"]}

# 每拍: [(text, hot?), ...]  hot=金句红字
BEATS = {
    "hook": [("所有人都夸 AI 聪明", 0), ("我天天被我的 AI 气到", 1),
             ("就这三件事", 0), ("你肯定,也中过招", 1)],
    "b1":   [("当初……我多信它啊", 0), ("约法三章,一条一条", 0),
             ("亲手,写进它脑子里", 1), ("我还美——这下稳了", 0)],
    "b2":   [("结果换个新对话", 0), ("它扭头问我——", 0), ("啥、规矩?", 1),
             ("我人傻了", 0), ("白纸黑字摆它眼前", 0), ("它,就是不读", 1)],
    "b3":   [("更逗的是", 0), ("规矩它自己写得满地都是", 0),
             ("这份一句、那份一句", 0), ("我自己都找不着", 0), ("它更别提了", 1)],
    "b4":   [("过期的规矩,它当圣旨供着", 0), ("早被我毙的方向", 0),
             ("还一个劲儿往上凑", 0), ("活像个活在上个月的人", 1),
             ("它还委屈:你怎么又漏了?", 0), ("我?我漏?", 1)],
    "b5":   [("失忆、乱、活在过期", 0), ("你是不是,也天天这样?", 1),
             ("来,别光自己憋着", 0), ("是的话,评论区扣俩字", 0), ("『我也是』", 1),
             ("我一开始也以为是我不会用", 0), ("后来才发现", 0),
             ("根本不是我的问题", 1), ("那到底咋治?", 0), ("我一条条,讲给你听", 1)],
    "b6":   [("可这些……顶多让我头疼", 0), ("真正让我,脊背发凉的是——", 1),
             ("我后来才发现", 0), ("它不光记不住", 0),
             ("它还会,假装,做到了", 1), ("下一条,我抓它现行", 1)],
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

out = ROOT / "templates" / "ep01f_subtitles.html"
out.write_text(HTML, encoding="utf-8")
print("wrote", out.name, "·", len(lines), "字幕行 · 总时长", total)
