// Renders invite.html + reel.css into 30fps PNG frames: node render-reel.js <inviteDir> <outFramesDir> [seconds=10]
const {chromium}=require('playwright');const fs=require('fs');
(async()=>{
  const [dir,out]=process.argv.slice(2);fs.mkdirSync(out,{recursive:true});
  const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
  await p.goto('file://'+dir+'/invite.html',{waitUntil:'networkidle'});
  await p.addStyleTag({path:dir+'/reel/reel.css'});
  const orbit=fs.readFileSync(dir+'/reel/orbit.html','utf8');
  await p.evaluate(h=>document.querySelector('.photo-wrap').insertAdjacentHTML('beforebegin',h),orbit);
  // extra rockets that fly past before the last one parks
  await p.evaluate(()=>{const r=document.querySelector('.rocket');
    for(const c of ['rk1','rk2','rk3','rk4','rk5']){const n=r.cloneNode(true);n.setAttribute('class',c);r.parentNode.insertBefore(n,r);}});
  await p.evaluate(()=>document.fonts.ready);
  await p.evaluate(()=>document.getAnimations().forEach(a=>a.pause()));
  const FPS=30,N=Math.round(FPS*(+process.argv[4]||10));
  for(let i=0;i<N;i++){
    const t=i*1000/FPS;
    await p.evaluate(t=>document.getAnimations().forEach(a=>a.currentTime=t),t);
    await p.screenshot({path:`${out}/f${String(i).padStart(4,'0')}.png`});
  }
  await b.close();
})();
