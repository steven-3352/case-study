#!/usr/bin/env python3
"""P001 发布物渲染：MP4 视频 + 图文 PNG.

用法:
  python3 pipeline/render_p001.py --all
  python3 pipeline/render_p001.py --video douyin xhs channels
  python3 pipeline/render_p001.py --carousel douyin xhs-story xhs-howto channels

输出（可直接上传）:
  publish/P001/{platform}/video.mp4
  publish/P001/{platform}/carousel/*.png
"""
from __future__ import annotations

import argparse
import base64
import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pipeline.screen_dims import CANVAS_H, CANVAS_W, VIDEO_H, VIDEO_W

PUB = ROOT / "publish" / "P001"
SL = ROOT / "slides"
SHOTS = ROOT / "assets" / "shots"
EVID = ROOT / "assets" / "broll" / "generated"
TMP = PUB / "_tmp"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
FONT_SRC = "/System/Library/Fonts/STHeiti Medium.ttc"
EDGE = str(ROOT / ".venv" / "bin" / "edge-tts")
VOICE = "zh-CN-YunjianNeural"
RATE, PITCH, VOL = "+15%", "-2Hz", "-2%"
PAD, FADE = 0.35, 0.25
CW, CH = CANVAS_W, CANVAS_H  # 图文 9:16
VW, VH = VIDEO_W, VIDEO_H  # 视频 9:16（与图文同尺寸）

VIDEO_FRAME_CSS = f"""
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{width:{VW}px;height:{VH}px;overflow:hidden;background:#0b0d10;}}
body{{position:relative;}}
.bg{{width:100%;height:100%;object-fit:fill;display:block;}}
.sub{{position:absolute;left:0;right:0;bottom:0;padding:28px 36px 56px;text-align:center;
  background:linear-gradient(180deg,rgba(11,13,16,0) 0%,rgba(11,13,16,.88) 45%,rgba(11,13,16,.95) 100%);
  font-family:"Hiragino Sans GB","STHeiti",sans-serif;font-size:40px;font-weight:700;line-height:1.35;
  color:#fff;text-shadow:0 2px 10px rgba(0,0,0,.9);}}
"""

CAROUSEL_CSS = f"""
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{width:{CW}px;height:{CH}px;}}
body{{font-family:"Hiragino Sans GB","STHeiti",sans-serif;background:#f5f2eb;color:#1a1a1a;}}
.card{{width:{CW}px;height:{CH}px;padding:72px 64px;display:flex;flex-direction:column;}}
.tag{{font-size:28px;color:#8a7a62;letter-spacing:.08em;margin-bottom:24px;}}
.title{{font-size:54px;font-weight:800;line-height:1.35;margin-bottom:28px;}}
.sub{{font-size:34px;color:#444;line-height:1.55;}}
.body{{font-size:36px;color:#333;line-height:1.65;flex:1;display:flex;align-items:center;}}
.img-wrap{{flex:1;display:flex;align-items:center;justify-content:center;margin:20px 0;}}
.img-wrap img{{max-width:920px;max-height:1200px;border-radius:20px;box-shadow:0 16px 48px rgba(0,0,0,.12);}}
.dual{{display:flex;gap:28px;justify-content:center;align-items:center;flex:1;}}
.dual img{{width:420px;border-radius:16px;box-shadow:0 12px 36px rgba(0,0,0,.1);}}
.foot{{font-size:26px;color:#999;margin-top:auto;padding-top:24px;border-top:1px solid #e0dcd3;}}
.center{{justify-content:center;text-align:center;}}
"""

BROLL = {
    "BR001": SL / "shot_pages.png",
    "BR002": SHOTS / "success.png",
    "BR003": SL / "slide_03.png",
    "BR004": SL / "slide_07.png",
    "BR006": SL / "slide_06.png",
    "BR007": SL / "shot_pins.png",
}


def b64(p: pathlib.Path) -> str:
    return base64.b64encode(p.read_bytes()).decode()


def img_src(p: pathlib.Path) -> str:
    return f"data:image/png;base64,{b64(p)}"


