/** Ordinary isolated headed Chrome: public page plus one advertised HTML export.
 * No existing profile, cookies, credentials, stealth, certificate overrides or CAPTCHA actions.
 * node standalone_acquire.mjs PLAN.json NEW_OUTPUT_DIR
 */
import {chromium} from 'playwright';
import {validateJob,validateDownloadUrl} from './transport_guards.mjs';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const sha=b=>createHash('sha256').update(b).digest('hex');
const [planPath,out]=process.argv.slice(2);if(!planPath||!out)throw Error('PLAN NEW_OUTPUT_DIR required');
const plan=JSON.parse(await readFile(planPath,'utf8'));await mkdir(out,{recursive:false});
const revision=sha(await readFile(new URL(import.meta.url)));
const browser=await chromium.launch({headless:false,channel:process.env.BROWSER_CHANNEL||'chrome'});
const stoppedHosts=new Set();
try{for(const job of plan.jobs){
 validateJob(job);const host=new URL(job.section_url).host;
 if(stoppedHosts.has(host)){console.log(job.slug,'SKIPPED host stopped by earlier429/challenge');continue;}
 const context=await browser.newContext({acceptDownloads:true});
 const d=out+'/'+job.slug;await mkdir(d);const page=await context.newPage();
 const receipt={job,transport:'standalone ordinary headed Playwright',node:process.version,playwright:'1.62.1',browser:browser.version(),script_sha256:revision,started_at:new Date().toISOString(),operator_actions:[],operator_assisted:false,stages:[],whole_corpus_validated:false};
 page.on('response',res=>{if(new URL(res.url()).host===host&&res.status()===429){stoppedHosts.add(host);receipt.host_stopped=true;(receipt.rate_limit_responses??=[]).push({url:res.url(),http_status:429,retry_after:res.headers()['retry-after']??null});void page.close().catch(()=>{});}});
 try{for(const [kind,url] of [['page',job.section_url],['html-export',job.export_url]].filter(([kind])=>!job.stages||job.stages.includes(kind))){
  if(stoppedHosts.has(host))break;
  if(!url.startsWith('https://')||!new URL(url).hostname.endsWith('.municipal.codes'))throw Error('Only advertised municipal.codes HTTPS routes');
  const started=new Date().toISOString();let response=null,error=null,download=null;
  let downloadPromise=kind==='html-export'?page.waitForEvent('download',{timeout:45000}).catch(()=>null):null;
  try{response=await page.goto(url,{waitUntil:'domcontentloaded',timeout:25000});}catch(e){error=String(e);}
  if(downloadPromise)download=await downloadPromise;
  if(kind==='page'){try{await page.locator('article[id="'+job.expected_id+'"]').waitFor({state:'attached',timeout:10000});}catch(e){error=String(e);}}
  let raw,artifact,before_sha256=null,after_sha256=null;
  if(kind==='page'){const before=Buffer.from(await page.content().catch(()=>''));await writeFile(d+'/page-before.html',before);before_sha256=sha(before);}
  if(download){validateDownloadUrl(download.url(),job);artifact=kind+'.download';await download.saveAs(d+'/'+artifact);raw=await readFile(d+'/'+artifact);}
  else{artifact=kind+'.html';raw=Buffer.from(await page.content().catch(()=>''));await writeFile(d+'/'+artifact,raw);}
  if(kind==='page'){const after=Buffer.from(await page.content().catch(()=>''));await writeFile(d+'/page-after.html',after);after_sha256=sha(after);}
  const html=raw.toString('utf8');const title=await page.title().catch(()=> '');
  const blocked=/Just a moment|Attention Required|Access denied/i.test(title)||/window\._cf_chl_opt|id="challenge-form"/.test(html);
  const expected=html.includes('id="'+job.expected_id+'"');
  const accepted=(kind==='page'?!error:!!download||!error)&&!blocked&&raw.length>0&&expected&&(!download||download.url()===url)&&(kind==='page'?page.url()===url:!!download||response?.status()===200);
  await page.screenshot({path:d+'/'+kind+'.png',fullPage:true}).catch(()=>{});
  receipt.stages.push({kind,requested_url:url,final_url:page.url(),http_status:response?.status()??null,retry_after:response?.headers()['retry-after']??null,started_at:started,finished_at:new Date().toISOString(),error,download_url:download?.url()??null,download_failure:download?await download.failure():null,download_filename:download?.suggestedFilename()??null,raw_artifact_path:artifact,raw_sha256:sha(raw),before_sha256,after_sha256,bytes:raw.length,title,expected_identity_present:expected,access_challenge:blocked,accepted});
  if(response?.status()===429||blocked){stoppedHosts.add(host);receipt.host_stopped=true;break;}
 }
 }catch(e){receipt.error=String(e);}finally{receipt.finished_at=new Date().toISOString();receipt.accepted=receipt.stages.some(s=>s.accepted);await writeFile(d+'/receipt.json',JSON.stringify(receipt,null,2)+'\n');console.log(job.slug,JSON.stringify(receipt.stages.map(s=>({kind:s.kind,status:s.http_status,accepted:s.accepted,bytes:s.bytes}))));await context.close();}
 }}finally{await browser.close();}
