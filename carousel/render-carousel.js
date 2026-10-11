// Renders a connected incbusiness news carousel (1080x1350 slides) from a slides.json file.
// All slides are laid out side by side on one long canvas, so the swipe pill and the track
// line run across every seam, then each slide is cut out with its own red frame.
// Usage: node carousel/render-carousel.js carousels/<date>/slides.json carousels/<date>
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const [, , dataFile, outDir] = process.argv;
const data = JSON.parse(fs.readFileSync(dataFile, 'utf8'));
fs.mkdirSync(outDir, { recursive: true });

const W = 1080, H = 1350, FRAME = 6;
const stories = data.stories;
const N = stories.length;
const SLIDES = N + 2; // hero + stories + recap
const pad = (n) => String(n).padStart(2, '0');
const fileUrl = (p) => 'file://' + path.resolve(ROOT, p);
const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
// [[word]] -> red highlight
const hl = (s) => esc(s).replace(/\[\[(.+?)\]\]/g, '<span class="hl">$1</span>');

const ARROW = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12h15M13 5l7 7-7 7"/></svg>`;

const header = (dark) => `
  <img class="brand" src="${fileUrl(`carousel/assets/incbusiness-logo${dark ? '-white' : ''}.png`)}">
  <div class="date${dark ? ' dark' : ''}">${esc(data.date)}</div>`;

const progress = (cur) => `<div class="prog">${Array.from({ length: N }, (_, i) =>
  `<i class="${i + 1 === cur ? 'on' : i + 1 < cur ? 'done' : ''}"></i>`).join('')}</div>`;

// One tile of the hero news wall: the story's real photo, its real logo (or name) and its key number
function wallTile(t) {
  const s = stories[t.story - 1];
  let mark;
  if (t.darkLogo) mark = `<img class="dlogo" src="${fileUrl(t.darkLogo)}">`;
  else if (t.logo || (s.logos && !t.name)) {
    const logos = t.logo ? [t.logo] : s.logos;
    mark = `<div class="wpill${logos.length > 1 ? ' two' : ''}">${logos.map((l) => `<img src="${fileUrl(l)}">`).join('<i></i>')}</div>`;
  } else if (t.name || s.pill) {
    mark = `<div class="wpill${(t.name || s.pill).length > 10 ? ' long' : ''}"><b style="color:${t.nameColor || '#111'}">${esc(t.name || s.pill)}</b></div>`;
  } else mark = '';
  const arrow = { up: '▲', down: '▼', warn: '!' }[t.dir] || '';
  return `<div class="wt${t.big ? ' big' : ''}">
    <img class="wphoto${s.fullPhoto ? ' full' : ''}" src="${fileUrl(s.photo)}">
    ${mark}
    <div class="wstat ${t.dir}"><span>${arrow}</span>${esc(t.stat)}</div>
    <div class="wnum">#${t.story}</div>
  </div>`;
}

function hero() {
  const h = data.hero;
  const lines = h.headline.map((l) => /^\[\[.*\]\]$/.test(l)
    ? `<div class="hlbox">${esc(l.slice(2, -2))}</div>` : `<div>${hl(l)}</div>`).join('');
  return `<section class="slide hero" style="left:0">
    <div class="glow"></div>
    <div class="wall">${h.wall.map(wallTile).join('')}</div>
    <div class="shade"></div>
    <img class="brand" src="${fileUrl('carousel/assets/incbusiness-logo-white.png')}">
    <div class="counter">1/${SLIDES}</div>
    <div class="headline">${lines}</div>
    <div class="nudge">${esc(h.nudge)}</div>
  </section>`;
}

function storySlide(s, i) {
  const num = i + 1;
  let media;
  if (s.fullPhoto) {
    media = `<img class="photo" src="${fileUrl(s.photo)}">`;
  } else {
    const inner = s.logos
      ? s.logos.map((l) => `<img class="logo" src="${fileUrl(l)}">`).join('<span class="sep"></span>')
      : `<span class="name">${esc(s.pill)}</span>`;
    media = `<img class="photo dim" src="${fileUrl(s.photo)}">
      <div class="pill${s.logos && s.logos.length > 1 ? ' two' : ''}">${inner}</div>`;
  }
  return `<section class="slide story" style="left:${num * W}px">
    ${header(false)}
    <div class="ghost">${pad(num)}</div>
    <div class="media">${media}
      <div class="badge">${pad(num)}<small>/${pad(N)}</small></div>
    </div>
    <div class="tag">${esc(s.category)}</div>
    <div class="titlebox"><h1 class="fit">${hl(s.title)}</h1></div>
    <p class="line">${esc(s.line)}${s.note ? `<em>${esc(s.note)}</em>` : ''}</p>
    <div class="count">${pad(num)} <span>/ ${pad(N)}</span></div>
    ${progress(num)}
  </section>`;
}

