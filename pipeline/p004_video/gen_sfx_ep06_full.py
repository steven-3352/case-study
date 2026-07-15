#!/usr/bin/env python3
"""EP06 全长版 · SFX 床(重定时到 9 场景真声时间轴)。

原则:VO 是灵魂,sfx 只给关键视觉命中(弹入/砸字/落章/发送)加一层"叮/咚/唰",
      低增益不抢人声;金句"航母送快递"给一记 boom 助推停划。总时长 101.594s。
scene 绝对起点(cut=beat_start-0.2):
  hook 0.00 · stance 6.59 · crash1 16.74 · fix1 31.21 · crash2 37.41
  fix2 48.62 · crash3 58.69 · boundary 74.36 · land 85.96
用法: ./.venv/bin/python pipeline/p004_video/gen_sfx_ep06_full.py
"""
import wave, numpy as np, pathlib
np.random.seed(6)
SR, TOTAL = 48000, 101.594
ROOT = pathlib.Path(__file__).resolve().parents[2]

def read(rel):
    with wave.open(str(ROOT/rel),'rb') as w:
        n,ch=w.getnframes(),w.getnchannels()
        a=np.frombuffer(w.readframes(n),dtype=np.int16).astype(np.float32)
    a=a.reshape(-1,2) if ch==2 else np.stack([a,a],1)
    m=np.abs(a).max(); return a/m if m>0 else a

click=read("assets/sfx/tick/keyboard_typing_sequence_14.wav")
clen=int(0.13*SR); click=click[:clen].copy()
fd=np.ones(clen); f0=int(clen*0.55); fd[f0:]=np.linspace(1,0,clen-f0); click*=fd[:,None]
boom=read("assets/sfx/hit/impact_soft_boom.wav")[:int(0.9*SR)]
whoo=read("assets/sfx/whoosh/whoosh_transition_soft.wav")[:int(0.8*SR)]
tap =read("assets/sfx/tick/subtle_ui_tap_soft.wav")[:int(0.35*SR)]
tick=read("assets/sfx/hit/check_tick_soft.wav")[:int(0.22*SR)]

buf=np.zeros((int(TOTAL*SR),2),dtype=np.float32)
def place(c,t,g):
    s=int(max(0,t)*SR); e=min(len(buf),s+len(c))
    if e>s: buf[s:e]+=c[:e-s]*g
def lay(n,start,stag,g=0.5):
    for i in range(n):
        place(click,start+i*stag+np.random.uniform(-0.004,0.004),g*np.random.uniform(0.72,1.0))

# ── s0 hook 0.00 (自嘲钩子) ──
place(tap,1.3,0.42); place(boom,1.35,0.42)          # "翻了3次车" 砸
for i,t in enumerate((2.6,3.15,3.7)): place(tick,t,0.32)  # 三个 ✗ 弹入
place(tap,4.5,0.4)                                   # "包括最蠢那次"

# ── s1 stance 6.59 (别人炸裂/我发翻车) ──
for i,t in enumerate((6.99,7.54,8.09)): place(tick,t,0.26)  # 三条炸裂划掉
place(boom,9.99,0.42); place(whoo,10.1,0.4)          # "翻车实录" 盖章式弹入

# ── s2 crash1 16.74 (盲签) ──
place(boom,17.14,0.42); place(whoo,17.2,0.38)        # 翻车①卡片入
place(tick,18.24,0.3)                                # 标题
place(boom,23.7,0.5)                                  # "挡在门外" 卡片震
place(tap,27.7,0.4)                                   # "盲签" punch

# ── s3 fix1 31.21 (摘要贴脸·绿) ──
place(tick,31.41,0.34)                                # ✓ 修 badge
place(tap,32.4,0.4); place(boom,32.45,0.34)           # "贴脸上" 砸
place(tick,33.8,0.28); place(tick,34.4,0.28)          # before/after 弹入

# ── s4 crash2 37.41 (拿琐事问) ──
place(boom,37.81,0.42); place(whoo,37.9,0.38)        # 翻车②卡片入
place(tick,38.11,0.3)                                 # 标题
place(tap,44.0,0.34)                                  # "屁大的事" 强调
place(boom,45.6,0.42)                                 # "踩规矩" 红光

# ── s5 fix2 48.62 (裁判由此而生·回扣EP05) ──
place(tick,48.82,0.32)                                # ② 修 badge
place(tap,50.0,0.34)                                  # step1 立规
place(tap,51.8,0.34)                                  # step2 裁判
place(boom,54.2,0.5); place(whoo,54.35,0.4)          # 回扣EP05卡砸入
place(tap,55.4,0.36)                                  # "被逼出来的"

# ── s6 crash3 58.69 (★金句 航母送快递) ──
lay(6,60.1,0.06,0.36)                                 # docker 部署打字
place(tick,65.5,0.36)                                 # ✓ 全跑通
# ★金句:航母送快递(scene t10.4 → abs 69.09)
place(boom,69.09,0.6); place(whoo,69.2,0.42)          # 金句砸出停划
place(boom,71.5,0.5); place(whoo,71.6,0.4)            # "清退全删" 落章

# ── s7 boundary 74.36 (边界救命) ──
place(tick,75.36,0.3); place(tick,75.76,0.3)          # 两仓库弹入
place(whoo,76.36,0.36)                                # 边界墙落下
place(boom,78.56,0.42)                                # 删地盘(项目仓库淡掉)
place(tap,81.96,0.4); place(boom,82.0,0.4)            # "救了我一命" 落实

# ── s8 land 85.96 (落点留痕勾EP07) ──
for i,t in enumerate((90.56,91.41,92.26)): place(tick,t,0.32)  # 三块墓碑立
place(tap,93.36,0.4)                                  # "硬一分"
place(boom,96.86,0.55); place(whoo,97.0,0.42)         # EP07 追更卡
place(tap,98.4,0.4)                                   # "复刻5步"

buf=np.tanh(buf*0.85)*0.9
out_dir=ROOT/"pipeline/p004_video/out/ep06full"; out_dir.mkdir(parents=True,exist_ok=True)
with wave.open(str(out_dir/"sfx_bed_full.wav"),'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((buf*32767).astype(np.int16).tobytes())
print("sfx_bed_full.wav 峰值",round(float(np.abs(buf).max()),3),"· 时长",round(TOTAL,2),"s")
