// Portable module for the supported Codex CUA REPL.
// Pass an existing authorized tab, output path, and source-observed readiness selector.
export async function captureCua(tab, output, readySelector) {
  const fs = await import('node:fs/promises');
  const crypto = await import('node:crypto');
  if (!await tab.playwright.locator(readySelector).isVisible()) throw Error('Requested source is not ready');
  const metadata = await tab.playwright.evaluate(() => ({url:location.href,title:document.title,chars:document.documentElement.outerHTML.length,sourceEncoding:document.characterSet}));
  const pieces=[];
  for (let i=0;i<metadata.chars;i+=60000) pieces.push(await tab.playwright.evaluate(({start})=>document.documentElement.outerHTML.slice(start,start+60000),{start:i}));
  const html=pieces.join('');
  if(html.length!==metadata.chars || !html.endsWith('</html>') || html.includes('[Truncated]'))throw Error('Capture integrity failure');
  const data=Buffer.from(html,'utf8');
  const receipt={...metadata,retrieved_at:new Date().toISOString(),transport:'supported Codex CUA',retained_encoding:'utf-8',original_http_bytes:false,sha256:crypto.createHash('sha256').update(data).digest('hex'),bytes:data.length,ready_selector:readySelector,ready_text:await tab.playwright.locator(readySelector).innerText()};
  await fs.mkdir((await import('node:path')).dirname(output),{recursive:true});
  await fs.writeFile(output,data,{flag:'wx'});await fs.writeFile(output+'.capture.json',JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});return receipt;
}
// Single-call scoped DOM evidence for dynamic pages. Receipt explicitly declares the scope.
export async function captureCuaScope(tab, output, selector) {
  const fs=await import('node:fs/promises'),crypto=await import('node:crypto'),path=await import('node:path');
  if(!await tab.playwright.locator(selector).isVisible())throw Error('Scoped source not ready');
  const capture=await tab.playwright.evaluate(({selector})=>{
    const nodes=document.querySelectorAll(selector);if(nodes.length!==1)throw Error('Ambiguous scoped source');
    return {url:location.href,title:document.title,sourceEncoding:document.characterSet,html:nodes[0].outerHTML};
  },{selector});
  if(capture.html.length>150000 || capture.html.includes('[Truncated]'))throw Error('Scoped capture exceeds bounded limit');
  const data=Buffer.from(capture.html,'utf8'),receipt={url:capture.url,title:capture.title,sourceEncoding:capture.sourceEncoding,scope_selector:selector,capture_scope:'exact DOM element outerHTML',retrieved_at:new Date().toISOString(),transport:'supported Codex CUA',retained_encoding:'utf-8',original_http_bytes:false,sha256:crypto.createHash('sha256').update(data).digest('hex'),bytes:data.length};
  await fs.mkdir(path.dirname(output),{recursive:true});await fs.writeFile(output,data,{flag:'wx'});await fs.writeFile(output+'.capture.json',JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});return receipt;
}
