const {chromium}=require('/opt/node22/lib/node_modules/playwright');
const {spawn}=require('child_process');const fs=require('fs');
(async()=>{
  const mode=process.argv[2]; // 'stills' or 'video'
  const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'}).catch(()=>chromium.launch());
  const pg=await b.newPage({viewport:{width:1080,height:1920}});
  await pg.goto('file://'+__dirname+'/anim.html');await pg.evaluate(()=>document.fonts.ready);
  await pg.waitForTimeout(500);
  const grab=async t=>{const d=await pg.evaluate(t=>{draw(t);return document.getElementById('c').toDataURL('image/jpeg',0.93)},t);return Buffer.from(d.split(',')[1],'base64')};
  if(mode==='stills'){
    const ts=process.argv.slice(3).map(Number);fs.mkdirSync('stills',{recursive:true});
    for(const t of ts){fs.writeFileSync(`stills/${t.toFixed(1)}.jpg`,await grab(t))}
  } else {
    const total=JSON.parse(fs.readFileSync('timeline.json')).total, fps=30, N=Math.ceil(total*fps);
    const ff=spawn('ffmpeg',['-v','error','-y','-f','image2pipe','-framerate',String(fps),'-c:v','mjpeg','-i','-','-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-preset','medium','silent.mp4'],{stdio:['pipe','inherit','inherit']});
    for(let f=0;f<N;f++){const buf=await grab(f/fps);if(!ff.stdin.write(buf))await new Promise(r=>ff.stdin.once('drain',r));if(f%300===0)console.log('frame',f,'/',N)}
    ff.stdin.end();await new Promise(r=>ff.on('close',r));
  }
  await b.close();
})();
