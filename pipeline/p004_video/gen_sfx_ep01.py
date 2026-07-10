#!/usr/bin/env python3
"""EP01 症状三连 · SFX 床合成(键盘/落章咚/消息叮/commit tick/whoosh).

按动效时间戳把 CC0 单发音效铺成完整音效床 → out/sfx_bed_full.wav。
素材来自 assets/sfx/(fetch_sfx.py 拉的 Freesound CC0)。
用法: ./.venv/bin/python pipeline/p004_video/gen_sfx_ep01.py
再混: ffmpeg -i out/ep01_silent.mp4 -i out/sfx_bed_full.wav -map 0:v -map 1:a ...
"""
import wave, numpy as np, pathlib
np.random.seed(7)
SR, TOTAL = 48000, 27.5
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
    s=int(max(0,t)*SR); e=min(len(buf),s+len(c)); buf[s:e]+=c[:e-s]*g
def lay(text,start,stag,off,base=0.75):
    for i,_ in enumerate(text):
        place(click,off+start+i*stag+np.random.uniform(-0.004,0.004),base*np.random.uniform(0.72,1.0))
lay("记住:出片先过质量门,不能跳。这是死规矩。",0.30,0.050,0.0)
lay("按之前那条规矩来",3.50,0.055,0.0)
lay(r"git log | grep 收敛\|清全尸\|一事一处",0.30,0.040,9.5)
lay("你确定是按系统的规范在做吗?",0.50,0.045,18.0,base=0.68)
lay("为什么又出现漏掉规范?",1.85,0.045,18.0,base=0.68)
lay("系统的核心宗旨又忘记了吗?",3.20,0.045,18.0,base=0.68)
place(tap,1.50,0.42); place(tick,2.05,0.38); place(tick,4.70,0.34); place(boom,6.02,0.92); place(whoo,6.18,0.5)
place(whoo,9.5,0.42)
for i in range(6): place(tick,9.5+1.6+i*0.34,0.22)
place(tap,9.5+3.84,0.38); place(boom,9.5+5.00,0.92); place(whoo,9.5+5.18,0.5)
place(whoo,18.0,0.42)
for t in (0.5,1.85,3.20): place(tap,18.0+t,0.40)
place(tick,18.0+4.55,0.30); place(boom,18.0+5.91,0.92); place(whoo,18.0+6.12,0.5)
buf=np.tanh(buf*0.9)*0.92
out_dir=ROOT/"pipeline/p004_video/out"; out_dir.mkdir(exist_ok=True)
with wave.open(str(out_dir/"sfx_bed_full.wav"),'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((buf*32767).astype(np.int16).tobytes())
print("sfx_bed_full.wav 峰值",round(float(np.abs(buf).max()),3))
