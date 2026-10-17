// Ordinary Playwright + installed Chrome; no Codex browser/runtime dependency.
const { chromium } = require('playwright');
const fs = require('node:fs'); const path = require('node:path'); const crypto = require('node:crypto');
const out = path.resolve(process.argv[2] || __dirname); fs.mkdirSync(path.join(out,'raw'),{recursive:true});
const url='https://city.milwaukee.gov/cityclerk/lrb/ordinances/tableofcontents';
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:false});
 try {
 const context=await browser.newContext({acceptDownloads:true}); const page=await context.newPage();
 const response=await page.goto(url,{waitUntil:'domcontentloaded',timeout:60000});
 const body=await page.content(); const file='raw/milwaukee_browser_index.html'; fs.writeFileSync(path.join(out,file),body);
 const meta={url,final_url:page.url(),retrieved_utc:new Date().toISOString(),status:response?.status(),bytes:Buffer.byteLength(body),path:file,sha256:crypto.createHash('sha256').update(body).digest('hex'),method:'ordinary headed Playwright Chrome'};
 fs.writeFileSync(path.join(out,'raw/milwaukee_browser_index.meta.json'),JSON.stringify(meta,null,2)); console.log(JSON.stringify(meta));
 await page.screenshot({path:path.join(out,'raw/milwaukee_browser_index.png'),fullPage:false});
 if (response.status()!==200 || !body.includes('Volume 2')) {console.log('Access not available; no challenge interaction or retry.');return;}
 const links=await page.locator('a[href]').evaluateAll(els=>els.map(a=>({title:a.textContent.trim(),url:a.href})).filter(a=>a.url.includes('/Ordinances/')));
 fs.writeFileSync(path.join(out,'raw/milwaukee_browser_links.json'),JSON.stringify(links,null,2));
 const target=links.find(a=>a.url.endsWith('CH295-sub5.pdf')); if(!target)throw Error('Expected residential zoning link absent');
 await new Promise(r=>setTimeout(r,3000));
 const pdf=await context.request.get(target.url,{timeout:90000}); const buf=await pdf.body();const pf='raw/milwaukee_zoning_browser.pdf'; fs.writeFileSync(path.join(out,pf),buf);
 const pm={url:target.url,retrieved_utc:new Date().toISOString(),status:pdf.status(),bytes:buf.length,path:pf,sha256:crypto.createHash('sha256').update(buf).digest('hex'),headers:pdf.headers(),method:'Playwright browser-context HTTP'};fs.writeFileSync(path.join(out,'raw/milwaukee_zoning_browser.meta.json'),JSON.stringify(pm,null,2));console.log(JSON.stringify(pm));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
