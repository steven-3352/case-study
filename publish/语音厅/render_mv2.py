#!/usr/bin/env python3
"""语音厅《明月天涯》立绘 MV 渲染引擎 v2 · 22 单元多手法版.

推翻 v1 的三个差评:
  ① 运镜幅度太小/单一 → 8 种运镜(猛推/局部快扫/横向甩镜/卡拍snap/竖向升降/倾斜dutch/猛拉远/手持抖动),
     全部前置缓动(front-load easing),幅度过 ≥380px 或 ≥25pt 硬底线,相邻禁重复.
  ② 转场慢/单一/PPT → 7 种转场(黑场亮起/缩放冲切/硬切卡拍/白闪/方向滑入/黑闪/短叠化),
     用 xfade 原生转场 + 卡拍点 offset,副歌 1-2 拍即切.
  ③ 表现形式单一 → 7 种版式(单人全屏/局部极特写/左右双人分屏/四宫格/群像拉远/满屏书法大字卡/剪影黑金).

依据 design/motion_storyboard_v2.md 的 22 单元 observable_metric.
运镜为 zoompan(单帧 -i + d=n,禁 -loop -t);位移经验式 dy≈H*(z_avg-1)*py_sweep.
用法: python3 render_mv2.py U01     # 单元测试
      python3 render_mv2.py all     # 全片(渲染+xfade+mux)
      python3 render_mv2.py mux      # 只重跑 xfade 拼接+混音
"""
import os, sys, subprocess, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

SRC = os.path.dirname(os.path.abspath(__file__))
AB  = os.path.join(SRC, "assets_build")
OUT = os.path.join(SRC, "out2"); os.makedirs(OUT, exist_ok=True)
PLATE = os.path.join(OUT, "plates"); os.makedirs(PLATE, exist_ok=True)
UNIT = os.path.join(OUT, "units"); os.makedirs(UNIT, exist_ok=True)
FF = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"
if not os.path.exists(FF): FF = "ffmpeg"

W, H, FPS = 1080, 1920, 30
PW, PH = 1620, 2880          # plate 1.5x 给运镜余量
WAV = os.path.join(SRC, "明月天涯 导唱(1).WAV")

FONT_HEAVY = os.path.expanduser("~/Library/Fonts/SourceHanSansSC-Heavy.otf")
FONT_SONG  = "/System/Library/Fonts/Supplemental/Songti.ttc"
FONT_NORM  = os.path.expanduser("~/Library/Fonts/SourceHanSansSC-Normal.otf")

CHAR = {k: os.path.join(AB, f"lihui_{k}.png") for k in ["cy","nuolan","xuanheng","zhongli"]}
BG   = lambda n: os.path.join(AB, f"bg_{n}.png")
PET  = os.path.join(AB, "particles_petals.png")
BOK  = os.path.join(AB, "particles_bokeh.png")
GOLD = (212, 175, 55)

# ---- 蓝紫压制(中里毅立绘含紫,过禁霓虹色门) ----
def deblue(im):
    rgba = np.asarray(im.convert("RGBA")).astype(np.uint8)
    rgb = Image.fromarray(rgba[..., :3], "RGB").convert("HSV")
    hsv = np.asarray(rgb).astype(np.int16)
    h, s = hsv[..., 0], hsv[..., 1]
    mask = (h >= 165) & (h <= 210)
    hsv[..., 0][mask] = 28
    hsv[..., 1][mask] = (s[mask] * 0.45).astype(np.int16)
    out = Image.fromarray(hsv.astype(np.uint8), "HSV").convert("RGB")
    res = np.dstack([np.asarray(out), rgba[..., 3]])
    return Image.fromarray(res.astype(np.uint8), "RGBA")

