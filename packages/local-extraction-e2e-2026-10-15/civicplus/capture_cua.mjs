// Execute only inside supported cua_repl with an already observed official tab.
// No browser connection, profile access, hidden API, network fetch or TLS override.
import { mkdir, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
const digest = data => createHash('sha256').update(data).digest('hex');
export async function capturePortland(tab, directory) {
  const requestedUrl = await tab.url();
  const url = new URL(requestedUrl);
  if (url.hostname !== 'portlandmaine.gov' || !['/city-code','/734/City-Code'].includes(url.pathname)) throw new Error('Expected observed official Portland code tab');
  const startedAt = new Date().toISOString();
  const heading = tab.playwright.getByRole('heading',{name:'City Code Documents',exact:true});
  await heading.waitFor({state:'visible',timeoutMs:30000});
  const widget = await heading.evaluate(e=>e.parentElement.parentElement.outerHTML);
  const config = await tab.playwright.evaluate(()=>Array.from(document.scripts).filter(s=>s.textContent.includes('City Code Documents') && /const\s+n\s*=\s*\{/.test(s.textContent)).map(s=>s.outerHTML));
  if (config.length !== 1) throw new Error('Expected exactly one observed semantic widget configuration script');
  await mkdir(directory,{recursive:false});
  const files = {'index.html':config[0],'widget.html':widget};
  for (const [name,data] of Object.entries(files)) await writeFile(`${directory}/${name}`,data);
  const receipt = {runtime:'supported_cua_chrome',requested_url:requestedUrl,started_at:startedAt,finished_at:new Date().toISOString(),result:'captured',browser_version:null,browser_version_note:'Not exposed by supported CUA DOM API; navigator is intentionally unavailable in its read-only scope',browser_executable:'Not exposed by supported CUA API; browser controlled through registered Chrome extension',source_kind:'Observed rendered widget plus its page DOM configuration script, not HTTP response bytes',http_status:null,response_headers_available:false,files:Object.fromEntries(Object.entries(files).map(([name,data])=>[name,digest(data)]))};
  await writeFile(`${directory}/capture-receipt.json`,JSON.stringify(receipt,null,2)+'\n');
  return receipt;
}
