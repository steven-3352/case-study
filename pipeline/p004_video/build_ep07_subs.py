#!/usr/bin/env python3
"""EP07 收官全长版 · 底部跟读字幕层生成(复刻 EP01)。

按 master VO 每拍时间轴,把逐字稿切成 ≤14 字/屏,拍内按字数比例分配时间,
金句用红色 accent。输出 templates/ep07f_subtitles.html(透明层)。
"""
from __future__ import annotations
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
TL = json.loads((ROOT / "out/ep07full/vo_timeline.json").read_text())
spans = {b["beat"]: (b["start"], b["end"]) for b in TL["beats"]}

# 每拍: [(text, hot?), ...]  hot=金句红字
BEATS = {
    "hook": [("想自己造一个?", 0), ("5 步,坑我都替你标好了", 1)],
    "b1":   [("从被它骗", 0), ("到想通「机械大于自觉」", 0),
             ("搭团队、上锁", 0), ("翻了一路的车——", 0),
             ("到现在,像个能用的助理了", 1), ("你想搞一个,我把路铺平", 0)],
    "b2":   [("第一步:一个常驻核心文件", 0), ("写清你是谁,开工自动注入", 0),
             ("第二步:铁律加固化流程", 0), ("挂个体检脚本,提交前自动跑", 0)],
    "b3":   [("第三步:关键纪律用 hooks", 0), ("注入、阻断、裁判", 0),
             ("而且逃生门先建先测", 1), ("第四步:结构人格化成组织", 0),
             ("第五步:只报告不擅改", 0), ("再硬的约束,也留个自救口子", 1)],
    "b4":   [("效果?", 0), ("体检全绿、结构零孤立", 0),
             ("一天十几次提交零脏改", 0), ("就……这些", 0),
             ("是「绿」——不是「炸裂」", 1)],
    "b5":   [("丑话说前面:这只是雏形", 0), ("实战时长以「天」计", 0),
             ("行为约束没有 100%", 0), ("裁判会漏", 0),
             ("hooks 吃平台,换环境重搭", 0), ("而且单人、单机、纯文字", 0),
             ("多 agent、语音都还没做", 0), ("是路线,不是现状", 1)],
    "b6":   [("我做这一整个连载", 0), ("就守一条:", 0),
             ("写成真实记录,是内容", 1), ("写成效果炸裂,就是元叙事", 1)],
    "b7":   [("我不求它多牛", 0), ("也不求这条爆", 0),
             ("我求的是——真往前走一步", 0), ("和真能一起造的人", 1),
             ("你也在折腾这个?", 0), ("评论区,见", 1)],
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

out = ROOT / "templates" / "ep07f_subtitles.html"
out.write_text(HTML, encoding="utf-8")
print("wrote", out.name, "·", len(lines), "字幕行 · 总时长", total)