# ---- 立绘 plate: bg 铺满 + 立绘按 framing 放置 ----
# framing 控制立绘高度(相对 PH)与竖位; 决定该单元是全景/半身/脸部/眼部/局部.
# 脸/眼/局部为"焦点锚定": 把立绘上的焦点(头心/眼线/腰配饰)放到 plate 竖向 0.42 处,
# 这样相机居中 py 就能真正框住该焦点, 而不是扫到胸口(v1 病灶).
def compose_plate(bg, char, framing, out, size=(PW, PH)):
    pw, ph = size
    canvas = Image.open(bg).convert("RGBA").resize((pw, ph), Image.LANCZOS)
    ch = deblue(Image.open(char).convert("RGBA"))
    # (立绘高度相对 ph, 焦点在立绘上的竖向比例 anchor, 焦点落在 plate 的竖向比例 place)
    SPEC = {"full":(0.82,None,None),"half":(1.10,None,None),
            "face":(1.75,0.08,0.40),"eye":(2.6,0.05,0.42),"detail":(1.65,0.30,0.40)}
    hfrac, anchor, place = SPEC[framing]
    th = int(ph*hfrac); r = th/ch.height
    ch = ch.resize((max(1,int(ch.width*r)), th), Image.LANCZOS)
    if anchor is None:
        if framing=="full":  y = ph - ch.height - int(ph*0.02)
        else:                y = ph - ch.height + int(ph*0.28)   # half: 腰上
    else:
        y = int(place*ph - anchor*ch.height)                     # 焦点锚定
    x = (pw - ch.width)//2
    canvas.alpha_composite(ch, (x, y))
    canvas.convert("RGB").save(out); return out

def compose_group_plate(out, dim=0.0, size=(PW, PH)):
    pw, ph = size
    canvas = Image.open(BG("bamboo_bright")).convert("RGBA").resize((pw, ph), Image.LANCZOS)
    order = ["xuanheng","cy","nuolan","zhongli"]
    cw = pw//4
    for i,k in enumerate(order):
        ch = deblue(Image.open(CHAR[k]).convert("RGBA"))
        th = int(ph*0.70); r=th/ch.height
        ch = ch.resize((int(ch.width*r), th), Image.LANCZOS)
        x = i*cw + cw//2 - ch.width//2
        y = ph - ch.height - int(ph*0.05)
        canvas.alpha_composite(ch,(x,y))
    im = canvas.convert("RGB")
    if dim>0:
        im = Image.eval(im, lambda p:int(p*(1-dim)))
    im.save(out); return out

# ---- 剪影黑金: 主体压成金边黑剪影, 背景压暗镀金 ----
def compose_silhouette(bg, char, out):
    canvas = Image.open(bg).convert("RGB").resize((PW, PH), Image.LANCZOS)
    canvas = Image.eval(canvas, lambda p:int(p*0.22))            # 背景压暗
    tint = Image.new("RGB",(PW,PH),(60,45,12)); canvas = Image.blend(canvas,tint,0.35)
    ch = deblue(Image.open(char).convert("RGBA"))
    th = int(PH*0.82); r=th/ch.height
    ch = ch.resize((int(ch.width*r), th), Image.LANCZOS)
    a = ch.split()[3]
    body = Image.new("RGBA", ch.size, (8,8,8,0)); body.putalpha(a)   # 近黑主体
    rim = a.filter(ImageFilter.MaxFilter(9))
    rim = Image.fromarray(np.clip(np.asarray(rim).astype(np.int16)-np.asarray(a).astype(np.int16),0,255).astype(np.uint8))
    goldrim = Image.new("RGBA", ch.size, GOLD+(0,)); goldrim.putalpha(rim)
    x=(PW-ch.width)//2; y=PH-ch.height-int(PH*0.03)
    base = canvas.convert("RGBA")
    base.alpha_composite(body,(x,y)); base.alpha_composite(goldrim,(x,y))
    base.convert("RGB").save(out); return out

# ---- 满屏书法大字卡: 黑金底 + 竖排书法, 无立绘 ----
def make_textcard(text, out, size=None):
    pw, ph = size or (int(W*1.3), int(H*1.3))
    im = Image.new("RGB",(pw,ph),(10,9,8))
    # 中心金色径向光晕
    yy,xx = np.mgrid[0:ph,0:pw]
    d = np.sqrt((xx-pw/2)**2+((yy-ph/2)*0.9)**2)/(pw*0.6)
    glow = np.clip(1-d,0,1)**2.2
    arr = np.asarray(im).astype(np.float32)
    for c,g in enumerate((70,55,18)): arr[...,c]+=glow*g
    im = Image.fromarray(np.clip(arr,0,255).astype(np.uint8))
    dr = ImageDraw.Draw(im)
    n=len(text); fs=int(ph*0.16)
    fnt=ImageFont.truetype(FONT_SONG, fs)
    gap=int(fs*1.14); total=gap*n
    y0=(ph-total)//2; cx=pw//2
    for i,c in enumerate(text):
        b=dr.textbbox((0,0),c,font=fnt); cwd=b[2]-b[0]
        px=cx-cwd//2-b[0]; py=y0+i*gap
        dr.text((px+4,py+4),c,font=fnt,fill=(0,0,0))          # 阴影
        dr.text((px,py),c,font=fnt,fill=GOLD)
    im.save(out); return out

