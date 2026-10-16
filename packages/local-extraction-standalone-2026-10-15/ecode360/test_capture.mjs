import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {mkdtemp,readFile,writeFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {sha256Browser} from './sha256_browser.mjs';
import {captureJob} from './acquire_cua.mjs';
const sha=s=>createHash('sha256').update(s).digest('hex');
let tests=0;
for(const value of ['', 'abc', 'x'.repeat(100000), '§ 1.01.010 – Code 🏛', '\ud800']){assert.equal(sha256Browser(value),sha(value));tests++;}
const base=await mkdtemp(join(tmpdir(),'ecode-cua-capture-'));
function fake(raw,options={}){
 let reads=0;const ident={customer_id:'TE0000',code_id:'1',currency_raw:'2026-01-01'};
 const before={url:'https://ecode360.com/123',title:'Chapter 1 Test',length:raw.length,sha256:sha(raw),source_html:raw.length<=120000?raw:null,identity:ident,challenge:false,section_bodies:['124_content'],toc:[{node_id:'124'}],heading_node_id:options.stale?'789':'123',legal_header_ids:['124']};
 return {outputRoot:base,browserId:'mock',closed:false,tab:{url:async()=>before.url,getAXState:async()=> 'retained mock AX',playwright:{locator:()=>({first:()=>({waitFor:async()=>{}})}),evaluate:async(fn,arg)=>{reads++;if(typeof fn==='string'){if(fn.includes('section_bodies:'))return structuredClone(before);return {url:before.url,length:raw.length,sha256:sha(raw),identity:ident,heading_node_id:before.heading_node_id};}let piece=raw.slice(arg.offset,arg.offset+40000);if(options.corrupt&&arg.offset===40000)piece='X'+piece.slice(1);return piece;} }},get reads(){return reads;}};
}
const job=id=>({slug:'test-ca',id,url:'https://ecode360.com/123',kind:'legal',expected_node_id:'123'});
try{
 const source='<div>'+'a'.repeat(39994)+'🏛'+'b'.repeat(100000)+'</div>';
 const acq=fake(source);const first=await captureJob(acq,job('unicode'));assert.equal(first.accepted,true);assert.equal((await readFile(base+'/test-ca/unicode.html','utf8')),source);tests++;
 const priorReads=acq.reads;const again=await captureJob(acq,job('unicode'));assert.equal(again.status,'verified_existing_immutable_capture');assert.equal(acq.reads,priorReads);tests++;
 const receiptBefore=await readFile(base+'/test-ca/unicode.receipt.json','utf8');await writeFile(base+'/test-ca/unicode.html','changed');await assert.rejects(captureJob(acq,job('unicode')),/binding changed/);assert.equal(await readFile(base+'/test-ca/unicode.receipt.json','utf8'),receiptBefore);tests++;
 const stale=await captureJob(fake('<div>legal text</div>',{stale:true}),job('stale'));assert.equal(stale.accepted,false);const staleReceipt=JSON.parse(await readFile(stale.receipt_path,'utf8'));assert.equal(staleReceipt.requested_node_ready,false);tests++;
 const corrupt=await captureJob(fake(source,{corrupt:true}),job('corrupt'));assert.equal(corrupt.accepted,false);tests++;
 const large=await captureJob(fake('a'.repeat(2000001)),job('large'));assert.equal(large.accepted,false);assert.match(JSON.parse(await readFile(large.receipt_path,'utf8')).error,/capture limit/);tests++;
 console.log(tests+' acquisition regressions passed (5 SHA vectors +6 capture/immutability/mutation/UTF16/identity/size checks)');
}finally{await rm(base,{recursive:true,force:true});}
