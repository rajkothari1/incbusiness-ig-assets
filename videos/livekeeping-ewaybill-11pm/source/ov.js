const {chromium}=require('/opt/node22/lib/node_modules/playwright');
const items={
 t1:'<div class="title"><div class="tag">🌙 Raat 11:00 baje</div><br>Truck taiyaar…<br>par <span class="r">E-Way Bill</span> nahi! 😰</div>',
 t2:'<div class="title" style="font-size:80px">Office band ❌<br>Tally door ❌</div>',
 t3:'<div class="title" style="font-size:74px">Par manager ke paas hai<br><b>Livekeeping</b> 📱</div>',
 t4:'<div class="title"><div class="tag g">✅ 11:03 PM</div><br>Bill taiyaar,<br>tension khatam! 👍</div>',
 t5:'<div class="title">Truck rawaana! 🚚💨</div>',
 lg:'<div class="badge"><img src="logo_full.png"></div>',
 s1:'<div class="sub"><span><i>Ramu:</i> Sir! The truck is ready,<br>but no E-Way Bill!</span></div>',
 s2:'<div class="sub"><span><i>Ramu:</i> Office closed, Tally\'s there too…<br>what do we do now?!</span></div>',
 s3:'<div class="sub"><span><i>Sharma ji:</i> Relax,<br>I have my phone!</span></div>',
 s5:'<div class="sub"><span><i>Ramu:</i> Wow sir!<br>I\'m off!</span></div>',
 sh:'<div class="sub"><span>11 PM! Truck out without E-Way Bill?<br>Straight penalty!</span></div>',
 s6:'<div class="sub"><span>Download Livekeeping —<br>E-Way Bill in 1 second!</span></div>',
};
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
await p.goto('file://'+process.cwd()+'/ov.html');
for(const [k,h] of Object.entries(items)){await p.evaluate(h=>{document.getElementById('c').innerHTML=h},h);await p.evaluate(()=>document.fonts.ready);await p.screenshot({path:`ov_${k}.png`,omitBackground:true});}
await b.close();})();