def dur(path: pathlib.Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return float(json.loads(out)["format"]["duration"])


def composite_video_frame(img: pathlib.Path, subtitle: str, out: pathlib.Path) -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{VIDEO_FRAME_CSS}</style></head>
<body><img class="bg" src="{img_src(img)}"><div class="sub">{subtitle}</div></body></html>"""
    chrome_shot(html, out, VW, VH)


def render_video_segment(img: pathlib.Path, aud: pathlib.Path, subtitle: str, seg: pathlib.Path, frame: pathlib.Path) -> float:
    composite_video_frame(img, subtitle, frame)
    d = dur(aud) + PAD
    vf = f"scale={VW}:{VH},fps=30,format=yuv420p,fade=t=in:st=0:d={FADE},fade=t=out:st={d - FADE:.2f}:d={FADE}"
    af = f"apad,afade=t=out:st={d - 0.35:.2f}:d=0.3"
    subprocess.run(
        [
            "ffmpeg", "-y", "-loop", "1", "-i", str(frame), "-i", str(aud),
            "-filter_complex", f"[0:v]{vf}[v];[1:a]{af}[a]",
            "-map", "[v]", "-map", "[a]", "-t", f"{d:.2f}",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-pix_fmt", "yuv420p", str(seg),
        ],
        capture_output=True,
        check=True,
    )
    return d


def chrome_shot(html: str, out: pathlib.Path, w: int, h: int) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html)
        path = f.name
    subprocess.run(
        [
            CHROME,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            f"--screenshot={out}",
            f"--window-size={w},{h}",
            "--force-device-scale-factor=1",
            f"file://{path}",
        ],
        capture_output=True,
        timeout=120,
        check=True,
    )


def render_text_card(title: str, sub: str = "", tag: str = "真实项目 · P001") -> str:
    sub_html = f'<div class="sub">{sub}</div>' if sub else ""
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CAROUSEL_CSS}</style></head>
<body><div class="card center"><div class="tag">{tag}</div>
<div class="body"><div><div class="title">{title}</div>{sub_html}</div></div>
<div class="foot">备忘录风 · 真实截图</div></div></body></html>"""


def render_image_card(title: str, img_path: pathlib.Path, caption: str = "") -> str:
    cap = f'<div class="sub" style="margin-top:20px;text-align:center">{caption}</div>' if caption else ""
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CAROUSEL_CSS}</style></head>
<body><div class="card"><div class="tag">真实项目 · P001</div>
<div class="title">{title}</div>
<div class="img-wrap"><img src="{img_src(img_path)}"></div>{cap}
<div class="foot">项目实拍 · 非样机</div></div></body></html>"""


def render_dual_card(title: str, left: pathlib.Path, right: pathlib.Path) -> str:
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CAROUSEL_CSS}</style></head>
<body><div class="card"><div class="tag">真实项目 · P001</div>
<div class="title">{title}</div>
<div class="dual"><img src="{img_src(left)}"><img src="{img_src(right)}"></div>
<div class="foot">项目实拍 · 非样机</div></div></body></html>"""


def tts(text: str, out: pathlib.Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [EDGE, "--voice", VOICE, "--rate", RATE, "--pitch", PITCH, "--volume", VOL, "--text", text, "--write-media", str(out)],
        check=True,
        capture_output=True,
        text=True,
    )


def concat_segments(segs: list[pathlib.Path], out: pathlib.Path) -> None:
    lst = TMP / f"list_{out.stem}.txt"
    lst.write_text("".join(f"file '{s}'\n" for s in segs), encoding="utf-8")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-c:a", "aac", "-b:a", "160k", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)],
        capture_output=True,
        check=True,
    )


VIDEO_SPECS: dict[str, list[tuple[pathlib.Path, str, str]]] = {
    "douyin": [
        (EVID / "BR004_analytics_annotated.png", "第五天一看数据，我傻眼了。", "第5天，我傻眼了"),
        (EVID / "BR001_safari_landing.png", "帮海外小品牌，一天搭完落地页收邮箱和自动邮件，预算几乎为零。", "一天全链路上线"),
        (EVID / "STACK_submit_welcome.png", "留资秒发欢迎信，后面邮件全自动跑。", "邮件全自动"),
        (EVID / "BR004_day5_tagged.png", "结果第五天，曝光有了，留资寥寥无几。问题不在系统，在内容。", "曝光有，留资少"),
        (EVID / "BR006_ai_vs_manual.png", "改成AI只出背景，文字自己排。你们会先搞系统还是先搞内容？", "系统 vs 内容？"),
    ],
    "xhs": [
        (EVID / "BR004_analytics_annotated.png", "第五天一看数据，我傻眼了。", "第5天，我傻眼了"),
        (EVID / "MEMO01_background.png", "做了二十年互联网，我还是会在这事上翻车。这是我自己做的一个项目：帮一个海外小品牌，从0搭一套自己会跑的获客系统。要求挺离谱——没人天天盯，预算几乎为零，还得能看数据。", "海外小品牌 · 零预算"),
        (EVID / "BR001_safari_landing.png", "我赌了一把，一天搞定。上午落地页，中午接邮箱，下午自动邮件和埋点，傍晚出内容，全链路上线。当时觉得，行，可以躺了。", "一天全链路上线"),
        (EVID / "STACK_submit_welcome.png", "留资秒发欢迎信，后面序列自动跑，不用人盯。", "邮件全自动"),
        (EVID / "BR004_day5_tagged.png", "结果第五天，曝光有了，留资的人寥寥无几。", "曝光有，留资少"),
        (EVID / "BR006_ai_vs_manual.png", "复盘下来，问题不在系统，在内容太机器。AI一键出的图谁都刷过，没人停。后来改成AI只出背景，文字自己排，才像活人发的。", "内容得像人"),
        (EVID / "MEMO02_cta.png", "系统能跑，内容得先像人。你们会先搞系统还是先搞内容？我当初选反了。", "系统 vs 内容？"),
    ],
    "channels": [
        (EVID / "BR004_analytics_annotated.png", "分享一个邮件获客项目复盘：一天搭完，第五天踩坑。", "项目复盘"),
        (EVID / "MEMO01_background.png", "海外小品牌，没人盯、预算紧，我用免费工具拼了一套获客链路。", "零预算获客"),
        (EVID / "STACK_submit_welcome.png", "落地页、表单、欢迎信、定时养熟，全链路上线。", "邮件全自动"),
        (EVID / "BR004_day5_tagged.png", "第五天看数据，曝光有了，留资不多。复盘是内容太像机器批量出的。", "内容得像人"),
        (EVID / "MEMO02_cta.png", "系统能跑，内容得先像人。也在做类似小系统的，评论区交流。", "欢迎交流"),
    ],
}

