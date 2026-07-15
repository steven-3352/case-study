#!/usr/bin/env python3
"""EP03 全长版 · SFX 床(重定时到 7 场景真声时间轴)。

原则:VO 是灵魂,sfx 只给关键视觉命中(打字/落章/弹入/一字一顿)加一层"叮/咚/唰",
      低增益不抢人声。EP03 是顿悟/亮的调子,不用发凉低频。总时长 82.531s。
用法: ./.venv/bin/python pipeline/p004_video/gen_sfx_ep03_full.py
"""
import wave, numpy as np, pathlib
np.random.seed(33)
SR, TOTAL = 48000, 82.531
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

# ── s0 hook 0.0–8.59 (换挡) ──
place(tap,2.2,0.4)                       # setup 出
place(boom,4.9,0.5); place(whoo,5.05,0.42)  # "记不住的员工" 换挡砸出
for t in (6.4,6.9,7.4): place(tick,t,0.3)   # 三管手段 chip

# ── s1 dumbfix 8.59–20.88 (蠢办法) ──
lay(16,8.99,0.05,0.4)                    # type 打字
for t in (11.59,14.09,16.59): place(tick,t,0.34)  # 三次 Memory updated
place(boom,18.59,0.5)                    # fail 换会话还是漏

# ── s2 read 20.88–28.85 (读过还是没做到) ──
place(tap,22.08,0.4)                     # read bubble
place(tick,22.48,0.34)                   # ✓ 已读
place(boom,24.58,0.55)                   # 还是没做到 砸
place(tap,26.28,0.4)                     # 记了也不算数

# ── s3 deadends 28.85–43.63 (两条死路·顿悟) ──
place(tap,29.85,0.34); place(tick,32.35,0.3)  # 路一 + ✗
place(tap,33.35,0.34); place(tick,35.35,0.3)  # 路二 + ✗
place(tap,37.35,0.4)                     # 两条人力的路
place(boom,39.85,0.6); place(whoo,40.0,0.45)  # 死路 顿悟戳

# ── s4 mechanical 43.63–56.11 (机械·全集的锤) ──
place(tap,44.03,0.34)                    # rule
place(tick,45.73,0.34)                   # 绕不过的闸门
place(boom,47.23,0.62); place(whoo,47.38,0.46)  # 机械>自觉 THE HAMMER
for t in (51.43,52.28,53.13,53.98): place(tick,t,0.4)  # 绕·不·过·去 一字一顿

# ── s5 rule 56.11–66.53 (不靠自觉靠机制) ──
for t in (57.11,59.51,62.11): place(tap,t,0.42)  # 红绿灯/护具/助理
place(boom,64.51,0.5)                    # 一模一样

# ── s6 land 66.53–82.53 (落点勾EP04) ──
place(tap,67.53,0.38)                    # 乱文件
place(tick,71.03,0.34)                   # 不是写代码
place(whoo,74.33,0.42)                   # ↓ 变身
for i,t in enumerate((75.03,75.19,75.35)): place(tick,t,0.3)  # 三节点团队
place(tap,77.53,0.4)                     # 拆成一家公司
place(tick,79.53,0.34)                   # CTA

buf=np.tanh(buf*0.85)*0.9
out_dir=ROOT/"pipeline/p004_video/out/ep03full"; out_dir.mkdir(parents=True,exist_ok=True)
with wave.open(str(out_dir/"sfx_bed_full.wav"),'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((buf*32767).astype(np.int16).tobytes())
print("sfx_bed_full.wav 峰值",round(float(np.abs(buf).max()),3),"· 时长",round(TOTAL,2),"s")
