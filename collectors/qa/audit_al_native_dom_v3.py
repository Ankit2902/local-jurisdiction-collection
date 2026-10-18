"""Independent original AL native-export DOM cells; no family parser imports."""
import argparse,hashlib,json,re
from pathlib import Path
from playwright.sync_api import sync_playwright
from inert_browser_source import attach_inert_html, provenance

def audit(run,normalized):
 requests=json.loads((run/'requests.json').read_text());entry=requests['native-export'];raw=(run/entry['file']).read_bytes();assert hashlib.sha256(raw).hexdigest()==entry['sha256'];record_bytes=(normalized/'sections.jsonl').read_bytes();rs=[json.loads(s) for s in record_bytes.splitlines() if s];owners={};errors=[]
 for r in rs:
  for block in r['body_block_ids']:
   if block in owners:raise ValueError('Duplicate raw body block owner')
   owners[block]=r['document_id']
 blocked=[]
 with sync_playwright() as pw:
  browser=pw.chromium.launch(channel='chrome',headless=True);c=browser.new_context(java_script_enabled=False);c.route('**/*',lambda route:(blocked.append(route.request.url),route.abort()));p=c.new_page();attach_inert_html(p,raw)
  source=p.evaluate(r'''owners=>{let out={},staged=[],stage=document.createElement('table');for(let t of document.querySelectorAll('table')){let carrier=t.closest('[id^="rid-"]');let owner=carrier?owners[carrier.id.slice(4)]:null;if(!owner&&t.classList.contains('footnote')){let headers=Array.from(t.parentElement.children).filter(e=>(e.id||'').startsWith('rid-')&&e.classList.contains('toc-destination'));let previous=t.previousElementSibling;if(headers.length===1&&previous&&previous.textContent.trim()==='Notes'){let wrapper=t.parentElement;let anchors=Array.from(t.querySelectorAll('a[name^="foot--"]'));let reciprocal=anchors.length>0&&anchors.every(a=>{let label=a.getAttribute('name').slice(6),back=a.nextElementSibling;if(!back||back.getAttribute('href')!=='#text--'+label)return false;let refs=Array.from(wrapper.querySelectorAll('a[name]')).filter(x=>x.getAttribute('name')==='text--'+label);return refs.length===1&&refs[0].nextElementSibling&&refs[0].nextElementSibling.getAttribute('href')==='#foot--'+label});if(!reciprocal)throw Error('Footnote source reciprocal anchors not bound');owner=owners[headers[0].id.slice(4)]}}if(!owner)throw Error('Unowned original table');(out[owner]||=[]).push(t)}let result={};for(let [id,tables] of Object.entries(out)){result[id]=tables.map(t=>({parent:tables.indexOf(t.parentElement.closest('table'))<0?null:tables.indexOf(t.parentElement.closest('table')),rows:Array.from(t.rows).map(row=>Array.from(row.cells).map(cell=>{let copy=cell.cloneNode(true);for(let e of copy.querySelectorAll('script,style,annotationdrawer,codeoptions,.clearfix'))e.remove();for(let e of Array.from(copy.querySelectorAll('img,picture,svg,image,use,object,embed,input,source,iframe'))){if(!e.parentNode)continue;let tag=e.tagName.toLowerCase(),url=e.getAttribute('src')||e.getAttribute('data')||'';if(['picture','svg','img','image','use'].includes(tag)||/[.](png|jpe?g|gif|webp|svg|avif|bmp|ico|tiff?)([?#]|$)/i.test(url)||/^data:image[/]/i.test(url)||(e.type||'').trim().toLowerCase().startsWith('image/')||(tag==='input'&&(e.type||'').toLowerCase()==='image'))e.replaceWith(document.createTextNode('[IMAGE]'))}for(let e of [copy,...copy.querySelectorAll('*')]){for(let attr of ['background','poster'])if(e.hasAttribute(attr)){e.prepend(document.createTextNode('[IMAGE]'));e.removeAttribute(attr)}let n=((e.getAttribute('style')||'').match(/url[ ]*[(]/gi)||[]).length;if(n){e.prepend(document.createTextNode('[IMAGE]'.repeat(n)));e.removeAttribute('style')}if(e.tagName==='A'&&(/[.](png|jpe?g|gif|webp|svg|avif|bmp|ico|tiff?)([?#]|$)/i.test(e.href)||/^data:image[/]/i.test(e.getAttribute('href')||'')))e.replaceWith(document.createTextNode('[IMAGE]'))}let tr=document.createElement('tr');tr.append(copy);stage.append(tr);let value={text:null,tag:cell.tagName.toLowerCase(),rowspan:Number(cell.getAttribute('rowspan')||1),colspan:Number(cell.getAttribute('colspan')||1)};staged.push({copy,value});return value}))}))}document.body.replaceChildren(stage);for(let {copy,value}of staged)value.text=copy.innerText;return result}''',owners)
  version=browser.version;browser.close()
 tables=rows=cells=0
 for r in rs:
  ts=source.get(r['document_id'],[])
  if len(ts)!=len(r['tables']):errors.append({'id':r['document_id'],'field':'table_count','source':len(ts),'output':len(r['tables'])})
  for ti,t in enumerate(ts):
   tables+=1;nt=r['tables'][ti] if ti<len(r['tables']) else []
   if t['parent']!=r['table_parent_indices'][ti]:errors.append({'id':r['document_id'],'table':ti,'field':'parent_index'})
   if len(t['rows'])!=len(nt):errors.append({'id':r['document_id'],'table':ti,'field':'row_count'})
   for ri,row in enumerate(t['rows']):
    rows+=1;nr=nt[ri] if ri<len(nt) else []
    if len(row)!=len(nr):errors.append({'id':r['document_id'],'table':ti,'row':ri,'field':'cell_count'})
    for ci,cell in enumerate(row):
     cells+=1
     for f,v in cell.items():
      n=nr[ci].get(f) if ci<len(nr) else None
      if f=='text':v=' '.join(v.split());n=' '.join((n or '').split())
      if f in ['rowspan','colspan']:v=str(v);n=str(n)
      if v!=n:errors.append({'id':r['document_id'],'table':ti,'row':ri,'cell':ci,'field':f,'source':v,'normalized':n})
 return {'schema_version':1,'kind':'independent-original-native-browser-DOM-tables','script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'source_sha256':entry['sha256'],'records_sha256':hashlib.sha256(record_bytes).hexdigest(),'records':len(rs),'table_records':len(source),'tables':tables,'rows':rows,'cells':cells,'browser':version,'inert_source_preparation':provenance(),'network_requests_sent':0,'resource_requests_aborted':len(blocked),'mismatches':errors,'passed':not errors,'limits':['Whitespace collapsed; full-body and independent TOC reconciliation remain separate.']}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('--normalized',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 if a.out.exists() or a.run.resolve() in a.out.resolve().parents:raise SystemExit('Fresh report outside evidence required')
 r=audit(a.run,a.normalized);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='mismatches'},indent=2));print('mismatch sample',r['mismatches'][:5]);raise SystemExit(0 if r['passed'] else 2)
