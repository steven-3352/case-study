#!/usr/bin/env python3
"""EP04 全长版 · SFX 床(重定时到 8 场景真声时间轴)。

原则:VO 是灵魂,sfx 只给关键视觉命中(弹入/落章/派活/枢纽/转折)加一层"叮/咚/唰",
      低增益不抢人声。基调自信明亮(得意)→ 末拍转折加一层克制低音给重量。
      总时长 95.44s。
用法: ./.venv/bin/python pipeline/p004_video/gen_sfx_ep04_full.py
"""
import wave, numpy as np, pathlib
np.random.seed(29)
SR, TOTAL = 48000, 95.44
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

def low_tone(t0,dur,f=58.0,g=0.10,sweep=0.0):
    n=int(dur*SR); tt=np.arange(n)/SR
    freq=f+sweep*tt/dur
    env=np.minimum(1,tt/0.6)*np.minimum(1,(dur-tt)/0.8)
    sig=(np.sin(2*np.pi*freq*tt)+0.3*np.sin(2*np.pi*freq*2*tt))*env*g
    st=int(t0*SR); e=min(len(buf),st+n)
    buf[st:e,0]+=sig[:e-st]; buf[st:e,1]+=sig[:e-st]

# ── s0 hook 0–5.90 (当一整个团队) ──
place(tap,0.15,0.36)                          # kick
place(boom,3.15,0.55); place(whoo,3.30,0.5)   # "一整个团队" 砸出
for i in range(6): place(tick,3.90+i*0.17,0.26)  # 团队成员逐个弹入

# ── s1 scatter 5.90–18.88 (乱的根) ──
place(whoo,6.00,0.42)                          # 终端滑入
for i in range(9): place(tick,10.50+i*0.55,0.22)  # 9 文件散落
place(boom,15.00,0.55); place(whoo,15.15,0.42)    # ✗ 散在 9 个文件

# ── s2 rule3 18.88–27.92 (灵光一闪 立规矩) ──
place(tick,19.18,0.34)                         # 💡 bulb
place(boom,23.08,0.55); place(whoo,23.23,0.48) # 规矩卡砸实
place(tap,24.48,0.42)                          # "3" 弹大

# ── s3 heads 27.92–43.55 (三个头儿 ★得意) ──
for i,t in enumerate((28.42,32.22,36.72)):     # 三头儿逐个滑入
    place(tap,t,0.46); place(tick,t+0.4,0.24)
for t in (30.52,34.52,39.02): place(tick,t,0.24)  # ↳ 各带一队 sub
place(boom,40.82,0.42); place(whoo,40.97,0.36)    # 仨人各带一队 齐亮

# ── s4 auto 43.55–53.42 (自动派活) ──
place(tap,43.85,0.36)                          # 我
for t in (45.05,45.30,45.55): place(tick,t,0.26)  # 三头儿
place(boom,47.35,0.55); place(whoo,47.50,0.5)     # ⚡自动 slam
for t in (48.15,48.45,48.75): place(tick,t,0.26)  # 研究员/史官/门卫
place(tick,50.75,0.4)                          # 不用记谁管谁 ✓

# ── s5 graph 53.42–69.04 (零孤立点) ──
for i in range(5): place(tick,53.92+i*0.28,0.20)  # 节点弹出
place(whoo,56.02,0.42)                         # 连线铺开
place(tick,58.02,0.34)                         # 计数出现
place(tap,61.22,0.44)                          # 枢纽高亮(参谋长+前台)
place(boom,63.82,0.5); place(whoo,63.97,0.42)     # 没有一个孤立点 全绿闪

# ── s6 parallel 69.04–81.97 (平行独立仓库) ──
place(tap,70.44,0.42)                          # 大脑框
for t in (71.34,71.62,71.90): place(tick,t,0.24)  # 三门牌
place(whoo,72.64,0.4)                          # 平行独立分割
for t in (73.04,73.39,73.74): place(tick,t,0.26)  # 三独立仓库
place(tick,77.64,0.30)                         # 伏笔"救了我一命"(克制)

# ── s7 land 81.97–95.44 (转折落点 勾EP05) ──
place(boom,84.17,0.42)                         # 它还是这么说
place(tick,87.77,0.30); place(tick,88.47,0.30)    # 治乱✓ / 治不了骗✗
place(boom,89.07,0.55); place(whoo,89.22,0.46)    # "治不了骗" 转折砸实
low_tone(88.80,3.6,f=60,g=0.08,sweep=-5)          # 转折沉下来的重量(克制,非发凉)
place(boom,91.87,0.55); place(whoo,92.02,0.48)    # EP05 追更卡

buf=np.tanh(buf*0.85)*0.9
out_dir=ROOT/"pipeline/p004_video/out/ep04full"; out_dir.mkdir(parents=True,exist_ok=True)
with wave.open(str(out_dir/"sfx_bed_full.wav"),'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((buf*32767).astype(np.int16).tobytes())
print("sfx_bed_full.wav 峰值",round(float(np.abs(buf).max()),3),"· 时长",round(TOTAL,2),"s")
