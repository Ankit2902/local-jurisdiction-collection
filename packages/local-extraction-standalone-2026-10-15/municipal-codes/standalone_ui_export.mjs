/** Ordinary publisher Save UI in a fresh, headed standalone Chrome context. */
import {chromium} from 'playwright';
import {validateJob,validateDownloadUrl} from './transport_guards.mjs';
import {mkdir,writeFile,readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const sha=x=>createHash('sha256').update(x).digest('hex');
const [planPath,out]=process.argv.slice(2);const plan=JSON.parse(await readFile(planPath,'utf8'));await mkdir(out);
const script_sha256=sha(await readFile(new URL(import.meta.url)));const browser=await chromium.launch({channel:'chrome',headless:false});
const stoppedHosts=new Set();
try{for(const job of plan.jobs){
 validateJob(job);const host=new URL(job.section_url).host;
 if(stoppedHosts.has(host)){console.log(job.slug,'SKIPPED host stopped by earlier429/challenge');continue;}
 const dir=out+'/'+job.slug;await mkdir(dir);const context=await browser.newContext({acceptDownloads:true});const page=await context.newPage();
 const receipt={job,script_sha256,browser:browser.version(),node:process.version,transport:'standalone ordinary headed publisher Save UI',operator_assisted:false,started_at:new Date().toISOString(),accepted:false,whole_corpus_validated:false};
 page.on('response',res=>{if(new URL(res.url()).host===host&&res.status()===429){stoppedHosts.add(host);receipt.host_stopped=true;(receipt.rate_limit_responses??=[]).push({url:res.url(),http_status:429,retry_after:res.headers()['retry-after']??null});void page.close().catch(()=>{});}});
 try{
  const response=await page.goto(job.share_url,{waitUntil:'domcontentloaded',timeout:30000});receipt.http_status=response?.status();receipt.retry_after=response?.headers()['retry-after']??null;
  if(response?.status()===429){stoppedHosts.add(host);receipt.host_stopped=true;throw Error('HTTP429; stop host and honor Retry-After');}
  const raw=await page.content();await writeFile(dir+'/share-before.html',raw);receipt.discovery_sha256=sha(raw);
  if(/Just a moment|Attention Required|Access denied/i.test(await page.title())||response?.status()>=400){stoppedHosts.add(host);receipt.host_stopped=true;throw Error('Access challenge/error; stopped without interaction');}
  if(stoppedHosts.has(host))throw Error('Host stopped after429');
  await page.locator('#share-save-tab').click();await page.locator('a[href="'+new URL(job.export_url).pathname+new URL(job.export_url).search+'"]').first().waitFor({state:'visible',timeout:10000});
  let downloadError=null;const downloadPromise=page.waitForEvent('download',{timeout:45000}).catch(error=>{downloadError=String(error);return null;});await page.getByRole('link',{name:'Web Page (HTML)',exact:false}).click();
  const download=await downloadPromise;if(!download)throw Error(downloadError||'No completed publisher download');validateDownloadUrl(download.url(),job);await download.saveAs(dir+'/download.html');const bytes=await readFile(dir+'/download.html');
  receipt.download_url=download.url();receipt.suggested_filename=download.suggestedFilename();receipt.raw_sha256=sha(bytes);receipt.bytes=bytes.length;receipt.download_failure=await download.failure();receipt.accepted=!receipt.download_failure&&bytes.toString('utf8').includes('id="'+job.expected_id+'"');
 }catch(error){receipt.error=String(error);}finally{await writeFile(dir+'/share-after.html',await page.content().catch(()=>''));await page.screenshot({path:dir+'/result.png',fullPage:true}).catch(()=>{});if(/Just a moment|Attention Required|Access denied/i.test(await page.title().catch(()=>''))){stoppedHosts.add(host);receipt.host_stopped=true;}receipt.finished_at=new Date().toISOString();await writeFile(dir+'/receipt.json',JSON.stringify(receipt,null,2)+'\n');console.log(job.slug,receipt.accepted,receipt.error||receipt.bytes);await context.close();}
}}finally{await browser.close();}
