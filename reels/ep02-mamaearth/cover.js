// Renders cover.html to the Instagram reel cover (1080x1920 JPG) plus a 3:4 grid-crop preview.
const path = require('path');
const { chromium } = require(require.resolve('playwright', { paths: ['/opt/node22/lib/node_modules'] }));
(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto('file://' + path.join(__dirname, 'cover.html'));
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: path.join(__dirname, 'ep02-mamaearth-cover.jpg'), type: 'jpeg', quality: 95 });
  await browser.close();
})();
