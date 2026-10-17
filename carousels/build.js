// Renders an Instagram carousel (1080x1350 PNGs) from a slide-content module.
// Usage: node carousels/build.js carousels/001-mamaearth/slides.js
const path = require('path');
const fs = require('fs');
const { chromium } = require(require.resolve('playwright', { paths: ['/opt/node22/lib/node_modules'] }));

const ROOT = path.resolve(__dirname, '..');
const specPath = path.resolve(process.argv[2]);
const spec = require(specPath);
const outDir = path.dirname(specPath);

const fileUrl = (p) => 'file://' + path.resolve(ROOT, p);

const CSS = `
  :root {
    --navy: #28275a; --mid: #3a3778; --purple: #544aa0;
    --amber: #F9CB42; --amber-deep: #F2A623; --dark: #1c1b3a;
    --lav: #cfc9f2; --sub: #c9c6e8; --red: #ff5a5f; --green: #3ddc97;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { width: 1080px; height: 1350px; }
  body {
    font-family: 'Inter', 'DejaVu Sans', sans-serif; color: #fff;
    background: linear-gradient(180deg, var(--navy) 0%, var(--mid) 45%, var(--purple) 100%);
    position: relative; overflow: hidden;
  }
  .stars { position: absolute; inset: 0; opacity: .18; pointer-events: none;
    background-image: radial-gradient(#fff 1.2px, transparent 1.6px);
    background-size: 46px 46px; mask-image: linear-gradient(180deg, #000 0%, transparent 55%); }
  .header { position: absolute; top: 56px; left: 64px; right: 64px; display: flex;
    justify-content: space-between; align-items: center; z-index: 5; }
  .brandpill { background: #fff; border-radius: 999px; padding: 16px 30px; display: flex; align-items: center;
    box-shadow: 0 8px 30px rgba(0,0,0,.25); }
  .brandpill img { height: 44px; display: block; }
  .tag { border: 2px solid var(--amber); color: var(--amber); border-radius: 999px; padding: 12px 24px; background: rgba(28,27,58,.78);
    font-weight: 700; font-size: 24px; letter-spacing: 2px; }
  .content { position: absolute; top: 190px; left: 64px; right: 64px; bottom: 210px; z-index: 4; }
  .eyebrow { color: var(--amber); font-weight: 800; font-size: 26px; letter-spacing: 4px; text-transform: uppercase; margin-bottom: 18px; }
  h1 { font-size: 68px; line-height: 1.08; font-weight: 800; letter-spacing: -1.5px; }
  h1 .hl { color: var(--amber); }
  .lead { font-size: 32px; line-height: 1.4; color: var(--sub); margin-top: 22px; }
  .source { position: absolute; left: 64px; right: 64px; bottom: 150px; font-size: 18px; color: rgba(255,255,255,.55); z-index: 5; }
  .footer { position: absolute; left: 64px; right: 64px; bottom: 56px; display: flex; justify-content: space-between;
    align-items: center; z-index: 5; }
  .footer img { height: 46px; }
  .pager { display: flex; align-items: center; gap: 18px; font-size: 24px; font-weight: 700; color: var(--sub); }
  .pager .arrow { background: var(--amber); color: var(--dark); width: 64px; height: 64px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center; font-size: 34px; font-weight: 900; }
  .card { background: rgba(28,27,58,.55); border: 1.5px solid rgba(207,201,242,.22); border-radius: 28px; padding: 30px 34px; }
  .amber { color: var(--amber); } .red { color: var(--red); } .green { color: var(--green); }
`;

function page(slide, i, total) {
  const bg = slide.bgImage ? `
    <div style="position:absolute;inset:0;background:url('${fileUrl(slide.bgImage)}') center/cover no-repeat;"></div>
    <div style="position:absolute;inset:0;background:linear-gradient(180deg, rgba(40,39,90,.15) 0%, rgba(40,39,90,.35) 35%, rgba(40,39,90,.92) 62%, #3a3778 100%);"></div>` : '<div class="stars"></div>';
  const isLast = i === total;
  return `<!doctype html><html><head><meta charset="utf-8"><style>${CSS}${slide.css || ''}</style></head><body>
    ${bg}
    <div class="header">
      <div class="brandpill"><img src="${fileUrl(spec.brandLogo)}"></div>
      <div class="tag">${spec.seriesTag}</div>
    </div>
    <div class="content">${slide.html}</div>
    ${slide.source ? `<div class="source">${slide.source}</div>` : ''}
    <div class="footer">
      <img src="${fileUrl(spec.ownLogo)}">
      <div class="pager">${i} / ${total}${isLast ? '' : '<div class="arrow">→</div>'}</div>
    </div>
  </body></html>`;
}

(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const ctx = await browser.newContext({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: 1 });
  const pg = await ctx.newPage();
  const total = spec.slides.length;
  for (let i = 0; i < total; i++) {
    const html = page(spec.slides[i], i + 1, total);
    const htmlPath = path.join(outDir, `.slide-${i + 1}.html`);
    fs.writeFileSync(htmlPath, html);
    await pg.goto('file://' + htmlPath);
    await pg.waitForLoadState('networkidle');
    const out = path.join(outDir, `slide-${String(i + 1).padStart(2, '0')}.png`);
    await pg.screenshot({ path: out });
    fs.unlinkSync(htmlPath);
    console.log('wrote', path.relative(ROOT, out));
  }
  await browser.close();
})();
