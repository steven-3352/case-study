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
 ("slide_01", "我用一天时间,给一个海外生活方式品牌,搭了一套全自动获客系统。落地页、邮箱捕获、自动养熟、内容流水线、数据闭环,全部打通,月成本几乎为零。"),
 ("slide_02", "先看全景。A I 内容流水线产出素材,社媒免费引流,把人导到品牌落地页;留下邮箱后自动发邮件养熟,再用数据回流不断优化。一个会自我迭代的闭环。"),
 ("slide_03", "用户一留下邮箱,一切自动发生:秒发欢迎邮件,之后第二、四、六、八、十天自动推送养熟内容,退订的人自动剔除,全程零人工。"),
 ("slide_04", "客户的需求很明确:从零跑通,引流到邮箱、再到成交的闭环。但没人能天天盯,预算也紧,还要能看数据。所以必须全自动、尽量免费。"),
 ("slide_05", "第一步,落地页加邮箱捕获,而且零后端。表单不用写服务器就能收集名单,用户留完邮箱立刻拿到免费资料。"),
 ("shot_pages", "这些都是真实上线的页面:品牌落地页、蓝图等候页,移动优先,几秒讲清价值。"),
 ("slide_06", "怎么防止那股 A I 味?让 A I 只出背景图,文字用代码精排,品牌字体统一,批量产出还风格一致。"),
 ("shot_pins", "内容也是真实产出的——你看,完全没有那种廉价的 A I 拼接感。"),
 ("slide_07", "全站埋点,把访问、留资、下载、意向全部打点,串成完整漏斗,再用热图看用户怎么用页面。数据反哺内容,带量的加产,不带量的砍掉。"),
 ("slide_08", "整套系统跑在各家免费层上:静态托管、表单、无服务器函数、事务邮件、定时任务、数据分析。月运营成本几乎为零。"),
 ("slide_09", "而这一切,只用了一天。上午定方案和落地页,中午做邮箱捕获,下午接自动邮件和埋点,傍晚产出内容、全链路上线。"),
 ("slide_10", "现在系统已经在自动运行,进入数据爬坡期。新账号起量本来就要六到八周,我们给两个月,用领先指标诚实复盘。"),
 ("slide_11", "如果你也想要一套搭好就自动跑的系统:落地页、邮箱漏斗、自动邮件、内容流水线、数据看板,我都能端到端帮你搭。私信或评论自动化,找腾铂森科技。"),
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
