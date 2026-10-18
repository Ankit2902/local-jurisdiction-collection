"""Independent Flagstaff raw document body/table conservation, inert before attachment."""
import argparse,collections,hashlib,json,re
from pathlib import Path
from urllib.parse import urldefrag
from playwright.sync_api import sync_playwright
from inert_browser_source import attach_inert_html,provenance

def sha(b):return hashlib.sha256(b).hexdigest()
def clean(s):return ' '.join(s.split())
def decode_raw(raw):
 try:return raw.decode('utf-8-sig'),'utf-8-sig'
 except UnicodeDecodeError:
  match=re.search(br'charset\s*=\s*[\"\']?([A-Za-z0-9_-]+)',raw[:4096],re.I);enc=match.group(1).decode() if match else 'cp1252'
  if enc.lower() in ['iso-8859-1','latin1','windows-1252']:enc='cp1252'
  return raw.decode(enc),enc
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--normalized',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 if a.out.exists():raise ValueError('Fresh report required')
 raw_records=(a.normalized/'records.jsonl').read_bytes();records=[json.loads(x) for x in raw_records.split(b'\n') if x.strip()];groups=collections.defaultdict(list)
 for r in records:groups[urldefrag(r['source_url'])[0]].append(r)
 checkpoint_bytes=(a.source/'checkpoint.json').read_bytes();cp=json.loads(checkpoint_bytes);
 content=[v for v in cp['artifacts'] if v['role']=='content'];assert len(content)==len({v['source_url'] for v in content});assert set(groups)=={v['source_url'] for v in content};
 normalization_manifest=json.loads((a.normalized/'executed-normalization.json').read_text());normalization_sources={n:sha((a.normalized/'executed-normalization'/n).read_bytes()) for n in normalization_manifest};assert normalization_sources==normalization_manifest;errors=[];body_errors=[];checked=[];transforms=[];counts=collections.Counter();requests=[]
 with sync_playwright() as pw:
  b=pw.chromium.launch(channel='chrome',headless=True);c=b.new_context(java_script_enabled=False);c.route('**/*',lambda route:(requests.append(route.request.url),route.abort()));p=c.new_page()
  for item in cp['artifacts']:
   if item['role']!='content':continue
   raw=(a.source/item['path']).read_bytes();assert sha(raw)==item['sha256'];rows=groups[item['source_url']];assert all(r['source_sha256']==item['sha256'] for r in rows);text,encoding=decode_raw(raw);attach_inert_html(p,text)
   source=p.evaluate(r'''()=>{let transformations=[];for(let e of document.querySelectorAll('[style]'))if(e.style.textTransform&&e.style.textTransform!=='none'){transformations.push({tag:e.tagName.toLowerCase(),source_text:e.textContent,source_transform:e.style.textTransform});e.style.textTransform='none'}const blocks=new Set('p h1 h2 h3 h4 h5 h6 table ul ol pre blockquote svg img picture object iframe hr'.split(' '));let out=[];
const table=t=>({rows:Array.from(t.rows).map(row=>Array.from(row.cells).map(cell=>({text:cell.innerText,tag:cell.tagName.toLowerCase(),rowspan:cell.getAttribute('rowspan')||'1',colspan:cell.getAttribute('colspan')||'1'})))});
function walk(e){for(let n of e.childNodes){if(n.nodeType===3){if(n.textContent.trim())out.push({text:n.textContent,tables:[],heading:false});continue}if(n.nodeType!==1||['SCRIPT','STYLE','HEAD'].includes(n.tagName))continue;if(blocks.has(n.tagName.toLowerCase())){let ts=n.tagName==='TABLE'?[n]:Array.from(n.querySelectorAll('table'));out.push({text:n.innerText,tables:ts.map(table),heading:/^H[1-6]$/.test(n.tagName)||(n.tagName==='P'&&n.classList.contains('Division'))})}else walk(n)}}const legal=document.querySelector('#mainContent');if(!legal)throw Error('Original source mainContent absent');walk(legal);return {blocks:out,transformations}}''')
   transforms.append({'url':item['source_url'],'source_raw_sha256':item['sha256'],'occurrences':source['transformations']});source=source['blocks']
   owned=[];table_source=[];table_output=[]
   for r in rows:
    indices=r['block_indices'];owned.extend(indices)
    expected=clean(' '.join(source[i]['text'] for i in indices if i<len(source)))
    if expected!=clean(r['full_text']):body_errors.append({'record_id':r['record_id'],'url':item['source_url'],'source':expected,'normalized':r['full_text']})
    table_output.extend(r['tables'])
   owners={i:r for r in rows for i in r['block_indices']}
   for index,block in enumerate(source):
    if block['heading'] and clean(block['text']):
     counts['substantive_source_headings']+=1;owner=owners.get(index)
     if not owner or owner['block_indices'][0]!=index or clean(owner['heading'])!=clean(block['text']):errors.append({'url':item['source_url'],'kind':'source_heading_metadata_or_boundary','block':index,'source':clean(block['text']),'owner':owner['record_id'] if owner else None,'normalized':owner['heading'] if owner else None})
   if sorted(owned)!=list(range(len(source))):errors.append({'url':item['source_url'],'kind':'source_block_ownership','source_count':len(source),'owned_count':len(owned),'missing':sorted(set(range(len(source)))-set(owned))[:30]})
   for block in source:table_source.extend(block['tables'])
   if len(table_source)!=len(table_output):errors.append({'url':item['source_url'],'kind':'table_count','source':len(table_source),'normalized':len(table_output)})
   for ti,table in enumerate(table_source):
    counts['tables']+=1;nr=table_output[ti]['rows'] if ti<len(table_output) else []
    if len(table['rows'])!=len(nr):errors.append({'url':item['source_url'],'table':ti,'kind':'row_count'})
    for ri,row in enumerate(table['rows']):
     counts['rows']+=1;nc=nr[ri] if ri<len(nr) else []
     if len(row)!=len(nc):errors.append({'url':item['source_url'],'table':ti,'row':ri,'kind':'cell_count'})
     for ci,cell in enumerate(row):
      counts['cells']+=1
      for key,value in cell.items():
       got=nc[ci].get(key) if ci<len(nc) else None
       if key=='text':value=clean(value);got=clean(got or '')
       else:value=str(value);got=str(got)
       if value!=got:errors.append({'url':item['source_url'],'table':ti,'row':ri,'cell':ci,'field':key,'source':value,'normalized':got})
   counts['source_blocks']+=len(source);counts['records']+=len(rows);checked.append({'url':item['source_url'],'raw_sha256':item['sha256'],'source_blocks':len(source),'records':len(rows),'tables':len(table_source)})
  version=b.version;b.close()
 assert (a.normalized/'records.jsonl').read_bytes()==raw_records and (a.source/'checkpoint.json').read_bytes()==checkpoint_bytes
 report={'passed':not errors and not body_errors,'table_and_ownership_passed':not errors,'script_sha256':sha(Path(__file__).read_bytes()),'inert_source_preparation':provenance(),'records_sha256':sha(raw_records),'source_checkpoint_sha256':sha(checkpoint_bytes),'executed_normalization_sources':normalization_sources,'documents':checked,**counts,'errors':errors,'body_text_mismatches':body_errors,'source_text_transform_dispositions':transforms,'browser':version,'network_requests_sent':0,'resource_requests_aborted':len(requests),'scope':'Actual HTML source-body exclusive block ownership/cells and browser text. Exact native text casing is retained; observed inline CSS text-transform display effects are separately inventoried and disabled only for native-text comparison. Candidate only; This receipt qualifies exact full-source body/table conservation; graph/closing/dependencies and current integrated runtime are separately bound. No image pixels rendered or source network requests.'};a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],**counts,'table_errors':len(errors),'body_errors':len(body_errors)}));return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
