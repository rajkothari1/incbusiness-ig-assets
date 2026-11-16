// Renders every build/NNN_*.html page to PDF (vector) and merges them into the book
const {chromium}=require('playwright'),{PDFDocument}=require('pdf-lib'),fs=require('fs'),path=require('path');
(async()=>{const dir=path.resolve(__dirname,'../build');const files=fs.readdirSync(dir).filter(f=>/^\d+_.*\.html$/.test(f)).sort();
const b=await chromium.launch();const out=await PDFDocument.create();
for(const f of files){const p=await b.newPage();await p.goto('file://'+path.join(dir,f));await p.evaluate(()=>document.fonts.ready);
 const buf=await p.pdf({width:'140mm',height:'210mm',printBackground:true,preferCSSPageSize:true});
 const d=await PDFDocument.load(buf);for(const pg of await out.copyPages(d,d.getPageIndices()))out.addPage(pg);await p.close();}
out.setTitle('હળવે હાથે — નટવર ખી. શાહ');out.setAuthor('નટવર ખી. શાહ');
fs.writeFileSync(path.resolve(__dirname,'../Halve_Hathe_Natvar_Kh_Shah.pdf'),await out.save());await b.close();console.log(files.length,'pages');})();
