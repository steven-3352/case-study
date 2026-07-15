#!/usr/bin/env python3
"""EP07 收官全长版 · SFX 床(重定时到 8 场景真声时间轴)。

收官集基调:沉稳交底、克制。sfx 只给关键视觉命中(卡片弹入/清单勾/落点)
一层极轻的"叮/嗒",金句段用极弱低频悬音给"重量",绝不喧宾夺主抢真声。
总时长 97.16s。
用法: ./.venv/bin/python pipeline/p004_video/gen_sfx_ep07_full.py
"""
import wave, numpy as np, pathlib
np.random.seed(77)
SR, TOTAL = 48000, 97.16
ROOT = pathlib.Path(__file__).resolve().parents[2]

def read(rel):
    with wave.open(str(ROOT/rel),'rb') as w:
        n,ch=w.getnframes(),w.getnchannels()
        a=np.frombuffer(w.readframes(n),dtype=np.int16).astype(np.float32)
    a=a.reshape(-1,2) if ch==2 else np.stack([a,a],1)
    m=np.abs(a).max(); return a/m if m>0 else a

boom=read("assets/sfx/hit/impact_soft_boom.wav")[:int(0.9*SR)]
whoo=read("assets/sfx/whoosh/whoosh_transition_soft.wav")[:int(0.8*SR)]
tap =read("assets/sfx/tick/subtle_ui_tap_soft.wav")[:int(0.35*SR)]
tick=read("assets/sfx/hit/check_tick_soft.wav")[:int(0.22*SR)]

buf=np.zeros((int(TOTAL*SR),2),dtype=np.float32)
def place(c,t,g):
    s=int(max(0,t)*SR); e=min(len(buf),s+len(c))
    if e>s: buf[s:e]+=c[:e-s]*g

def low_tone(t0,dur,f=55.0,g=0.08,sweep=0.0):
    n=int(dur*SR); tt=np.arange(n)/SR
    freq=f+sweep*tt/dur
    env=np.minimum(1,tt/0.8)*np.minimum(1,(dur-tt)/1.0)
    sig=(np.sin(2*np.pi*freq*tt)+0.3*np.sin(2*np.pi*freq*2*tt))*env*g
    st=int(t0*SR); e=min(len(buf),st+n)
    buf[st:e,0]+=sig[:e-st]; buf[st:e,1]+=sig[:e-st]

# ── s0 hook 0–4.89(给货钩子) ──
place(tap,1.0,0.42)                 # "5步 复刻" 弹入
place(tick,1.4,0.34)                # "5步"数字pop
place(tap,2.2,0.42); place(boom,2.25,0.4)  # "坑我都标好了" 落定(轻)

# ── s1 recap 4.89–19.32(回望弧线) ──
for t in (5.29,6.69,9.09,11.19,13.49): place(tick,t,0.26)  # 5 段弧线逐条
place(tap,16.09,0.4)                # "把路给你铺平"

# ── s2 steps12 19.32–31.95(步①②) ──
place(tap,19.82,0.4); place(tick,20.0,0.3)   # 步1
place(tap,25.52,0.4); place(tick,25.7,0.3)   # 步2
place(tap,29.72,0.36)               # caption

# ── s3 steps345 31.95–51.74(步③④⑤) ──
place(tap,32.45,0.4); place(tick,32.63,0.3)  # 步3
place(tick,36.15,0.3)               # 逃生门先建先测 高亮
place(tap,41.35,0.4); place(tick,41.53,0.3)  # 步4
place(tap,44.55,0.4); place(tick,44.73,0.3)  # 步5
place(tap,48.75,0.36)               # caption

# ── s4 effect 51.74–61.74(克制效果卡) ──
for t in (53.14,54.24,55.34): place(tick,t,0.3)   # 三条 ✓ 勾(克制,不用boom)
place(tap,58.14,0.3)                # caption 慢淡入,极轻

# ── s5 limits 61.74–81.82(诚实局限四条) ──
place(tap,62.14,0.36)               # 丑话说前面
for t in (63.74,67.74,71.14,74.34): place(tap,t,0.34)  # 四条一条一顿
place(tap,79.14,0.4)                # 是路线不是现状

# ── s6 creed 81.82–88.89(自警金句·留白) ──
low_tone(82.0,6.2,f=54,g=0.075,sweep=-4)   # 极弱低频给"重量"
place(tap,83.62,0.22)               # 第一句(极轻)
place(tap,85.42,0.22)               # 第二句(极轻)

# ── s7 cta 88.89–97.16(收官邀请·平视) ──
place(tap,89.19,0.32)               # 我不求它多牛
place(tap,91.09,0.32)               # 我求的是
place(tick,93.29,0.34)              # 评论区,见
place(tap,95.09,0.26)               # 连载·完

buf=np.tanh(buf*0.85)*0.9
out_dir=ROOT/"pipeline/p004_video/out/ep07full"; out_dir.mkdir(parents=True,exist_ok=True)
with wave.open(str(out_dir/"sfx_bed_full.wav"),'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((buf*32767).astype(np.int16).tobytes())
print("sfx_bed_full.wav 峰值",round(float(np.abs(buf).max()),3),"· 时长",round(TOTAL,2),"s")
