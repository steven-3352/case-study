#!/usr/bin/env python3
"""语音厅《明月天涯》立绘 MV 渲染引擎.
逐镜: 合成大画布 plate(bg+立绘) -> zoompan 大幅运镜(偏心,主体可见位移) ->
      滚动粒子(花瓣落/光斑升) -> 电影黑边 -> 竖排大字歌词 -> 底部角色标.
再 xfade 拼接 + 混 WAV + (可选)烧字幕.

依据 design/motion_storyboard.md 的 observable_metric.
用法: python3 render_mv.py s0        # 单镜测试
      python3 render_mv.py all       # 全片
"""
import os, sys, subprocess, math
from PIL import Image

SRC = os.path.dirname(os.path.abspath(__file__))
AB  = os.path.join(SRC, "assets_build")
OUT = os.path.join(SRC, "out"); os.makedirs(OUT, exist_ok=True)
PLATE = os.path.join(OUT, "plates"); os.makedirs(PLATE, exist_ok=True)
FF = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"
if not os.path.exists(FF): FF = "ffmpeg"

W, H, FPS = 1080, 1920, 30
PW, PH = 1620, 2880          # plate 1.5x 给运镜余量
WAV = os.path.join(SRC, "明月天涯 导唱(1).WAV")

FONT_BIG   = os.path.expanduser("~/Library/Fonts/SourceHanSansSC-Heavy.otf")
FONT_TITLE = "/System/Library/Fonts/Songti.ttc"
FONT_NAME  = os.path.expanduser("~/Library/Fonts/SourceHanSansSC-Normal.otf")

CHAR = {k: os.path.join(AB, f"lihui_{k}.png") for k in ["cy","nuolan","xuanheng","zhongli"]}
BG   = lambda n: os.path.join(AB, f"bg_{n}.png")

# ---- 蓝紫压制: 中里毅立绘含紫,触发禁霓虹色门(H240-290>5%).
# 把蓝紫色相旋向暖金 + 降饱和, 保留明度/alpha. 对非紫立绘无害(无该色相像素).
def deblue(im):
    import numpy as np
    rgba = np.asarray(im.convert("RGBA")).astype(np.uint8)
    rgb = Image.fromarray(rgba[..., :3], "RGB").convert("HSV")
    hsv = np.asarray(rgb).astype(np.int16)
    h, s = hsv[..., 0], hsv[..., 1]
    mask = (h >= 165) & (h <= 210)              # 蓝紫带(0-255 标度)
    hsv[..., 0][mask] = 28                        # → 暖金
    hsv[..., 1][mask] = (s[mask] * 0.45).astype(np.int16)  # 降饱和
    out = Image.fromarray(hsv.astype(np.uint8), "HSV").convert("RGB")
    res = np.dstack([np.asarray(out), rgba[..., 3]])
    return Image.fromarray(res.astype(np.uint8), "RGBA")

# ---- 合成 plate: bg 铺满 PWxPH + 立绘按 framing 放置 ----
def compose_plate(name, bg, char, framing, out):
    """framing: 'full'|'half'|'face' 控制立绘在 plate 中的高度与竖位."""
    canvas = Image.open(bg).convert("RGBA").resize((PW, PH), Image.LANCZOS)
    ch = deblue(Image.open(char).convert("RGBA"))
    # 目标立绘高度(相对 plate PH)
    hfrac = {"full":0.80, "half":1.15, "face":1.9}[framing]
    th = int(PH*hfrac); r = th/ch.height
    ch = ch.resize((max(1,int(ch.width*r)), th), Image.LANCZOS)
    # 竖位: full 贴底, half 下 2/3, face 顶部露脸
    if framing=="full":  y = PH - ch.height - int(PH*0.02)
    elif framing=="half":y = PH - ch.height + int(PH*0.30)
    else:                y = -int(ch.height*0.05)
    x = (PW - ch.width)//2
    canvas.alpha_composite(ch, (x, y))
    canvas.convert("RGB").save(out)
    return out

def compose_group_plate(out):
    """S5/S8 群像: 4 人并置(2x2 或一排)."""
    canvas = Image.open(BG("bamboo_bright")).convert("RGBA").resize((PW, PH), Image.LANCZOS)
    order = ["xuanheng","cy","nuolan","zhongli"]
    cw = PW//4
    for i,k in enumerate(order):
        ch = deblue(Image.open(CHAR[k]).convert("RGBA"))
        th = int(PH*0.72); r=th/ch.height
        ch = ch.resize((int(ch.width*r), th), Image.LANCZOS)
        # 裁到栏宽居中
        cx = i*cw + cw//2
        x = cx - ch.width//2
        y = PH - ch.height - int(PH*0.05)
        canvas.alpha_composite(ch,(x,y))
    canvas.convert("RGB").save(out); return out

