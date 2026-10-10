#!/usr/bin/env bash
# Assemble the Laith documentary from generated/filmed shots.
#
#   shots/01.mp4 … shots/30.mp4   one clip per row of shots.csv (.mp4 or .mov)
#   music/score.(wav|mp3|m4a)     optional: licensed documentary score, 3:00
#   music/foley.(wav|mp3|m4a)     optional: breaths/effort/foley bed, 3:00
#
# Each clip is conformed to 1920x1080 @ 24 fps, trimmed (or held on its last
# frame) to its length in shots.csv, given the same warm documentary grade,
# then joined with hard cuts and followed by the animated end card.
#
# Env: KEEP_CLIP_AUDIO=1  keep each clip's own ambience (low level)
#      LETTERBOX=1        add 2.39:1 cinema bars
#      GRADE=0            skip the colour grade
set -euo pipefail
cd "$(dirname "$0")"

OUT=${OUT:-laith-documentary.mp4}
WORK=build
KEEP_CLIP_AUDIO=${KEEP_CLIP_AUDIO:-1}
LETTERBOX=${LETTERBOX:-0}
GRADE=${GRADE:-1}
ENC=(-c:v libx264 -preset medium -crf 17 -pix_fmt yuv420p -r 24 -c:a aac -b:a 192k -ar 48000 -ac 2)

rm -rf "$WORK"; mkdir -p "$WORK"

look="scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=24,setsar=1"
if [ "$GRADE" = 1 ]; then
  # warm, slightly lifted blacks, gentle desaturation, vignette, fine grain
  look="$look,eq=contrast=1.04:saturation=0.9:gamma=0.98,colorbalance=rs=0.03:gs=0.01:bs=-0.04:rh=0.04:bh=-0.05,curves=all='0/0.03 0.5/0.49 1/0.97',vignette=PI/5,noise=alls=5:allf=t"
fi
if [ "$LETTERBOX" = 1 ]; then
  look="$look,drawbox=x=0:y=0:w=iw:h=138:color=black:t=fill,drawbox=x=0:y=ih-138:w=iw:h=138:color=black:t=fill"
fi

find_one() { for e in mp4 mov m4v mkv webm wav mp3 m4a; do [ -f "$1.$e" ] && { echo "$1.$e"; return; }; done; true; }

: > "$WORK/list.txt"
tail -n +2 shots.csv | while IFS=, read -r id scene start dur audio; do
  src=$(find_one "shots/$id")
  if [ -z "$src" ]; then
    echo "!! missing shots/$id.mp4 — using a black placeholder (${dur}s)" >&2
    ffmpeg -nostdin -loglevel error -y -f lavfi -i "color=c=black:s=1920x1080:r=24:d=$dur" \
      -f lavfi -i "anullsrc=r=48000:cl=stereo" -t "$dur" "${ENC[@]}" "$WORK/$id.mp4"
  else
    echo "-- $id  scene $scene  ${dur}s  <- $src"
    has_audio=$(ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "$src" | head -n1)
    if [ "$KEEP_CLIP_AUDIO" = 1 ] && [ -n "$has_audio" ]; then
      afilt="[0:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.35,apad,atrim=0:$dur,afade=t=in:d=0.15,afade=t=out:st=$(echo "$dur-0.2" | bc):d=0.2[a]"
      amap=(-map "[a]")
      ain=()
    else
      afilt="[1:a]atrim=0:$dur[a]"
      amap=(-map "[a]")
      ain=(-f lavfi -i "anullsrc=r=48000:cl=stereo")
    fi
    ffmpeg -nostdin -loglevel error -y -i "$src" "${ain[@]}" -filter_complex \
      "[0:v]$look,tpad=stop_mode=clone:stop_duration=$dur,trim=0:$dur,setpts=PTS-STARTPTS[v];$afilt" \
      -map "[v]" "${amap[@]}" -t "$dur" "${ENC[@]}" "$WORK/$id.mp4"
  fi
  echo "file '$id.mp4'" >> "$WORK/list.txt"
done

# end card: 5 s, fade in / slow push / fade out
ffmpeg -nostdin -loglevel error -y -loop 1 -i assets/end-card.png -f lavfi -i "anullsrc=r=48000:cl=stereo" \
  -filter_complex "[0:v]scale=2112:-2,zoompan=z='1+0.0006*on':d=120:s=1920x1080:fps=24:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',fade=t=in:st=0:d=1.2,fade=t=out:st=4:d=1,setsar=1[v]" \
  -map "[v]" -map 1:a -t 5 "${ENC[@]}" "$WORK/99-end.mp4"
echo "file '99-end.mp4'" >> "$WORK/list.txt"

ffmpeg -nostdin -loglevel error -y -f concat -safe 0 -i "$WORK/list.txt" -c copy "$WORK/picture.mp4"
total=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$WORK/picture.mp4")

# final mix: clip ambience + score + foley, fade from black, loudness to -16 LUFS
inputs=(-i "$WORK/picture.mp4"); mix="[0:a]volume=1[a0]"; labels="[a0]"; n=1
score=$(find_one music/score); foley=$(find_one music/foley)
if [ -n "$score" ]; then
  inputs+=(-i "$score")
  mix="$mix;[$n:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:$total,afade=t=in:d=3,afade=t=out:st=$(echo "$total-4" | bc):d=4,volume=0.8[a$n]"
  labels="$labels[a$n]"; n=$((n+1))
fi
if [ -n "$foley" ]; then
  inputs+=(-i "$foley")
  mix="$mix;[$n:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:$total,volume=0.6[a$n]"
  labels="$labels[a$n]"; n=$((n+1))
fi
mix="$mix;${labels}amix=inputs=$n:normalize=0:duration=first,loudnorm=I=-16:TP=-1.5:LRA=11[aout]"

ffmpeg -nostdin -loglevel error -y "${inputs[@]}" -filter_complex "[0:v]fade=t=in:st=0:d=2[vout];$mix" \
  -map "[vout]" -map "[aout]" "${ENC[@]}" -movflags +faststart "$OUT"

echo "== done: $OUT ($(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s)"
