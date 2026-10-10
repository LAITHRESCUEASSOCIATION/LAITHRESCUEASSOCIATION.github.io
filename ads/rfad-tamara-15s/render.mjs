// Renders index.html to an MP4 frame by frame (deterministic timeline).
// Usage:
//   node render.mjs                      -> rfad-tamara-15s.mp4 (1080x1920, 30fps)
//   node render.mjs --stills 1,4,8,12,14 -> PNG stills in ./stills
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { mkdirSync, existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const FPS = 30, DUR = 15, W = 1080, H = 1920;
const stillsArg = args.includes('--stills') ? args[args.indexOf('--stills') + 1] : null;
const out = args.includes('--out') ? args[args.indexOf('--out') + 1] : path.join(dir, 'build', 'video-silent.mp4');

const exe = existsSync('/opt/pw-browsers/chromium') ? '/opt/pw-browsers/chromium' : undefined;
const browser = await chromium.launch({ executablePath: exe, args: ['--allow-file-access-from-files'] });
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(path.join(dir, 'index.html')).href + '?render');
await page.evaluate(() => window.__ready);

if (stillsArg) {
  const sd = path.join(dir, 'build', 'stills'); mkdirSync(sd, { recursive: true });
  for (const s of stillsArg.split(',').map(Number)) {
    await page.evaluate(t => window.render(t), s);
    await page.screenshot({ path: path.join(sd, `t${s.toFixed(2)}.png`) });
  }
} else {
  mkdirSync(path.dirname(out), { recursive: true });
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const N = FPS * DUR;
  for (let f = 0; f < N; f++) {
    await page.evaluate(t => window.render(t), f / FPS);
    const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (f % 30 === 0) process.stdout.write(`frame ${f}/${N}\n`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  console.log('wrote', out);
}
await browser.close();
