/** Reproducible acquisition using ONLY the documented Codex CUA/IAB browser API.
 * Load this module in cua_repl and pass its initialized `cua` object.
 * No credentials, HTTP APIs, challenge solving, stealth, or TLS overrides.
 */
import {mkdir,writeFile,readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {sha256Browser} from './sha256_browser.mjs';
const hash = value => createHash('sha256').update(value).digest('hex');
export function domFingerprint(s){let a=2166136261,b=2246822519;for(let i=0;i<s.length;i++){a=Math.imul(a^s.charCodeAt(i),16777619);b=Math.imul(b^s.charCodeAt(i),3266489917);}return s.length+':'+(a>>>0)+':'+(b>>>0);}
const moduleHash=hash(await readFile(new URL(import.meta.url)));
export async function createAcquirer(cua,outputRoot,firstUrl,options={}) {
 const browserId=options.browserId||'iab';
 const browserOptions=browserId==='iab'?{visible:false}:{sessionName:options.sessionName||'🏛 Municipal E2E'};
 const tab=await cua.createBrowserTab(browserId,firstUrl,browserOptions);
 return {tab,outputRoot,moduleHash,browserId,closed:false};
}
export async function captureJob(acquirer,job) {
 const {tab,outputRoot}=acquirer;
 if(acquirer.closed)throw Error('Acquirer already closed');
 const url=new URL(job.url);
 if(url.protocol!=='https:'||!url.hostname.endsWith('.municipal.codes'))throw Error('Only public HTTPS municipal.codes jobs accepted');
 if(!/^[a-z0-9_-]+$/.test(job.slug)||!/^[a-z0-9_-]+$/.test(job.id))throw Error('Safe slug/id required');
 const dir=outputRoot+'/'+job.slug;await mkdir(dir,{recursive:true});
 const prefix=dir+'/'+job.id;const started=new Date().toISOString();let navigation_error=null,readiness_error=null;
 try{if(await tab.url()!==job.url)await tab.goto(job.url);}catch(e){navigation_error=String(e);}
 try{await tab.playwright.locator(job.wait_selector||'main').first().waitFor({state:'attached',timeoutMs:12000});}catch(e){readiness_error=String(e);}
 const ax=await tab.getAXState({emit:false});await writeFile(prefix+'.ax.txt',String(ax));
 const snapshotExpression='(()=>{const checksum='+sha256Browser.toString()+';const html=document.documentElement.outerHTML;return {url:location.href,title:document.title,length:html.length,contents_links:document.querySelectorAll("main ul.contents-toc a[href]").length,section_cards:document.querySelectorAll("main article.type-Section").length,main:!!document.querySelector("main"),challenge:!!document.querySelector("#challenge-form,#cf-error-details")||/just a moment|attention required|access denied/i.test(document.title),currency:document.querySelector("#site-footer, .site-footer, footer")?.textContent||"",dom_sha256:checksum(html)};})()';
 const before=await tab.playwright.evaluate(snapshotExpression);
 if(before.length>3000000)throw Error('DOM exceeds bounded capture limit of 3 million UTF16 units');
 const pieces=[];
 for(let offset=0;offset<before.length;offset+=40000){
  const piece=await tab.playwright.evaluate(({offset})=>document.documentElement.outerHTML.slice(offset,offset+40000),{offset});
  if(typeof piece!=='string'||piece.length>40000)throw Error('Unexpected DOM chunk');
  pieces.push(piece);
 }
 const html=pieces.join('');const path=prefix+'.html';await writeFile(path,html);
 const after=await tab.playwright.evaluate(snapshotExpression);
 const raw=await readFile(path);
 const identity=job.expected_id ? await tab.playwright.evaluate(({id})=>!!document.getElementById(id),{id:job.expected_id}):null;
 const accepted=!navigation_error&&!readiness_error&&before.dom_sha256===hash(raw)&&after.dom_sha256===hash(raw)&&!before.challenge&&before.main&&before.url===job.url&&after.url===job.url&&html.length===before.length&&after.length===before.length&&html.endsWith('</html>')&&(!job.expected_id||identity)&&(job.kind!=='contents'||before.contents_links>0);
 const receipt={schema_version:1,job,started_at:started,finished_at:new Date().toISOString(),transport:'Codex CUA documented browser API',runtime:{node:'managed cua_repl runtime; node global unavailable',context:'cua_repl',browser:acquirer.browserId},acquisition_script_sha256:moduleHash,checksum_helper_sha256:hash(await readFile(new URL('./sha256_browser.mjs',import.meta.url))),raw_artifact_path:job.id+'.html',sha256:hash(raw),bytes:raw.length,utf16_length:html.length,browser_state:before,after_capture:after,expected_node_found:identity,navigation_error,readiness_error,http_status:null,accepted,whole_corpus_complete:false};
 await writeFile(prefix+'.receipt.json',JSON.stringify(receipt,null,2)+'\n');
 return {slug:job.slug,id:job.id,accepted,bytes:raw.length,sha256:receipt.sha256,sections:before.section_cards,contents_links:before.contents_links,title:before.title};
}
export async function closeAcquirer(acquirer){if(!acquirer.closed){await acquirer.tab.close();acquirer.closed=true;}}
