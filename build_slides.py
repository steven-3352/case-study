#!/usr/bin/env python3
"""Case-study slide renderer — 1080x1920 (9:16) PNG slides via headless Chrome.
Half-anonymized automation case study (Chinese). Run: python3 build_slides.py
"""
import subprocess, tempfile, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "slides"; OUT.mkdir(exist_ok=True)
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
HANDLE = "@ 自动化笔记"   # ← 改成你的小红书 ID(C 端账号,正文/页脚都不放公司名)

CSS = """
  *{margin:0;padding:0;box-sizing:border-box;}
  html,body{width:1080px;height:1920px;}
  body{font-family:"Hiragino Sans GB","PingFang SC",sans-serif;
    background:
      radial-gradient(130% 70% at 50% -10%, rgba(224,176,94,.16), rgba(11,13,16,0) 55%),
      #0b0d10;
    color:#ede6da;-webkit-font-smoothing:antialiased;overflow:hidden;}
  .slide{position:relative;width:1080px;height:1920px;padding:120px 90px 110px;display:flex;flex-direction:column;}
  .eyebrow{display:flex;align-items:center;gap:18px;color:#e0b15e;font-size:30px;letter-spacing:.12em;font-weight:600;margin-bottom:48px;}
  .eyebrow .idx{font-size:26px;color:#7c8088;letter-spacing:.05em;}
  .eyebrow .dot{width:10px;height:10px;border-radius:50%;background:#e0b15e;}
  h1{font-size:104px;line-height:1.14;font-weight:800;color:#fff;letter-spacing:-.01em;}
  h1 .g{color:#e8be72;}
  h2{font-size:72px;line-height:1.22;font-weight:800;color:#fff;margin-bottom:42px;letter-spacing:-.01em;}
  .sub{font-size:38px;line-height:1.6;color:#aeb3bb;font-weight:400;}
  .grow{flex:1;}
  .chips{display:flex;flex-wrap:wrap;gap:16px;margin-top:8px;}
  .chip{font-size:31px;padding:14px 26px;border:1.5px solid rgba(224,176,94,.45);border-radius:999px;color:#e8be72;}
  .foot{display:flex;align-items:center;justify-content:space-between;border-top:1px solid rgba(237,230,218,.12);padding-top:34px;margin-top:40px;}
  .foot .who{font-size:34px;color:#ede6da;font-weight:700;letter-spacing:.02em;}
  .foot .tag{font-size:28px;color:#7c8088;}
  /* flow boxes */
  .flow{display:flex;flex-direction:column;gap:0;}
  .node{background:linear-gradient(180deg,#171a20,#11141a);border:1.5px solid rgba(224,176,94,.30);
    border-radius:22px;padding:30px 34px;display:flex;align-items:center;gap:26px;}
  .node .ic{font-size:46px;width:64px;text-align:center;}
  .node .tt{font-size:40px;font-weight:700;color:#fff;}
  .node .dd{font-size:29px;color:#9aa0a8;margin-top:4px;}
  .arrow{height:46px;display:flex;align-items:center;justify-content:center;color:#e0b15e;font-size:40px;}
  .loop{margin-top:22px;text-align:center;color:#8a909a;font-size:30px;}
  /* steps */
  .steps{display:flex;flex-direction:column;gap:30px;}
  .step{display:flex;gap:30px;align-items:flex-start;}
  .step .n{flex:0 0 auto;width:74px;height:74px;border-radius:50%;border:2px solid #e0b15e;color:#e8be72;
    font-size:38px;font-weight:800;display:flex;align-items:center;justify-content:center;}
  .step .b .t{font-size:44px;font-weight:700;color:#fff;}
  .step .b .d{font-size:32px;color:#9aa0a8;margin-top:6px;line-height:1.5;}
  .big-accent{color:#e8be72;}
"""

def shell(idx, total, eyebrow, inner, foot_tag="全自动 · 免费层 · 1 天上线"):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CSS}</style></head>
<body><div class="slide">
  <div class="eyebrow"><span class="dot"></span>{eyebrow}<span class="idx">&nbsp;&nbsp;{idx:02d}/{total:02d}</span></div>
  {inner}
  <div class="foot"><div class="who">{HANDLE}</div><div class="tag">{foot_tag}</div></div>