CAROUSEL_SPECS: dict[str, list[tuple[str, dict]]] = {
    "xhs-howto": [
        ("01", {"type": "image", "title": "几乎不写后端，怎么搭邮件获客", "img": BROLL["BR001"]}),
        ("02", {"type": "text", "title": "一句话链路", "sub": "内容 → 引流 → 留邮箱 → 自动邮件 → 看数据"}),
        ("03", {"type": "image", "title": "落地页：几秒讲清，表单免服务器", "img": BROLL["BR001"]}),
        ("04", {"type": "image", "title": "邮件：欢迎信 + 定时养熟 + 退订剔除", "img": BROLL["BR003"]}),
        ("05", {"type": "image", "title": "内容：AI出背景，人排版", "img": BROLL["BR006"]}),
        ("06", {"type": "image", "title": "数据：每步打点，好的加产差的砍", "img": BROLL["BR004"]}),
        ("07", {"type": "text", "title": "月成本≈0", "sub": "静态页、表单、邮件、定时任务，先用各家免费额度拼起来"}),
        ("08", {"type": "text", "title": "哪块想细看？评论区说"}),
    ],
}

ROUTE1_CAROUSEL = {"xhs-story", "douyin", "channels"}

CAROUSEL_OUT: dict[str, pathlib.Path] = {
    "douyin": PUB / "douyin" / "carousel",
    "xhs-story": PUB / "xhs" / "carousel_story",
    "xhs-howto": PUB / "xhs" / "carousel_howto",
    "channels": PUB / "channels" / "carousel",
}


def render_carousel(key: str) -> None:
    if key in ROUTE1_CAROUSEL:
        subprocess.run(
            [sys.executable, str(ROOT / "pipeline" / "render_route1_carousel.py"), key],
            check=True,
        )
        return
    out_dir = CAROUSEL_OUT[key]
    out_dir.mkdir(parents=True, exist_ok=True)
    for num, spec in CAROUSEL_SPECS[key]:
        out = out_dir / f"{num}.png"
        t = spec["type"]
        if t == "text":
            html = render_text_card(spec["title"], spec.get("sub", ""))
        elif t == "image":
            html = render_image_card(spec["title"], spec["img"])
        elif t == "dual":
            html = render_dual_card(spec["title"], spec["left"], spec["right"])
        else:
            raise ValueError(t)
        chrome_shot(html, out, CW, CH)
        print(f"  carousel {key}/{num}.png")


def render_video(platform: str) -> None:
    subprocess.run([sys.executable, str(ROOT / "pipeline" / "gen_evidence.py")], check=True)
    plat_dir = {"douyin": PUB / "douyin", "xhs": PUB / "xhs", "channels": PUB / "channels"}[platform]
    out = plat_dir / "video.mp4"
    segs: list[pathlib.Path] = []
    total = 0.0
    for i, (img, text, sub) in enumerate(VIDEO_SPECS[platform]):
        aud = TMP / f"{platform}_a_{i:02d}.mp3"
        seg = TMP / f"{platform}_seg_{i:02d}.mp4"
        frame = TMP / f"{platform}_frame_{i:02d}.png"
        tts(text, aud)
        d = render_video_segment(img, aud, sub, seg, frame)
        total += d
        segs.append(seg)
        print(f"  {platform} seg{i}: {d:.1f}s · {img.name}")
    concat_segments(segs, out)
    print(f"  ✓ {platform}/video.mp4 · {dur(out):.1f}s")


def main() -> None:
    ap = argparse.ArgumentParser(description="P001 发布物渲染")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--video", nargs="*", choices=["douyin", "xhs", "channels"])
    ap.add_argument("--carousel", nargs="*", choices=list(CAROUSEL_SPECS))
    args = ap.parse_args()

    if not (args.all or args.video or args.carousel):
        ap.print_help()
        sys.exit(1)

    TMP.mkdir(parents=True, exist_ok=True)

    videos = args.video or (["douyin", "xhs", "channels"] if args.all else [])
    carousels = args.carousel or (list(CAROUSEL_SPECS) if args.all else [])

    for c in carousels:
        print(f"[carousel] {c}")
        render_carousel(c)

    for v in videos:
        print(f"[video] {v}")
        render_video(v)

    print("\n完成。发布物：")
    for v in videos:
        print(f"  publish/P001/{v}/video.mp4")
    for c in carousels:
        print(f"  publish/P001/.../{CAROUSEL_OUT[c].name}/*.png")


if __name__ == "__main__":
    main()
