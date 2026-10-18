#!/usr/bin/env python3
"""Read-only active-image/inline-payload audit of actual normalized publication records."""
import argparse,hashlib,json,re
from pathlib import Path
from bs4 import BeautifulSoup
IMAGE=re.compile(r'(?:data:image/|\.(?:png|jpe?g|gif|webp|avif|svg|tiff?|bmp|ico)(?:[?#]|$))',re.I)
NORMALIZED_RECORD_NAMES=('records.jsonl','sections.jsonl','pdf-pages.jsonl')
def audit(root):
 root=Path(root).resolve();errors=[];files=[];records=0;markers=0
 for path in sorted(root.rglob('*.jsonl')):
  if path.name not in NORMALIZED_RECORD_NAMES or any(p in path.parts for p in ('executed-source','fixtures','normalization-source')):continue
  raw=path.read_bytes();count=0
  # JSONL uses LF delimiters; legal text may contain literal Unicode line separators.
  for line in raw.decode('utf-8').split('\n'):
   if not line.strip():continue
   record=json.loads(line);records+=1;count+=1;ident=record.get('id',record.get('node_id'))
   def walk(value,loc=''):
    nonlocal markers
    if isinstance(value,dict):
     for k,v in value.items():walk(v,loc+'/'+str(k))
    elif isinstance(value,list):
     for n,v in enumerate(value):walk(v,loc+'/'+str(n))
    elif isinstance(value,str):
     if re.search('data:image/',value,re.I):errors.append({'record':ident,'field':loc,'kind':'inline-image-payload-or-URI'})
     if loc.rsplit('/',1)[-1] not in ('html','body_html','text','heading','title','footnotes') and not re.search(r'<[a-z][^>]*>',value,re.I):return
     markers+=value.count('[IMAGE]')
     if not re.search(r'<[a-z][^>]*>',value,re.I):return
     soup=BeautifulSoup(value,'html.parser')
     for e in soup.find_all(True):
      attrs=e.attrs;tag=e.name.lower();reason=None
      if tag in ('img','picture','svg','image') or tag=='input' and str(attrs.get('type','')).lower()=='image':reason='active-image-element'
      if any(a in attrs for a in ('background','poster')):reason='active-image-attribute'
      if re.search(r'url\s*\(',str(attrs.get('style','')),re.I) or tag=='style' and re.search(r'url\s*\(',e.get_text(),re.I):reason='active-CSS-image-url'
      if tag in ('object','embed','source') and (str(attrs.get('type','')).lower().startswith('image/') or IMAGE.search(str(attrs.get('data',attrs.get('src',''))))):reason='active-object-source-image'
      if tag=='a' and IMAGE.search(str(attrs.get('href',''))):reason='active-image-link'
      if reason:errors.append({'record':ident,'field':loc,'tag':tag,'kind':reason})
   walk(record)
  files.append({'path':str(path.relative_to(root)),'sha256':hashlib.sha256(raw).hexdigest(),'records':count})
 return {'schema_version':1,'read_only':True,'network_requests_sent':0,'run_name':root.name,'record_files':files,'normalized_records':records,'placeholder_occurrences_across_serializations':markers,'passed':bool(files) and not errors,'errors':errors,'scope_note':'Actual normalized record fields and recursive metadata only; raw originals may retain original image markup. Marker count includes separate HTML/text/table serializations and is not source image occurrence count.'}
def main():
 p=argparse.ArgumentParser();p.add_argument('run',type=Path);a=p.parse_args();r=audit(a.run);print(json.dumps(r,indent=2));return 0 if r['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
