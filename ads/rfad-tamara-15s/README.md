# رفاد – إعلان 15 ثانية (Luxury Fintech)

- `rfad-tamara-15s.mp4` — الفيديو النهائي 1080×1920 (9:16)، 30fps، مع مؤثرات صوتية.
- `index.html` — المشاهد كخط زمني قابل للتعديل (افتحه في المتصفح للمعاينة المباشرة).
- `render.mjs` — يصدّر الفيديو إطاراً بإطار (Playwright + ffmpeg).
- `audio.py` — يولّد الخلفية الصوتية.

إعادة التصدير:

```sh
node render.mjs              # build/video-silent.mp4
python3 audio.py             # build/audio.wav
ffmpeg -i build/video-silent.mp4 -i build/audio.wav -c:v copy -c:a aac -b:a 192k \
  -af loudnorm=I=-16:TP=-1.5 -shortest -movflags +faststart rfad-tamara-15s.mp4
```
