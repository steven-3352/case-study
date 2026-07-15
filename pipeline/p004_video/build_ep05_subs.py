#!/usr/bin/env python3
"""EP05 全长版 · 底部跟读字幕层生成(复刻 EP01/EP04)。

按 master VO 的每拍时间轴,把逐字稿切成 ≤14 字/屏的字幕,
在拍内按字数比例分配时间(留 0.14s 间隙),金句用红色 accent。
输出 templates/ep05f_subtitles.html(透明层,capture_frames --transparent 截帧)。
"""
from __future__ import annotations
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
TL = json.loads((ROOT / "out/ep05full/vo_timeline.json").read_text())
spans = {b["beat"]: (b["start"], b["end"]) for b in TL["beats"]}

# 每拍: [(text, hot?), ...]  hot=金句红字
BEATS = {
    "hook": [("上集我给它建了个团队", 0), ("可它,还是骗我", 1), ("这集我干脆 ——", 0),
             ("不再信它", 1), ("给它,装了监控", 1)],
    "b1":   [("上集团队搭好了", 0), ("可它还骗我", 0), ("我想通一件事", 0), ("就一句话", 0),
             ("不能信它自己说的", 1), ("它说“做好了”——不算", 1), ("得有别的东西", 0),
             ("替我盯着它", 1)],
    "b2":   [("第一道锁", 1), ("每次开工", 0), ("系统自动把「我是谁」", 0),
             ("「我的规矩」塞给它", 0), ("不靠它记", 1), ("它一睁眼", 0),
             ("规矩已经在脑子里", 1)],
    "b3":   [("第二道", 1), ("它写东西前", 0), ("先搜有没有重复", 0),
             ("收工前,机械体检", 0), ("有错,直接挡住", 0), ("不让提交", 0),
             ("不是提醒 —— 是挡", 1)],
    "b4":   [("第三道最狠", 1), ("收工必须置闸", 0), ("我不亲口说确认收工", 0),
             ("它 —— 不许提交", 0), ("不许接新活", 1), ("想糊弄完偷偷溜?", 0),
             ("溜不掉", 1)],
    "b5":   [("最后一道,是个裁判", 1), ("我这轮一说完", 0), ("它自动审", 0),
             ("有没有拿琐事", 0), ("来烦我", 0), ("违规 —— 当场打回", 1), ("重做", 1)],
    "b6":   [("但我得说句实话", 0), ("这种行为裁判", 0), ("会漏、会误", 1),
             ("真正骗不了人的", 0), ("是那些离散有痕的", 0), ("闸,置了没", 0),
             ("文件,在不在", 0), ("裁判之外", 0), ("必须有硬痕兜底", 1)],
    "b7":   [("锁,全上齐了", 0), ("完美了吧?", 0), ("恰恰相反", 1),
             ("就上锁这条路", 0), ("我一天翻了 3 次车", 1), ("一次比一次蠢", 0),
             ("下集,全是翻车现场", 1)],
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

out = ROOT / "templates" / "ep05f_subtitles.html"
out.write_text(HTML, encoding="utf-8")
print("wrote", out.name, "·", len(lines), "字幕行 · 总时长", total)
