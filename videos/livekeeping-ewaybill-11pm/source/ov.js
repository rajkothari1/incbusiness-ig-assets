const {chromium}=require('/opt/node22/lib/node_modules/playwright');
const items={
 t1:'<div class="title"><div class="tag">🌙 रात 11:00 बजे</div><br>ट्रक तैयार…<br>पर <span class="r">E-Way Bill</span> नहीं! 😰</div>',
 t2:'<div class="title" style="font-size:76px">ऑफिस बंद ❌<br>Tally दूर ❌</div>',
 t3:'<div class="title" style="font-size:72px">पर मैनेजर के पास है<br><b>Livekeeping</b> 📱</div>',
 t4:'<div class="title"><div class="tag g">✅ 11:03 PM</div><br>बिल तैयार,<br>टेंशन ख़त्म! 👍</div>',
 t5:'<div class="title">ट्रक रवाना! 🚚💨</div>',
 lg:'<div class="badge"><img src="logo_full.png"></div>',
 s1:'<div class="sub"><span><i>Ramu:</i> Sir! It\'s 11 PM… the truck is ready,<br>but the E-Way Bill isn\'t made!</span></div>',
 s2:'<div class="sub"><span><i>Ramu:</i> The office is closed, and the Tally<br>computer is there too… what now?</span></div>',
 s3:'<div class="sub"><span><i>Sharma ji:</i> Relax, Ramu.<br>I have my phone!</span></div>',
 s5:'<div class="sub"><span><i>Ramu:</i> Wow sir, the bill is here!<br>I\'m off!</span></div>',
 s6:'<div class="sub"><span>Download Livekeeping —<br>E-Way Bill in just 1 second!</span></div>',
};
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
await p.goto('file://'+process.cwd()+'/ov.html');
for(const [k,h] of Object.entries(items)){await p.evaluate(h=>{document.getElementById('c').innerHTML=h},h);await p.evaluate(()=>document.fonts.ready);await p.screenshot({path:`ov_${k}.png`,omitBackground:true});}
await b.close();})();
