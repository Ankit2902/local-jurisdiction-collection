"""Raw native + acquired publisher-client projection versus independent browser DOM.
No Gridics parser imports, no publisher network, no image extraction.
"""
import argparse,hashlib,json
from pathlib import Path
from playwright.sync_api import sync_playwright
from inert_browser_source import attach_inert_html, provenance
RENDERER='e02b7d56c01f9a7d2b3a980fe469efdcd5a10f1effb387075fd75c7ec9c6564a'
JS=r'''({nodes,projection,rendered})=>{
const image=(node)=>{for(let e of Array.from(node.querySelectorAll('img,picture,svg,image,use,input,object,embed,source'))){if(!e.parentNode)continue;let tag=e.tagName.toLowerCase(),u=e.getAttribute('src')||e.getAttribute('data')||'';if(['img','picture','svg','image','use'].includes(tag)||tag==='input'&&(e.getAttribute('type')||'').toLowerCase()==='image'||(e.getAttribute('type')||'').trim().toLowerCase().startsWith('image/')||/^data:image[/]/i.test(u)||/[.](png|jpe?g|gif|webp|svg|avif|bmp|ico|tiff?)([?#]|$)/i.test(u))e.replaceWith(document.createTextNode('[IMAGE]'))}for(let e of Array.from(node.querySelectorAll('script')))e.remove();for(let e of [node,...node.querySelectorAll('*')]){for(let a of ['background','poster'])if(e.hasAttribute(a)){e.prepend(document.createTextNode('[IMAGE]'));e.removeAttribute(a)}let n=((e.getAttribute('style')||'').match(/url[ ]*[(]/gi)||[]).length;if(n){e.prepend(document.createTextNode('[IMAGE]'.repeat(n)));e.removeAttribute('style')}if(e.tagName==='STYLE'){let n=(e.textContent.match(/url[ ]*[(]/gi)||[]).length;e.replaceWith(document.createTextNode('[IMAGE]'.repeat(n)))}if(e.tagName==='A'&&(/[.](png|jpe?g|gif|webp|svg|avif|bmp|ico|tiff?)([?#]|$)/i.test(e.getAttribute('href')||'')||/^data:image[/]/i.test(e.getAttribute('href')||'')))e.replaceWith(document.createTextNode('[IMAGE]'))}};
const read=(body)=>({text:body.innerText,tables:Array.from(body.querySelectorAll('table')).map(t=>Array.from(t.rows).map(tr=>Array.from(tr.cells).map(c=>({text:c.innerText,tag:c.tagName.toLowerCase(),rowspan:c.getAttribute('rowspan')||'1',colspan:c.getAttribute('colspan')||'1'}))))});let stage=document.createElement('main'),bodies=[],heads=[];
if(nodes){let transform=new Function('e','return '+projection);for(let n of nodes){let original=document.createElement('div'),projected=document.createElement('div'),heading=document.createElement('div');let values=[n.body,['section','subsection'].includes(n.dataTag)?transform({text:n.body}):n.body,n.heading];[original,projected,heading].forEach((e,i)=>{let t=document.createElement('template');t.innerHTML=values[i];image(t.content);e.append(t.content);stage.append(e)})bodies.push({id:n.path,original,projected});heads.push(heading)}document.body.replaceChildren(stage);let out={};bodies.forEach((b,i)=>out[b.id]={original:read(b.original),projected:read(b.projected),heading:heads[i].innerText});return out}
let sections=Array.from(document.querySelectorAll('div.section[data-path]'));for(let s of sections){let c=s.cloneNode(true),id=c.dataset.path;for(let child of c.querySelectorAll('div.section[data-path]'))child.remove();let h=c.querySelector('h1,h2,h3,h4,h5,h6');if(!h)throw Error('Missing original browser heading');let heading=h.cloneNode(true),anchor=h.parentElement;if(anchor.id.startsWith('anchor-'))anchor.remove();else h.remove();for(let e of c.querySelectorAll('.share-print'))e.remove();image(c);image(heading);stage.append(c,heading);bodies.push({id,body:c});heads.push(heading)}document.body.replaceChildren(stage);let out={};bodies.forEach((b,i)=>{if(out[b.id])throw Error('Duplicate original rendered source path');out[b.id]={...read(b.body),heading:heads[i].innerText}});return out}'''
def digest(b):return hashlib.sha256(b).hexdigest()
def clean(value):
 if isinstance(value,str):return ' '.join(value.split())
 if isinstance(value,list):return [clean(v) for v in value]
 if isinstance(value,dict):return {k:clean(v) for k,v in value.items()}
 return value
