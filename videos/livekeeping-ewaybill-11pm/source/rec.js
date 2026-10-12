const {chromium}=require('/opt/node22/lib/node_modules/playwright');
(async()=>{const [,,file,outdir,fps]=process.argv;const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
await p.goto('file://'+file);await p.evaluate(()=>document.fonts.ready);const dur=await p.evaluate(()=>DUR);const n=Math.round(dur*fps);
for(let i=0;i<n;i++){await p.evaluate(t=>render(t),i/fps);await p.screenshot({path:`${outdir}/f${String(i).padStart(4,'0')}.png`});}
await b.close();})();
