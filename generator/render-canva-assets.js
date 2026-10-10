// Renders Canva-ready assets: logo strips (transparent PNG) and hero photos sized
// to the Canva template's photo frame (1464x953, rounded corners baked in).
// Usage: node generator/render-canva-assets.js <stories.json> <outDir>
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const [, , storiesFile, outDir] = process.argv;
const stories = JSON.parse(fs.readFileSync(storiesFile, 'utf8'));
fs.mkdirSync(outDir, { recursive: true });
const abs = (p) => 'file://' + path.resolve(ROOT, p);

function svgAspect(file) {
  const vb = fs.readFileSync(path.resolve(ROOT, file), 'utf8').match(/viewBox="([^"]+)"/)[1].split(/[\s,]+/).map(Number);
  return vb[2] / vb[3];
}

(async () => {
  const browser = await chromium.launch();
  const shoot = async (html, file, w, h, selector) => {
    const p = await browser.newPage({ viewport: { width: w, height: h } });
    const tmp = path.resolve(outDir, '_tmp.html');
    fs.writeFileSync(tmp, html);
    await p.goto('file://' + tmp, { waitUntil: 'networkidle' });
    const target = selector ? await p.$(selector) : p;
    await target.screenshot({ path: path.join(outDir, file), omitBackground: true });
    fs.unlinkSync(tmp);
    await p.close();
  };
  for (const s of stories) {
    const src = s.heroPhoto || s.background;
    if (src) {
      const dim = s.heroPhoto ? '' : 'filter:brightness(.55) saturate(1.2);';
      await shoot(`<body style="margin:0;background:transparent"><img src="${abs(src)}" style="width:1464px;height:953px;object-fit:cover;border-radius:40px;display:block;${dim}"></body>`,
        `hero-${s.slug}.png`, 1464, 953);
    }
    if (s.logos) {
      const h = s.logos.length > 1 ? [150, 80] : [180];
      const imgs = s.logos.map((l, i) => `<img src="${abs(l)}" style="height:${h[i]}px;width:${Math.round(h[i] * svgAspect(l))}px">`).join('');
      await shoot(`<body style="margin:0;background:transparent"><div id="w" style="display:inline-flex;align-items:center;gap:70px;padding:4px">${imgs}</div></body>`,
        `logo-${s.slug}.png`, 2400, 400, '#w');
    }
  }
  await browser.close();
  console.log('done');
})();
