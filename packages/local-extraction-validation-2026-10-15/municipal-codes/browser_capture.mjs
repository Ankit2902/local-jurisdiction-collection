// Optional ordinary, visible browser acquisition. npm install playwright; npx playwright install chromium
// node browser_capture.mjs URL OUTPUT_DIR section OBSERVED_NODE_ID
// node browser_capture.mjs URL OUTPUT_DIR inventory OBSERVED_TOC_SELECTOR
import { chromium } from 'playwright';
import { mkdir,writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
const [url,out,mode,expected]=process.argv.slice(2);
if(!url||!out||!['section','inventory'].includes(mode)||!expected)throw Error('URL OUTPUT_DIR section|inventory EXPECTED_NODE_OR_SELECTOR required');
const u=new URL(url);if(u.protocol!=='https:'||!u.hostname.endsWith('.municipal.codes'))throw Error('Expected public municipal.codes HTTPS URL');
await mkdir(out,{recursive:true});const browser=await chromium.launch({headless:false});
const context=await browser.newContext();const page=await context.newPage();
try{
 const response=await page.goto(url,{waitUntil:'domcontentloaded',timeout:45000});
 await page.locator('main').waitFor({timeout:15000});
 if(mode==='section'){
  const found=await page.locator('article').evaluateAll((cards,id)=>cards.some(c=>[c.id,c.getAttribute('data-id'),c.getAttribute('data-node-id')].includes(id)),expected);
  if(!found)throw Error('Requested legal node absent; stale or unprofiled route');
 }else if(await page.locator(expected).count()!==1)throw Error('Observed TOC selector must match exactly one container');
 const html=await page.content();const blocked=/just a moment|attention required|access denied/i.test(await page.title())||await page.locator('#challenge-form,#cf-error-details').count()>0;
 await writeFile(out+'/rendered.html',html);await page.screenshot({path:out+'/rendered.png',fullPage:true});
 await writeFile(out+'/receipt.json',JSON.stringify({requested_url:url,final_url:page.url(),http_status:response?.status(),retrieved_at:new Date().toISOString(),sha256:createHash('sha256').update(html).digest('hex'),accepted:!blocked,mode,expected,inventory_complete:false},null,2)+'\n');
 if(blocked)throw Error('Access challenge; ordinary operator access required, no legal content accepted');
}catch(error){
 const html=await page.content().catch(()=> '');await writeFile(out+'/blocked.html',html);
 await writeFile(out+'/failure.json',JSON.stringify({url,error:String(error),retrieved_at:new Date().toISOString(),sha256:createHash('sha256').update(html).digest('hex'),accepted:false},null,2)+'\n');process.exitCode=2;
}finally{await context.close();await browser.close();}