function recap() {
  const rows = data.recap.map((r, i) => `<li><b>${i + 1}</b><span>${esc(r)}</span></li>`).join('');
  return `<section class="slide recap" style="left:${(N + 1) * W}px">
    ${header(false)}
    <h2>${hl(data.recapTitle)}</h2>
    <div class="sub">${esc(data.recapSub)}</div>
    <ol>${rows}</ol>
    <div class="cta">
      <div class="handle">@incbusiness.official</div>
      <div class="ctasub">Top business news every day, in simple words</div>
      <div class="acts"><span>SAVE</span><span>SHARE</span><span class="red">FOLLOW</span></div>
    </div>
    <div class="follow">FOLLOW FOR TOMORROW'S ${N} ${ARROW}</div>
  </section>`;
}

// Swipe pill sits across every seam: "SWIPE ->" on the right edge of slide k,
// its tail continues into the left edge of slide k+1.
const seams = Array.from({ length: SLIDES - 1 }, (_, k) =>
  `<div class="seam${k === 0 ? ' first' : ''}" style="left:${(k + 1) * W}px"><span>${k === 0 ? 'SWIPE NOW' : 'NEXT STORY'}</span>${ARROW}</div>`).join('');
const frames = Array.from({ length: SLIDES }, (_, k) => `<div class="frame" style="left:${k * W}px"></div>`).join('');

