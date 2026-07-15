#!/usr/bin/env python3
"""EP05 全长版 · SFX 床(重定时到 6 场景真声时间轴)。

原则:VO 是灵魂,sfx 只给关键视觉命中(上闸/打字/挡push/落章/翻车)加一层"叮/咔/咚/唰",
      低增益不抢人声。基调冷硬机制感(掌控)→ 诚实段收住 → 末拍翻车加克制低音。
      总时长 84.48s。
用法: ./.venv/bin/python pipeline/p004_video/gen_sfx_ep05_full.py
"""
import wave, numpy as np, pathlib
np.random.seed(29)
SR, TOTAL = 48000, 84.484
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

# 场景绝对起点: hook 0 · seed 8.48 · locks12 20.31 · locks34 42.71 · honest 65.54 · land 73.56

# ── s0 hook 0–8.48 (不再信它·上锁) ──
place(tap,0.2,0.36)                          # kick
place(boom,1.85,0.5); place(whoo,2.0,0.42)   # "还是骗我" 砸出
place(boom,4.1,0.5); place(whoo,4.25,0.42)   # "不再信它" 冷砸
for i in range(4): place(tick,5.5+i*0.22,0.28)   # 4 道锁咔落

# ── s1 seed 8.48–20.31 (不能信它自己说的) ──
place(tick,8.9,0.34)                         # 它说做好了✓(欺骗性平静)
place(boom,14.7,0.42); place(whoo,14.85,0.36)    # 铁律浮出:得有别的东西盯着它
place(tick,16.9,0.30)                        # 红字咬实

# ── s2 locks12 20.31–42.71 (闸①② · in-scene +20.31) ──
# 闸① 开工注入
place(boom,20.8,0.42); place(tap,21.0,0.34)  # 卡① 咔落(20.31+0.5/0.7)
lay(4,23.6,0.06,0.34)                        # 塞规矩(打字感)
place(tick,28.3,0.42)                        # 🟢 已上闸(20.31+8.0)
# 闸② 搜重·体检挡
place(whoo,30.9,0.4); place(tap,31.1,0.34)   # 卡② 咔落(20.31+10.6)
lay(3,33.9,0.07,0.32)                        # 搜重复
place(boom,38.7,0.55); place(whoo,38.85,0.46)    # "不是提醒——是挡" 砸实(20.31+18.4)

# ── s3 locks34 42.71–65.54 (闸③+裁判 · in-scene +42.71) ──
# 闸③ 收工硬互锁
place(boom,43.2,0.42); place(tap,43.4,0.34)  # 卡③ 咔落
place(tick,44.2,0.30)                        # 「确认收工」锁扣
place(tick,51.2,0.42)                        # 🟢 溜不掉(42.71+8.5)
# 裁判 Stop
place(whoo,54.6,0.4); place(tap,54.8,0.34)   # 裁判 卡落(42.71+11.9)
place(tap,57.7,0.34)                         # 每轮自动审
place(boom,62.1,0.55); place(whoo,62.25,0.46)    # "当场打回,重做" 砸实(42.71+19.4)

# ── s4 honest 65.54–73.56 (★诚实 放慢·收住) ──
place(tap,65.84,0.30)                        # 但我得说句实话(轻)
place(tick,67.5,0.26)                        # 行为裁判(会漏会误)
place(tick,69.3,0.30)                        # 离散有痕(骗不了人)
low_tone(67.4,5.4,f=62,g=0.07,sweep=-4)      # 诚实沉住的重量(克制,非发凉)

# ── s5 land 73.56–84.48 (自嘲翻车 勾EP06) ──
for i in range(4): place(tick,73.96+i*0.28,0.26)  # 4 锁弹齐(73.56+0.4)
place(boom,76.86,0.55); place(whoo,77.0,0.48)     # "恰恰相反" 翻车砸出(73.56+3.3)
low_tone(76.7,3.4,f=58,g=0.07,sweep=-5)           # 翻车的反差重量(克制)
place(boom,78.76,0.5); place(whoo,78.9,0.42)      # EP06 追更卡(73.56+5.2)

buf=np.tanh(buf*0.85)*0.9
out_dir=ROOT/"pipeline/p004_video/out/ep05full"; out_dir.mkdir(parents=True,exist_ok=True)
with wave.open(str(out_dir/"sfx_bed_full.wav"),'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((buf*32767).astype(np.int16).tobytes())
print("sfx_bed_full.wav 峰值",round(float(np.abs(buf).max()),3),"· 时长",round(TOTAL,2),"s")
