// Renders transparent 1080x1920 overlays (reel + cover) per entry: node render-overlays.js [id...]
const {chromium}=require('playwright');const fs=require('fs');const path=require('path');
(async()=>{
  const all=JSON.parse(fs.readFileSync(path.join(__dirname,'data/reels.json')));
  const ids=process.argv.slice(2);const list=ids.length?all.filter(r=>ids.includes(r.id)):all;
  const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
  await p.goto('file://'+path.join(__dirname,'template/theme.html'));await p.evaluate(()=>document.fonts.ready);
  fs.mkdirSync(path.join(__dirname,'build'),{recursive:true});
  for(const r of list) for(const mode of ['reel','cover']){
    await p.evaluate(([r,m])=>window.render(r,m),[r,mode]);
    await p.evaluate(()=>Promise.all([...document.images].map(i=>i.complete?1:new Promise(f=>i.onload=i.onerror=f))));
    const box=await p.evaluate(()=>{const b=document.getElementById('w').getBoundingClientRect();return {top:b.top,bottom:b.bottom,sh:document.getElementById('w').scrollHeight,ch:document.getElementById('w').clientHeight}});
    if(mode==='reel'&&box.bottom>1600) console.warn(`WARN ${r.id} reel: content ends at ${Math.round(box.bottom)}px (keep < 1600)`);
    if(mode==='cover'&&box.sh>box.ch+2) console.warn(`WARN ${r.id} cover: content overflows the 3:4 grid area`);
    await p.screenshot({path:path.join(__dirname,'build',`${r.id}-${mode}.png`),omitBackground:true});
    console.log(mode,r.id,Math.round(box.bottom));
  }
  await b.close();
})();