const html = `<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,500;0,600;0,700;0,800;0,900;1,800&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--red:#E03131;--red2:#D92B2B;--navy:#0B1257;--ink:#111}
body{width:${SLIDES * W}px;height:${H}px;font-family:Poppins,sans-serif;position:relative;overflow:hidden;background:#F4F4F2}
.slide{position:absolute;top:0;width:${W}px;height:${H}px;overflow:hidden;
  background:#F4F4F2;background-image:linear-gradient(#e9e9e4 1px,transparent 1px),linear-gradient(90deg,#e9e9e4 1px,transparent 1px);background-size:44px 44px}
.brand{position:absolute;top:58px;left:64px;height:44px;mix-blend-mode:multiply;z-index:3}
.hero .brand{mix-blend-mode:normal}
.date{position:absolute;top:52px;right:64px;height:56px;padding:0 26px;border-radius:28px;background:var(--navy);color:#fff;
  font-weight:700;font-size:24px;letter-spacing:1px;display:flex;align-items:center;z-index:3}
.date.dark{background:var(--red)}
.hl{color:var(--red)}

/* track line: one continuous line through every slide */
.track{position:absolute;left:0;right:0;top:1229px;height:4px;background:repeating-linear-gradient(90deg,var(--red) 0 18px,transparent 18px 30px);z-index:4;opacity:.55}

/* ---------- hero ---------- */
.hero{background:#000}
.glow{position:absolute;left:-200px;right:-200px;top:120px;height:760px;z-index:0;
  background:radial-gradient(closest-side,rgba(224,49,49,.55),rgba(224,49,49,.12) 60%,transparent)}
.wall{position:absolute;left:50%;top:70px;width:960px;margin-left:-480px;display:grid;grid-template-columns:repeat(3,1fr);gap:16px;z-index:0;
  transform:perspective(1600px) rotateX(14deg) rotateZ(-4deg);transform-origin:50% 40%}
.wt{position:relative;height:250px;border-radius:22px;overflow:hidden;background:#111;box-shadow:0 18px 40px rgba(0,0,0,.6);border:2px solid rgba(255,255,255,.12)}
.wall{opacity:.5;filter:saturate(.7) blur(1.2px)}
.wt.big{transform:scale(1.14);z-index:2;border:4px solid #E03131;box-shadow:0 0 0 6px rgba(224,49,49,.25),0 24px 60px rgba(0,0,0,.8)}
.wphoto{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;filter:brightness(.5) saturate(1.2)}
.wphoto.full{filter:brightness(.9)}
.wpill{position:absolute;left:50%;top:44%;transform:translate(-50%,-50%);background:#fff;border-radius:18px;height:84px;padding:0 24px;
  display:flex;align-items:center;justify-content:center;box-shadow:0 8px 20px rgba(0,0,0,.4);white-space:nowrap}
.wpill img{height:52px;max-width:220px;object-fit:contain}
.wpill.two{padding:0 16px}.wpill.two img{height:30px;max-width:120px}
.wpill.long b{font-size:28px}
.wpill i{width:2px;height:44px;background:#ddd;margin:0 14px}
.wpill b{font-weight:800;font-size:38px;letter-spacing:-.5px}
.dlogo{position:absolute;left:50%;top:44%;transform:translate(-50%,-50%);max-width:240px;max-height:70px;filter:drop-shadow(0 4px 12px rgba(0,0,0,.6))}
.wstat{position:absolute;left:14px;bottom:14px;background:#fff;color:#111;font-weight:800;font-size:30px;border-radius:12px;padding:4px 14px;display:flex;align-items:center;gap:8px}
.wstat span{font-size:20px}
.wstat.up span{color:#12a150}.wstat.down span,.wstat.warn span{color:#E03131}
.wstat.down,.wstat.warn{background:#E03131;color:#fff}.wstat.down span,.wstat.warn span{color:#fff}
.wstat,.wnum{display:none}
.wnum{position:absolute;right:12px;top:10px;color:#fff;font-weight:800;font-size:24px;opacity:.85}
.shade{position:absolute;inset:0;z-index:1;pointer-events:none;
  background:linear-gradient(180deg,rgba(0,0,0,.5) 0%,rgba(0,0,0,.05) 14%,rgba(0,0,0,.25) 34%,rgba(0,0,0,.9) 48%,#000 56%)}
.counter{position:absolute;top:52px;right:52px;z-index:3;height:60px;padding:0 24px;border-radius:30px;background:rgba(20,20,30,.6);
  color:#fff;font-weight:600;font-size:26px;display:flex;align-items:center;backdrop-filter:blur(6px)}
.headline{position:absolute;left:36px;right:36px;bottom:260px;z-index:3;text-align:center;color:#fff;font-weight:900;font-size:84px;
  line-height:1.12;letter-spacing:-2.5px;text-shadow:0 6px 24px rgba(0,0,0,.6)}
.headline .hlbox{display:inline-block;background:linear-gradient(90deg,#E03131 0%,#B3122A 70%,rgba(140,10,30,.85) 100%);
  border-radius:12px;padding:0 18px 6px;margin:8px 0;text-shadow:none;white-space:nowrap}
.nudge{position:absolute;left:0;right:0;top:1118px;z-index:3;text-align:center;color:#fff;font-weight:600;font-size:34px}
.nudge b{color:#ff5a5a}
/* ---------- story ---------- */
.ghost{position:absolute;right:30px;top:640px;font-weight:900;font-size:420px;line-height:1;color:rgba(11,18,87,.045);letter-spacing:-20px;z-index:0}
.media{position:absolute;left:64px;right:64px;top:140px;height:540px;border-radius:30px;overflow:hidden;background:#0a1640;box-shadow:0 22px 44px rgba(0,0,0,.18);z-index:1}
.photo{width:100%;height:100%;object-fit:cover;display:block}
.dim{filter:brightness(.55) saturate(1.2)}
.pill{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);background:#fff;border-radius:40px;min-width:480px;height:160px;max-width:820px;
  padding:0 54px;display:flex;align-items:center;justify-content:center;box-shadow:0 10px 30px rgba(0,0,0,.35)}
.logo{height:112px;width:auto;max-width:540px;object-fit:contain}
.pill.two .logo{height:64px;max-width:290px}
.sep{width:2px;height:76px;background:#ddd;margin:0 32px}
.name{font-weight:800;font-size:76px;color:var(--ink);letter-spacing:-1px;white-space:nowrap}
.badge{position:absolute;left:26px;top:26px;background:var(--red);color:#fff;font-weight:800;font-size:46px;line-height:1;border-radius:20px;padding:16px 22px 14px;
  box-shadow:0 8px 20px rgba(0,0,0,.3)}
.badge small{font-size:24px;font-weight:700;opacity:.8;margin-left:2px}
.tag{position:absolute;top:640px;left:50%;transform:translateX(-50%);background:var(--red2);color:#fff;font-weight:700;font-size:34px;white-space:nowrap;
  height:84px;padding:0 62px;display:flex;align-items:center;clip-path:polygon(9% 0,91% 0,100% 50%,91% 100%,9% 100%,0 50%);z-index:2}
.titlebox{position:absolute;left:64px;right:64px;top:752px;height:258px;display:flex;align-items:center;z-index:1}
.titlebox h1{font-weight:800;line-height:1.07;color:var(--ink);letter-spacing:-1.5px}
.line{position:absolute;left:64px;right:64px;top:1026px;border-left:8px solid var(--red);padding:4px 0 4px 26px;font-weight:500;font-size:32px;line-height:1.35;color:#3a3a46;z-index:1}
.line em{display:block;font-style:normal;font-size:22px;color:#8a8a96;margin-top:6px}
.count{position:absolute;left:150px;top:1205px;z-index:5;font-weight:800;font-size:40px;color:var(--navy);line-height:50px;background:#F4F4F2;padding:0 16px}
.count span{color:#9a9aa8;font-size:28px}
.prog{position:absolute;left:316px;top:1220px;z-index:5;display:flex;gap:8px;background:#F4F4F2;padding:0 14px}
.prog i{width:20px;height:20px;border-radius:50%;background:#d8d8de;display:block}
.prog i.done{background:#f1a5a5}
.prog i.on{background:var(--red);box-shadow:0 0 0 5px rgba(224,49,49,.22)}

/* ---------- recap ---------- */
.recap h2{position:absolute;left:64px;top:150px;font-weight:800;font-size:96px;letter-spacing:-2px;color:var(--ink);line-height:1}
.recap .sub{position:absolute;left:66px;top:262px;font-weight:600;font-size:30px;color:#6a6a78}
.recap ol{position:absolute;left:64px;right:64px;top:318px;list-style:none;background:#fff;border-radius:28px;padding:20px 34px;box-shadow:0 18px 40px rgba(0,0,0,.10)}
.recap li{display:flex;align-items:center;gap:22px;height:60px;border-bottom:1.5px dashed #e3e3e8;font-weight:600;font-size:30px;color:var(--ink)}
.recap li:last-child{border-bottom:0}
.recap li b{flex:none;width:46px;height:46px;border-radius:50%;background:var(--red);color:#fff;font-size:24px;font-weight:800;display:flex;align-items:center;justify-content:center}
.cta{position:absolute;left:64px;right:64px;top:918px;height:240px;border-radius:28px;background:var(--navy);color:#fff;padding:28px 36px}
.handle{font-weight:800;font-size:46px;letter-spacing:-.5px}
.ctasub{font-weight:500;font-size:26px;color:#c9cdf2;margin-top:2px}
.acts{display:flex;gap:16px;margin-top:20px}
.acts span{font-weight:800;font-size:24px;letter-spacing:2px;border:2px solid rgba(255,255,255,.5);border-radius:30px;padding:6px 24px}
.acts span.red{background:var(--red);border-color:var(--red)}

.follow{position:absolute;right:${FRAME}px;top:1196px;height:70px;padding:0 34px 0 40px;border-radius:35px 0 0 35px;background:var(--red);color:#fff;z-index:6;
  display:flex;align-items:center;gap:14px;font-weight:800;font-size:28px;letter-spacing:2px;box-shadow:0 10px 24px rgba(224,49,49,.35)}
.follow svg{width:38px;height:38px}
/* ---------- connectors + frames ---------- */
.seam{position:absolute;top:1196px;height:70px;width:520px;margin-left:-400px;border-radius:35px;background:var(--red);color:#fff;z-index:6;
  display:flex;align-items:center;padding-left:36px;gap:14px;font-weight:800;font-size:30px;letter-spacing:2px;box-shadow:0 10px 24px rgba(224,49,49,.35)}
.seam.first{width:500px;margin-left:-380px}
.seam svg{width:40px;height:40px}
.frame{position:absolute;top:0;width:${W}px;height:${H}px;border:${FRAME}px solid var(--red);z-index:10;pointer-events:none}
</style></head><body>
${hero()}
${stories.map(storySlide).join('')}
${recap()}
<div class="track"></div>
${seams}
${frames}
</body></html>`;

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: SLIDES * W, height: H } });
  const htmlPath = path.join(outDir, 'carousel.html');
  fs.writeFileSync(htmlPath, html);
  await page.goto('file://' + path.resolve(htmlPath), { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  // Shrink each title until it fits its box
  await page.evaluate(() => {
    for (const h of document.querySelectorAll('h1.fit')) {
      const box = h.parentElement;
      let size = 86;
      h.style.fontSize = size + 'px';
      while ((h.scrollHeight > box.clientHeight || h.scrollWidth > box.clientWidth) && size > 48) {
        size -= 2; h.style.fontSize = size + 'px';
      }
    }
    for (const n of document.querySelectorAll('.name')) {
      let size = 76;
      while (n.scrollWidth > 680 && size > 36) { size -= 2; n.style.fontSize = size + 'px'; }
    }
  });
  const slidesDir = path.join(outDir, 'slides');
  fs.mkdirSync(slidesDir, { recursive: true });
  for (let k = 0; k < SLIDES; k++) {
    const file = path.join(slidesDir, `${pad(k + 1)}.png`);
    await page.screenshot({ path: file, clip: { x: k * W, y: 0, width: W, height: H } });
    console.log('rendered', file);
  }
  fs.unlinkSync(htmlPath);
  await browser.close();
})();
