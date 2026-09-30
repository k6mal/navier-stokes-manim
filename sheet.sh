#!/bin/zsh
# sheet.sh <video> <out.png> [cols] [rows]
V=$1; OUT=$2; C=${3:-4}; R=${4:-3}; N=$((C*R))
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$V")
TMP=$(mktemp -d)
for i in $(seq 0 $((N-1))); do
  TS=$(python3 -c "print(max(0.05,$D*($i+0.5)/$N))")
  ffmpeg -nostdin -v error -ss $TS -i "$V" -frames:v 1 -vf scale=480:-1 "$TMP/f$(printf %02d $i).png" -y
done
ffmpeg -nostdin -v error -pattern_type glob -i "$TMP/*.png" -filter_complex "tile=${C}x${R}:margin=6:padding=4:color=0x1a1f2e" -frames:v 1 "$OUT" -y
rm -rf $TMP
echo "$OUT  (duration ${D}s)"
