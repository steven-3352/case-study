#!/usr/bin/env python3
"""语音厅《明月天涯》立绘 MV — 素材预处理:
1. 裁立绘到 alpha bbox + 降采样(保留缩放余量)
2. 生成 5 张仙侠青绿背景(禁蓝紫,绿为主)
3. 生成滚动粒子场(花瓣 + 光斑,超高供竖向滚动)
"""
import os, math, random
from PIL import Image, ImageDraw, ImageFilter
Image.MAX_IMAGE_PIXELS = None
random.seed(20260721)

SRC = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SRC, "assets_build")
os.makedirs(OUT, exist_ok=True)
W, H = 1080, 1920

# ---------- 1. 立绘裁切 ----------
LIHUI = {"cy":"cy.png","nuolan":"诺兰.png","xuanheng":"轩珩.png","zhongli":"中里毅2.png"}
def trim_lihui():
    for key, fn in LIHUI.items():
        im = Image.open(os.path.join(SRC, fn)).convert("RGBA")
        bbox = im.split()[3].getbbox()
        im = im.crop(bbox)
        # 降采样到高度 <=2600(留缩放余量),宽按比例
        if im.height > 2600:
            r = 2600/im.height
            im = im.resize((max(1,int(im.width*r)), 2600), Image.LANCZOS)
        im.save(os.path.join(OUT, f"lihui_{key}.png"))
        print(f"lihui_{key}: {im.size}")

# ---------- 2. 背景(1296x2304 = 1.2x 给运镜余量) ----------
BW, BH = 1296, 2304
def vgrad(c_top, c_mid, c_bot):
    img = Image.new("RGB",(BW,BH))
    px = img.load()
    for y in range(BH):
        t = y/BH
        if t < 0.5:
            k=t/0.5; c=[int(c_top[i]+(c_mid[i]-c_top[i])*k) for i in range(3)]
        else:
            k=(t-0.5)/0.5; c=[int(c_mid[i]+(c_bot[i]-c_mid[i])*k) for i in range(3)]
        for x in range(BW): px[x,y]=tuple(c)
    return img

def add_bokeh(img, n, colors, rmin, rmax, amax):
    layer = Image.new("RGBA",(BW,BH),(0,0,0,0))
    d = ImageDraw.Draw(layer)
    for _ in range(n):
        x=random.randint(0,BW); y=random.randint(0,BH)
        r=random.randint(rmin,rmax); c=random.choice(colors)
        a=random.randint(amax//3,amax)
        d.ellipse([x-r,y-r,x+r,y+r], fill=(c[0],c[1],c[2],a))
    layer = layer.filter(ImageFilter.GaussianBlur(random.randint(8,18)))
    img = img.convert("RGBA"); img.alpha_composite(layer); return img.convert("RGB")

def radial_glow(img, cx, cy, rad, color, strength):
    glow = Image.new("RGBA",(BW,BH),(0,0,0,0))
    d=ImageDraw.Draw(glow)
    d.ellipse([cx-rad,cy-rad,cx+rad,cy+rad], fill=(color[0],color[1],color[2],strength))
    glow=glow.filter(ImageFilter.GaussianBlur(180))
    img=img.convert("RGBA"); img.alpha_composite(glow); return img.convert("RGB")

def vignette(img):
    v=Image.new("L",(BW,BH),0); d=ImageDraw.Draw(v)
    d.ellipse([-BW*0.25,-BH*0.15,BW*1.25,BH*1.15], fill=255)
    v=v.filter(ImageFilter.GaussianBlur(220))
    black=Image.new("RGB",(BW,BH),(0,0,0))
    return Image.composite(img,black,v)

BGS = {
    "bamboo_bright": dict(g=[(28,58,40),(58,102,66),(30,54,38)],
        bokeh=([(150,200,120),(210,230,150),(120,170,90)],46,20,120,120),
        glow=(BW//2,int(BH*0.32),620,(140,190,110),90)),
    "courtyard_warm": dict(g=[(34,50,34),(74,90,52),(30,44,30)],
        bokeh=([(210,180,110),(230,200,140),(150,170,90)],40,24,130,120),
        glow=(int(BW*0.6),int(BH*0.3),640,(200,170,110),95)),
    "mist_cool": dict(g=[(40,54,48),(92,108,98),(44,56,50)],
        bokeh=([(210,225,215),(180,205,190),(150,180,165)],52,18,100,110),
        glow=(int(BW*0.4),int(BH*0.28),700,(200,220,210),100)),
    "floral_warm": dict(g=[(36,52,38),(88,96,60),(40,50,36)],
        bokeh=([(220,170,130),(230,200,150),(160,180,100),(210,150,140)],44,22,120,120),
        glow=(int(BW*0.5),int(BH*0.3),640,(215,180,130),95)),
    "riverside_night": dict(g=[(14,30,26),(30,58,48),(12,26,22)],
        bokeh=([(90,150,120),(140,190,150),(110,160,120)],38,20,110,110),
        glow=(int(BW*0.55),int(BH*0.34),560,(90,150,110),85)),
}
def build_bgs():
    for name,cfg in BGS.items():
        img=vgrad(*cfg["g"])
        img=radial_glow(img,*cfg["glow"])
        bk=cfg["bokeh"]; img=add_bokeh(img,bk[1],bk[0],bk[2],bk[3],bk[4])
        img=img.filter(ImageFilter.GaussianBlur(6))
        img=vignette(img)
        img.save(os.path.join(OUT,f"bg_{name}.png")); print(f"bg_{name}: {img.size}")

# ---------- 3. 粒子场(1080 x 3840,竖向滚动) ----------
PW,PH=1080,3840
def petal_shape(d,x,y,s,ang,col,a):
    # 简单花瓣:旋转椭圆
    petal=Image.new("RGBA",(s*2,s*2),(0,0,0,0))
    pd=ImageDraw.Draw(petal)
    pd.ellipse([s*0.6,0,s*1.4,s*2],fill=(col[0],col[1],col[2],a))
    petal=petal.rotate(ang,expand=True)
    return petal
def build_particles():
    # 花瓣层
    pet=Image.new("RGBA",(PW,PH),(0,0,0,0))
    for _ in range(150):
        x=random.randint(0,PW); y=random.randint(0,PH)
        s=random.randint(6,16); ang=random.randint(0,360)
        col=random.choice([(255,225,230),(255,240,235),(245,220,225),(255,235,215)])
        a=random.randint(70,160)
        sp=petal_shape(None,x,y,s,ang,col,a)
        pet.alpha_composite(sp,(x,y))
    pet=pet.filter(ImageFilter.GaussianBlur(0.6))
    pet.save(os.path.join(OUT,"particles_petals.png")); print("petals:",pet.size)
    # 光斑层(散景上浮)
    bok=Image.new("RGBA",(PW,PH),(0,0,0,0)); d=ImageDraw.Draw(bok)
    for _ in range(90):
        x=random.randint(0,PW); y=random.randint(0,PH); r=random.randint(8,34)
        col=random.choice([(210,230,160),(230,240,190),(180,210,140),(240,225,170)])
        a=random.randint(40,110)
        d.ellipse([x-r,y-r,x+r,y+r],fill=(col[0],col[1],col[2],a))
    bok=bok.filter(ImageFilter.GaussianBlur(5))
    bok.save(os.path.join(OUT,"particles_bokeh.png")); print("bokeh:",bok.size)

if __name__=="__main__":
    trim_lihui(); build_bgs(); build_particles()
    print("DONE ->",OUT)