def audit(run):
 ledger=json.loads((run/'responses.json').read_text());records_bytes=(run/'records.jsonl').read_bytes();records=[json.loads(x) for x in records_bytes.splitlines()];by_path={r['source_path']:r for r in records};errors=[];text_differences=[];projection_differences=[];sources=[];blocked=[];counts={'phases':2,'roots':0,'records_checked_across_phases':0,'table_comparisons_across_phases':0,'cell_comparisons_across_phases':0};root_counts=[]
 def checked(receipt):
  assert receipt in ledger and receipt['status']==200;raw=(run/receipt['path']).read_bytes();assert digest(raw)==receipt['sha256'] and len(raw)==receipt['bytes'];return raw
 with sync_playwright() as pw:
  browser=pw.chromium.launch(channel='chrome',headless=True);context=browser.new_context(java_script_enabled=False);context.route('**/*',lambda route:(blocked.append(route.request.url),route.abort()));page=context.new_page()
  for phase in ['start','end']:
   cp=json.loads((run/(phase+'-checkpoint.json')).read_text());assert cp['phase_complete'];epoch=cp['roots_response']['epoch'];client=next(r for r in ledger if r['phase']==phase and r['epoch']==epoch and '/build/static/js/Doc.' in r['url'] and r['sha256']==RENDERER);js=checked(client).decode();marker='e.text=e.text.replace(';start=js.index(marker)+len('e.text=');end=js.index(',n.body.push(e.text)',start);projection=js[start:end];assert projection.count('.replace(')==3 and projection.startswith('e.text.replace(');sources.append({'phase':phase,'client_path':client['path'],'client_sha256':digest(js.encode()),'exact_projection_expression':projection})
   for row in cp['roots']:
    receipt=row['tree_response'];assert receipt['phase']==phase and receipt['epoch']==epoch;raw=checked(receipt);tree=json.loads(raw);nodes=[]
    def walk(n):
     assert n['docId']=='45' and n['path'].endswith('/'+n['id'])
     if n['li_attr'].get('dataTag')=='BodyM':return
     nodes.append({'id':n['id'],'path':n['path'],'heading':n['text'],'body':''.join(c['text'] for c in n.get('children',[]) if c['li_attr'].get('dataTag')=='BodyM'),'dataTag':n['li_attr'].get('dataTag')})
     for c in n.get('children',[]):walk(c)
    for n in tree:walk(n)
    page.set_content('<html><body></body></html>');native=page.evaluate(JS,{'nodes':nodes,'projection':projection,'rendered':False});dom=(run/row['dom_path']).read_bytes();assert digest(dom)==row['dom_sha256'];attach_inert_html(page,dom);witness=page.evaluate(JS,{'nodes':None,'projection':projection,'rendered':True});counts['roots']+=1;counts['records_checked_across_phases']+=len(nodes)
    if set(native)!=set(witness):errors.append({'phase':phase,'root':row['root']['id'],'kind':'source inventory mismatch'})
    for path,source in native.items():
     record=by_path[path];observed=witness.get(path,{});original=clean(source['original']);projected=clean(source['projected']);observed=clean(observed)
     if clean(source['heading'])!=clean(record['heading']) or clean(source['heading'])!=observed.get('heading'):errors.append({'phase':phase,'path':path,'field':'heading'})
     for field in ['text','tables']:
      if projected[field]!=observed.get(field):errors.append({'phase':phase,'path':path,'field':'projected-'+field,'expected':projected[field] if field=='text' else None,'rendered':observed.get(field) if field=='text' else None})
      if original[field]!=projected[field]:projection_differences.append({'phase':phase,'path':path,'field':field})
     if original['tables']!=clean(record['tables']):errors.append({'phase':phase,'path':path,'field':'native-record-tables','source':original['tables'],'normalized':clean(record['tables'])})
     if original['text']!=clean(record['text']):text_differences.append({'phase':phase,'path':path,'source_browser_text':original['text'],'normalized_native_text':record['text'],'note':'Informational: browser innerText omits generated list labels; requires source-specific review, never waived as proof.'})
     counts['table_comparisons_across_phases']+=len(original['tables']);counts['cell_comparisons_across_phases']+=sum(len(r) for t in original['tables'] for r in t)
    root_counts.append({'phase':phase,'root_id':row['root']['id'],'records':len(nodes),'native_response_sha256':digest(raw),'rendered_dom_sha256':digest(dom)})
  version=browser.version;browser.close()
 return {'schema_version':1,'kind':'independent-original-native-and-publisher-projected-browser-DOM-fidelity','script_sha256':digest(Path(__file__).read_bytes()),'records_sha256':digest(records_bytes),**counts,'source_client_evidence':sources,'root_checks':root_counts,'native_to_ui_projection_differences':projection_differences,'native_record_body_text_differences_requiring_review':text_differences,'errors':errors,'passed':not errors,'browser':version,'inert_source_preparation':provenance(),'network_requests_sent':0,'resource_requests_aborted':len(blocked),'scope_note':'Retained full source, not fresh acquisition. Original native source kept independent of UI projection. All tables/body UI projection compared with offline browser, no family parser imports. Informational browser-native text differences do not establish native body word loss without review. Missing external documents/empty provisions remain separate incomplete gates.'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args()
 if a.out.exists() or a.run.resolve() in a.out.resolve().parents:raise SystemExit('Fresh report outside retained evidence required')
 result=audit(a.run);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['errors','native_record_body_text_differences_requiring_review','native_to_ui_projection_differences','root_checks','source_client_evidence']},indent=2));print('errors',len(result['errors']),result['errors'][:3]);print('bodytext differences',len(result['native_record_body_text_differences_requiring_review']));raise SystemExit(0 if result['passed'] else 2)
