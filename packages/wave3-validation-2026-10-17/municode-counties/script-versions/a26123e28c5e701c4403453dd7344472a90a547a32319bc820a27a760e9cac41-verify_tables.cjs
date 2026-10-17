/* Independent offline Chrome DOM QA for every table-bearing normalized record.
 * All requests aborted. Output defaults to a new temporary directory; source never changed.
 */
const {createRequire}=require('module');
const {chromium}=createRequire(process.env.PLAYWRIGHT_MODULE_ROOT||(__dirname+'/package.json'))('playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto'),os=require('os');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex'),space=s=>s.replace(/\s+/g,' ').trim();
(async()=>{
 const [folder,requestedOut]=process.argv.slice(2),out=requestedOut||fs.mkdtempSync(path.join(os.tmpdir(),'municode-major-table-qa-'));
 const sourcePath=path.join(folder,'normalized/sections.jsonl'),bytes=fs.readFileSync(sourcePath),records=bytes.toString().trim().split('\n').map(JSON.parse).filter(r=>r.tables?.length);fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({headless:true,channel:process.env.BROWSER_CHANNEL||'chrome'}),ctx=await browser.newContext({viewport:{width:1440,height:1000}});let blocked=[];await ctx.route('**/*',r=>{blocked.push(r.request().url());return r.abort()});const page=await ctx.newPage();let checks=[];
 for(let n=0;n<records.length;n++){
  const record=records[n];await page.setContent('<!doctype html><html><head><style>body{font:16px Georgia;line-height:1.45;padding:30px}table{border-collapse:collapse;max-width:100%}td,th{border:1px solid #888;padding:8px}a{color:#12477d}</style></head><body>'+record.html+'</body></html>');
  const tables=await page.locator('table').evaluateAll(ts=>ts.map(t=>Array.from(t.rows).map(r=>Array.from(r.cells).map(c=>({text:c.innerText,rowspan:c.getAttribute('rowspan')||'1',colspan:c.getAttribute('colspan')||'1',tag:c.tagName.toLowerCase()})))));
  let mismatches=[],cells=0;
  if(tables.length!==record.tables.length)mismatches.push({table_count:[tables.length,record.tables.length]});
  for(let ti=0;ti<tables.length;ti++){
   if(tables[ti].length!==record.tables[ti]?.length)mismatches.push({table:ti,row_count:[tables[ti].length,record.tables[ti]?.length]});
   for(let ri=0;ri<tables[ti].length;ri++){
    const row=tables[ti][ri],parsed=record.tables[ti]?.[ri];if(row.length!==parsed?.length)mismatches.push({table:ti,row:ri,cell_count:[row.length,parsed?.length]});
    for(let ci=0;ci<row.length;ci++){cells++;for(const k of ['text','rowspan','colspan','tag'])if(space(row[ci][k])!==space(parsed?.[ci]?.[k]||''))mismatches.push({table:ti,row:ri,cell:ci,field:k,source:row[ci][k],normalized:parsed?.[ci]?.[k]});}
   }
  }
  await page.screenshot({path:path.join(out,'table-'+n+'-top.png')});checks.push({source_node_id:record.node_id,source_html_sha256:sha(Buffer.from(record.html)),table_count:tables.length,row_count:tables.reduce((n,t)=>n+t.length,0),cell_count:cells,fields_checked:['rendered_cell_innerText_whitespace_normalized','tag','rowspan','colspan'],mismatches,passed:tables.length>0&&mismatches.length===0});
 }
 const qa={offline:true,network_requests_sent:0,blocked_resource_requests:blocked,normalized_jsonl_sha256:sha(bytes),checks,passed:checks.length>0&&checks.every(c=>c.passed),browser:browser.version(),node:process.version,script_sha256:sha(fs.readFileSync(__filename)),visual_note:'Offline source HTML rendering; not live acquisition or publisher export'};
 fs.writeFileSync(path.join(out,'table-dom-qa.json'),JSON.stringify(qa,null,2));await browser.close();console.log(JSON.stringify({...qa,output_dir:out}));if(!qa.passed)process.exitCode=2;
})();
