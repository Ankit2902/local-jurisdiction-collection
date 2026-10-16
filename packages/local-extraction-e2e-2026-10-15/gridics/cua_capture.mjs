/** Supported CUA adapter. Import only inside cua_repl; pass your own isolated tab.
 * Never creates/reuses another agent's tab, reads browser hidden state or issues HTTP.
 * Output snapshot-manifest.json is consumed directly by gridics.py replay.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
const sha=value=>crypto.createHash('sha256').update(value).digest('hex');
export async function capture(tab,out,url,{snapshotId,sourceVersion}={}) {
 if(!snapshotId||!sourceVersion)throw Error('Explicit snapshot and source version required');
 if(!/^https:\/\/codehub\.gridics\.com\/us\/ca\/cupertino#\/[0-9a-f-]{36}(\/[0-9a-f-]{36})*$/i.test(url))throw Error('Cupertino UUID route required');
 if(await tab.url()!==url)await tab.goto(url);
 const observations=[];let previous=null;let stable=0;
 for(let attempt=0;attempt<12;attempt++) {
  await tab.playwright.domSnapshot();
  const state=await tab.playwright.evaluate(()=>({url:location.href,characters:document.documentElement.outerHTML.length,containers:Array.from(document.querySelectorAll('div.section[data-path]')).map(n=>({path:n.getAttribute('data-path'),id:n.id,heading:Array.from(n.querySelectorAll('h1,h2,h3,h4,h5,h6')).find(h=>h.closest('.section')===n)?.innerText||''}))}));
  observations.push(state);let target=state.containers.find(n=>n.path===new URL(url).hash.slice(1));
  if(state.url!==url||!target||target.id!=='section-'+target.path.split('/').at(-1)||!target.heading){stable=0;continue;}
  const key=JSON.stringify(state);stable=key===previous?stable+1:1;previous=key;
  if(stable<3)continue;
  let html='';for(let offset=0;offset<state.characters;offset+=70000)html+=await tab.playwright.evaluate(arg=>document.documentElement.outerHTML.slice(arg.offset,arg.end),{offset,end:offset+70000});
  const end=await tab.playwright.evaluate(()=>({url:location.href,characters:document.documentElement.outerHTML.length}));
  if(html.length!==state.characters||end.url!==url||end.characters!==state.characters||html.includes('[Truncated]'))throw Error('Incomplete or drifting DOM capture');
  await fs.mkdir(path.join(out,'raw'),{recursive:true});const name='raw/'+sha(url)+'.html';await fs.writeFile(path.join(out,name),html);
  const receipt={url,actual_url:end.url,characters:html.length,byte_length:Buffer.byteLength(html),uuid_containers:state.containers.length,observations:observations.length,complete_chunk_capture:true,adapter_sha256:sha(await fs.readFile(new URL(import.meta.url))),retrieved_at:new Date().toISOString()};
  await fs.writeFile(path.join(out,'capture-receipt.json'),JSON.stringify(receipt,null,2)+'\n');
  const manifest={snapshot_id:snapshotId,source_version:sourceVersion,currency_raw:null,artifacts:[{path:name,sha256:sha(html),url,retrieved_at:receipt.retrieved_at,acquisition_method:'supported CUA read-only DOM chunk capture',state_evidence:'capture-receipt.json'}],inventory:null,full_inventory_qualified:false,full_collection_validated:false,acquisition_status:'completed_bounded_routes'};
  await fs.writeFile(path.join(out,'snapshot-manifest.json'),JSON.stringify(manifest,null,2)+'\n');return receipt;
 }
 throw Error('Requested UUID/heading/URL did not stabilize through supported CUA');
}
