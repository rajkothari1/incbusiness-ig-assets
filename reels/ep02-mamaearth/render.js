// Renders reel.html frame by frame and muxes it with the voice-over into an Instagram reel (1080x1920, 30fps).
// Usage: node reels/ep02-mamaearth/render.js [--preview t1,t2,...]
const path = require('path');
const { spawn } = require('child_process');
const { chromium } = require(require.resolve('playwright', { paths: ['/opt/node22/lib/node_modules'] }));

const DIR = __dirname;
const FPS = 30;
const DUR = 43.4;

// waits until every <img> (e.g. the swapped mascot frame) has finished loading
const imagesReady = () => Promise.all([...document.images].map((i) => i.complete ? 0 : new Promise((r) => { i.onload = i.onerror = r; })));

(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto('file://' + path.join(DIR, 'reel.html'));
  await page.evaluate(() => document.fonts.ready);

  const previewArg = process.argv.indexOf('--preview');
  if (previewArg > -1) {
    for (const t of process.argv[previewArg + 1].split(',').map(Number)) {
      await page.evaluate((x) => window.render(x), t);
      await page.evaluate(imagesReady);
      await page.screenshot({ path: path.join(DIR, `preview-${t}.png`) });
    }
    await browser.close();
    return;
  }

  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
    '-i', path.join(DIR, 'mix.wav'), '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
    '-c:a', 'aac', '-b:a', '192k', '-af', 'apad', '-t', String(DUR), '-movflags', '+faststart',
    path.join(DIR, 'ep02-mamaearth-reel.mp4')], { stdio: ['pipe', 'inherit', 'inherit'] });

  const frames = Math.round(DUR * FPS);
  for (let i = 0; i < frames; i++) {
    await page.evaluate((x) => window.render(x), i / FPS);
    await page.evaluate(imagesReady);
    const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
    if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
  }
  ff.stdin.end();
  await new Promise((r) => ff.on('close', r));
  await browser.close();
})();
