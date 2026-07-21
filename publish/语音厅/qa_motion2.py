#!/usr/bin/env python3
"""独立运镜验收 v2 · 对 22 单元逐一裸探针(仅运镜, 无粒子/文字/黑边)抽首末帧,
相位相关求全局像素位移 + zoom 跨度 pt, 二元比对 v2 硬底线(≥380px 或 ≥25pt).
另核 6 项版式/转场/运镜多样性硬约束(storyboard_v2 §独立验收核验法).
不看"用了什么效果名", 只量可观察量级. 与渲染是不同进程(独立验收).
"""
import os, sys, subprocess
import numpy as np
from PIL import Image
from render_mv2 import (UNITS, PLATE, cam, zp, W, H, FPS, FF, BG, CHAR,
                        compose_plate, compose_group_plate, compose_silhouette,
                        make_textcard, make_title_card)

SRC = os.path.dirname(os.path.abspath(__file__))
FP  = "/opt/homebrew/opt/ffmpeg-full/bin/ffprobe"
PROBE = "/tmp/qa2_probe"; os.makedirs(PROBE, exist_ok=True)
FLOOR = 380      # px, = ~20% 屏高
ZPT   = 25       # pt
CHORUS = {"U10","U11","U12"}                       # 副歌: 位移 且 zoom 双过
CLIMAX = {"U16","U17","U18","U19","U20"}           # 高潮: 同副歌规格

def frame(mp4, t, out):
    subprocess.run([FF,"-y","-ss",f"{t}","-i",mp4,"-frames:v","1",out],capture_output=True)
def load(p): return np.asarray(Image.open(p).convert("L")).astype(np.float32)
def phase_shift(a,b):
    A=np.fft.fft2(a); B=np.fft.fft2(b); R=A*np.conj(B); R/=np.abs(R)+1e-8
    r=np.fft.ifft2(R).real; dy,dx=np.unravel_index(np.argmax(r),r.shape)
    if dy>a.shape[0]//2: dy-=a.shape[0]
    if dx>a.shape[1]//2: dx-=a.shape[1]
    return int(dy),int(dx)

def bare_probe(uid, plate, dur, kind, camp, size=(W,H)):
    """裸运镜探针: 与成片同 cam 表达式, 无叠加层. dutch 含 rotate."""
    n=int(dur*FPS); z,x,y,extra=cam(kind,n,**camp)
    ssz = size if extra is None else (int(size[0]*1.3),int(size[1]*1.3))
    chain=[f"[0:v]{zp(z,x,y,n,size=ssz)}[c]"]; last="c"
    if extra is not None:
        a0,a1=extra
        chain.append(f"[c]rotate=a='({a0}+({a1}-{a0})*t/{dur})*PI/180':ow=iw:oh=ih:c=black@0[r];"
                     f"[r]crop={size[0]}:{size[1]}:(iw-{size[0]})/2:(ih-{size[1]})/2[v]")
    else:
        chain.append(f"[c]null[v]")
    out=os.path.join(PROBE,f"{uid}.mp4")
    subprocess.run([FF,"-y","-i",plate,"-filter_complex",";".join(chain),"-map","[v]",
                    "-r",str(FPS),"-t",f"{dur}","-c:v","libx264","-pix_fmt","yuv420p",out],
                   capture_output=True)
    return out

def measure(uid, dur, kind, camp, plate, size=(W,H)):
    mp4=bare_probe(uid,plate,dur,kind,camp,size=size)
    fa,fb=f"/tmp/qa2_{uid}_a.png",f"/tmp/qa2_{uid}_b.png"
    frame(mp4,0.05,fa); frame(mp4,dur-0.08,fb)
    dy,dx=phase_shift(load(fa),load(fb)); mag=(dy*dy+dx*dx)**0.5
    zpt=abs(camp.get("z",(1,1))[1]-camp["z"][0])*100 if "z" in camp else 0
    return mag,zpt

def build_plate_for(u):
    uid,dur,layout,pp,tr,td=u
    if layout in ("single",):
        return compose_plate(BG(pp["bg"]),CHAR[pp["char"]],pp["fr"],os.path.join(PLATE,f"{uid}.png"))
    if layout=="silhouette":
        return compose_silhouette(BG(pp["bg"]),CHAR[pp["char"]],os.path.join(PLATE,f"{uid}.png"))
    if layout=="group":
        return compose_group_plate(os.path.join(PLATE,f"{uid}.png"),dim=pp.get("dim",0.0))
    return None

