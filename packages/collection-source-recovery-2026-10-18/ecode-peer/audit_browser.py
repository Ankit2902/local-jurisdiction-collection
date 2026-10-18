"""Original retained native DOM ownership/table/cell audit, before any normalizer."""
import sys
sys.dont_write_bytecode=True
import hashlib,json,time
from pathlib import Path
from playwright.sync_api import sync_playwright
from inert_browser_source import attach_inert_html,provenance
ROOT=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00');SOURCE=ROOT/'outputs/collection-readiness-post-91f6c59-2026-10-17/ecode/albany-image-context-replay-v2';TARGET=ROOT/'outputs/collection-readiness-post716cfcb-2026-10-17/ecode-recovery-audit-v1/albany-derived-v2';OUT=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
COLLECT=r'''()=>{let code=document.querySelector('#codeContent');if(!code)throw Error('Missing source codeContent');let originals=Array.from(code.querySelectorAll('[id]')).filter(x=>/^[0-9]+_content$/.test(x.id)&&x.classList.contains('content')),stage=document.createElement('div'),sources=[];for(let e of originals){let copy=e.cloneNode(true);for(let n of Array.from(copy.querySelectorAll('[id]')))if(/^[0-9]+_content$/.test(n.id)&&n.classList.contains('content'))n.remove();for(let n of copy.querySelectorAll('script,style,button,input,.actions,.selection-control'))n.remove();let id=e.id.slice(0,-8);stage.append(copy);sources.push([id,copy])}document.body.replaceChildren(stage);let out={};for(let[id,copy]of sources){let ts=Array.from(copy.querySelectorAll('table'));out[id]={text_content:copy.textContent,inner_text:copy.innerText,tables:ts.map(t=>({parent_table_index:ts.indexOf(t.parentElement.closest('table'))<0?null:ts.indexOf(t.parentElement.closest('table')),rows:Array.from(t.rows).map(r=>Array.from(r.cells).map(c=>({tag:c.tagName.toLowerCase(),rowspan:c.getAttribute('rowspan')||'1',colspan:c.getAttribute('colspan')||'1',scope:c.getAttribute('scope'),headers:c.getAttribute('headers'),text:c.innerText})))}))}}return out}'''
start=time.time();cp=json.loads((SOURCE/'checkpoint.json').read_text());records=[json.loads(x) for x in (TARGET/'records.jsonl').read_text().split('\n') if x];by={r['id']:r for r in records};original={};blocked=[];errors=[];tables=rows=cells=0
with sync_playwright() as pw:
 browser=pw.chromium.launch(channel='chrome',headless=True);context=browser.new_context(java_script_enabled=False);context.route('**/*',lambda route:(blocked.append(route.request.url),route.abort()));page=context.new_page()
 for ai,a in enumerate(cp['artifacts']):
  if a['status']!=200:continue
  raw=(SOURCE/a['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==a['sha256'];attach_inert_html(page,raw);got=page.evaluate(COLLECT)
  for key,value in got.items():assert key not in original;original[key]=value
  if ai%50==0:print('source raw documents',ai,'owners',len(original),flush=True)
 # Canonical output fragments stage in one inert document, with original ownerID restored only for this QA lookup.
 document='<div id="codeContent">'+''.join('<div class="content" id="'+r['id']+'_content">'+r['semantic_html']+'</div>' for r in records)+'</div>'
 attach_inert_html(page,document.encode());normalized=page.evaluate(COLLECT);version=browser.version;browser.close()
assert set(normalized)==set(by)
def collapse(s):return ' '.join(s.split())
def compact(s):return ''.join(x for x in s if not x.isspace())
for ident,source in original.items():
 if ident not in by:
  if compact(source['text_content']) or source['tables']:errors.append({'id':ident,'field':'unemitted_original_content'})
  continue
 target=normalized[ident]
 for field in ['text_content','inner_text']:
  s,t=source[field],target[field]
  if (compact(s) if field=='text_content' else collapse(s))!=(compact(t) if field=='text_content' else collapse(t)):errors.append({'id':ident,'field':field,'source_sample':s[:300],'output_sample':t[:300],'source_chars':len(s),'output_chars':len(t)})
 if len(source['tables'])!=len(target['tables']):errors.append({'id':ident,'field':'table_count','source':len(source['tables']),'output':len(target['tables'])})
 for ti,table in enumerate(source['tables']):
  tables+=1;nt=target['tables'][ti] if ti<len(target['tables']) else {'rows':[]}
  if table['parent_table_index']!=nt.get('parent_table_index'):errors.append({'id':ident,'table':ti,'field':'table_parent'})
  if len(table['rows'])!=len(nt['rows']):errors.append({'id':ident,'table':ti,'field':'rows'})
  for ri,row in enumerate(table['rows']):
   rows+=1;nr=nt['rows'][ri] if ri<len(nt['rows']) else []
   if len(row)!=len(nr):errors.append({'id':ident,'table':ti,'row':ri,'field':'cell_count'})
   for ci,c in enumerate(row):
    cells+=1;nc=nr[ci] if ci<len(nr) else {}
    for field,value in c.items():
     nv=nc.get(field)
     if field=='text':value=collapse(value);nv=collapse(nv or '')
     if value!=nv:errors.append({'id':ident,'table':ti,'row':ri,'cell':ci,'field':field,'source':value,'normalized':nv})
summary={'passed':not errors,'raw_artifacts':401,'successful_original_raw_HTML':400,'explicit_original_owner_bodies':len(original),'acquired_records':len(by),'tables':tables,'rows':rows,'cells':cells,'browser':version,'source_preparation':provenance(),'source_image_link_policy':'Keep available label/child text and append marker, matching two explicit image-reference positions when image is inside image hyperlink','network_requests_sent':0,'resource_attempts':len(blocked),'blocked_resources':blocked,'image_render_decode_extract_OCR_calls':0,'source_text_content_comparison':'Only whitespace removed; all other literal codepoints/order/markers exact','source_innerText_and_cell_comparison':'Only whitespace collapsed; no punctuation/Unicode aliases or source rewriting','mismatches':errors,'seconds':time.time()-start,'script_sha256':sha(Path(__file__)),'corrected_records_sha256':sha(TARGET/'records.jsonl'),'corrected_frozen_manifest_sha256':sha(TARGET.parent/'DERIVATIVE-V2-MANIFEST.json')};(OUT/'original-native-browser-audit.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k not in ['mismatches','blocked_resources']},indent=2));print('MISMATCHES',errors[:12]);raise SystemExit(0 if summary['passed'] else 2)
