#!/usr/bin/env python3
"""EP01 全长版 · SFX 床(重定时到 6 场景真声时间轴)。

原则:VO 是灵魂,sfx 只给关键视觉命中(打字/落章/弹入/评论发送/EP02 卡)加一层"叮/咚/唰",
      低增益不抢人声;发凉段用合成低频悬音。总时长 106.944s。
用法: ./.venv/bin/python pipeline/p004_video/gen_sfx_ep01_full.py
"""
import wave, numpy as np, pathlib
np.random.seed(29)
SR, TOTAL = 48000, 106.944
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
    """合成低频悬音(发凉)。"""
    n=int(dur*SR); tt=np.arange(n)/SR
    freq=f+sweep*tt/dur
    env=np.minimum(1,tt/0.6)*np.minimum(1,(dur-tt)/0.8)
    sig=(np.sin(2*np.pi*freq*tt)+0.3*np.sin(2*np.pi*freq*2*tt))*env*g
    st=int(t0*SR); e=min(len(buf),st+n)
    buf[st:e,0]+=sig[:e-st]; buf[st:e,1]+=sig[:e-st]

# ── 开场 hook 0–8.89 ──
place(tap,1.72,0.5); place(boom,1.74,0.5)          # "气到" 砸出
for i,t in enumerate((4.0,5.0,6.0)): place(tick,t,0.34)  # 三 chip 飞入
place(tap,7.1,0.42)                                 # 你也中过招

# ── chatlog 8.89–35.08 (拍1+拍2) ──
lay(18,9.1,0.05,0.42)         # type1 打字
place(tick,11.4,0.4)          # ✓ Memory updated 叮
place(whoo,21.8,0.42)         # 第二天 divider
lay(8,22.6,0.06,0.42)         # type2 打字
place(boom,24.3,0.5)          # 打脸 punch 低咚
place(boom,25.6,0.9); place(whoo,25.75,0.5)  # 抓包 落章

# ── gitscar 35.08–46.67 (拍3) ──
lay(16,35.4,0.045,0.4)        # grep 命令
for i in range(6): place(tick,37.0+i*0.52,0.24)   # commits 流入
place(boom,41.4,0.9); place(whoo,41.55,0.5)       # 全是伤疤 落章

# ── triquiz 46.67–64.30 (拍4) ──
place(tap,47.0,0.3)           # badge
for t in (48.3,51.3,54.3): place(tap,t,0.5); place(tick,t+0.22,0.3)  # 三连"又"踩点
place(boom,58.7,0.9); place(whoo,58.85,0.5)       # 同一天 落章

# ── recap 64.30–88.68 (拍5 互动) ──
for i,t in enumerate((64.6,65.5,66.4)): place(tick,t,0.3)  # 三症状回顾
place(tap,67.9,0.42)          # 反问
place(whoo,71.5,0.45)         # 评论条滑入
lay(3,72.5,0.28,0.5)          # "我也是" 打字
place(tick,73.7,0.5)          # 发送 叮
place(tap,77.7,0.4)           # 不是你不会用
place(tap,83.7,0.42)          # 那到底咋治(承诺)

# ── land 88.68–106.94 (拍6 发凉勾EP02) ──
low_tone(91.8,6.0,f=55,g=0.11,sweep=-8)    # 脊背发凉 悬音
place(tick,95.1,0.34)          # 假"✓ 全部搞定了"(欺骗性平静)
place(boom,98.1,0.55)          # 它还会假装做到了
low_tone(98.0,4.0,f=48,g=0.09,sweep=-6)
place(boom,102.1,0.85); place(whoo,102.25,0.5)   # EP02 卡

buf=np.tanh(buf*0.85)*0.9
out_dir=ROOT/"pipeline/p004_video/out/ep01full"; out_dir.mkdir(parents=True,exist_ok=True)
with wave.open(str(out_dir/"sfx_bed_full.wav"),'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((buf*32767).astype(np.int16).tobytes())
print("sfx_bed_full.wav 峰值",round(float(np.abs(buf).max()),3),"· 时长",round(TOTAL,2),"s")
