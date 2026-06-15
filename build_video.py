#!/usr/bin/env python3
"""Build narrated 9:16 MP4: slides + real-screenshot showcase frames,
Edge neural TTS voiceover, background music. Faster pace.
Run: python3 build_video.py   Output: out/case_study_narrated.mp4
"""
import subprocess, pathlib, json

ROOT = pathlib.Path(__file__).resolve().parent
SL = ROOT / "slides"; TMP = ROOT / "out" / "_seg"; OUT = ROOT / "out"
TMP.mkdir(parents=True, exist_ok=True)
VOICE = "zh-CN-XiaoxiaoNeural"
RATE = "+22%"        # 更快节奏
PAD = 0.35           # 每段旁白后停顿(更短=更快)
FADE = 0.25
EDGE = str(ROOT / ".venv" / "bin" / "edge-tts")
MUSIC = ROOT / "我曾经的丫头.mp3"
MUSIC_VOL = 0.12     # 背景音乐音量(人声为 1.0)

# 顺序 = (图片名, 旁白)。在 05 后插真实页面,06 后插真实内容。
ORDER = [
 ("slide_01", "以前我最怕重复劳动,同样的活天天干,时间全耗进去了。后来我开始把会重复的活,全部变成系统自己跑。最近就花一天,给一个海外小品牌搭了套自动获客系统,搭完它自己运转,几乎零成本。"),
 ("slide_02", "整条链路其实就一句话:出内容、免费引流、落地页留邮箱、自动发邮件养熟,再用数据回流不断优化。一个会自己迭代的闭环。"),
 ("slide_03", "最省心的是邮件。用户一留下邮箱,一切自动发生:秒发欢迎信,之后每隔两天自动养熟,退订的自动剔除,我一根手指都不用动。"),
 ("slide_04", "客户的要求挺离谱:没人能天天盯,预算几乎为零,还得能看数据。所以只有一条路,全自动、尽量免费。"),
 ("slide_05", "第一步,落地页加邮箱捕获,而且不用写后端。表单几秒收下名单,用户留完邮箱立刻拿到免费资料。门槛越低,留的人越多。"),
 ("shot_pages", "这些都是真实上线的页面,移动端打开几秒,就讲清你能拿到什么。"),
 ("slide_06", "这里我踩过坑:全让 A I 生成内容,根本没人看,太机器了。后来 A I 只出背景图,文字自己精排,才像个活人发的。A I 是放大器,不是替身。"),
 ("shot_pins", "你看,这些内容完全没有那种廉价的 A I 拼接感。"),
 ("slide_07", "再把每一步都埋点:访问、留资、下载、意向,串成一条漏斗。带量的内容加产,不带量的直接砍。"),
 ("slide_08", "整套跑在各家免费层上,月成本几乎是零。这就是杠杆,你搭一次,它替你跑一万次。"),
 ("slide_09", "而这一切,只用了一天。上午定方案和落地页,中午做邮箱捕获,下午接自动邮件和埋点,傍晚产出内容、全链路上线。"),
 ("slide_10", "现在它已经在自己跑,进入数据爬坡期。新账号起量本来就要六到八周,我打算用两个月,慢慢喂数据、越调越准。"),
 ("slide_11", "所以如果你也总被重复的活困住,真心建议:先找出你天天在重复的那件事,想办法让它跑一次、之后就自动。你最想自动化掉哪件事?评论区聊聊。"),
]


def dur(path):
    out = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","json",str(path)], capture_output=True, text=True).stdout
    return float(json.loads(out)["format"]["duration"])


def main():
    segs = []
    for k, (name, text) in enumerate(ORDER):
        img = SL / f"{name}.png"
        aud = TMP / f"a_{k:02d}.mp3"
        subprocess.run([EDGE,"--voice",VOICE,"--rate",RATE,"--text",text,
                        "--write-media",str(aud)], check=True, capture_output=True)
        d = dur(aud) + PAD
        seg = TMP / f"seg_{k:02d}.mp4"
        vf = (f"scale=1080:1920,fps=30,format=yuv420p,"
              f"fade=t=in:st=0:d={FADE},fade=t=out:st={d-FADE:.2f}:d={FADE}")
        af = f"apad,afade=t=out:st={d-0.35:.2f}:d=0.3"
        subprocess.run(["ffmpeg","-y","-loop","1","-i",str(img),"-i",str(aud),
            "-filter_complex",f"[0:v]{vf}[v];[1:a]{af}[a]","-map","[v]","-map","[a]",
            "-t",f"{d:.2f}","-c:v","libx264","-preset","medium","-crf","20",
            "-c:a","aac","-b:a","160k","-ar","44100","-pix_fmt","yuv420p",str(seg)],
            capture_output=True)
        segs.append(seg); print(f"{name}: {d:.1f}s")

    lst = TMP / "list.txt"
    lst.write_text("".join(f"file '{s}'\n" for s in segs))
    narr = TMP / "narrated.mp4"
    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(lst),
        "-c:v","libx264","-preset","medium","-crf","20","-c:a","aac","-b:a","160k",
        "-pix_fmt","yuv420p",str(narr)], capture_output=True)
    T = dur(narr); print(f"narrated total: {T:.1f}s")

    out = OUT / "case_study_narrated.mp4"
    if MUSIC.exists():
        fc = (f"[1:a]volume={MUSIC_VOL},afade=t=in:st=0:d=1.5,afade=t=out:st={T-2.5:.2f}:d=2.5[bg];"
              f"[0:a][bg]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]")
        subprocess.run(["ffmpeg","-y","-i",str(narr),"-stream_loop","-1","-i",str(MUSIC),
            "-filter_complex",fc,"-map","0:v","-map","[a]","-c:v","copy",
            "-c:a","aac","-b:a","192k","-movflags","+faststart",str(out)],
            capture_output=True)
        print("加背景音乐 ✓")
    else:
        subprocess.run(["ffmpeg","-y","-i",str(narr),"-c","copy",str(out)], capture_output=True)
        print("⚠️ 未找到音乐,输出无背景乐版")
    print(f"TOTAL: {dur(out):.1f}s -> {out}")


if __name__ == "__main__":
    main()
