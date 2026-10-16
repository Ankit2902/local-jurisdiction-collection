/** Read-only current export metadata; does not click/download or request URLs. */
import {mkdir,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
export async function captureExportState(tab,out){
 await mkdir(out,{recursive:true});const ax=await tab.getAXState({emit:false});
 const data=await tab.playwright.evaluate(()=>({source_url:location.href,title:document.title,identity:{customer_id:document.body.getAttribute('data-cust-id'),code_id:document.body.getAttribute('data-code-id'),currency_raw:document.body.getAttribute('data-code-date')},export_body_attributes:Object.fromEntries(Array.from(document.body.attributes).filter(x=>/pdf|word|export|download|logged/i.test(x.name)).map(x=>[x.name,x.value])),buttons:Array.from(document.querySelectorAll('button')).filter(x=>/print|download/i.test(x.getAttribute('aria-label')||x.textContent)).map(x=>({label:x.getAttribute('aria-label'),text:x.textContent,disabled:x.disabled})),legal_body_count:document.querySelectorAll('.section_content').length}));
 const evidence={observed_at:new Date().toISOString(),method:'supported CUA read-only current DOM metadata; no export action/no new navigation',standalone_acquisition_verified:false,...data};const bytes=JSON.stringify(evidence,null,2)+'\n';await writeFile(out+'/metadata.json',bytes);await writeFile(out+'/ax.txt',String(ax));return {path:out+'/metadata.json',sha256:createHash('sha256').update(bytes).digest('hex'),...evidence};
}
