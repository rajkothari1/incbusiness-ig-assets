const {chromium}=require('playwright');
(async()=>{const [,,file,out,w,h,scale]=process.argv;const b=await chromium.launch();const p=await b.newPage({viewport:{width:+w,height:+h},deviceScaleFactor:+(scale||1)});
await p.goto('file://'+require('path').resolve(file));await p.waitForTimeout(800);await p.screenshot({path:out});await b.close();})();
