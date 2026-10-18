"""Independent actual King County source DOM ownership/tables, inert before attachment."""
import argparse,collections,hashlib,json,re
from pathlib import Path
from playwright.sync_api import sync_playwright
from inert_browser_source import attach_inert_html,provenance

def sha(b):return hashlib.sha256(b).hexdigest()
def clean(s):return ' '.join(s.split())
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--normalized',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 if a.out.exists():raise ValueError('Fresh report required')
 raw_records=(a.normalized/'records.jsonl').read_bytes();records=[json.loads(x) for x in raw_records.splitlines()];groups=collections.defaultdict(list)
 for r in records:groups[r['source_document_id']].append(r)
 cp=json.loads((a.source/'checkpoint.json').read_text());errors=[];body_errors=[];checked=[];transforms=[];counts=collections.Counter();requests=[]
 with sync_playwright() as pw:
  b=pw.chromium.launch(channel='chrome',headless=True);c=b.new_context(java_script_enabled=False);c.route('**/*',lambda route:(requests.append(route.request.url),route.abort()));p=c.new_page()
  for item in cp['artifacts']:
   if item['role']!='content':continue
   raw=(a.source/item['path']).read_bytes();assert sha(raw)==item['sha256'];rows=groups[item['source_url']];assert all(r['source_sha256']==item['sha256'] for r in rows);encoding=re.search(br'charset\s*=\s*[\"\']?([A-Za-z0-9_-]+)',raw[:4096],re.I);encoding=encoding.group(1).decode() if encoding else 'utf-8';attach_inert_html(p,raw.decode(encoding))
   source=p.evaluate(r'''()=>{let transformations=[];for(let e of document.querySelectorAll('[style]'))if(e.style.textTransform&&e.style.textTransform!=='none'){transformations.push({tag:e.tagName.toLowerCase(),source_text:e.textContent,source_transform:e.style.textTransform});e.style.textTransform='none'}const blocks=new Set('p h1 h2 h3 h4 h5 h6 table ul ol pre blockquote svg img picture object iframe hr'.split(' '));let out=[];
const table=t=>({rows:Array.from(t.rows).map(row=>Array.from(row.cells).map(cell=>({text:cell.innerText,tag:cell.tagName.toLowerCase(),rowspan:cell.getAttribute('rowspan')||'1',colspan:cell.getAttribute('colspan')||'1'})))});
function walk(e){for(let n of e.childNodes){if(n.nodeType===3){if(n.textContent.trim())out.push({text:n.textContent,tables:[]});continue}if(n.nodeType!==1||['SCRIPT','STYLE','HEAD'].includes(n.tagName))continue;if(blocks.has(n.tagName.toLowerCase())){let ts=n.tagName==='TABLE'?[n]:Array.from(n.querySelectorAll('table'));out.push({text:n.innerText,tables:ts.map(table)})}else walk(n)}}walk(document.body);return {blocks:out,transformations}}''')
   transforms.append({'url':item['source_url'],'source_raw_sha256':item['sha256'],'occurrences':source['transformations']});source=source['blocks']
   owned=[];table_source=[];table_output=[]
   for r in sorted(rows,key=lambda r:r['source_ordinal']):
    indices=r['block_indices'];owned.extend(indices)
    expected=clean(' '.join(source[i]['text'] for i in indices if i<len(source)))
    if expected!=clean(r['full_text']):body_errors.append({'record_id':r['record_id'],'url':item['source_url'],'source':expected,'normalized':r['full_text']})
    table_output.extend(r['tables'])
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
 report={'passed':not errors and not body_errors,'table_and_ownership_passed':not errors,'script_sha256':sha(Path(__file__).read_bytes()),'inert_source_preparation':provenance(),'records_sha256':sha(raw_records),'documents':checked,**counts,'errors':errors,'body_text_mismatches':body_errors,'source_text_transform_dispositions':transforms,'browser':version,'network_requests_sent':0,'resource_requests_aborted':len(requests),'scope':'Actual HTML source-body exclusive block ownership/cells and browser text. Exact native text casing is retained; observed inline CSS text-transform display effects are separately inventoried and disabled only for native-text comparison. Candidate only; source date/dependency/closing gaps remain. No image pixels rendered or source network requests.'};a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],**counts,'table_errors':len(errors),'body_errors':len(body_errors)}));return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
