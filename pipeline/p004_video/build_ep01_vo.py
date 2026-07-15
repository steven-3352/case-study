#!/usr/bin/env python3
"""EP01 连载 · 真声主轨拼接。

对 7 段真人录音去首尾静音 + 统一响度,按拍插入自然气口,拼成 master VO,
并输出每拍精确起止时间(供分镜 storyboard 各场景对齐)。

用法: ./.venv/bin/python pipeline/p004_video/build_ep01_vo.py
"""
from __future__ import annotations
import json, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "publish/2026-W29/连载-把AI调教成我的助理/脚本/EP01"
OUT = pathlib.Path(__file__).resolve().parent / "out" / "ep01full"
OUT.mkdir(parents=True, exist_ok=True)
SR = 48000

# (源文件, beat_id, 拍后气口秒)
BEATS = [
    ("0-3秒.m4a",      "hook",  0.55),  # 开场钩子
    ("当初多信.m4a",    "b1",    0.40),  # 拍1 当初多信
    ("它失忆了.m4a",    "b2",    0.50),  # 拍2 失忆
    ("规律散一地.m4a",  "b3",    0.42),  # 拍3 文档乱
    ("活在上个月.m4a",  "b4",    0.60),  # 拍4 活在过期
    ("拉观众.m4a",      "b5",    0.75),  # 拍5 拉观众互动
    ("发凉勾下集.m4a",  "b6",    0.80),  # 拍6 发凉勾EP02(尾)
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
        # 去首尾静音(阈值-40dB,保留 0.12s pad) + 单声道 48k + 温和响度统一(保留情绪动态)
        af = (
            "silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.12,"
            "areverse,"
            "silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.12,"
            "areverse,"
            "loudnorm=I=-16:TP=-1.5:LRA=13,"
            "highpass=f=70,"          # 去低频隆隆/桌面震动
            f"aformat=sample_rates={SR}:channel_layouts=mono"
        )
        run(["ffmpeg","-y","-i",str(src),"-af",af,str(clip)])
        clips.append((bid, clip, _gap))

    # 生成静音气口 + 拼接;记录 beat 时间轴
    concat_parts = []
    timeline = []
    t = 0.0
    silences = {}
    for bid, clip, gap in clips:
        d = dur(clip)
        timeline.append({"beat": bid, "start": round(t, 3), "end": round(t + d, 3),
                         "dur": round(d, 3)})
        concat_parts.append(clip)
        t += d
        if gap > 0:
            sfn = OUT / f"sil_{bid}.wav"
            if gap not in silences:
                run(["ffmpeg","-y","-f","lavfi","-i",
                     f"anullsrc=r={SR}:cl=mono","-t",f"{gap:.3f}",str(sfn)])
            else:
                run(["ffmpeg","-y","-f","lavfi","-i",
                     f"anullsrc=r={SR}:cl=mono","-t",f"{gap:.3f}",str(sfn)])
            concat_parts.append(sfn)
            t += gap

    # concat
    lst = OUT / "vo_concat.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in concat_parts))
    master = OUT / "vo_master.wav"
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(lst),
         "-c:a","pcm_s16le",str(master)])
    # mp3 版备用
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
