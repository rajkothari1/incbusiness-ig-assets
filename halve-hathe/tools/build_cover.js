// Rebuilds the cover as vector art: 140x210mm page, design canvas 1400x2100
const fs=require('fs'),path=require('path');
const F='node_modules/@fontsource';
const ff=(fam,dir,w)=>`@font-face{font-family:'${fam}';font-weight:${w};src:url('../tools/${F}/${dir}/files/${dir}-gujarati-${w}-normal.woff2') format('woff2');}`;
const fonts=[ff('Noto Sans Gujarati','noto-sans-gujarati',900),ff('Baloo Bhai 2','baloo-bhai-2',800),ff('Mukta Vaani','mukta-vaani',700),ff('Mukta Vaani','mukta-vaani',800)].join('\n');
const art=(n,x,y,w,h)=>{const s=fs.readFileSync(`../art/${n}.svg`,'utf8');const vb=s.match(/viewBox="([^"]+)"/)[1];
  const body=s.replace(/^[\s\S]*?<svg[^>]*>/,'').replace(/<\/svg>\s*$/,'');
  return `<svg x="${x}" y="${y}" width="${w}" height="${h}" viewBox="${vb}" preserveAspectRatio="xMidYMid meet">${body}</svg>`;};
// seeded starburst
function burst(cx,cy,ai,bi,ao,bo,n,seed,rot=0){let r=seed;const rnd=()=>{r=(r*16807)%2147483647;return r/2147483647;};
  const se=(v)=>Math.sign(v)*Math.pow(Math.abs(v),0.5);
  const p=[];for(let i=0;i<n*2;i++){const t=rot+i*Math.PI/n+(rnd()-.5)*0.12;const out=i%2==0;
  const c=Math.cos(t),s=Math.sin(t);let x=ai*se(c),y=bi*se(s);
  if(out){const L=Math.hypot(x,y),e=(ao-ai)*(0.7+rnd()*0.6);x+=x/L*e;y+=y/L*e;}
  p.push(`${(cx+x).toFixed(1)},${(cy+y).toFixed(1)}`);}
  return `<polygon points="${p.join(' ')}" fill="#fffef8" stroke="#1d1d3a" stroke-width="3.5" stroke-linejoin="miter"/>`;}
const tri=[ // pastel geometric panel, top-right
 ['720,475 1400,470 1400,700','#9fd3f0'],['980,470 1400,470 1400,1050','#f5b9c4'],['1200,470 1400,470 1400,900','#b8a8e0'],
 ['820,820 1300,560 1400,1000','#fbf1a0'],['950,700 1150,560 1050,900','#2e9b5a'],['820,820 1000,700 1180,1000','#a8e0d0'],
 ['1100,960 1400,880 1400,1350','#f2a0c8'],['1240,640 1400,600 1400,800','#f7a8a0'],['1150,760 1400,760 1300,960','#d9f07a']];
const tris=tri.map(([p,c])=>`<polygon points="${p}" fill="${c}" fill-opacity="0.78" stroke="#ffffff" stroke-opacity=".7" stroke-width="2"/>`).join('');
const html=`<!doctype html><html><head><meta charset="utf-8"><style>${fonts}
@page{size:140mm 210mm;margin:0}html,body{margin:0;padding:0}svg.page{width:140mm;height:210mm;display:block}</style></head><body>
<svg class="page" viewBox="0 0 1400 2100" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#93ca45"/><stop offset="1" stop-color="#7fbb36"/></linearGradient>
<clipPath id="pg"><rect width="1400" height="2100"/></clipPath></defs>
<g clip-path="url(#pg)">
<rect width="1400" height="2100" fill="url(#g)"/>
${tris}
<rect x="40" y="48" width="1320" height="350" fill="#fffef8" stroke="#1d1d3a" stroke-width="3"/>
<text x="700" y="262" text-anchor="middle" font-family="Noto Sans Gujarati" font-weight="900" font-size="215" fill="#d4202c" letter-spacing="18">હળવે હાથે</text>
<text x="700" y="364" text-anchor="middle" font-family="Mukta Vaani" font-weight="700" font-size="58" fill="#26245f" letter-spacing="2">(હાસ્ય, કટાક્ષ અને અધ્યાત્મનો ત્રિવેણી સંગમ)</text>
<rect x="68" y="436" width="1264" height="44" fill="#fffef8" stroke="#1d1d3a" stroke-width="3"/>
${burst(1165,1532,205,325,330,0,9,7,-0.3)}
${burst(330,1555,230,290,350,0,9,19,0.2)}
${burst(742,1040,285,260,420,0,12,3,-1.2)}
${art('dentist',490,815,505,450)}
${art('handstand',130,1295,400,520)}
${art('cricketer',995,1235,340,595)}
<rect x="565" y="1738" width="330" height="58" fill="#fffef8" stroke="#1d1d3a" stroke-width="3"/>
<text x="730" y="1781" text-anchor="middle" font-family="Mukta Vaani" font-weight="800" font-size="42" fill="#d4202c" letter-spacing="1">નટવર ખી. શાહ</text>
</g></svg></body></html>`;
fs.mkdirSync('../build',{recursive:true});fs.writeFileSync('../build/000_cover.html',html);console.log('ok');