</div></body></html>"""

TOTAL = 11

def node(ic, tt, dd):
    return f'<div class="node"><div class="ic">{ic}</div><div><div class="tt">{tt}</div><div class="dd">{dd}</div></div></div>'
ARR = '<div class="arrow">↓</div>'

SLIDES = {}

# 01 Cover —— C 端「个人成长/搞钱」口吻:情绪钩子 > 信息密度
SLIDES[1] = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CSS}</style></head>
<body><div class="slide">
  <div class="eyebrow"><span class="dot"></span>用 AI 放大自己 · 实战</div>
  <div style="margin-top:30px;">
    <h1>把一周的活<br><span class="g">干成一天</span><br>之后让它<br><span class="g">自己跑</span></h1>
    <p class="sub" style="margin-top:50px;">我花一天搭了套自动获客系统<br>搭完它 24 小时替我干活 · 几乎零成本</p>
  </div>
  <div class="grow"></div>
  <div class="chips">
    <span class="chip">一天搭完</span><span class="chip">自己会跑</span>
    <span class="chip">月成本≈0</span><span class="chip">AI 只做辅助</span>
  </div>
  <div class="foot"><div class="who">{HANDLE}</div><div class="tag">先做一次,之后自动</div></div>
</div></body></html>"""

# 02 架构总览
inner2 = f"""<h2>一张图看懂<br>这套系统</h2>
<div class="flow">
  {node("🏭","AI 内容流水线","选题→出图→排版,批量产社媒素材")}
  {ARR}
  {node("📌","社媒免费引流","内容矩阵带量,导向落地页")}
  {ARR}
  {node("🎯","品牌落地页","承接流量,引导留下邮箱")}
  {ARR}
  {node("✉️","邮箱捕获 + 自动邮件","秒发钩子 + 多日养熟序列")}
  {ARR}
  {node("📊","数据回流","全链路埋点,反哺内容")}
</div>
<div class="loop">↺ 数据驱动迭代 · 越跑越准</div>
<div class="grow"></div>"""
SLIDES[2] = shell(2, TOTAL, "系统全景", inner2)

# 03 邮件自动化
inner3 = """<h2>留下邮箱后,<br>一切<span class="big-accent">自动</span>发生</h2>
<div class="steps">
  <div class="step"><div class="n">1</div><div class="b"><div class="t">秒发欢迎邮件</div><div class="d">附带免费钩子,第一时间建立信任</div></div></div>
  <div class="step"><div class="n">2</div><div class="b"><div class="t">2/4/6/8/10 天自动养熟</div><div class="d">6 封序列陆续触达,按注册时间错峰</div></div></div>
  <div class="step"><div class="n">3</div><div class="b"><div class="t">退订自动剔除</div><div class="d">一键退订,后续自动跳过,合规</div></div></div>
  <div class="step"><div class="n">4</div><div class="b"><div class="t">全程零人工</div><div class="d">定时任务每天自动跑,无需盯</div></div></div>
</div>
<div class="grow"></div>"""
SLIDES[3] = shell(3, TOTAL, "邮件全自动", inner3)


def step(n, t, d):
    return f'<div class="step"><div class="n">{n}</div><div class="b"><div class="t">{t}</div><div class="d">{d}</div></div></div>'

# 04 背景 / 需求
inner4 = f"""<h2>客户的需求</h2>
<p class="sub" style="margin-bottom:46px;">一个海外女性向生活方式 DTC 品牌,<br>要从 0 跑通这条增长闭环:</p>
<div style="font-size:40px;line-height:1.7;color:#e8be72;font-weight:700;margin-bottom:50px;">
免费社媒引流 → 留邮箱 → 自动养熟 → 导流成交</div>
<div class="steps">
  {step("痛","没人能天天盯","所以必须全自动、搭好就跑")}
  {step("省","预算紧","能用免费层就不花钱")}
  {step("数","要能看数据","用数据决定下一步做什么")}
</div>
<div class="grow"></div>"""
SLIDES[4] = shell(4, TOTAL, "项目背景", inner4)

# 05 落地页 + 邮箱捕获
inner5 = f"""<h2>落地页 +<br>邮箱捕获<span class="big-accent">(零后端)</span></h2>
<div class="steps">
  {step("1","品牌落地页","移动优先,几秒讲清价值 + 引导留邮箱")}
  {step("2","表单零后端","不写服务器,自动收集邮箱名单")}
  {step("3","即时交付钩子","留完邮箱秒下载免费资料,建立信任")}
  {step("4","自定义域名 + HTTPS","品牌可信、加载快、可被搜索引擎收录")}
</div>
<div class="grow"></div>"""
SLIDES[5] = shell(5, TOTAL, "落地承接", inner5)

# 06 内容流水线
inner6 = f"""<h2>内容流水线 ·<br>防「AI 味」</h2>
<div class="steps">
  {step("①","AI 只出背景图","不让 AI 写字(AI 文字必糊、显廉价)")}
  {step("②","文字用代码精排","品牌字体、排版统一,质感拉满")}
  {step("③","批量出图、风格一致","一套模板量产,不像随手 AI 图")}
  {step("④","人工只管选题 + 质检","AI 做苦力,人把关方向与合规")}
</div>
<div class="grow"></div>"""
SLIDES[6] = shell(6, TOTAL, "内容生产", inner6)

