/** Public UI collection. No challenge solving, stealth, proxies or private APIs. */
import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import {fileURLToPath} from 'node:url';import {createRequire} from 'node:module';
const req=createRequire(import.meta.url);const {chromium}=req(process.env.PLAYWRIGHT_MODULE||'playwright');
const base=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');const args=process.argv.slice(2);let rows=JSON.parse(fs.readFileSync(path.join(base,'assignment.json')));const seq=args.includes('--sequence')?Number(args[args.indexOf('--sequence')+1]):null;if(seq)rows=rows.filter(r=>r.sequence===seq);
const browser=await chromium.launch({channel:process.env.BROWSER_CHANNEL||'chrome',headless:args.includes('--headless')});const page=await browser.newPage({acceptDownloads:true});page.setDefaultTimeout(25000);let last=0;
async function pace(){await new Promise(r=>setTimeout(r,Math.max(0,3500-(Date.now()-last))));last=Date.now();}
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');const write=(p,v)=>fs.writeFileSync(p,typeof v==='string'?v:JSON.stringify(v,null,2)+'\n');
for(const row of rows){
 const slug=new URL(row.source_lead_url).pathname.split('/')[2],dir=path.join(base,'raw',slug);fs.mkdirSync(dir,{recursive:true});let report={sequence:row.sequence,jurisdiction:row.jurisdiction,started_at:new Date().toISOString(),method:'Playwright installed Chrome public website UI',runtime:process.version,script_sha256:hash(fs.readFileSync(fileURLToPath(import.meta.url))),pages:[],requests:[],publisher_export:{status:'not_tested'}};let pending=[];
 const listen=r=>{if(r.url().startsWith('https://codelibrary.amlegal.com/')&&(r.request().resourceType()==='document'||r.url().includes('/api/'))){let item={url:r.url(),status:r.status(),method:r.request().method(),at:new Date().toISOString()};report.requests.push(item);if(r.url().includes('/api/export'))pending.push(r.text().then(t=>{item.response=t.slice(0,12000)}).catch(()=>{}));}};page.on('response',listen);
 async function save(name){const html=await page.content();write(path.join(dir,name+'.html'),html);const content=await page.locator('.codenav__section-body').innerText().catch(()=>page.locator('body').innerText());write(path.join(dir,name+'.txt'),content);const links=await page.locator('a.toc-link').evaluateAll(es=>es.map(e=>({text:e.textContent.trim(),url:e.href,docid:e.dataset.docid||null})));const meta={name,url:page.url(),title:await page.title(),at:new Date().toISOString(),html_sha256:hash(html),html_bytes:Buffer.byteLength(html),links};report.pages.push(meta);return meta;}
 async function go(url){await pace();const response=await page.goto(url,{waitUntil:'domcontentloaded',timeout:60000});await page.waitForTimeout(6000);if([403,429].includes(response?.status()))throw Error('Access block '+response.status());const text=await page.locator('body').innerText();if(/verify you are human|access denied|unusual traffic/i.test(text))throw Error('Access challenge; stopped');}
 try{
  await go(row.source_lead_url);let overview=await save('overview');let roots=overview.links.filter(x=>x.docid);let primary=roots[0]||overview.links.find(x=>!x.url.endsWith('overview'));if(!primary)throw Error('No publication root');report.publications=overview.links.filter(x=>!x.url.endsWith('overview'));
  await go(primary.url);let root=await save('publication');let candidates=root.links;let general=candidates.find(x=>/GENERAL PROVISIONS/i.test(x.text));
  if(!general){let vol=candidates.find(x=>/^VOLUME I$/.test(x.text))||candidates.find(x=>/^TITLE (?:1|I)\b|^CHAPTER (?:1|I)\b/i.test(x.text));if(vol){await go(vol.url);root=await save('division');general=root.links.find(x=>/GENERAL PROVISIONS/i.test(x.text))||vol;}}
  if(!general){general=root.links.find(x=>/^CHAPTER|^TITLE|^ARTICLE/i.test(x.text)&&x.docid&&x.url!==primary.url);}if(!general)throw Error('No sample division located');
  await go(general.url);let sample=await save('sample');report.sample_url=general.url;report.sample_title=general.text;
  const sections=await page.locator('.codenav__section-body [id^="section-"]').count();console.log(row.jurisdiction,'sample sections rendered',sections,general.url);
  await pace();await page.getByRole('button',{name:'Download',exact:true}).last().click();await page.waitForTimeout(2000);const dialog=page.locator('[role=dialog]');write(path.join(dir,'export-selection.html'),await dialog.innerHTML());
  // Select exactly the sampled division, using the publisher's labeled checkbox.
  const cb=dialog.getByRole('checkbox',{name:general.text,exact:true});if(await cb.count())await cb.check();
  await dialog.getByRole('button',{name:'Download',exact:true}).click();await page.waitForTimeout(800);write(path.join(dir,'export-format.html'),await dialog.innerHTML());
  await dialog.getByRole('button',{name:'Save HTML',exact:true}).click();
  await page.locator('.exports a[href*="/download/"]').first().waitFor({state:'visible',timeout:60000});
  const exportLink=await page.locator('.exports a[href*="/download/"]').first().getAttribute('href');
  write(path.join(dir,'export-after.html'),await page.content());await pace();
  const exportPage=await page.context().newPage();const er=await exportPage.goto(exportLink,{waitUntil:'domcontentloaded',timeout:60000});
  const bytes=await er.body();const ct=er.headers()['content-type']||'';await exportPage.close();
  if(er.status()!==200||!(/html|zip|octet-stream/.test(ct)))throw Error('Native export GET '+er.status()+' '+ct);
  const destination=path.join(dir,'publisher-export'+(bytes[0]===80&&bytes[1]===75?'.zip':'.html'));fs.writeFileSync(destination,bytes);
  report.publisher_export={status:'passed',url:exportLink,file:path.relative(base,destination),bytes:bytes.length,sha256:hash(bytes),content_type:ct,http_status:er.status(),scope:general.text,format:'publisher Save HTML; not browser print'};
  console.log(row.jurisdiction,'export',bytes.length,destination);
  if(await dialog.count())await page.keyboard.press('Escape');report.outcome='acquired';
 }catch(e){report.error=String(e);report.outcome='partial';write(path.join(dir,'failure.html'),await page.content().catch(()=>''));console.log(row.jurisdiction,'ERROR',String(e));}
 await Promise.allSettled(pending);report.ended_at=new Date().toISOString();write(path.join(dir,'receipt.json'),report);page.off('response',listen);
}
await browser.close();
