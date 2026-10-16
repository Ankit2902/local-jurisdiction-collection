/** Ordinary publisher Save UI in a fresh, headed standalone Chrome context. */
import {chromium} from 'playwright';
import {mkdir,writeFile,readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const sha=x=>createHash('sha256').update(x).digest('hex');
const [planPath,out]=process.argv.slice(2);const plan=JSON.parse(await readFile(planPath,'utf8'));await mkdir(out);
const script_sha256=sha(await readFile(new URL(import.meta.url)));const browser=await chromium.launch({channel:'chrome',headless:false});
try{for(const job of plan.jobs){
 const dir=out+'/'+job.slug;await mkdir(dir);const context=await browser.newContext({acceptDownloads:true});const page=await context.newPage();
 const receipt={job,script_sha256,browser:browser.version(),node:process.version,transport:'standalone ordinary headed publisher Save UI',operator_assisted:false,started_at:new Date().toISOString(),accepted:false,whole_corpus_validated:false};
 try{
  const response=await page.goto(job.share_url,{waitUntil:'domcontentloaded',timeout:30000});receipt.http_status=response?.status();
  const raw=await page.content();await writeFile(dir+'/share-before.html',raw);receipt.discovery_sha256=sha(raw);
  if(/Just a moment|Attention Required|Access denied/i.test(await page.title())||response?.status()>=400)throw Error('Access challenge/error; stopped without interaction');
  await page.locator('#share-save-tab').click();await page.locator('a[href="'+new URL(job.export_url).pathname+new URL(job.export_url).search+'"]').first().waitFor({state:'visible',timeout:10000});
  const downloadPromise=page.waitForEvent('download',{timeout:45000});await page.getByRole('link',{name:'Web Page (HTML)',exact:false}).click();
  const download=await downloadPromise;await download.saveAs(dir+'/download.html');const bytes=await readFile(dir+'/download.html');
  receipt.download_url=download.url();receipt.suggested_filename=download.suggestedFilename();receipt.raw_sha256=sha(bytes);receipt.bytes=bytes.length;receipt.download_failure=await download.failure();receipt.accepted=!receipt.download_failure&&bytes.toString('utf8').includes('id="'+job.expected_id+'"');
 }catch(error){receipt.error=String(error);}finally{await writeFile(dir+'/share-after.html',await page.content().catch(()=>''));await page.screenshot({path:dir+'/result.png',fullPage:true}).catch(()=>{});receipt.finished_at=new Date().toISOString();await writeFile(dir+'/receipt.json',JSON.stringify(receipt,null,2)+'\n');console.log(job.slug,receipt.accepted,receipt.error||receipt.bytes);await context.close();}
}}finally{await browser.close();}