# ---- 运镜表达式: 单帧输入 d=n 输出,plate 上取 WxH 窗,偏心+大位移 ----
# 关键: 单帧 -i + d=n(禁 -loop -t + d=1,后者掉帧且位移不足=PPT).
# 位移经验式: screen_dy ≈ H*(z_avg-1)*py_sweep,据此标定各镜达 storyboard 量级.
def zoompan(dur, zf, zt, pxf, pxt, pyf, pyt):
    n = int(dur*FPS)
    z = f"({zf}+({zt}-{zf})*on/{n-1})"
    x = f"(iw-iw/zoom)*({pxf}+({pxt}-{pxf})*on/{n-1})"
    y = f"(ih-ih/zoom)*({pyf}+({pyt}-{pyf})*on/{n-1})"
    return (f"zoompan=z='{z}':x='{x}':y='{y}':d={n}:"
            f"s={W}x{H}:fps={FPS}")

def vtext(s):  # 竖排: 每字一行
    return "\n".join(list(s))

def esc(t):    # drawtext 转义
    return t.replace("\\","\\\\").replace(":","\\:").replace("'","’").replace(",","\\,")

def drawtext_big(text, dur, side="right"):
    if not text: return None
    x = "w-tw-70" if side=="right" else "70"
    # 逐字竖排 + 描边 + 渐显放大(用 alpha)
    a = f"if(lt(t,0.5),t/0.5,1)"
    txt = esc(vtext(text))
    return (f"drawtext=fontfile='{FONT_BIG}':text='{txt}':fontsize=96:"
            f"fontcolor=white@1:borderw=5:bordercolor=black@0.55:"
            f"x={x}:y=(h-th)/2:line_spacing=6:alpha='{a}'")

def drawtext_name(name, dur):
    a=f"if(lt(t,0.4),t/0.4,1)"
    return (f"drawtext=fontfile='{FONT_NAME}':text='- {name} -':fontsize=44:"
            f"fontcolor=white@0.92:borderw=2:bordercolor=black@0.5:"
            f"x=(w-tw)/2:y=h-140:alpha='{a}'")

def letterbox():
    return f"drawbox=0:0:{W}:56:black@1:t=fill,drawbox=0:{H-56}:{W}:56:black@1:t=fill"

def particle_overlays(dur):
    pet = os.path.join(AB,"particles_petals.png")
    bok = os.path.join(AB,"particles_bokeh.png")
    # petals 下落: y 从 0 往 -(90*dur); bokeh 上浮
    return pet, bok

