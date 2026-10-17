/* Standalone ordinary headed browser acquisition, public APIs observed in publisher application.
 * npm install playwright; node collect_browser.cjs URL OUTDIR [sample-count=4]
 * MUNICODE_GATE_DIR shared across processes; gate_cli.py requires python3 stdlib.
 * No challenge interaction, fingerprint changes, imported cookies, login or proxy.
 */
const {createRequire}=require('module');
const {chromium}=createRequire(process.env.PLAYWRIGHT_MODULE_ROOT || (__dirname+'/package.json'))('playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{execFile}=require('child_process');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const gate=(...args)=>new Promise((res,rej)=>execFile(process.env.PYTHON||'python3',[path.join(__dirname,'gate_cli.py'),...args],(err,stdout,stderr)=>err?rej(Error(stderr||String(err))):res(stdout)));
const write=(out,name,obj)=>fs.writeFileSync(path.join(out,name),typeof obj==='string'||Buffer.isBuffer(obj)?obj:JSON.stringify(obj,null,2)+'\n');
(async()=>{
 const [url,out,countArg]=process.argv.slice(2),sampleCount=Number(countArg||4);if(!url||!out)throw Error('URL OUTDIR required');fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({headless:false,channel:process.env.BROWSER_CHANNEL||'chrome'});const ctx=await browser.newContext({acceptDownloads:true});const page=await ctx.newPage();let pending=[],responses=[],seq=0,blocked=false;
 const executed=fs.readFileSync(__filename);write(out,'executed-collect_browser.cjs',executed);write(out,'executed-gate_cli.py',fs.readFileSync(path.join(__dirname,'gate_cli.py')));
 const result={url,os:process.platform,architecture:process.arch,started_at:new Date().toISOString(),browser:browser.version(),node:process.version,script_sha256:sha(fs.readFileSync(__filename)),gate_script_sha256:sha(fs.readFileSync(path.join(__dirname,'gate_cli.py'))),method:'standalone-headed-chrome-public-application-api',cookies_imported:false,challenge_interaction:false,complete_corpus:false};
 await ctx.route('**/*',async route=>{const u=route.request().url();if(['image','font','media'].includes(route.request().resourceType()))return route.abort();if(new URL(u).hostname.endsWith('municode.com')){try{await gate('reserve',u);}catch(e){blocked=true;result.gate_error=String(e);return route.abort();}}await route.continue();});
 ctx.on('response',r=>{const u=r.url();if(new URL(u).hostname.endsWith('municode.com')){const index=seq++;pending.push((async()=>{if(r.status()===429){blocked=true;await gate('cooldown',r.headers()['retry-after']||'300');}if(u.includes('/api/')||r.request().resourceType()==='document'){const body=await r.body().catch(()=>Buffer.from(''));const file='response-'+index+'.bin';write(out,file,body);responses.push({url:u,status:r.status(),file,bytes:body.length,sha256:sha(body),retrieved_at:new Date().toISOString()});}})());}});
 const api=async(p,params={})=>{if(blocked)throw Error('Gate/cooldown blocked');const u='https://library.municode.com/api/'+p+'?'+new URLSearchParams(params);return page.evaluate(async u=>{let r=await fetch(u,{headers:{'X-CSRF':'1'}});let t=await r.text();return {status:r.status,text:t}},u).then(r=>{if(r.status!==200)throw Error('API '+r.status+' '+u);return JSON.parse(r.text)});};
 try{
  let r=await page.goto(url,{waitUntil:'domcontentloaded',timeout:600000});result.http_status=r.status();let deadline=Date.now()+600000;while(!responses.some(x=>x.url.includes('/Products/name')&&x.status===200)&&Date.now()<deadline){if(/Just a moment|Access denied/.test(await page.title()))throw Error('Access challenge; stopped');await page.waitForTimeout(250);}
  if(/Just a moment|Access denied/.test(await page.title()))throw Error('Access challenge; stopped');
  await Promise.all(pending);let prodResp=responses.find(x=>x.url.includes('/Products/name')&&x.status===200);if(!prodResp)throw Error('No successful Products/name response');let product=JSON.parse(fs.readFileSync(path.join(out,prodResp.file))).Model;
  let jobResp=responses.find(x=>x.url.includes('/Jobs/latest/')&&x.status===200);let job=jobResp?JSON.parse(fs.readFileSync(path.join(out,jobResp.file))):await api('Jobs/latest/'+product.ProductID);
  result.product=product;result.job=job;write(out,'product.json',product);write(out,'job.json',job);
  const productId=product.ProductID,jobId=job.Id;let toc=await api('codesToc/fullTree',{productId,jobId,nodeId:productId});write(out,'toc-full.json',toc);
  let nodes=[];const walk=(n,parents=[])=>{if(n.Id)nodes.push({...n,path:[...parents,n.Heading]});(n.Children||[]).forEach(c=>walk(c,[...parents,n.Heading]));};walk(toc);result.inventory_nodes=nodes.length;result.families_top_level=(toc.Children||[]).map(n=>({id:n.Id,heading:n.Heading}));
  let sections=nodes.filter(n=>!n.HasChildren&&/^(?:Sec(?:tion)?\.?\s*|§\s*|[0-9]+[.\-])[0-9a-zA-Z.\-]*/i.test(n.Heading||''));if(!sections.length)sections=nodes.filter(n=>!n.HasChildren&&n.Data?.DocType===1);
  // First substantive multiple-section sample; appendix/charter remain separately inventoried.
  let filtered=sections.filter(n=>!/reser|comparative|contents/i.test(n.Heading));let preferred=filtered.filter(n=>!n.path.some(h=>/charter|constitution/i.test(h)));let selected=(preferred.length?preferred:filtered).slice(0,sampleCount);if(!selected.length)throw Error('No leaf provisions');
  let samples=[];for(let n of selected){let content=await api('CodesContent',{productId,jobId,nodeId:n.Id,groupChunks:false});samples.push({node:n,content});}
  write(out,'samples.json',samples);result.selected_nodes=selected.map(n=>({id:n.Id,heading:n.Heading}));
  // Publisher-native PDF is a feature-gated publication download, not browser print.
  let ccResp=responses.find(x=>x.url.includes('/ClientContent/')&&x.status===200);let cc=ccResp?JSON.parse(fs.readFileSync(path.join(out,ccResp.file))):await api('ClientContent/'+product.Client.ClientID);write(out,'client-content.json',cc);
  result.publications=cc?.codes||[];
  let pdfPublication=result.publications.find(p=>p.productId===productId&&p.hasPdf&&p.hasPdfDownloadEnabled);
  if(pdfPublication&&pdfPublication.publicationId){
   try{let pdf=await api('PublicationPdfDownload/'+pdfPublication.publicationId);write(out,'pdf-url.json',pdf);let pdfUrl=typeof pdf==='string'?pdf:(pdf.url||pdf.Url);if(!pdfUrl)throw Error('Unknown PDF URL response shape');
    await gate('reserve',pdfUrl);let pr=await ctx.request.get(pdfUrl,{timeout:600000});if(pr.status()===429)await gate('cooldown',pr.headers()['retry-after']||'300');let body=await pr.body();write(out,pr.status()===200&&body.subarray(0,5).equals(Buffer.from('%PDF-'))?'publisher-export.pdf':'publisher-export-response.bin',body);write(out,'publisher-export.receipt.json',{url:pdfUrl,status:pr.status(),bytes:body.length,sha256:sha(body),acquired_at:new Date().toISOString(),kind:'publisher-native-publication-pdf'});if(pr.status()!==200||!body.subarray(0,5).equals(Buffer.from('%PDF-')))throw Error('Publisher response not PDF');result.publisher_download={status:'passed',url:pdfUrl,reason:'Publisher-native publication PDF acquired automatically',bytes:body.length,sha256:sha(body),publication_id:pdfPublication.publicationId};
   }catch(e){result.publisher_download={status:'blocked',reason:String(e),publication_id:pdfPublication.publicationId};}
  }
  else result.publisher_download={status:'unavailable',reason:'ClientContent inventory reports no enabled publication PDF for primary code',publication:pdfPublication||null};
  // Navigate to sample section for rendered QA of source-backed text.
  const sampleUrl=url.split('?')[0]+'?nodeId='+encodeURIComponent(selected[0].Id);result.sample_url=sampleUrl;result.title=await page.title();write(out,'rendered.html',await page.content());await page.screenshot({path:path.join(out,'rendered.png'),fullPage:true});result.status='acquired';
 }catch(e){result.status='failed';result.error=String(e);write(out,'failure.html',await page.content().catch(()=>''));await page.screenshot({path:path.join(out,'failure.png')}).catch(()=>{});}
 await Promise.all(pending);result.responses=responses;result.finished_at=new Date().toISOString();write(out,'receipt.json',result);await browser.close();console.log(JSON.stringify({out,status:result.status,error:result.error,selected:result.selected_nodes,publications:result.publications,publisher_download:result.publisher_download}));
 if(result.status!=='acquired')process.exitCode=2;
})();
