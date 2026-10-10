// Renders layers for editable Canva cards: one shared base (page, logo, card, dots, footer)
// and one hero image per story (rounded photo, darkened when used behind a logo pill).
// Usage: node generator/render-layers.js <stories.json> <outDir>
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const [, , storiesFile, outDir] = process.argv;
const stories = JSON.parse(fs.readFileSync(storiesFile, 'utf8'));
fs.mkdirSync(outDir, { recursive: true });
const fileUrl = (p) => 'file://' + path.resolve(ROOT, p);

let html = fs.readFileSync(path.join(__dirname, 'render.js'), 'utf8');
const css = html.match(/<style>([\s\S]*?)<\/style>/)[1];
const dots = (side) => `<div class="dots ${side}">` + '<i></i>'.repeat(12) + '</div>';
const social = html.match(/<div class="social">[\s\S]*?<\/div>\n<\/div>/)[0].replace(/\n<\/div>$/, '');

const base = `<!doctype html><html><head><meta charset="utf-8"><style>${css}</style></head><body>
<img class="brand" src="${fileUrl('generator/assets/incbusiness-logo.png')}">
<div class="card">${dots('d1')}${dots('d2')}<div class="readmore">READ MORE</div>${social}</div></body></html>`;

const heroPage = (s) => `<!doctype html><html><head><meta charset="utf-8"><style>
*{margin:0}body{width:896px;height:548px;background:transparent}
img{width:896px;height:548px;object-fit:cover;border-radius:24px;display:block;${s.heroPhoto ? '' : 'filter:brightness(.55) saturate(1.2)'}}
</style></head><body><img src="${fileUrl(s.heroPhoto || s.background)}"></body></html>`;

(async () => {
  const browser = await chromium.launch();
  const shoot = async (content, file, w, h) => {
    const p = await browser.newPage({ viewport: { width: w, height: h } });
    const tmp = path.join(outDir, '_tmp.html');
    fs.writeFileSync(tmp, content);
    await p.goto('file://' + path.resolve(tmp), { waitUntil: 'networkidle' });
    await p.evaluate(() => document.fonts.ready);
    await p.screenshot({ path: path.join(outDir, file), omitBackground: true });
    fs.unlinkSync(tmp);
    await p.close();
  };
  await shoot(base, 'base.png', 1080, 1440);
  for (const s of stories) await shoot(heroPage(s), `hero-${s.slug}.png`, 896, 548);
  await browser.close();
  console.log('done');
})();
