/* Independent source-section graph, headings and exclusive browser text.
   Publisher source is sanitized in an inert template before attachment. */
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{createRequire}=require('module');
const {attachInert,provenance}=require('./inert_browser_source.cjs');
const {chromium}=createRequire(process.env.PLAYWRIGHT_MODULE_ROOT)('playwright');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex'),space=s=>String(s??'').replace(/[\s\x1c-\x1f]+/g,' ').replace(/\s*\[IMAGE\]\s*/g,' [IMAGE] ').trim();
(async()=>{
const [run,out]=process.argv.slice(2);if(fs.existsSync(out)||path.resolve(out).startsWith(path.resolve(run)+path.sep))throw Error('Fresh outside report required');
const bytes=fs.readFileSync(path.join(run,'records.jsonl')),rs=bytes.toString().split('\n').filter(Boolean).map(JSON.parse),cp=JSON.parse(fs.readFileSync(path.join(run,'checkpoint.json'))),inv=JSON.parse(fs.readFileSync(path.join(run,'inventory.json'))),toc=new Map(inv.nodes.map(n=>[n.id,n]));
let groups=new Map(),errors=[],sources=[],blocked=0,checked=0,graphIDs=[],headingFallback=0,operativeHeadings=0,contextCount=0;
for(let r of rs){if(!groups.has(r.raw_path))groups.set(r.raw_path,[]);groups.get(r.raw_path).push(r)}
const browser=await chromium.launch({headless:true,channel:'chrome'});
try{const context=await browser.newContext({javaScriptEnabled:false});await context.route('**/*',r=>{blocked++;return r.abort()});const page=await context.newPage();
for(const [rawPath,records] of groups){
 const block=cp.blocks.find(x=>x.path===rawPath);if(!block)throw Error('Block absent');const raw=fs.readFileSync(path.join(run,rawPath));if(sha(raw)!==block.sha256||records.some(r=>r.raw_sha256!==sha(raw)))throw Error('Source SHA mismatch');
 await attachInert(page,raw.toString());
 const found=await page.evaluate(({requested,tocIDs})=>{
  const clean=s=>String(s??'').replace(/\s+/g,' ').trim(),key=e=>(Array.from(e.classList).filter(c=>/^_\d+(?:-\d+)*$/.test(c)).sort((a,b)=>b.length-a.length)[0]||null);
  const pg=document.querySelector('#thePage'),sections=Array.from(pg.querySelectorAll('section[data-secid]')),selected=sections.find(e=>e.dataset.secid===requested);if(!selected)throw Error('Requested body absent');
  const sk=key(selected),expected=[],context=[],nodes={};
  const outside=pg.cloneNode(true);for(let s of outside.querySelectorAll('section[data-secid]'))if(!s.parentElement.closest('section[data-secid]'))s.remove();
  // Only publisher banner is outside legal body; its inert marker is handled
  // by original-source-only independent outside-body check in binding.py.
  for(let s of sections){const id=s.dataset.secid,k=key(s),belongs=s===selected||(sk&&k&&k.startsWith(sk+'-'))||selected.contains(s);
   if(!belongs){context.push({id,key:k,ancestor:!!(k&&sk&&sk.startsWith(k+'-'))});continue}
   expected.push(id);const exclusive=s.cloneNode(true);for(let d of exclusive.querySelectorAll('section[data-secid]'))d.remove();
   for(let e of exclusive.querySelectorAll('.archiveNotice.nullValue'))e.remove();
   const h=exclusive.querySelector('h1,h2,h3,h4,h5,h6');let heading='',operative=false;
   if(h){const hc=h.cloneNode(true);for(let sup of hc.querySelectorAll('sup'))sup.remove();heading=clean((hc.querySelector('.def')||hc).textContent).replace(/\[IMAGE\]/g,'').trim();const def=h.querySelector('.def');operative=!!(def&&clean(h.textContent)!==clean(def.textContent))||(!tocIDs.includes(id)&&/\b(shall|means|is defined)\b/i.test(h.textContent));if(!operative)h.remove()}
   for(let m of exclusive.querySelectorAll('.mini-TOC'))m.remove();
   const stage=document.createElement('div');stage.append(exclusive);document.body.append(stage);const text=exclusive.innerText;stage.remove();
   nodes[id]={heading,definition:clean(exclusive.querySelector('.def')?.textContent||''),text,operative,key:k,domParent:s.parentElement.closest('section[data-secid]')?.dataset.secid||null};
  }
  return {expected,context,nodes,allIDs:sections.map(s=>s.dataset.secid)};
 },{requested:block.requested,tocIDs:Array.from(toc.keys())});
 const got=records.map(r=>r.id).sort(),expected=[...found.expected].sort();if(JSON.stringify(got)!==JSON.stringify(expected))errors.push({raw_path:rawPath,field:'source_graph_coverage',source:expected,normalized:got});
 if(new Set(found.allIDs).size!==found.allIDs.length)errors.push({raw_path:rawPath,field:'duplicate_source_ids'});
 for(let c of found.context){contextCount++;if(!c.ancestor)errors.push({raw_path:rawPath,field:'unexplained_context',context:c})}
 for(let r of records){checked++;const n=found.nodes[r.id];if(!n){errors.push({id:r.id,field:'missing_source_body'});continue}graphIDs.push(r.id);
  let h=n.heading;if(!h){headingFallback++;h=toc.get(r.id)?.heading||n.definition||''}
  if(space(h)!==space(r.heading))errors.push({id:r.id,field:'heading',source:h,normalized:r.heading});
  if(space(n.text)!==space(r.text))errors.push({id:r.id,field:'exclusive_text',source:n.text,normalized:r.text});
  if(n.operative)operativeHeadings++;if(n.operative!==r.operative_heading_retained_as_body)errors.push({id:r.id,field:'operative_heading_ownership'});
  if(n.key!==r.canonical_body_key)errors.push({id:r.id,field:'canonical_key'});
  if(n.domParent&&n.domParent!==r.parent_id)errors.push({id:r.id,field:'DOM_parent',source:n.domParent,normalized:r.parent_id});
 }
 sources.push({raw_path:rawPath,sha256:sha(raw),requested:block.requested,source_owned_ids:found.expected.length,context:found.context});
}
const report={schema_version:1,kind:'independent-inert-original-DOM-exclusive-body-heading-and-source-graph',script_sha256:sha(fs.readFileSync(__filename)),inert_source_preparation:provenance(),records_sha256:sha(bytes),records_checked:checked,unique_owned_source_ids:new Set(graphIDs).size,source_responses:sources,headless_TOC_heading_fallbacks:headingFallback,operative_heading_bodies:operativeHeadings,ancestor_context_occurrences:contextCount,browser:browser.version(),network_requests_sent:0,blocked_resource_requests:blocked,passed:!errors.length,mismatches:errors};fs.writeFileSync(out,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({...report,source_responses:undefined,mismatches:errors.slice(0,8)}));if(errors.length)process.exitCode=2;
}finally{await browser.close()}
})().catch(e=>{console.error(e.stack);process.exitCode=1});