def make_title_card(out):
    pw,ph=int(W*1.15),int(H*1.15)
    p=compose_group_plate(os.path.join(PLATE,"_titbg.png"), dim=0.55, size=(pw,ph))
    im=Image.open(p).convert("RGB").filter(ImageFilter.GaussianBlur(7))
    im=Image.eval(im,lambda v:int(v*0.75))
    dr=ImageDraw.Draw(im)
    fs=int(ph*0.10); fnt=ImageFont.truetype(FONT_SONG,fs)
    t="明月天涯"; b=dr.textbbox((0,0),t,font=fnt)
    tw=b[2]-b[0]; tx=(pw-tw)//2-b[0]; ty=int(ph*0.30)
    dr.text((tx+4,ty+4),t,font=fnt,fill=(0,0,0))
    dr.text((tx,ty),t,font=fnt,fill=(245,240,230))
    sub="· 语音厅立绘同人 ·"; fn2=ImageFont.truetype(FONT_NORM,int(fs*0.32))
    b2=dr.textbbox((0,0),sub,font=fn2); sw=b2[2]-b2[0]
    dr.text(((pw-sw)//2,ty+int(fs*1.3)),sub,font=fn2,fill=GOLD)
    im.save(out); return out

# ================= 运镜表达式 (on/n 为时间; 前置缓动 min(1,p/k)) =================
def _lin(a,b,frac): return f"({a}+({b}-{a})*({frac}))"

def cam(kind, n, **p):
    """返回 (z_expr, x_expr, y_expr, extra) — extra 给 dutch 用旋转角."""
    P  = f"(on/{n-1})"
    def ease(k): return f"min(1,{P}/{k})"               # 前 k 比例内完成
    zf,zt = p.get("z",(1.10,1.10))
    pxf,pxt = p.get("px",(0.5,0.5)); pyf,pyt = p.get("py",(0.5,0.5))
    xr = f"(iw-iw/zoom)"; yr = f"(ih-ih/zoom)"
    extra=None
    if kind=="punch":            # 猛推: zoom 前置爆推
        e=ease(p.get("k",0.14)); z=_lin(zf,zt,e)
        x=f"{xr}*{_lin(pxf,pxt,P)}"; y=f"{yr}*{_lin(pyf,pyt,P)}"
    elif kind=="pullback":       # 猛拉远: zoom 反向前置
        e=ease(p.get("k",0.18)); z=_lin(zf,zt,e)
        x=f"{xr}*{_lin(pxf,pxt,P)}"; y=f"{yr}*{_lin(pyf,pyt,P)}"
    elif kind=="scan":           # 局部快扫: zoom 锁, pan 前置猛扫
        e=ease(p.get("k",0.3)); z=_lin(zf,zt,P)
        x=f"{xr}*{_lin(pxf,pxt,e)}"; y=f"{yr}*{_lin(pyf,pyt,e)}"
    elif kind=="whip":           # 横向甩镜: 横 pan 极快前置
        e=ease(p.get("k",0.2)); z=_lin(zf,zt,P)
        x=f"{xr}*{_lin(pxf,pxt,e)}"; y=f"{yr}*{_lin(pyf,pyt,P)}"
    elif kind=="snap":           # 卡拍: 1 拍内 snap 缩放
        e=ease(p.get("k",0.22)); z=_lin(zf,zt,e)
        x=f"{xr}*{_lin(pxf,pxt,e)}"; y=f"{yr}*{_lin(pyf,pyt,e)}"
    elif kind=="rise":           # 竖向大幅升降: 大 pan(线性稳)
        z=_lin(zf,zt,P); x=f"{xr}*{_lin(pxf,pxt,P)}"; y=f"{yr}*{_lin(pyf,pyt,P)}"
    elif kind=="shake":          # 手持抖动: 缓推 + 高频 sin 抖
        z=_lin(zf,zt,P)
        amp=p.get("amp",12); fr=p.get("fr",2.6)
        x=f"{xr}*{_lin(pxf,pxt,P)}+{amp}*sin(on*{fr})"
        y=f"{yr}*{_lin(pyf,pyt,P)}+{amp}*cos(on*{fr*1.3})"
    elif kind=="dutch":          # 倾斜: zoompan + 后置 rotate(extra)
        z=_lin(zf,zt,P); x=f"{xr}*{_lin(pxf,pxt,P)}"; y=f"{yr}*{_lin(pyf,pyt,P)}"
        extra=p.get("rot",(0,8))
    else: raise ValueError(kind)
    return z,x,y,extra

def zp(z,x,y,n,size=(W,H)):
    return (f"zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={size[0]}x{size[1]}:fps={FPS}")

# ---- 叠层 ----
def letterbox(): return f"drawbox=0:0:{W}:54:black@1:t=fill,drawbox=0:{H-54}:{W}:54:black@1:t=fill"
def name_tag(name):
    return (f"drawtext=fontfile='{FONT_NORM}':text='- {name} -':fontsize=42:"
            f"fontcolor=white@0.9:borderw=2:bordercolor=black@0.5:x=(w-tw)/2:y=h-130")

def _run(cmd, tag):
    r=subprocess.run(cmd,capture_output=True,text=True)
    if r.returncode!=0:
        print(f"[{tag}] ERR\n{r.stderr[-1600:]}"); sys.exit(1)

# ================= 单元渲染 =================
def render_single(uid, plate, dur, kind, camp, size=(W,H), particles="pet",
                  name=None, letter=True):
    n=int(dur*FPS)
    z,x,y,extra=cam(kind,n,**camp)
    chain=[f"[0:v]{zp(z,x,y,n,size=size if extra is None else (int(size[0]*1.3),int(size[1]*1.3)))}[cam]"]
    last="cam"
    if extra is not None:                # dutch: 旋转后中心裁回 size
        a0,a1=extra
        rot=f"[cam]rotate=a='({a0}+({a1}-{a0})*t/{dur})*PI/180':ow=iw:oh=ih:c=black@0[rot];" \
            f"[rot]crop={size[0]}:{size[1]}:(iw-{size[0]})/2:(ih-{size[1]})/2[cr]"
        chain.append(rot); last="cr"
    inputs=["-i",plate]
    idx=1
    if particles:
        pf=PET if particles=="pet" else BOK
        inputs+=["-loop","1","-t",f"{dur}","-i",pf]
        aa="0.7" if particles=="pet" else "0.5"
        yexpr=f"-(mod(t*90,{max(1,size[1]*2)}))" if particles=="pet" else f"(mod(t*45,{max(1,size[1]*2)}))-{size[1]}"
        chain.append(f"[{idx}:v]scale={size[0]}:-1,format=rgba,colorchannelmixer=aa={aa}[pt]")
        chain.append(f"[{last}][pt]overlay=x=0:y='{yexpr}':shortest=1[pv]"); last="pv"; idx+=1
    post=[]
    if letter: post.append(letterbox())
    if name: post.append(name_tag(name))
    if post: chain.append(f"[{last}]"+",".join(post)+"[v]")
    else:    chain.append(f"[{last}]null[v]")
    fc=";".join(chain)
    out=os.path.join(UNIT,f"{uid}.mp4")
    _run([FF,"-y",*inputs,"-filter_complex",fc,"-map","[v]","-r",str(FPS),
          "-t",f"{dur}","-c:v","libx264","-pix_fmt","yuv420p","-crf","18",out],uid)
    print(f"[{uid}] single/{kind} -> {out}"); return out

def render_split2(uid, dur, left, right):
    """左右双人分屏: left/right = (char,bg,kind,camp), 各 W/2×H, hstack."""
    hw=W//2; n=int(dur*FPS); parts=[]
    inputs=[]; chain=[]
    for i,(char,bg,kind,camp) in enumerate([left,right]):
        p=compose_plate(BG(bg),CHAR[char],"face",os.path.join(PLATE,f"{uid}_{i}.png"),size=(int(hw*1.5),PH))
        inputs+=["-i",p]
        z,x,y,_=cam(kind,n,**camp)
        chain.append(f"[{i}:v]{zp(z,x,y,n,size=(hw,H))}[c{i}]")
    chain.append(f"[c0][c1]hstack=inputs=2[hs]")
    chain.append(f"[hs]drawbox={hw-2}:0:4:{H}:black@0.9:t=fill,{letterbox()}[v]")
    out=os.path.join(UNIT,f"{uid}.mp4")
    _run([FF,"-y",*inputs,"-filter_complex",";".join(chain),"-map","[v]","-r",str(FPS),
          "-t",f"{dur}","-c:v","libx264","-pix_fmt","yuv420p","-crf","18",out],uid)
    print(f"[{uid}] split2 -> {out}"); return out

def render_grid4(uid, dur, cells):
    """四宫格: cells=[(char,bg,zf,zt)]×4, 各 W/2×H/2, 2x2."""
    cw,cellh=W//2,H//2; n=int(dur*FPS)
    inputs=[]; chain=[]
    for i,(char,bg,zf,zt) in enumerate(cells):
        p=compose_plate(BG(bg),CHAR[char],"face",os.path.join(PLATE,f"{uid}_{i}.png"),size=(int(cw*1.5),int(cellh*1.5)))
        inputs+=["-i",p]
        z,x,y,_=cam("snap",n,z=(zf,zt),k=0.25,py=(0.35,0.2) if i%2==0 else (0.65,0.8))
        chain.append(f"[{i}:v]{zp(z,x,y,n,size=(cw,cellh))}[c{i}]")
    chain.append(f"[c0][c1]hstack=inputs=2[t];[c2][c3]hstack=inputs=2[b];[t][b]vstack=inputs=2[g]")
    chain.append(f"[g]drawbox={cw-2}:0:4:{H}:black@0.9:t=fill,drawbox=0:{cellh-2}:{W}:4:black@0.9:t=fill,{letterbox()}[v]")
    out=os.path.join(UNIT,f"{uid}.mp4")
    _run([FF,"-y",*inputs,"-filter_complex",";".join(chain),"-map","[v]","-r",str(FPS),
          "-t",f"{dur}","-c:v","libx264","-pix_fmt","yuv420p","-crf","18",out],uid)
    print(f"[{uid}] grid4 -> {out}"); return out

def render_textcard(uid, dur, text, zf, zt, k=0.24, title=False):
    card=(make_title_card(os.path.join(PLATE,f"{uid}.png")) if title
          else make_textcard(text,os.path.join(PLATE,f"{uid}.png")))
    cw,ch=Image.open(card).size; n=int(dur*FPS)
    z,x,y,_=cam("snap",n,z=(zf,zt),k=k)
    chain=[f"[0:v]{zp(z,x,y,n,size=(W,H))}[v]"]
    out=os.path.join(UNIT,f"{uid}.mp4")
    _run([FF,"-y","-i",card,"-filter_complex",";".join(chain),"-map","[v]","-r",str(FPS),
          "-t",f"{dur}","-c:v","libx264","-pix_fmt","yuv420p","-crf","18",out],uid)
    print(f"[{uid}] textcard '{text}' -> {out}"); return out

# ================= 22 单元定义 =================
# 每项: uid, dur, layout, params, trans(转场入 name), tdur
UNITS = [
 ("U01",4.6,"single",dict(char="xuanheng",bg="bamboo_bright",fr="full",kind="punch",
    camp=dict(z=(1.08,1.34),px=(0.42,0.56),py=(0.80,0.30),k=0.10),particles="pet",name="轩珩"),
    "black_in",0.35),
 ("U02",1.9,"single",dict(char="xuanheng",bg="bamboo_bright",fr="detail",kind="scan",
    camp=dict(z=(1.44,1.44),px=(0.5,0.5),py=(0.08,0.94),k=0.34),particles=None),"zoomin",0.16),
 ("U03",3.7,"single",dict(char="cy",bg="courtyard_warm",fr="full",kind="whip",
    camp=dict(z=(1.10,1.36),px=(0.03,0.85),py=(0.4,0.34),k=0.14),particles="bok",name="Cy"),"hard",0.04),
 ("U04",2.8,"single",dict(char="cy",bg="courtyard_warm",fr="eye",kind="snap",
    camp=dict(z=(1.08,1.54),px=(0.5,0.5),py=(0.34,0.28),k=0.18),particles=None),"white",0.12),
 ("U05",2.8,"split2",dict(left=("nuolan","mist_cool","rise",dict(z=(1.12,1.40),py=(0.90,0.06))),
    right=("zhongli","floral_warm","rise",dict(z=(1.12,1.40),py=(0.06,0.90)))),"slide",0.28),
 ("U06",2.3,"single",dict(char="nuolan",bg="mist_cool",fr="face",kind="dutch",
    camp=dict(z=(1.12,1.40),px=(0.5,0.5),py=(0.34,0.62),rot=(0,8)),particles="bok"),"black",0.10),
 ("U07",1.9,"single",dict(char="zhongli",bg="floral_warm",fr="half",kind="rise",
    camp=dict(z=(1.14,1.34),px=(0.5,0.5),py=(0.92,0.06)),particles="pet"),"dissolve",0.18),
 ("U08",2.8,"textcard",dict(text="游侠俊名远",zf=0.80,zt=1.18,k=0.20),"hard",0.04),
 ("U09",2.8,"single",dict(char="xuanheng",bg="riverside_night",fr="full",kind="punch",
    camp=dict(z=(1.08,1.34),px=(0.46,0.58),py=(0.75,0.30),k=0.12),particles="bok"),"zoomin",0.18),
 ("U10",1.8,"group",dict(kind="pullback",camp=dict(z=(1.44,1.02),px=(0.5,0.5),py=(0.30,0.55),k=0.16)),"white",0.14),
 ("U11",1.9,"grid4",dict(cells=[("xuanheng","bamboo_bright",1.04,1.46),("cy","courtyard_warm",1.46,1.04),
    ("nuolan","mist_cool",1.04,1.46),("zhongli","floral_warm",1.46,1.04)]),"zoomin",0.16),
 ("U12",1.9,"single",dict(char="xuanheng",bg="floral_warm",fr="face",kind="shake",
    camp=dict(z=(1.04,1.48),px=(0.5,0.5),py=(0.44,0.30),amp=10,fr=2.6),particles=None),"hard",0.04),
 ("U13",2.3,"textcard",dict(text="纵横天下",zf=0.92,zt=1.20,k=0.16),"slide",0.26),
 ("U14",2.3,"silhouette",dict(char="cy",bg="riverside_night",kind="punch",
    camp=dict(z=(1.08,1.34),px=(0.44,0.56),py=(0.6,0.3),k=0.12)),"black",0.10),
 ("U15",2.3,"single",dict(char="nuolan",bg="mist_cool",fr="detail",kind="scan",
    camp=dict(z=(1.45,1.45),px=(0.06,0.94),py=(0.4,0.45),k=0.32),particles=None),"dissolve",0.15),
 ("U16",1.4,"single",dict(char="xuanheng",bg="floral_warm",fr="face",kind="snap",
    camp=dict(z=(1.02,1.46),px=(0.30,0.36),py=(0.44,0.30),k=0.24),particles=None),"hard",0.04),
 ("U17",1.4,"single",dict(char="cy",bg="mist_cool",fr="face",kind="whip",
    camp=dict(z=(1.08,1.52),px=(0.74,0.28),py=(0.36,0.44),k=0.18),particles=None),"zoomin",0.16),
 ("U18",1.4,"single",dict(char="nuolan",bg="bamboo_bright",fr="face",kind="dutch",
    camp=dict(z=(1.08,1.52),px=(0.5,0.5),py=(0.44,0.36),rot=(-7,7)),particles=None),"white",0.10),
 ("U19",1.4,"single",dict(char="zhongli",bg="riverside_night",fr="face",kind="shake",
    camp=dict(z=(1.10,1.42),px=(0.5,0.5),py=(0.44,0.28),amp=12,fr=2.8),particles=None),"black",0.08),
 ("U20",1.7,"textcard",dict(text="快意年华",zf=0.72,zt=1.20,k=0.16),"zoomin",0.16),
 ("U21",3.2,"group",dict(kind="pullback",camp=dict(z=(1.10,0.74),px=(0.5,0.5),py=(0.4,0.55),k=0.2),dim=0.15),"dissolve",0.2),
 ("U22",7.27,"title",dict(),"black",0.10),   # 4.48 名义 + 2.79 补 xfade 重叠 → 全片 53.08s 收全曲
]

def build_unit(u):
    uid,dur,layout,pp,trans,tdur = u
    if layout=="single":
        p=compose_plate(BG(pp["bg"]),CHAR[pp["char"]],pp["fr"],os.path.join(PLATE,f"{uid}.png"))
        return render_single(uid,p,dur,pp["kind"],pp["camp"],
                             particles=pp.get("particles","pet"),name=pp.get("name"))
    if layout=="split2":
        return render_split2(uid,dur,pp["left"],pp["right"])
    if layout=="grid4":
        return render_grid4(uid,dur,pp["cells"])
    if layout=="textcard":
        return render_textcard(uid,dur,pp["text"],pp["zf"],pp["zt"],k=pp.get("k",0.22))
    if layout=="silhouette":
        p=compose_silhouette(BG(pp["bg"]),CHAR[pp["char"]],os.path.join(PLATE,f"{uid}.png"))
        return render_single(uid,p,dur,pp["kind"],pp["camp"],particles=None)
    if layout=="group":
        p=compose_group_plate(os.path.join(PLATE,f"{uid}.png"),dim=pp.get("dim",0.0))
        return render_single(uid,p,dur,pp["kind"],pp["camp"],particles="pet",letter=True)
    if layout=="title":
        return render_textcard(uid,dur,"",0.94,1.08,k=0.34,title=True)
    raise ValueError(layout)

# ---- xfade 转场名映射 ----
XF = {"black_in":None,"black":"fadeblack","white":"fadewhite","dissolve":"dissolve",
      "zoomin":"zoomin","hard":"fade","slide":"slideright"}
# hard 用极短 fade≈硬切; zoomin=缩放冲切(需较新 ffmpeg, ffmpeg-full 支持).

def build_all():
    for u in UNITS: build_unit(u)

def concat_xfade():
    clips=[os.path.join(UNIT,f"{u[0]}.mp4") for u in UNITS]
    durs=[u[1] for u in UNITS]; transs=[u[4] for u in UNITS]; tdurs=[u[5] for u in UNITS]
    inputs=[];
    for c in clips: inputs+=["-i",c]
    # U01 头部 fade-from-black 已由 xfade 无前驱, 单独 bake: 用 fade=in
    chain=[f"[0:v]fade=t=in:st=0:d={tdurs[0]},format=yuv420p[x0]"]
    prev="x0"; running=durs[0]
    for i in range(1,len(clips)):
        td=tdurs[i]; tr=XF.get(transs[i],"fade") or "fade"
        off=max(0.0,running-td)
        chain.append(f"[{i}:v]format=yuv420p[s{i}]")
        chain.append(f"[{prev}][s{i}]xfade=transition={tr}:duration={td}:offset={off:.3f}[x{i}]")
        prev=f"x{i}"; running=off+td+(durs[i]-td)
    chain.append(f"[{prev}]fade=t=out:st={max(0,running-2.6):.3f}:d=2.6[vout]")
    fc=";".join(chain)
    silent=os.path.join(OUT,"_v2_silent.mp4")
    _run([FF,"-y",*inputs,"-filter_complex",fc,"-map","[vout]",
          "-r",str(FPS),"-c:v","libx264","-pix_fmt","yuv420p","-crf","18",silent],"xfade")
    final=os.path.join(OUT,"MV_明月天涯_v2_1080x1920.mp4")
    _run([FF,"-y","-i",silent,"-i",WAV,"-af","loudnorm=I=-16:TP=-1.5:LRA=11",
          "-map","0:v","-map","1:a","-c:v","copy","-c:a","aac","-b:a","192k","-shortest",final],"mux")
    print(f"[final] -> {final}"); return final

if __name__=="__main__":
    arg=sys.argv[1] if len(sys.argv)>1 else "U01"
    if arg=="all": build_all(); concat_xfade()
    elif arg=="mux": concat_xfade()
    else: build_unit(next(u for u in UNITS if u[0]==arg))
