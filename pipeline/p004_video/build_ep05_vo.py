#!/usr/bin/env python3
"""EP05 连载 · 真声主轨拼接(复刻 EP01/EP04)。

对 8 段真人录音去首尾静音 + 统一响度,按拍插入自然气口,拼成 master VO,
并输出每拍精确起止时间(供分镜 storyboard 各场景对齐)。
情绪主线:冷/稳/掌控 —— "不跟你讲道理了,我上规则"的笃定;第6段诚实放下身段;末拍自嘲翻车勾EP06。

用法: ./.venv/bin/python pipeline/p004_video/build_ep05_vo.py
"""
from __future__ import annotations
import json, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "publish/2026-W29/连载-把AI调教成我的助理/脚本/EP05"
OUT = pathlib.Path(__file__).resolve().parent / "out" / "ep05full"
OUT.mkdir(parents=True, exist_ok=True)
SR = 48000

# (源文件, beat_id, 拍后气口秒)  情绪:冷/稳/掌控 → 诚实放慢 → 末拍自嘲收
BEATS = [
    ("前3秒.m4a",  "hook", 0.50),  # 开场:不再信它,给它装了监控
    ("第一段.m4a", "b1",   0.45),  # 拍1 不能信它自己说的(seed)
    ("第二段.m4a", "b2",   0.35),  # 拍2 闸① 开工自动注入(lock1)
    ("第三段.m4a", "b3",   0.35),  # 拍3 闸② 写前搜·体检挡(lock2)
    ("第四段.m4a", "b4",   0.35),  # 拍4 闸③ 收工硬互锁(lock3)
    ("第五段.m4a", "b5",   0.55),  # 拍5 裁判 Stop(lock4 · 转诚实前松口气)
    ("第六段.m4a", "b6",   0.70),  # 拍6 ★诚信锚点 放下身段(honest)
    ("第七段.m4a", "b7",   0.30),  # 拍7 落点自嘲翻车 勾EP06(尾)
]


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-1500:]); sys.exit(f"ffmpeg 失败: {' '.join(cmd[:4])}")
    return r


def dur(p):
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                        "-of","json",str(p)], capture_output=True, text=True)
    return float(json.loads(r.stdout)["format"]["duration"])


def main():
    clips = []
    for fn, bid, _gap in BEATS:
        src = SRC / fn
        clip = OUT / f"vo_{bid}.wav"
        af = (
            "silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.12,"
            "areverse,"
            "silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.12,"
            "areverse,"
            "loudnorm=I=-16:TP=-1.5:LRA=13,"
            "highpass=f=70,"
            f"aformat=sample_rates={SR}:channel_layouts=mono"
        )
        run(["ffmpeg","-y","-i",str(src),"-af",af,str(clip)])
        clips.append((bid, clip, _gap))

    concat_parts = []
    timeline = []
    t = 0.0
    for bid, clip, gap in clips:
        d = dur(clip)
        timeline.append({"beat": bid, "start": round(t, 3), "end": round(t + d, 3),
                         "dur": round(d, 3)})
        concat_parts.append(clip)
        t += d
        if gap > 0:
            sfn = OUT / f"sil_{bid}.wav"
            run(["ffmpeg","-y","-f","lavfi","-i",
                 f"anullsrc=r={SR}:cl=mono","-t",f"{gap:.3f}",str(sfn)])
            concat_parts.append(sfn)
            t += gap

    lst = OUT / "vo_concat.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in concat_parts))
    master = OUT / "vo_master.wav"
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(lst),
         "-c:a","pcm_s16le",str(master)])
    master_mp3 = OUT / "vo_master.mp3"
    run(["ffmpeg","-y","-i",str(master),"-b:a","256k",str(master_mp3)])

    total = dur(master)
    meta = {"total": round(total, 3), "beats": timeline}
    (OUT / "vo_timeline.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    print(f"✓ master VO: {total:.2f}s → {master}")
    for b in timeline:
        print(f"  {b['beat']:5} {b['start']:7.2f} → {b['end']:7.2f}  ({b['dur']:.2f}s)")


if __name__ == "__main__":
    main()