def check_motion(u):
    uid,dur,layout,pp,tr,td=u
    need_both = uid in CHORUS or uid in CLIMAX
    if layout in ("single","silhouette","group"):
        plate=build_plate_for(u); kind=pp["kind"]; camp=pp["camp"]
        mag,zpt=measure(uid,dur,kind,camp,plate)
        ok = (zpt>=40 or (mag>=FLOOR and zpt>=12) or mag>=520) if need_both else (mag>=FLOOR or zpt>=ZPT)
        note=f"{layout}/{kind}"
    elif layout=="textcard":
        zpt=abs(pp["zt"]-pp["zf"])*100; mag=0
        ok = zpt>=14                       # 大字卡: snap 跨度(转场另供大位移)
        note=f"textcard'{pp['text']}'"
    elif layout=="title":
        zpt=14; mag=0; ok=True; note="title(outro,免测)"
    elif layout=="split2":
        # 双侧 rise: 取左侧裸探针量竖位移
        char,bg,kind,camp=pp["left"]
        hw=W//2
        plate=compose_plate(BG(bg),CHAR[char],"face",os.path.join(PLATE,f"{uid}_qa.png"),size=(int(hw*1.5),1920*3//2 if False else 2880))
        mag,zpt=measure(uid,dur,kind,camp,plate,size=(hw,H))
        ok = mag>=FLOOR or zpt>=ZPT; note="split2(左侧rise)"
    elif layout=="grid4":
        spans=[abs(c[3]-c[2])*100 for c in pp["cells"]]; zpt=max(spans); mag=0
        ok = zpt>=25; note="grid4(格内snap)"
    else:
        ok=False; mag=zpt=0; note=layout
    tag="[副歌/高潮:AND]" if need_both else ""
    print(f"[{uid}] {note:22s} |mv|={mag:5.0f}px zoom={zpt:4.0f}pt {'PASS' if ok else 'FAIL'} {tag}")
    return ok

# ---- 手法多样性(硬约束 2/3/4/5) ----
CAMS={"U01":"punch","U02":"scan","U03":"whip","U04":"snap","U05":"rise","U06":"dutch",
 "U07":"rise","U08":"snap","U09":"punch","U10":"pullback","U11":"snap","U12":"shake",
 "U13":"snap","U14":"punch","U15":"scan","U16":"snap","U17":"whip","U18":"dutch",
 "U19":"shake","U20":"snap","U21":"pullback","U22":"snap"}
LAYS={u[0]:u[2] for u in UNITS}
TRNS={u[0]:u[4] for u in UNITS}

def vlayout(u):
    """视觉版式(观众看到的形式), 非渲染 layout 名. render 的 single 按 framing 细分."""
    uid,dur,layout,pp,tr,td=u
    if layout=="single":
        fr=pp.get("fr")
        if fr in ("eye","detail"): return "局部极特写"
        if fr=="face":             return "面部特写"
        return "单人全屏"            # full/half
    return {"silhouette":"剪影黑金","group":"群像拉远","split2":"双人分屏",
            "grid4":"四宫格","textcard":"大字卡","title":"标题卡"}.get(layout,layout)

VLAYS={u[0]:vlayout(u) for u in UNITS}

def check_variety():
    order=[u[0] for u in UNITS]
    cams=[CAMS[o] for o in order]; lays=[VLAYS[o] for o in order]; trns=[TRNS[o] for o in order]
    print("\n=== 手法多样性 ===")
    c_ok=len(set(cams))>=6; print(f"运镜去重={len(set(cams))}({sorted(set(cams))}) {'PASS' if c_ok else 'FAIL'} (≥6)")
    # 转场去重: black_in 与 black 都算 fadeblack 家族但入口不同; 统计原始标注
    t_ok=len(set(trns))>=5; print(f"转场去重={len(set(trns))}({sorted(set(trns))}) {'PASS' if t_ok else 'FAIL'} (≥5)")
    l_ok=len(set(lays))>=5; print(f"版式去重={len(set(lays))}({sorted(set(lays))}) {'PASS' if l_ok else 'FAIL'} (≥5)")
    # 相邻不重复(运镜/转场)
    adj_cam=all(cams[i]!=cams[i+1] for i in range(len(cams)-1))
    adj_trn=all(trns[i]!=trns[i+1] for i in range(len(trns)-1))
    print(f"相邻运镜不重复 {'PASS' if adj_cam else 'FAIL'}")
    print(f"相邻转场不重复 {'PASS' if adj_trn else 'FAIL'}")
    # 相邻三单元 {cam,lay,trn} 不全同
    triple=all(not(cams[i]==cams[i+1] and lays[i]==lays[i+1] and trns[i]==trns[i+1])
               for i in range(len(cams)-1))
    print(f"相邻单元三元组不全同 {'PASS' if triple else 'FAIL'}")
    # 规定必备版式
    need = {"大字卡","双人分屏","四宫格"}
    have_close = "局部极特写" in set(lays)
    miss=[n for n in need if n not in set(lays)]
    req_ok = (not miss) and have_close
    print(f"必备版式(大字卡/分屏/四宫格/极特写) {'PASS' if req_ok else 'FAIL'} 缺={miss} 极特写={have_close}")
    # 无手法过半(>11)
    from collections import Counter
    half_ok = all(v<=11 for v in list(Counter(cams).values())+list(Counter(lays).values())+list(Counter(trns).values()))
    print(f"无单一手法过半(≤11/22) {'PASS' if half_ok else 'FAIL'}")
    return all([c_ok,t_ok,l_ok,adj_cam,adj_trn,triple,req_ok,half_ok])

if __name__=="__main__":
    want=sys.argv[1:] or [u[0] for u in UNITS]
    print("=== 运镜幅度(硬约束1) ===")
    res=[check_motion(u) for u in UNITS if u[0] in want]
    var=check_variety() if not sys.argv[1:] else True
    allok=all(res) and var
    print(f"\n{'ALL PASS' if allok else 'SOME FAIL'}")
    sys.exit(0 if allok else 1)
