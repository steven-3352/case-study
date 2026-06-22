#!/usr/bin/env bash
# 给 P004 K1 加 BGM · 不需要重跑 build.py
#
# 用法:
#   ./mix_bgm.sh                  # 合成默认 ambient drone + 叠到 final
#   ./mix_bgm.sh path/to/your.mp3 # 用你自己的 BGM
#
# 输出: pipeline/p004_video/out/final/p004_K1_with_bgm.mp4

set -euo pipefail
cd "$(dirname "$0")/../.."

FINAL=pipeline/p004_video/out/final/p004_K1.mp4
OUT=pipeline/p004_video/out/final/p004_K1_with_bgm.mp4
BGM=${1:-}

if [[ -z "$BGM" ]]; then
  BGM=pipeline/p004_video/out/audio/_bgm_drone.mp3
  if [[ ! -f "$BGM" ]]; then
    echo "→ 合成 ambient drone BGM (44s, A2 + E3 + brown noise, 目标 -16 dB RMS)"
    ffmpeg -y -loglevel error \
      -f lavfi -i "sine=frequency=110:duration=44" \
      -f lavfi -i "sine=frequency=164.81:duration=44" \
      -f lavfi -i "anoisesrc=duration=44:amplitude=0.5:color=brown" \
      -filter_complex "\
[0:a]volume=0.45[s1];\
[1:a]volume=0.30[s2];\
[2:a]volume=0.55[n];\
[s1][s2][n]amix=inputs=3:duration=longest:normalize=0[m];\
[m]aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-2.0:LRA=8,\
afade=t=in:st=0:d=2.0,afade=t=out:st=42:d=2.0[bgm]" \
      -map "[bgm]" -c:a libmp3lame -b:a 128k "$BGM"
  fi
fi

DUR=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$FINAL")
echo "→ FINAL=$DUR s · BGM=$BGM"

ffmpeg -y -loglevel error \
  -i "$FINAL" \
  -stream_loop -1 -i "$BGM" \
  -filter_complex "[0:a]volume=1.0[vo];\
[1:a]volume=0.35,afade=t=in:st=0:d=1.5,afade=t=out:st=$(echo "$DUR - 2.0" | bc):d=2.0[bg];\
[vo][bg]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]" \
  -map 0:v -map "[a]" \
  -c:v copy -c:a aac -b:a 192k -ar 44100 \
  -t "$DUR" -movflags +faststart \
  "$OUT"

echo "✓ $OUT"
ls -lh "$OUT"
