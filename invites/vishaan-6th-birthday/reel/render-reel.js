// Renders invite.html + reel.css into 30fps PNG frames: node render-reel.js <inviteDir> <outFramesDir>
const {chromium}=require('playwright');const fs=require('fs');
(async()=>{
  const [dir,out]=process.argv.slice(2);fs.mkdirSync(out,{recursive:true});
  const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
  await p.goto('file://'+dir+'/invite.html',{waitUntil:'networkidle'});
  await p.addStyleTag({path:dir+'/reel/reel.css'});
  await p.evaluate(()=>document.fonts.ready);
  await p.evaluate(()=>document.getAnimations().forEach(a=>a.pause()));
  const FPS=30,N=150;
  for(let i=0;i<N;i++){
    const t=i*1000/FPS;
    await p.evaluate(t=>document.getAnimations().forEach(a=>a.currentTime=t),t);
    await p.screenshot({path:`${out}/f${String(i).padStart(4,'0')}.png`});
  }
  await b.close();
})();
