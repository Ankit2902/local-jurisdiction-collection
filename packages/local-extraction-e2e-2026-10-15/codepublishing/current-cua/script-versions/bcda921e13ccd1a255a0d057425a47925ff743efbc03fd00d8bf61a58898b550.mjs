/** Reproducible acquisition using ONLY the documented Codex CUA/IAB browser API.
 * Load this module in cua_repl and pass its initialized `cua` object.
 * No credentials, HTTP APIs, challenge solving, stealth, or TLS overrides.
 */
import {mkdir,writeFile,readFile,appendFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const fingerprint = value => {let a=2166136261,b=5381;for(let i=0;i<value.length;i++){a=Math.imul(a^value.charCodeAt(i),16777619);b=Math.imul(b,33)^value.charCodeAt(i);}return (a>>>0).toString(16)+':'+(b>>>0).toString(16);};
const hash = value => createHash('sha256').update(value).digest('hex');
const moduleHash=hash(await readFile(new URL(import.meta.url)));
export async function createAcquirer(cua,outputRoot,firstUrl,options={}) {
 const browserId=options.browserId||'iab';
 const browserOptions=browserId==='iab'?{visible:false}:{sessionName:options.sessionName||'📚 Code Publishing E2E'};
 const tab=await cua.createBrowserTab(browserId,firstUrl,browserOptions);
 return {tab,outputRoot,moduleHash,browserId,closed:false};
}
export async function captureJob(acquirer,job) {
 const {tab,outputRoot}=acquirer;
 if(acquirer.closed)throw Error('Acquirer already closed');
 const url=new URL(job.url);
 if(url.protocol!=='https:'||url.hostname!=='www.codepublishing.com')throw Error('Only public HTTPS codepublishing.com jobs accepted');
 if(!/^[a-z0-9_-]+$/.test(job.slug)||!/^[a-z0-9_-]+$/.test(job.id))throw Error('Safe slug/id required');
 const scope=new URL(job.root_url);
 if(url.origin!==scope.origin||!(url.pathname+'/').startsWith(scope.pathname.replace(/\/?$/,'/')))throw Error('Out-of-jurisdiction source URL');
 const dir=outputRoot+'/'+job.slug;await mkdir(dir,{recursive:true});
 const prefix=dir+'/'+job.id;const started=new Date().toISOString();let navigation_error=null,readiness_error=null;
 try{if(job.refresh&&await tab.url()===job.url)await tab.reload();else if(await tab.url()!==job.url)await tab.goto(job.url);}catch(e){navigation_error=String(e);}
 try{await tab.playwright.locator(job.wait_selector||'body').first().waitFor({state:'attached',timeoutMs:12000});}catch(e){readiness_error=String(e);}
 const ax=await tab.getAXState({emit:false});await writeFile(prefix+'.ax.txt',String(ax));
 const before=await tab.playwright.evaluate(async()=>{const full=document.documentElement.outerHTML;let a=2166136261,b=5381;for(let i=0;i<full.length;i++){a=Math.imul(a^full.charCodeAt(i),16777619);b=Math.imul(b,33)^full.charCodeAt(i);}const fp=(a>>>0).toString(16)+':'+(b>>>0).toString(16);return ({fingerprint:fp,url:location.href,title:document.title,length:document.documentElement.outerHTML.length,
 main:!!document.querySelector('#mainContent'),
 legal_headings:Array.from(document.querySelectorAll('#mainContent h3.Cite')).map(h=>({id:h.id,text:h.textContent.trim()})),
 main_links:Array.from(document.querySelectorAll('#mainContent a[href]')).map(a=>({label:a.textContent.trim(),href:a.getAttribute('href'),container_class:a.parentElement.className})),
 all_links:Array.from(document.querySelectorAll('a[href]')).map(a=>({label:a.textContent.trim(),href:a.getAttribute('href')})),
 frames:Array.from(document.querySelectorAll('frame,iframe')).map(f=>({name:f.name,src:f.getAttribute('src')})),
 challenge:!!document.querySelector('#challenge-form,#cf-error-details')||/just a moment|attention required|access denied/i.test(document.title),
 currency:(document.querySelector('#pgFooter')?.textContent||document.body?.textContent||'').match(/(?:The )?[^.\n]*?(?:current through|Current through)[^.\n]*\./)?.[0]?.trim()||'',
 body_text:document.body?.innerText?.slice(0,10000)||''});});
 const path=prefix+'.html';await writeFile(path,'');
 for(let offset=0;offset<before.length;offset+=40000){
  const piece=await tab.playwright.evaluate(({offset})=>document.documentElement.outerHTML.slice(offset,offset+40000),{offset});
  if(typeof piece!=='string'||piece.length>40000)throw Error('Unexpected DOM chunk');
  await appendFile(path,piece);
 }
 const after=await tab.playwright.evaluate(()=>{const html=document.documentElement.outerHTML;let a=2166136261,b=5381;for(let i=0;i<html.length;i++){a=Math.imul(a^html.charCodeAt(i),16777619);b=Math.imul(b,33)^html.charCodeAt(i);}return {url:location.href,length:html.length,fingerprint:(a>>>0).toString(16)+':'+(b>>>0).toString(16)};});
 const raw=await readFile(path);const html=raw.toString('utf8');
 let secondPassEqual=true;for(let offset=0;offset<html.length;offset+=40000){const piece=await tab.playwright.evaluate(({offset})=>document.documentElement.outerHTML.slice(offset,offset+40000),{offset});if(piece!==html.slice(offset,offset+40000))secondPassEqual=false;}
 const identity=job.expected_id ? await tab.playwright.evaluate(({id})=>!!document.getElementById(id),{id:job.expected_id}):null;
 const accepted=!navigation_error&&!readiness_error&&secondPassEqual&&before.fingerprint===fingerprint(html)&&after.fingerprint===fingerprint(html)&&!before.challenge&&(job.kind!=='legal'||(before.main&&before.legal_headings.length>0))&&before.url===job.url&&after.url===job.url&&html.length===before.length&&after.length===before.length&&html.endsWith('</html>')&&(!job.expected_id||identity);
 const receipt={schema_version:1,job,started_at:started,finished_at:new Date().toISOString(),transport:'Codex CUA documented browser API',runtime:{node:'managed cua_repl runtime; node global unavailable',context:'cua_repl',browser:acquirer.browserId},acquisition_script_sha256:moduleHash,integrity:{secondPassEqual,fingerprint:fingerprint(html),algorithm:'two whole-DOM UTF16 fingerprints plus two byte-identical chunk passes and retained UTF8 SHA256'},raw_artifact_path:job.id+'.html',sha256:hash(raw),bytes:raw.length,utf16_length:html.length,browser_state:before,after_capture:after,expected_node_found:identity,navigation_error,readiness_error,http_status:null,accepted,whole_corpus_complete:false};
 await writeFile(prefix+'.receipt.json',JSON.stringify(receipt,null,2)+'\n');
 return {slug:job.slug,id:job.id,accepted,bytes:raw.length,sha256:receipt.sha256,sections:before.legal_headings.length,links:before.all_links.length,title:before.title};
}
export async function closeAcquirer(acquirer){if(!acquirer.closed){await acquirer.tab.close();acquirer.closed=true;}}
