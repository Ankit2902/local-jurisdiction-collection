/** Supported Code Publishing CUA acquisition. Browser actions use documented CUA
 * tab APIs; Node filesystem writes retain exact source outside DOM evaluation.
 * Public, source-observed URLs only; no credentials/stealth/TLS weakening. */
import {mkdir,writeFile,readFile,lstat} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {sha256Browser} from './sha256_browser.mjs';
const hash=v=>createHash('sha256').update(v).digest('hex');
const moduleBytes=await readFile(new URL(import.meta.url));
const checksumBytes=await readFile(new URL('./sha256_browser.mjs',import.meta.url));
const moduleHash=hash(moduleBytes),checksumHash=hash(checksumBytes);
export async function createAcquirer(cua,outputRoot,firstUrl,options={}){
 const browserId=options.browserId||'iab';
 const opts=browserId==='iab'?{visible:false}:{sessionName:options.sessionName||'📚 Code Publishing E2E'};
 const tab=await cua.createBrowserTab(browserId,firstUrl,opts);
 return {tab,outputRoot,browserId,closed:false};
}
export async function captureJob(acquirer,job){
 if(acquirer.closed)throw Error('Acquirer closed');
 const u=new URL(job.url),scope=new URL(job.root_url);
 if(u.protocol!=='https:'||u.hostname!=='www.codepublishing.com'||u.origin!==scope.origin||!(u.pathname+'/').startsWith(scope.pathname.replace(/\/?$/,'/'))||decodeURIComponent(u.pathname+'/'+u.hash).split('/').includes('..'))throw Error('Only scoped public Code Publishing HTTPS URLs accepted');
 if(!/^[a-z0-9-]+$/.test(job.slug)||!/^[a-z0-9-]+$/.test(job.id))throw Error('Safe slug/id required');
 const {tab,outputRoot}=acquirer,dir=outputRoot+'/'+job.slug,prefix=dir+'/'+job.id;
 for(const suffix of ['.html','.receipt.json','.ax.txt']){try{await lstat(prefix+suffix);throw Error('Immutable acquisition target exists; use fresh job id/output: '+prefix);}catch(e){if(e.code!=='ENOENT')throw e;}}
 await mkdir(dir,{recursive:true});await mkdir(outputRoot+'/script-versions',{recursive:true});
 await writeFile(outputRoot+'/script-versions/'+moduleHash+'.mjs',moduleBytes);
 await writeFile(outputRoot+'/script-versions/'+checksumHash+'.mjs',checksumBytes);
 const started_at=new Date().toISOString();let navigation_error=null,readiness_error=null;
 try{if(job.refresh&&await tab.url()===job.url)await tab.reload();else if(await tab.url()!==job.url)await tab.goto(job.url);}catch(e){navigation_error=String(e);}
 try{await tab.playwright.locator(job.wait_selector||'body').first().waitFor({state:'attached',timeoutMs:12000});}catch(e){readiness_error=String(e);}
 const ax=await tab.getAXState({emit:false});await writeFile(prefix+'.ax.txt',String(ax));
 const before=await tab.playwright.evaluate(`(()=>{const checksum=${sha256Browser.toString()};const html=document.documentElement.outerHTML;return {url:location.href,title:document.title,length:html.length,sha256:checksum(html),main:!!document.querySelector('#mainContent'),legal_headings:Array.from(document.querySelectorAll('#mainContent h3.Cite')).map(h=>({id:h.id,text:h.textContent.trim()})),main_links:Array.from(document.querySelectorAll('#mainContent a[href]')).map(a=>({label:a.textContent.trim(),href:a.getAttribute('href'),container_class:a.parentElement.className})),all_links:Array.from(document.querySelectorAll('a[href]')).map(a=>({label:a.textContent.trim(),href:a.getAttribute('href')})),frames:Array.from(document.querySelectorAll('frame,iframe')).map(f=>({name:f.name,src:f.getAttribute('src')})),challenge:!!document.querySelector('#challenge-form,#cf-error-details')||/just a moment|attention required|access denied/i.test(document.title),currency:(document.querySelector('#pgFooter')?.textContent||document.body?.textContent||'').match(/(?:The )?[^.\\n]*?(?:current through|Current through)[^.\\n]*\\./)?.[0]?.trim()||'',body_text:document.body?.innerText?.slice(0,10000)||''};})()`);
 if(before.length>2000000)throw Error('Bounded validation capture limit2MB exceeded');
 const chunks=[];
 for(let offset=0;offset<before.length;offset+=40000){
  const piece=await tab.playwright.evaluate(({offset})=>document.documentElement.outerHTML.slice(offset,offset+40000),{offset});
  if(typeof piece!=='string'||piece.length!==Math.min(40000,before.length-offset))throw Error('Truncated DOM chunk');chunks.push(piece);
 }
 // Join UTF16 before UTF8 encoding: preserve surrogate pairs split by chunk boundaries.
 const html=chunks.join('');await writeFile(prefix+'.html',html,'utf8');const raw=await readFile(prefix+'.html');
 const after=await tab.playwright.evaluate(`(()=>{const checksum=${sha256Browser.toString()};const html=document.documentElement.outerHTML;return {url:location.href,length:html.length,sha256:checksum(html)};})()`);
 const identity=!job.expected_id||before.legal_headings.some(h=>h.id===job.expected_id);
 const accepted=!navigation_error&&!readiness_error&&!before.challenge&&before.url===job.url&&after.url===job.url&&before.length===html.length&&after.length===html.length&&before.sha256===hash(raw)&&after.sha256===hash(raw)&&html.endsWith('</html>')&&identity&&(job.kind!=='legal'||(before.main&&before.legal_headings.length>0));
 const receipt={schema_version:2,job,started_at,finished_at:new Date().toISOString(),transport:'supported CUA documented browser API; filesystem outside DOM evaluation',runtime:{node:'managed cua_repl',browser:acquirer.browserId},acquisition_script_sha256:moduleHash,checksum_module_sha256:checksumHash,raw_artifact_path:job.id+'.html',sha256:hash(raw),bytes:raw.length,utf16_length:html.length,browser_state:before,after_capture:after,expected_heading_found:identity,navigation_error,readiness_error,http_status:null,accepted,inventory_complete:false,whole_corpus_complete:false};
 await writeFile(prefix+'.receipt.json',JSON.stringify(receipt,null,2)+'\n');
 return {slug:job.slug,id:job.id,accepted,bytes:raw.length,sha256:receipt.sha256,sections:before.legal_headings.length,links:before.all_links.length,title:before.title,currency:before.currency};
}
export async function closeAcquirer(acquirer){if(!acquirer.closed){await acquirer.tab.close();acquirer.closed=true;}}
