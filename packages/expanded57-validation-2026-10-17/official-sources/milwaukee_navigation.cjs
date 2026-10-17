const {chromium}=require('playwright');const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const out=path.resolve(process.argv[2]||__dirname); const url='https://city.milwaukee.gov/cityclerk/lrb/ordinances/tableofcontents';
(async()=>{const b=await chromium.launch({channel:'chrome',headless:false});try{
 const c=await b.newContext({acceptDownloads:true}); const p=await c.newPage(); await p.goto(url,{waitUntil:'domcontentloaded'});
 const pop=c.waitForEvent('page');await p.getByRole('link',{name:'Residential Districts',exact:true}).click();const q=await pop;
 await q.waitForLoadState('domcontentloaded');const doc=await q.content();fs.writeFileSync(path.join(out,'raw/milwaukee_pdf_navigation.html'),doc);await q.screenshot({path:path.join(out,'raw/milwaukee_pdf_navigation.png')});
 const m={url:q.url(),retrieved_utc:new Date().toISOString(),method:'ordinary headed Chrome actual published link click',path:'raw/milwaukee_pdf_navigation.html',bytes:Buffer.byteLength(doc),sha256:crypto.createHash('sha256').update(doc).digest('hex'),title:await q.title(),challenge:/Just a moment|challenge-platform/.test(doc)};fs.writeFileSync(path.join(out,'raw/milwaukee_pdf_navigation.meta.json'),JSON.stringify(m,null,2));console.log(JSON.stringify(m));
}finally{await b.close();}})().catch(e=>{console.error(e);process.exitCode=1});
