#!/usr/bin/env python3
"""EP02 全长版 · SFX 床(重定时到 8 场景真声时间轴)。

原则:VO 是灵魂,sfx 只给关键视觉命中(打字/落章/弹入/发送/发凉)加一层"叮/咚/唰",
      低增益不抢人声;发凉段(拍4/拍6)用合成低频悬音。总时长 103.70s。
用法: ./.venv/bin/python pipeline/p004_video/gen_sfx_ep02_full.py
"""
import wave, numpy as np, pathlib
np.random.seed(29)
SR, TOTAL = 48000, 103.70
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

# ── s0 hook 0.00–10.98(坦白 → "骗了好久"砸出) ──
place(tap,0.4,0.42)
place(boom,7.72,0.55); place(whoo,7.78,0.42)   # "骗了好久" 砸出
place(tick,8.1,0.34)

# ── s1 endure 10.98–19.71(三旧伤 → 都忍了 → 要个成品) ──
for i,t in enumerate((11.28,12.13,12.98)): place(tick,t,0.30)
place(tap,14.2,0.4)                             # 都忍了
place(tap,17.68,0.42); place(tick,17.95,0.32)   # 要个成品(转折)

# ── s2 ask 19.71–28.88(一字一顿下通牒 → 它秒回"好了") ──
lay(9,21.7,0.15,0.4)                            # 通牒逐字
place(tick,27.05,0.42)                          # "好了"(欺骗性秒回)

# ── s3 fakefilm 28.88–46.13(★顶点 抓包假成片) ──
lay(10,29.3,0.05,0.4)                           # open 命令
place(tick,31.3,0.4)                            # 假"✓ 已交付"
place(tap,32.9,0.34)                            # 体检面板落下
for i,t in enumerate((34.5,36.7,38.9,40.3)): place(tick,t,0.28)  # 四条揭穿✗
place(boom,42.68,0.9); place(whoo,42.83,0.5)    # ★落章"这也叫成片?"

# ── s4 unaware 46.13–55.55(发凉·它不知道) ──
low_tone(46.43,5.5,f=55,g=0.11,sweep=-8)        # 温度骤降 悬音
place(tick,51.13,0.30)                          # 它自信绿勾"我干完了"
place(boom,53.33,0.5); low_tone(53.0,3.4,f=48,g=0.09,sweep=-6)  # "它在糊弄我"

# ── s5 read 55.55–65.61(读过没做到) ──
place(tap,56.05,0.38)                           # naive
lay(6,57.45,0.075,0.4)                          # "你读过规矩没"
place(tick,58.95,0.34)                          # 读过了
place(tap,59.95,0.36)                           # 翻出错记录 面板
place(tick,62.95,0.34)                          # "读过。还是没做到"重锤

# ── s6 land 65.61–83.30(★落点 我没法验证) ──
place(tap,69.01,0.34)                           # 它说"锁好了"
place(tick,71.61,0.32)                          # 我能验证吗?
place(tick,72.21,0.30)                          # VS
low_tone(78.5,3.2,f=50,g=0.09,sweep=-5)
place(boom,79.41,0.9); place(whoo,79.56,0.5)    # ★落章"不敢信"

# ── s7 recap 83.30–103.70(共鸣反问 + 打个1 + 勾EP03) ──
place(tap,84.9,0.4)                             # 反问
place(tap,87.7,0.34)                            # 憋屈共鸣
place(whoo,91.3,0.45)                           # 评论条滑入
lay(2,92.2,0.1,0.5)                             # 打"1"
place(tick,93.5,0.5)                            # 发送 叮
place(tap,97.5,0.4)                             # 错的不是它笨
place(boom,100.5,0.55)                          # "是我方法蠢"(自警重锤)
place(tap,101.5,0.42); place(whoo,101.6,0.42)   # EP03 追更卡

buf=np.tanh(buf*0.85)*0.9
out_dir=ROOT/"pipeline/p004_video/out/ep02full"; out_dir.mkdir(parents=True,exist_ok=True)
with wave.open(str(out_dir/"sfx_bed_full.wav"),'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((buf*32767).astype(np.int16).tobytes())
print("sfx_bed_full.wav 峰值",round(float(np.abs(buf).max()),3),"· 时长",round(TOTAL,2),"s")
