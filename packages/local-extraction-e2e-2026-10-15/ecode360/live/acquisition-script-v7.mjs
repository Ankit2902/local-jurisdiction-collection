/** Supported CUA acquisition. Adapted from the municipal-codes team's delivered module.
 * Browser reads ONLY through documented tab.playwright APIs. Node filesystem writes
 * occur outside page evaluation. No stealth, credentials, or access-control bypass.
 */
import {mkdir,writeFile,readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {sha256Browser} from './sha256_browser.mjs';
const hash=v=>createHash('sha256').update(v).digest('hex');
const moduleHash=hash(await readFile(new URL(import.meta.url)));
const checksumModuleHash=hash(await readFile(new URL('./sha256_browser.mjs',import.meta.url)));
export async function createAcquirer(cua,outputRoot,firstUrl,options={}){
 const browserId=options.browserId||'iab';
 const opts=browserId==='iab'?{visible:false}:{sessionName:options.sessionName||'📜 eCode E2E'};
 const tab=await cua.createBrowserTab(browserId,firstUrl,opts);
 return {tab,outputRoot,moduleHash,browserId,closed:false};
}
export async function captureJob(acquirer,job){
 if(acquirer.closed)throw Error('Acquirer closed');
 const u=new URL(job.url);
 if(u.protocol!=='https:'||u.hostname!=='ecode360.com'||u.search||!/^\/(\d+|[A-Z]{2}\d{4})$/.test(u.pathname))throw Error('Only explicit public HTTPS eCode360 code routes accepted');
 if(!/^[a-z0-9-]+$/.test(job.slug)||!/^[a-z0-9-]+$/.test(job.id))throw Error('Safe slug/id required');
 const capture_selector=job.capture_selector||'#codeContent';if(!['#codeContent','html','#toc'].includes(capture_selector))throw Error('Unsupported capture selector');
 const {tab,outputRoot}=acquirer,dir=outputRoot+'/'+job.slug;await mkdir(dir,{recursive:true});
 const prefix=dir+'/'+job.id,started_at=new Date().toISOString();let navigation_error=null,readiness_error=null,before=null,after=null;
 try {
 try{if(await tab.url()!==job.url)await tab.goto(job.url);}catch(e){navigation_error=String(e);}
 try{await tab.playwright.locator(job.kind==='legal'?'.section_content':'#toc').first().waitFor({state:'attached',timeoutMs:12000});}catch(e){readiness_error=String(e);}
 const ax=await tab.getAXState({emit:false});await writeFile(prefix+'.ax.txt',String(ax));
 before=await tab.playwright.evaluate(`(()=>{const checksum=${sha256Browser.toString()};
  const html=document.querySelector(${JSON.stringify(capture_selector)}).outerHTML;const sha256=checksum(html);
  return {url:location.href,title:document.title,length:html.length,sha256,identity:{customer_id:document.body.getAttribute('data-cust-id'),code_id:document.body.getAttribute('data-code-id'),currency_raw:document.body.getAttribute('data-code-date')},challenge:!!document.querySelector('#challenge-form,#cf-error-details')||/just a moment|attention required|access denied/i.test(document.title),section_bodies:Array.from(document.querySelectorAll('.section_content')).map(x=>x.id),toc:Array.from(document.querySelectorAll('#toc .contentTitle[data-guid]')).map(t=>({node_id:t.getAttribute('data-guid'),kind:t.getAttribute('data-code-content-type'),number:t.querySelector('.titleNumber')?.textContent||'',heading:t.querySelector('.titleTitle')?.textContent||t.textContent,href:t.querySelector('a.titleLink')?.getAttribute('href')})),heading_node_id:document.querySelector('#pageTitle .titleTitle[data-guid]')?.getAttribute('data-guid'),heading_text:document.querySelector('#pageTitle')?.textContent||'',legal_header_ids:Array.from(document.querySelectorAll('header .contentTitle[data-guid]')).map(x=>x.getAttribute('data-guid')),new_law_indicators:document.querySelectorAll('[title*="New Laws"],[aria-label*="New Laws"]').length};
 })()`);
 if(before.length>2000000)throw Error('DOM exceeds bounded method-validation capture limit');
 const chunks=[];
 for(let offset=0;offset<before.length;offset+=40000){
  const piece=await tab.playwright.evaluate(({offset,selector})=>document.querySelector(selector).outerHTML.slice(offset,offset+40000),{offset,selector:capture_selector});
  if(typeof piece!=='string'||piece.length!==Math.min(40000,before.length-offset)||piece.includes('[Truncated]'))throw Error('DOM chunk incomplete/truncated at '+offset+'; expected '+Math.min(40000,before.length-offset)+'; received '+(typeof piece==='string'?piece.length:typeof piece));
  chunks.push(piece);
 }
 await writeFile(prefix+'.html',chunks.join(''),'utf8');
 after=await tab.playwright.evaluate(`(()=>{const checksum=${sha256Browser.toString()};const s=document.querySelector(${JSON.stringify(capture_selector)}).outerHTML;return {url:location.href,length:s.length,sha256:checksum(s),heading_node_id:document.querySelector('#pageTitle .titleTitle[data-guid]')?.getAttribute('data-guid'),identity:{customer_id:document.body.getAttribute('data-cust-id'),code_id:document.body.getAttribute('data-code-id'),currency_raw:document.body.getAttribute('data-code-date')}};})()`);
 const raw=await readFile(prefix+'.html'),html=raw.toString('utf8'),identityMatches=JSON.stringify(before.identity)===JSON.stringify(after.identity);
 const expectedMatches=!job.expected_identity||Object.keys(job.expected_identity).every(k=>job.expected_identity[k]===before.identity[k]);
 const expected_node_id=job.expected_node_id||u.pathname.slice(1);
 const requested_node_ready=job.kind!=='legal'||before.heading_node_id===expected_node_id||before.legal_header_ids.includes(expected_node_id);
 const expected_toc_matches=!job.expected_toc_node_ids||JSON.stringify([...job.expected_toc_node_ids].sort())===JSON.stringify(before.toc.map(x=>x.node_id).sort());
 const accepted=requested_node_ready&&expected_toc_matches&&before.heading_node_id===after.heading_node_id&&!navigation_error&&!readiness_error&&!before.challenge&&Object.values(before.identity).every(Boolean)&&before.url===job.url&&after.url===job.url&&html.length===before.length&&html.length===after.length&&hash(raw)===before.sha256&&before.sha256===after.sha256&&html.endsWith(capture_selector==='html'?'</html>':'</div>')&&identityMatches&&expectedMatches&&(job.kind!=='legal'||before.section_bodies.length>0);
 const receipt={schema_version:1,job,capture_selector,full_document:capture_selector==='html',capture_kind:capture_selector==='html'?'full document outerHTML':'exact legal-content DOM subtree',started_at,finished_at:new Date().toISOString(),transport:'supported CUA documented browser API; Node filesystem outside DOM evaluation',runtime:{node:'managed cua_repl',browser:acquirer.browserId},acquisition_script_sha256:moduleHash,checksum_module_sha256:checksumModuleHash,raw_artifact_path:job.id+'.html',sha256:hash(raw),bytes:raw.length,utf16_length:html.length,browser_state:before,after_capture:after,expected_node_id,requested_node_ready,expected_toc_matches,identity_matches:identityMatches,expected_identity_matches:expectedMatches,navigation_error,readiness_error,http_status:null,accepted,inventory_complete:false,whole_corpus_complete:false};
 await writeFile(prefix+'.receipt.json',JSON.stringify(receipt,null,2)+'\n');
 return {slug:job.slug,id:job.id,accepted,bytes:raw.length,sha256:receipt.sha256,sections:before.section_bodies.length,toc_nodes:before.toc.length,identity:before.identity,receipt_path:prefix+'.receipt.json'};
 } catch(error) {
  const failure={schema_version:1,job,started_at,finished_at:new Date().toISOString(),transport:'supported CUA',acquisition_script_sha256:moduleHash,checksum_module_sha256:checksumModuleHash,accepted:false,error:String(error),navigation_error,readiness_error,browser_state:before,after_capture:after,inventory_complete:false,whole_corpus_complete:false};
  await writeFile(prefix+'.failure.receipt.json',JSON.stringify(failure,null,2)+'\n');
  return {slug:job.slug,id:job.id,accepted:false,error:String(error),receipt_path:prefix+'.failure.receipt.json'};
 }
}
export async function closeAcquirer(acquirer){if(!acquirer.closed){await acquirer.tab.close();acquirer.closed=true;}}
