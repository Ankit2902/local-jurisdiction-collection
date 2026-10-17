#!/usr/bin/env python3
"""Independent original native HTML -> output table audit. No model normalization/parser calls."""
import argparse,hashlib,json,re,sys,zipfile
from pathlib import Path
sys.dont_write_bytecode=True
from bs4 import BeautifulSoup,NavigableString
IMAGE=re.compile(r'\.(?:png|jpe?g|gif|webp|svg|avif|bmp|ico|tiff?)(?:$|[?#])',re.I)
def cell_text(cell):
 s=BeautifulSoup(str(cell),'html.parser')
 for e in list(s.find_all(['picture','svg','img','image','use','object','embed','input','source','iframe'])):
  if e.parent is None or any(p.name in ['picture','svg'] for p in e.parents):continue
  u=e.get('src') or e.get('data') or ''
  if e.name in ['picture','svg','img','image','use'] or IMAGE.search(u) or u.lower().startswith('data:image/') or e.get('type','').strip().lower().startswith('image/') or (e.name=='input' and e.get('type','').strip().lower()=='image'):e.replace_with(NavigableString('[IMAGE]'))
 for e in list(s.find_all(True)):
  for attr in ['poster','background']:
   if e.get(attr):e.insert(0,NavigableString('[IMAGE]'))
  value=e.get('style','');urls=re.findall(r'url\([\s\'\"]*([^\)\'\"]+)',value,re.I)
  count=sum(bool(u.lower().startswith('data:image/') or IMAGE.search(u) or not re.search(r'\.(?:css|woff2?|ttf|otf|eot)(?:$|[?#])',u,re.I)) for u in urls)
  if count:e.insert(0,NavigableString('[IMAGE]'*count))
  if e.name=='a' and (IMAGE.search(e.get('href') or e.get('to') or '') or (e.get('href') or e.get('to') or '').lower().startswith('data:image/')):e.replace_with(NavigableString('[IMAGE]'))
 for e in s.select('script,style,annotationdrawer,codeoptions,.clearfix'):e.decompose()
 # Inline nodes contribute adjacent source characters. Only block/row/cell
 # boundaries contribute a separator; do not invent spaces around emphasis.
 for e in s.find_all(['address','article','aside','blockquote','caption','dd','div','dl','dt','fieldset','figcaption','figure','footer','form','h1','h2','h3','h4','h5','h6','header','hr','li','main','nav','ol','p','pre','section','table','tbody','td','tfoot','th','thead','tr','ul','br']):
  e.insert_before(NavigableString(' '));e.insert_after(NavigableString(' '))
 return ' '.join(s.get_text().split())
def audit(raw,records):
 source=BeautifulSoup(raw,'html.parser');owners={};byid={r['document_id']:r for r in records};fail=[]
 for r in records:
  for block in r['body_block_ids']:
   if block in owners:fail.append({'kind':'duplicate_block_owner','block':block})
   owners[block]=r['document_id']
 grouped={r['document_id']:[] for r in records};alltables=source.find_all('table');cells=0
 for i,t in enumerate(alltables):
  carrier=next((p for p in [t,*t.parents] if getattr(p,'attrs',None) and p.get('id','').startswith('rid-')),None)
  owner=owners.get(carrier['id'][4:]) if carrier else None
  if owner is None:fail.append({'kind':'unowned_original_table','source_table_index':i});continue
  grouped[owner].append(t)
 for did,tables in grouped.items():
  r=byid[did];expected=[];parents=[]
  for t in tables:
   p=t.find_parent('table');parents.append(next((i for i,q in enumerate(tables) if q is p),None));rows=[]
   for tr in t.find_all('tr'):
    if tr.find_parent('table') is not t:continue
    row=[{'tag':c.name,'text':cell_text(c),'rowspan':int(c.get('rowspan',1)),'colspan':int(c.get('colspan',1))} for c in tr.find_all(['td','th'],recursive=False)];cells+=len(row);rows.append(row)
   expected.append(rows)
  if expected!=r['tables']:fail.append({'kind':'original_cell_text_tag_or_span_mismatch','document_id':did,'source_tables':len(expected),'output_tables':len(r['tables'])})
  if parents!=r['table_parent_indices']:fail.append({'kind':'nested_table_parent_mismatch','document_id':did})
 return {'schema_version':1,'scope':'Original native HTML DOM table text/tag/rowspan/colspan/nesting fidelity; independent of model.py; not inventory completeness by itself','source_sha256':hashlib.sha256(raw).hexdigest(),'record_count':len(records),'source_table_count':len(alltables),'output_table_count':sum(len(r['tables']) for r in records),'source_cell_count':cells,'failures':fail,'passed':not fail}
def main():
 p=argparse.ArgumentParser();p.add_argument('run',type=Path);a=p.parse_args();z=zipfile.ZipFile(a.run) if a.run.is_file() else None
 def read(name):
  assert not Path(name).is_absolute() and '..' not in Path(name).parts
  return z.read(name) if z else (a.run/name).read_bytes()
 req=json.loads(read('requests.json'));entry=req['native-export'];raw=read(entry['file']);assert hashlib.sha256(raw).hexdigest()==entry['sha256'];records=[json.loads(v) for v in read('sections.jsonl').splitlines()];report=audit(raw,records);print(json.dumps(report,indent=2));return 0 if report['passed'] else 1
if __name__=='__main__':sys.exit(main())
