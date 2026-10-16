import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {mkdtemp,readFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {sha256Browser} from './sha256_browser.mjs';
import {captureJob} from './acquire_cua.mjs';
const hash=s=>createHash('sha256').update(s).digest('hex');
let checks=0;
for(const s of ['', 'abc', 'a'.repeat(100000),'§ café 中文 🏛️','\ud800x\udc00']){assert.equal(sha256Browser(s),hash(s));checks++;}
const folder=await mkdtemp(join(tmpdir(),'cp-cua-unit-'));
const root='https://www.codepublishing.com/WA/Renton/';
const html='<html>'+('x'.repeat(39993))+'😀 legal body</html>';
function tab({mutated=false,navigationError=false,wrongHeading=false}={}){return {url:async()=>root,goto:async()=>{if(navigationError)throw Error('navigation unavailable');},getAXState:async()=> 'document legal',playwright:{locator:()=>({first:()=>({waitFor:async()=>{}})}),evaluate:async (fn,arg)=>{
 if(typeof fn==='function')return html.slice(arg.offset,arg.offset+40000);
 const base={url:root,length:html.length,sha256:hash(html)};
 if(fn.includes('legal_headings'))return {...base,title:'Legal',main:true,legal_headings:[{id:wrongHeading?'wrong':'one',text:'1-1-1 Rule'}],all_links:[],main_links:[],frames:[],challenge:false,currency:'Known',body_text:'legal'};
 return {...base,sha256:mutated?hash(html.replace('legal','LEGAL')):hash(html)};
}}};}
const job={slug:'renton-wa',id:'ok',url:root,root_url:root,kind:'legal',wait_selector:'h3',expected_id:'one'};
try{
 const good=await captureJob({tab:tab(),outputRoot:folder,browserId:'fixture'},job);
 assert(good.accepted);assert.equal(await readFile(join(folder,'renton-wa/ok.html'),'utf8'),html);checks++;
 const prior=await readFile(join(folder,'renton-wa/ok.receipt.json'));
 await assert.rejects(()=>captureJob({tab:tab(),outputRoot:folder},job),/Immutable acquisition target exists/);
 assert.deepEqual(await readFile(join(folder,'renton-wa/ok.receipt.json')),prior);checks++;
 for(const [id,options] of [['mutation',{mutated:true}],['heading',{wrongHeading:true}]]){
  const r=await captureJob({tab:tab(options),outputRoot:folder}, {...job,id});assert.equal(r.accepted,false);checks++;
 }
 await assert.rejects(()=>captureJob({tab:tab(),outputRoot:folder},{...job,id:'scope',url:'https://www.codepublishing.com/WA/Burien/'}),/scoped public/);checks++;
 console.log(JSON.stringify({status:'passed',checks,sha_vectors:5,utf16_chunk_surrogate_preserved:true,immutable_target_rejected:true,same_length_mutation_rejected:true,stale_heading_rejected:true,scope_escape_rejected:true}));
}finally{await rm(folder,{recursive:true,force:true});}
