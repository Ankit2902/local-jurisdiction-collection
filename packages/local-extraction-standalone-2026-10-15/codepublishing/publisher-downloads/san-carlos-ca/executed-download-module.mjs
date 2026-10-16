/** Operator-assisted ordinary publisher SaveHTML, through documented CUA.
 * Not an unattended acquisition claim. Only retain own downloaded public export. */
import {mkdir,readFile,writeFile,lstat} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const hash=b=>createHash('sha256').update(b).digest('hex');
const source=await readFile(new URL(import.meta.url));
export async function downloadHtml(tab,folder,metadata){
 for(const name of ['publisher-export.html','download-receipt.json']){try{await lstat(folder+'/'+name);throw Error('Immutable download target exists');}catch(e){if(e.code!=='ENOENT')throw e;}}
 const url=await tab.url();if(url!==metadata.preview_url||!/^https:\/\/www\.codepublishing\.com\/(CA|WA|AZ)\/[A-Za-z]+\/cgi\/menuCompile\.pl$/.test(url))throw Error('Unexpected scoped publisher preview URL');
 const before=await tab.playwright.evaluate(()=>({title:document.title,headings:Array.from(document.querySelectorAll('#mainContent h3.Cite')).map(h=>h.textContent.trim()),options:Array.from(document.querySelector('select[name="type"]').options).map(o=>o.value)}));
 if(before.title!=='Print Preview'||!before.headings.length||!before.options.includes('HTML'))throw Error('Preview identity/content/HTML format unavailable');
 await tab.playwright.locator('select[name="type"]').selectOption('HTML');await tab.getAXState({emit:false});
 const selected=await tab.playwright.locator('select[name="type"]').getAttribute('name');if(selected!=='type')throw Error('Unexpected export control');
 const started_at=new Date().toISOString();
 const event=tab.playwright.waitForEvent('download',{timeoutMs:30000});
 await tab.playwright.locator('#saveAsSubmit').click();
 const download=await event;const path=await download.path({timeoutMs:30000});if(!path)throw Error('Browser download path unavailable; operator save required');
 const raw=await readFile(path);if(raw.length>20*1024*1024||raw.length<100)throw Error('Export bytes outside bounded limits');
 await mkdir(folder,{recursive:true});await writeFile(folder+'/publisher-export.html',raw);await writeFile(folder+'/executed-download-module.mjs',source);
 const receipt={schema_version:1,classification:'operator_assisted_publisher_download',metadata,started_at,finished_at:new Date().toISOString(),source_url:url,export_format:'HTML',publisher_preview_title:before.title,preview_legal_heading_count:before.headings.length,raw_artifact:'publisher-export.html',raw_sha256:hash(raw),bytes:raw.length,executed_module_sha256:hash(source),download_path_available:true,operator_browser_session_required:true,unattended_acquisition:false,http_status:null,cookies_exported:false};
 await writeFile(folder+'/download-receipt.json',JSON.stringify(receipt,null,2)+'\n');await tab.getAXState({emit:false});return {classification:receipt.classification,bytes:raw.length,sha256:receipt.raw_sha256,preview_legal_headings:before.headings.length};
}
