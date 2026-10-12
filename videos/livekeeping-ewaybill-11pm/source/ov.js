const {chromium}=require('/opt/node22/lib/node_modules/playwright');
const items={
 t1:'<div class="title"><div class="tag">🌙 रात 11:00 बजे</div><br>ट्रक तैयार…<br>पर <span class="r">E-Way Bill</span> नहीं! 😰</div>',
 t2:'<div class="title" style="font-size:76px">ऑफिस बंद ❌<br>Tally दूर ❌</div>',
 t3:'<div class="title" style="font-size:72px">पर मैनेजर के पास है<br><b>Livekeeping</b> 📱</div>',
 t4:'<div class="title"><div class="tag g">✅ 11:03 PM</div><br>बिल तैयार,<br>टेंशन ख़त्म! 👍</div>',
 t5:'<div class="title">ट्रक रवाना! 🚚💨</div>',
 s1:'<div class="sub"><span><i>रामू:</i> साहब! रात के 11 बज गए…<br>ट्रक तैयार है, पर ई-वे बिल नहीं बना!</span></div>',
 s2:'<div class="sub"><span><i>रामू:</i> ऑफिस बंद है, टैली वाला कंप्यूटर<br>भी वहीं है… अब क्या करें?</span></div>',
 s3:'<div class="sub"><span><i>शर्मा जी:</i> अरे रामू, टेंशन मत लो।<br>फ़ोन है ना!</span></div>',
 s5:'<div class="sub"><span><i>रामू:</i> वाह साहब! बिल आ गया!<br>चलो, निकलता हूँ!</span></div>',
};
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
await p.goto('file://'+process.cwd()+'/ov.html');
for(const [k,h] of Object.entries(items)){await p.evaluate(h=>{document.getElementById('c').innerHTML=h},h);await p.evaluate(()=>document.fonts.ready);await p.screenshot({path:`ov_${k}.png`,omitBackground:true});}
await b.close();})();
