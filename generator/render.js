// Renders incbusiness news cards (1080x1440) from a stories JSON file.
// Usage: node generator/render.js <stories.json> <outDir>
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const [, , storiesFile, outDir] = process.argv;
const stories = JSON.parse(fs.readFileSync(storiesFile, 'utf8'));
// REEL=1 renders only the card on a transparent background (for video compositing)
const REEL = process.env.REEL === '1';
fs.mkdirSync(outDir, { recursive: true });

const fileUrl = (p) => 'file://' + path.resolve(ROOT, p);
const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
// [[word]] -> red highlight
const headlineHtml = (h) => esc(h).replace(/\[\[(.+?)\]\]/g, '<span class="hl">$1</span>');

function hero(s) {
  if (s.heroPhoto) {
    return `<div class="hero"><img class="photo" src="${fileUrl(s.heroPhoto)}"></div>`;
  }
  const inner = s.logos
    ? s.logos.map((l) => `<img class="logo" src="${fileUrl(l)}">`).join('<span class="sep"></span>')
    : `<span class="name">${esc(s.pillText)}</span>`;
  return `<div class="hero"><img class="photo dim" src="${fileUrl(s.background)}"><div class="pill${s.logos && s.logos.length > 1 ? ' two' : ''}">${inner}</div></div>`;
}

const dots = (side) => `<div class="dots ${side}">` + '<i></i>'.repeat(12) + '</div>';

const page = (s) => `<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,600;0,700;0,800;1,800&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{width:1080px;height:1440px;${REEL ? 'background:transparent!important;' : ''}font-family:Poppins,sans-serif;position:relative;overflow:hidden;
  ${REEL ? '' : 'background:#F4F4F2;background-image:linear-gradient(#e9e9e4 1px,transparent 1px),linear-gradient(90deg,#e9e9e4 1px,transparent 1px);background-size:44px 44px;'}}
.brand{position:absolute;top:34px;left:50%;transform:translateX(-50%);width:400px;mix-blend-mode:multiply}
.card{position:absolute;left:66px;right:66px;top:128px;bottom:76px;background:#fff;border-radius:28px;box-shadow:0 18px 40px rgba(0,0,0,.12)}
.hero{position:absolute;left:26px;right:26px;top:30px;height:548px;border-radius:24px;overflow:hidden;background:#0a1640}
.photo{width:100%;height:100%;object-fit:cover;display:block}
.dim{filter:brightness(.55) saturate(1.2)}
.pill{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);background:#fff;border-radius:40px;min-width:520px;height:170px;
  max-width:830px;padding:0 56px;display:flex;align-items:center;justify-content:center;gap:0;box-shadow:0 10px 30px rgba(0,0,0,.35)}
.logo{height:120px;width:auto;max-width:560px;object-fit:contain}
.pill.two .logo{height:70px;max-width:300px}
.sep{width:2px;height:80px;background:#ddd;margin:0 34px}
.name{font-weight:800;font-size:76px;color:#111;letter-spacing:-1px;white-space:nowrap}
.tag{position:absolute;top:546px;left:50%;transform:translateX(-50%);background:#D92B2B;color:#fff;font-weight:700;font-size:38px;
  height:92px;padding:0 64px;display:flex;align-items:center;clip-path:polygon(9% 0,91% 0,100% 50%,91% 100%,9% 100%,0 50%)}
.dots{position:absolute;top:620px;display:grid;grid-template-columns:repeat(4,14px);gap:18px 18px}
.dots i{width:14px;height:14px;border-radius:50%;background:#9a9a9a;display:block}
.d1{left:36px}.d2{right:36px}
.headline{position:absolute;left:58px;right:58px;top:700px;height:400px;display:flex;align-items:center}
.headline h1{font-weight:800;line-height:1.08;color:#111;letter-spacing:-1.5px}
.hl{color:#E03131}
.readmore{position:absolute;left:0;bottom:30px;width:412px;height:76px;background:#0B1257;color:#fff;font-weight:800;font-style:italic;
  font-size:36px;display:flex;align-items:center;padding-left:52px;clip-path:polygon(0 0,100% 0,90% 100%,0 100%)}
.social{position:absolute;right:38px;bottom:34px;display:flex;gap:28px}
.social svg{width:66px;height:66px}
</style></head><body>
${REEL ? '' : `<img class="brand" src="${fileUrl('generator/assets/incbusiness-logo.png')}">`}
<div class="card">
  ${hero(s)}
  <div class="tag">${esc(s.category)}</div>
  ${dots('d1')}
  ${dots('d2')}
  <div class="headline"><h1 id="h">${headlineHtml(s.cardHeadline)}</h1></div>
  <div class="readmore">READ MORE</div>
  <div class="social">
    <svg viewBox="0 0 24 24" fill="none" stroke="#E03131" stroke-width="2.4"><rect x="2.5" y="2.5" width="19" height="19" rx="5.5"/><circle cx="12" cy="12" r="4.3"/><circle cx="17.6" cy="6.4" r="1" fill="#E03131" stroke="none"/></svg>
    <svg viewBox="0 0 24 24"><rect width="24" height="24" rx="3" fill="#E03131"/><path fill="#fff" d="M5.3 9.4h2.9V19H5.3zM6.75 4.8a1.7 1.7 0 110 3.4 1.7 1.7 0 010-3.4zM10.1 9.4h2.8v1.3c.4-.8 1.4-1.5 2.9-1.5 3 0 3.6 2 3.6 4.6V19h-2.9v-4.6c0-1.1 0-2.5-1.5-2.5s-1.8 1.2-1.8 2.4V19h-2.9z"/></svg>
  </div>
</div>
</body></html>`;

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1080, height: 1440 } });
  for (const s of stories) {
    const p = await ctx.newPage();
    const htmlPath = path.join(outDir, `${s.slug}.html`);
    fs.writeFileSync(htmlPath, page(s));
    await p.goto('file://' + path.resolve(htmlPath), { waitUntil: 'networkidle' });
    await p.evaluate(() => document.fonts.ready);
    // Shrink headline until it fits its box (max 4 lines look)
    await p.evaluate(() => {
      const h = document.getElementById('h'), box = h.parentElement;
      let size = 104;
      h.style.fontSize = size + 'px';
      while ((h.scrollHeight > box.clientHeight || h.scrollWidth > box.clientWidth) && size > 50) {
        size -= 2; h.style.fontSize = size + 'px';
      }
    });
    await p.evaluate(() => {
      const n = document.querySelector('.name');
      if (!n) return;
      let size = 76;
      while (n.scrollWidth > 700 && size > 36) { size -= 2; n.style.fontSize = size + 'px'; }
    });
    if (REEL) {
      // card sits at left 66, top 128, right 66, bottom 76; keep 40px for the shadow
      await p.screenshot({ path: path.join(outDir, `${s.slug}.png`), omitBackground: true,
        clip: { x: 26, y: 88, width: 1028, height: 1316 } });
    } else {
      await p.screenshot({ path: path.join(outDir, `${s.slug}.png`) });
    }
    fs.unlinkSync(htmlPath);
    await p.close();
    console.log('rendered', s.slug);
  }
  await browser.close();
})();
