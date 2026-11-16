const potrace=require('potrace'),fs=require('fs');
for (const n of ['dentist','handstand','cricketer']) {
  potrace.trace(`art_${n}.png`,{threshold:128,turdSize:6,optTolerance:0.3,color:'#1a1a2e',background:'transparent'},(e,svg)=>{if(e)throw e;fs.writeFileSync(`../art/${n}.svg`,svg);console.log(n,'ok')});
}
