// Renders a transparent 1080x1920 overlay PNG per reel: node render-overlays.js [id...]
const {chromium}=require('playwright');const fs=require('fs');const path=require('path');
(async()=>{
  const all=JSON.parse(fs.readFileSync(path.join(__dirname,'data/reels.json')));
  const ids=process.argv.slice(2);const list=ids.length?all.filter(r=>ids.includes(r.id)):all;
  const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
  await p.goto('file://'+path.join(__dirname,'template/reel.html'));await p.evaluate(()=>document.fonts.ready);
  fs.mkdirSync(path.join(__dirname,'build'),{recursive:true});
  for(const r of list){
    await p.evaluate(r=>window.render(r),r);
    await p.evaluate(()=>Promise.all([...document.images].map(i=>i.complete?1:new Promise(f=>i.onload=i.onerror=f))));
    const h=await p.evaluate(()=>document.getElementById('w').getBoundingClientRect().bottom);
    if(h>1600) console.warn(`WARN ${r.id}: content ends at ${Math.round(h)}px (keep < 1600 for IG safe zone)`);
    await p.screenshot({path:path.join(__dirname,'build',r.id+'.png'),omitBackground:true});
    console.log('overlay',r.id,Math.round(h));
  }
  await b.close();
})();