# 07 数据闭环
inner7 = f"""<h2>数据闭环</h2>
<div class="steps">
  {step("📈","全站埋点","访问 / 留资 / 下载 / 意向 全部打点")}
  {step("🔻","全链路漏斗","曝光 → 点击 → 落地 → 留邮箱 → 转化")}
  {step("🖱️","行为热图","看用户到底怎么用这个页面")}
  {step("♻️","数据反哺内容","带量的加产,不带量的砍掉")}
</div>
<div class="grow"></div>"""
SLIDES[7] = shell(7, TOTAL, "数据闭环", inner7)

# 08 技术栈 & 成本
inner8 = f"""<h2>技术栈 & 成本</h2>
<div class="chips" style="margin-bottom:60px;">
  <span class="chip">静态托管</span><span class="chip">表单捕获</span><span class="chip">无服务器函数</span>
  <span class="chip">事务邮件 API</span><span class="chip">定时任务</span><span class="chip">GA4 + 热图</span>
</div>
<div style="text-align:center;margin:30px 0;">
  <div style="font-size:46px;color:#aeb3bb;margin-bottom:10px;">月运营成本</div>
  <div style="font-size:170px;font-weight:800;color:#e8be72;line-height:1;">≈ ¥0</div>
  <div style="font-size:36px;color:#aeb3bb;margin-top:24px;">全部跑在各家免费层<br>流量起来再升级也值</div>
</div>
<div class="grow"></div>"""
SLIDES[8] = shell(8, TOTAL, "技术栈 & 成本", inner8)

# 09 时间线
inner9 = f"""<h2>1 天,<br>从 0 到上线</h2>
<div class="steps">
  {step("上午","方案 + 落地页 + 品牌视觉","定闭环、出落地页、品牌主视觉")}
  {step("中午","邮箱捕获 + 钩子资料","表单上线、免费 PDF 排版交付")}
  {step("下午","自动邮件 + 全站埋点","欢迎+养熟序列、GA4/热图")}
  {step("傍晚","首批内容 + 全链路验证","素材产出、端到端跑通上线")}
</div>
<div class="grow"></div>"""
SLIDES[9] = shell(9, TOTAL, "交付速度", inner9)

# 10 现状 / 进度
inner10 = f"""<h2>现在 · 进度</h2>
<div class="steps" style="margin-bottom:40px;">
  {step("✅","全自动闭环已上线","留邮箱→养熟→导流,无人值守")}
  {step("✅","内容持续产出","素材库就绪,每天滴灌发布")}
  {step("⏳","数据爬坡中","新账号 6–8 周起量是常态")}
  {step("🎯","2 个月看领先指标","诚实复盘,数据驱动迭代")}
</div>
<p class="sub">系统先跑通,再用数据把它越调越准。</p>
<div class="grow"></div>"""
SLIDES[10] = shell(10, TOTAL, "当前进度", inner10)

# 11 CTA —— C 端:不导流私域,只做反问 + 评论 + 收藏(避开限流)
SLIDES[11] = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CSS}</style></head>
<body><div class="slide">
  <div class="eyebrow"><span class="dot"></span>留给你一个问题<span class="idx">&nbsp;&nbsp;11/11</span></div>
  <div style="margin-top:20px;">
    <h1>你最想<br><span class="g">「自动化」掉</span><br>哪件事?</h1>
  </div>
  <p class="sub" style="margin-top:46px;">先找出你天天在重复的那件事,<br>想办法让它「跑一次,之后就自动」。<br>一开始麻烦,搭完是真的香。</p>
  <div class="grow"></div>
  <div style="background:linear-gradient(180deg,#1b1e25,#12151b);border:1.5px solid rgba(224,176,94,.4);border-radius:24px;padding:46px 40px;text-align:center;">
    <div style="font-size:44px;font-weight:800;color:#e8be72;margin-bottom:14px;">💬 评论区聊聊你的想法</div>
    <div style="font-size:36px;color:#fff;font-weight:700;">👀 觉得有用就收藏,别弄丢</div>
  </div>
  <div class="foot"><div class="who">{HANDLE}</div><div class="tag">AI 是放大器,不是替身</div></div>
</div></body></html>"""


def render(idx):
    html = SLIDES[idx]
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(html); path = f.name
    out = OUT / f"slide_{idx:02d}.png"
    subprocess.run([CHROME,"--headless=new","--disable-gpu","--hide-scrollbars",
        f"--screenshot={out}","--window-size=1080,1920","--force-device-scale-factor=1",
        f"file://{path}"], capture_output=True, timeout=120)
    print("OK" if out.exists() else "FAIL", out)


if __name__ == "__main__":
    targets = [int(x) for x in sys.argv[1:]] or sorted(SLIDES)
    for i in targets:
        if i in SLIDES: render(i)
