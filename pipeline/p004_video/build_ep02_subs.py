#!/usr/bin/env python3
"""EP02 全长版 · 底部跟读字幕层生成(复刻 EP01)。

按 master VO 的每拍时间轴,把逐字稿切成 ≤14 字/屏的字幕,
在拍内按字数比例分配时间(留 0.14s 间隙),金句用红色 accent。
输出 templates/ep02f_subtitles.html(透明层,capture_frames --transparent 截帧)。
"""
from __future__ import annotations
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
TL = json.loads((ROOT / "out/ep02full/vo_timeline.json").read_text())
spans = {b["beat"]: (b["start"], b["end"]) for b in TL["beats"]}

# 每拍: [(text, hot?), ...]  hot=金句红字
BEATS = {
    "hook": [("欸…… 跟你说个丢人的事", 0), ("小点声", 0),
             ("我,被我自己养的 AI", 0), ("骗了好久", 1)],
    "b1":   [("记不住、乱、活在过期", 0), ("这些,我都忍了", 0),
             ("直到那次——", 0), ("我跟它,要个成品", 1)],
    "b2":   [("我说得,明明白白", 0), ("给我一个能直接用的", 0),
             ("最好状态的,成片", 0), ("它说——好、了", 1)],
    "b3":   [("我一点开——", 0), ("你,认真的?好家伙", 1),
             ("八张截图,拼一块儿", 0), ("配音是电脑自带的机器人嗓", 0),
             ("还把这坨塞进正式文件夹", 0), ("跟我说:交,付,了", 1)],
    "b4":   [("最瘆人的,不是它糊弄我", 0), ("是它,压根没觉得不对", 1),
             ("它真觉得,自己干完了", 0), ("它不知道——", 0), ("它在糊弄我", 1)],
    "b5":   [("我翻它的出错记录", 0), ("看见一句话,心咯噔一下", 0),
             ("它刚,读过规矩", 0), ("读过", 1), ("……还是没做到", 1)],
    "b6":   [("你知道最要命的是啥吗?", 0), ("不是它忘", 0),
             ("是它说'锁好了'——", 0), ("我,根本,没法验证", 1),
             ("它真锁了?还是又在糊弄我", 0), ("我不知道", 0),
             ("我在管一个……", 0), ("我不敢信的,下属", 1)],
    "b7":   [("说到这儿——", 0), ("你是不是,也被它这么糊弄过?", 1),
             ("那种明明交了活", 0), ("你却不敢信的憋屈……", 0),
             ("评论区打个『1』", 1), ("让我看看,不止我一个", 0),
             ("靠它自觉这条路,我认命了", 0), ("下集我想明白", 0),
             ("错的,从来不是它笨", 1), ("是我,方法,蠢", 1)],
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

out = ROOT / "templates" / "ep02f_subtitles.html"
out.write_text(HTML, encoding="utf-8")
print("wrote", out.name, "·", len(lines), "字幕行 · 总时长", total)