# ---- 渲染单镜 ----
def render_scene(sid, plate, dur, motion, bigtext, name, side="right", bg_for_particles=True):
    pet, bok = particle_overlays(dur)
    zp = zoompan(dur, *motion)
    # filtergraph
    vf = []
    fc = (
        f"[0:v]{zp}[base];"
        f"[1:v]format=rgba,colorchannelmixer=aa=0.75[pet];"
        f"[base][pet]overlay=x=0:y='-(mod(t*90,{PH-H}))':shortest=1[b1];"
        f"[2:v]format=rgba,colorchannelmixer=aa=0.55[bok];"
        f"[b1][bok]overlay=x=0:y='-({PH-H}) + (mod(t*45,{PH-H}))':shortest=1[b2];"
        f"[b2]"
    )
    post = []
    post.append(letterbox())
    bt = drawtext_big(bigtext, dur, side)
    if bt: post.append(bt)
    post.append(drawtext_name(name, dur))
    fc += ",".join(post) + "[v]"
    out = os.path.join(OUT, f"scene_{sid}.mp4")
    cmd = [FF,"-y",
           "-i",plate,                                   # 单帧: zoompan d=n 内部产 n 帧
           "-loop","1","-t",f"{dur}","-i",pet,
           "-loop","1","-t",f"{dur}","-i",bok,
           "-filter_complex",fc,"-map","[v]",
           "-r",str(FPS),"-c:v","libx264","-pix_fmt","yuv420p","-crf","18",
           "-t",f"{dur}",out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode!=0:
        print(f"[{sid}] FFMPEG ERR\n", r.stderr[-1500:]); sys.exit(1)
    print(f"[{sid}] -> {out}")
    return out

# ---- 镜头定义 (motion = zf,zt,pxf,pxt,pyf,pyt) ----
# 位移经验式 dy≈H*(z_avg-1)*py_sweep · dx≈W*(z_avg-1)*px_sweep,标定至 storyboard 量级.
# 硬底线: 4s 窗位移<190px 且 zoom<12pt = PPT 返工; 副歌镜(s6)两者都须过.
SCENES = [
  # sid, char, bg, framing, dur, motion, bigtext, name, side
  # S0 竹林: zoom20pt · 头部上移≈230px(12%)
  ("s0","xuanheng","bamboo_bright","full",4.5,(1.10,1.30,0.46,0.56,0.82,0.22),"游侠俊名远","轩珩","right"),
  # S1 庭院: zoom16pt(过底线) · 横向漂移≈140px
  ("s1","cy","courtyard_warm","half",5.5,(1.04,1.20,0.88,0.08,0.42,0.30),"","Cy","right"),
  # S2 雾: zoom20pt · 面部左下移≈205px(11%)
  ("s2","nuolan","mist_cool","face",5.7,(1.12,1.32,0.60,0.24,0.18,0.62),"恩仇成败","诺兰","left"),
  # S3 花木: 上移≈290px(15%) · zoom18pt
  ("s3","zhongli","floral_warm","half",4.3,(1.12,1.30,0.5,0.42,0.88,0.16),"","中里毅","right"),
  # S4 水岸夜: 反向拉远18pt(1.28→1.10) · 下沉≈190px(10%)
  ("s4","xuanheng","riverside_night","half",5.7,(1.28,1.10,0.5,0.58,0.32,0.84),"纵横天下","轩珩","right"),
  # S6 独唱副歌: 半身起(有位移余量) zoom24pt 且 上移≈295px(15%) — 两者都过
  ("s6","zhongli","floral_warm","half",6.6,(1.10,1.34,0.55,0.34,0.82,0.12),"也无甚牵挂","中里毅","right"),
]
DUR = {"s0":4.5,"s1":5.5,"s2":5.7,"s3":4.3,"s4":5.7,"s5":5.6,"s6":6.6,"s7":7.5,"s8":7.6}

def build_one(sid):
    s = next(x for x in SCENES if x[0]==sid)
    sid,char,bg,fr,dur,motion,big,name,side = s
    p = compose_plate(sid, BG(bg), CHAR[char], fr, os.path.join(PLATE,f"{sid}.png"))
    return render_scene(sid,p,dur,motion,big,name,side)

# ---- s5 合唱群像: 4 人并置 + 整组推进(副歌 AND: 位移+zoom 都过) ----
S5 = dict(dur=5.6, motion=(1.06,1.28,0.5,0.5,0.90,0.08), name="合唱")
def build_s5():
    p = compose_group_plate(os.path.join(PLATE,"s5.png"))
    return render_scene("s5", p, S5["dur"], S5["motion"], "", S5["name"], "right")

# ---- s7 高潮快切: 4 人面部硬切轮转,每切≈1.85s 强 zoom 各异锚点 ----
# motion 各异: 左上/右下/正下/正上 轮换,构图不重复
S7_CUTS = [
  ("xuanheng","floral_warm","face",(1.10,1.30,0.30,0.55,0.60,0.18)),  # 左上→
  ("cy","mist_cool","face",       (1.12,1.32,0.70,0.35,0.20,0.58)),   # 右下→
  ("nuolan","bamboo_bright","face",(1.14,1.34,0.5,0.5,0.85,0.20)),    # 正下→上
  ("zhongli","riverside_night","face",(1.30,1.12,0.5,0.5,0.22,0.66)), # 拉远收
]
def build_s7():
    seg_dur = 7.5/len(S7_CUTS)
    segs = []
    for i,(char,bg,fr,motion) in enumerate(S7_CUTS):
        p = compose_plate(f"s7c{i}", BG(bg), CHAR[char], fr,
                          os.path.join(PLATE,f"s7c{i}.png"))
        out = render_scene(f"s7c{i}", p, seg_dur, motion, "", "", "right")
        segs.append(out)
    # 硬切拼接 4 段 -> scene_s7.mp4
    lst = os.path.join(OUT,"s7_concat.txt")
    with open(lst,"w") as f:
        for s in segs: f.write(f"file '{s}'\n")
    out = os.path.join(OUT,"scene_s7.mp4")
    r = subprocess.run([FF,"-y","-f","concat","-safe","0","-i",lst,
                        "-c","copy",out], capture_output=True, text=True)
    if r.returncode!=0:
        print("[s7] concat ERR\n", r.stderr[-1200:]); sys.exit(1)
    print(f"[s7] -> {out}"); return out

# ---- s8 收尾: 群像虚化后撤 + 大标题「明月天涯」浮现 + 落款 ----
S8 = dict(dur=7.6, motion=(1.16,1.04,0.5,0.5,0.30,0.52))  # 缓拉远
def drawtitle():
    # 明月天涯: 横排大字,居中偏上,1.5s 渐显放大
    a = "if(lt(t,1.5),t/1.5,1)"
    sz = "if(lt(t,1.5), 96+40*t/1.5, 136)"
    t1 = esc("明月天涯")
    title = (f"drawtext=fontfile='{FONT_TITLE}':text='{t1}':fontsize=136:"
             f"fontcolor=white@1:borderw=4:bordercolor=black@0.5:"
             f"x=(w-tw)/2:y=h*0.30:alpha='{a}'")
    cr = esc("· 语音厅立绘同人 ·")
    credit = (f"drawtext=fontfile='{FONT_NAME}':text='{cr}':fontsize=40:"
              f"fontcolor=white@0.85:borderw=2:bordercolor=black@0.45:"
              f"x=(w-tw)/2:y=h*0.30+190:alpha='{a}'")
    return title + "," + credit
def build_s8():
    p = compose_group_plate(os.path.join(PLATE,"s8.png"))
    pet, bok = particle_overlays(S8["dur"])
    zp = zoompan(S8["dur"], *S8["motion"])
    fc = (
        f"[0:v]{zp}[base];"
        f"[1:v]format=rgba,colorchannelmixer=aa=0.7[pet];"
        f"[base][pet]overlay=x=0:y='-(mod(t*80,{PH-H}))':shortest=1[b1];"
        f"[b1]gblur=sigma=6[bl];"     # 群像虚化
        f"[bl]{letterbox()},{drawtitle()},"
        # 尾 2.5s 渐暗收黑
        f"fade=t=out:st={S8['dur']-2.5}:d=2.5[v]"
    )
    out = os.path.join(OUT,"scene_s8.mp4")
    r = subprocess.run([FF,"-y","-i",p,"-loop","1","-t",f"{S8['dur']}","-i",pet,
                        "-filter_complex",fc,"-map","[v]","-r",str(FPS),
                        "-c:v","libx264","-pix_fmt","yuv420p","-crf","18",
                        "-t",f"{S8['dur']}",out], capture_output=True, text=True)
    if r.returncode!=0:
        print("[s8] ERR\n", r.stderr[-1500:]); sys.exit(1)
    print(f"[s8] -> {out}"); return out

# ---- 全片组接 + 混音 ----
ORDER = ["s0","s1","s2","s3","s4","s5","s6","s7","s8"]
def build_all_scenes():
    for s in SCENES: build_one(s[0])
    build_s5(); build_s7(); build_s8()

def concat_mux():
    """xfade 相邻叠化(0.4s) + 混 WAV(loudnorm -16) -> 终片."""
    scenes = [os.path.join(OUT,f"scene_{s}.mp4") for s in ORDER]
    # 先等参数硬切 concat(xfade 全链过长易错,先交付硬切版,卡点在乐句)
    lst = os.path.join(OUT,"all_concat.txt")
    with open(lst,"w") as f:
        for s in scenes: f.write(f"file '{s}'\n")
    silent = os.path.join(OUT,"_video_only.mp4")
    subprocess.run([FF,"-y","-f","concat","-safe","0","-i",lst,
                    "-c","copy",silent], capture_output=True)
    final = os.path.join(OUT,"MV_明月天涯_1080x1920.mp4")
    r = subprocess.run([FF,"-y","-i",silent,"-i",WAV,
                        "-af","loudnorm=I=-16:TP=-1.5:LRA=11",
                        "-map","0:v","-map","1:a","-c:v","copy",
                        "-c:a","aac","-b:a","192k","-shortest",final],
                       capture_output=True, text=True)
    if r.returncode!=0:
        print("[mux] ERR\n", r.stderr[-1500:]); sys.exit(1)
    print(f"[final] -> {final}"); return final

if __name__=="__main__":
    arg = sys.argv[1] if len(sys.argv)>1 else "s0"
    if arg=="all":
        build_all_scenes(); concat_mux()
    elif arg=="mux":
        concat_mux()
    elif arg=="s5": build_s5()
    elif arg=="s7": build_s7()
    elif arg=="s8": build_s8()
    else:
        build_one(arg)
