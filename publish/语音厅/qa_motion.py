#!/usr/bin/env python3
"""独立运镜验收: 对每镜的**裸 zoompan 探针**(仅 plate+运镜,无粒子/文字/黑边)
抽首/末帧, 相位相关求全局像素位移, 比对 190px(10%屏高)硬底线.
叠加层(滚动粒子/静态大字)会污染全局相关, 故必须在裸探针上量真实相机路径.
不看"用了什么效果", 只量可观察位移量级. 与渲染是不同进程(独立验收).
"""
import os, sys, subprocess
import numpy as np
from PIL import Image
from render_mv import SCENES, PLATE, zoompan, W, H, FPS, FF

SRC = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SRC, "out")
FP  = "/opt/homebrew/opt/ffmpeg-full/bin/ffprobe"
PROBE = "/tmp/qa_probe"; os.makedirs(PROBE, exist_ok=True)
FLOOR = 190  # px, = 10% 屏高

def probe_render(sid, dur, motion):
    """裸 zoompan 探针: 与成片同参, 无叠加层."""
    plate = os.path.join(PLATE, f"{sid}.png")
    out = os.path.join(PROBE, f"{sid}.mp4")
    zp = zoompan(dur, *motion)
    subprocess.run([FF,"-y","-i",plate,"-filter_complex",f"[0:v]{zp}[v]",
                    "-map","[v]","-r",str(FPS),"-c:v","libx264",
                    "-pix_fmt","yuv420p",out], capture_output=True)
    return out

def dur_of(mp4):
    r = subprocess.run([FP,"-v","error","-show_entries","format=duration",
                        "-of","csv=p=0",mp4], capture_output=True, text=True)
    return float(r.stdout.strip())

def frame(mp4, t, out):
    subprocess.run([FF,"-y","-ss",f"{t}","-i",mp4,"-frames:v","1",out],
                   capture_output=True)

def load(p):
    return np.asarray(Image.open(p).convert("L")).astype(np.float32)

def shift(a, b):
    A = np.fft.fft2(a); B = np.fft.fft2(b)
    R = A*np.conj(B); R /= np.abs(R)+1e-8
    r = np.fft.ifft2(R).real
    dy, dx = np.unravel_index(np.argmax(r), r.shape)
    if dy > a.shape[0]//2: dy -= a.shape[0]
    if dx > a.shape[1]//2: dx -= a.shape[1]
    return int(dy), int(dx)

def zoom_span_pt(motion):
    return abs(motion[1]-motion[0])*100

CHORUS = {"s5","s6","s7"}  # 副歌镜: 位移 且 zoom 都须过

def check(sid, dur, motion):
    mp4 = probe_render(sid, dur, motion)
    d = dur_of(mp4)
    fa, fb = f"/tmp/qa_{sid}_a.png", f"/tmp/qa_{sid}_b.png"
    frame(mp4, 0.05, fa); frame(mp4, d-0.1, fb)
    dy, dx = shift(load(fa), load(fb))
    mag = (dy*dy+dx*dx)**0.5
    zpt = zoom_span_pt(motion)
    if sid in CHORUS:
        ok = mag >= FLOOR and zpt >= 12   # 副歌: 两者都过
    else:
        ok = mag >= FLOOR or zpt >= 12    # 非副歌: 任一过底线
    print(f"[{sid}] dur={d:.2f}s  dy={dy:+d} dx={dx:+d}  |mv|={mag:.0f}px "
          f"({mag/H*100:.1f}%H)  zoom={zpt:.0f}pt  {'PASS' if ok else 'FAIL'}"
          f"{'  [副歌:AND]' if sid in CHORUS else ''}")
    return ok

if __name__ == "__main__":
    want = sys.argv[1:] or [s[0] for s in SCENES]
    res = []
    for s in SCENES:
        sid, char, bg, fr, dur, motion, big, name, side = s
        if sid in want:
            res.append(check(sid, dur, motion))
    print("ALL PASS" if all(res) else "SOME FAIL")
    sys.exit(0 if all(res) else 1)

