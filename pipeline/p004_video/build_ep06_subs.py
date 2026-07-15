#!/usr/bin/env python3
"""EP06 全长版 · 底部跟读字幕层生成(复刻 EP01/EP05)。

按 master VO 每拍时间轴,把逐字稿切成 ≤14 字/屏,拍内按字数比例分配时间(留 0.14s 间隙),
金句(航母送快递 / 被逼出来的 / 救了我一命)用红色 accent。
输出 templates/ep06f_subtitles.html(透明层)。
"""
from __future__ import annotations
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
TL = json.loads((ROOT / "out/ep06full/vo_timeline.json").read_text())
spans = {b["beat"]: (b["start"], b["end"]) for b in TL["beats"]}

# 每拍: [(text, hot?), ...]  hot=金句红字
BEATS = {
    "hook":     [("我做 AI 助理第一天", 0), ("翻了 3 次车", 1),
                 ("今天全给你看", 0), ("包括最蠢那次", 1)],
    "stance":   [("别人发'炸裂'", 0), ("我发翻车", 1), ("不是凡尔赛", 0),
                 ("真有用的部分", 0), ("恰恰是它翻过的车", 1), ("3 个,全给你看", 0)],
    "crash1":   [("第一车:刚上的收工锁", 0), ("第一次实战", 0),
                 ("就坑了我自己", 1), ("它置了闸", 0), ("让我去看那份报告", 0),
                 ("可那闸把我挡在门外", 0), ("我只能……盲签", 1)],
    "fix1":     [("修法就一句", 0), ("置闸,必须把摘要", 0),
                 ("贴脸上", 1), ("别让我去别处找", 0)],
    "crash2":   [("第二车:它问我", 0), ("'要不要记一句日志?'", 0),
                 ("屁大的事", 0), ("也来烦我一句", 1), ("这正好踩了我立的规矩", 0),
                 ("'别拿琐事问我'", 0)],
    "fix2":     [("我一点破,当场立规", 0), ("还给它加了个", 0),
                 ("Stop 裁判做后盾", 0), ("——没错", 0),
                 ("EP05 那个裁判", 0), ("就是这么被逼出来的", 1)],
    "crash3":   [("第三车,最蠢", 1), ("为了把大脑可视化", 0),
                 ("我部署了整套笔记系统", 0), ("容器、镜像、导入", 0),
                 ("全跑通了,图我都看上了", 0), ("然后我一拍脑袋", 0),
                 ("航母……送快递", 1), ("整条,清退,全删", 1)],
    "boundary": [("还好——它在平行仓库里", 0), ("就是 EP04", 0),
                 ("我写死的那条边界", 0), ("删地盘,一了百了", 0),
                 ("大脑只摘一条门牌", 0), ("那条边界", 0), ("真救了我一命", 1)],
    "land":     [("翻车不可怕", 0), ("可怕的是不留痕", 1),
                 ("每翻一次", 0), ("我立一条规矩", 0), ("刻一块墓碑", 0),
                 ("系统就硬一分", 1), ("到底成没成、值不值", 0), ("你也搞?", 0),
                 ("下集:复刻 5 步", 0), ("坑,我全给你标好", 1)],
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

out = ROOT / "templates" / "ep06f_subtitles.html"
out.write_text(HTML, encoding="utf-8")
print("wrote", out.name, "·", len(lines), "字幕行 · 总时长", total)
