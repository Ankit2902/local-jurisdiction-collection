"""Six exact retained source anchors; ordinary shared-gate GET, metadata only."""
import sys
sys.dont_write_bytecode=True
import hashlib,io,json,pathlib,time,urllib.parse
H=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(H/'captured'))
from bs4 import BeautifulSoup
from collectors.encodeplus.transport import fetch,Stopped
from collectors.encodeplus.retained_native import guards
from pypdf import PdfReader
rows=[r for r in json.loads((H/'catalog-input.json').read_text())if r['publisher']=='encodeplus'];raw=(H/'publisher-documents-retained.html').read_bytes();receipt=json.loads((H/'publisher-documents-retained.html.receipt.json').read_text());assert hashlib.sha256(raw).hexdigest()==receipt['sha256']and receipt['http_status']==200;soup=BeautifulSoup(raw,'html.parser');anchors={urllib.parse.urljoin(receipt['url'],a['href']):a for a in soup.select('a[href]')};results=[];d=H/'native-discovery';d.mkdir(exist_ok=False)
for row in rows:
 url=row['source_url'];assert url in anchors,'No exact observed source URL';a=anchors[url];item={'id':row['id'],'catalog_title':row['title'],'url':url,'literal_anchor':str(a),'source_label':a.get_text(' ',strip=True),'source_parent':str(a.parent),'anchor_source_sha256':receipt['sha256'],'anchor_source_url':receipt['url'],'requested_alias_substitution':False};p=d/(row['id']+'.bin');started=time.monotonic()
 try:
  body,m=fetch(url,p);item.update(status=m['http_status'],final_url=m['final_url'],bytes=len(body),sha256=m['sha256'],headers=m['headers'],redirects=m['redirects'],elapsed_seconds=time.monotonic()-started)
  if body.startswith(b'%PDF-'):
   with guards()as calls:
    reader=PdfReader(io.BytesIO(body),strict=True);item.update(native_pdf=True,pages=len(reader.pages),metadata={str(k):str(v)for k,v in(reader.metadata or{}).items()},encrypted=bool(reader.is_encrypted),metadata_only=True,forbidden_operations=calls)
  else:item.update(native_pdf=False,body_prefix=body[:100].decode('utf-8','replace'))
 except Exception as error:
  item['error']=str(error)
  if p.with_name(p.name+'.receipt.json').exists():
   m=json.loads(p.with_name(p.name+'.receipt.json').read_text());item.update(status=m.get('http_status'),bytes=m.get('bytes'),sha256=m.get('sha256'),challenge=m.get('challenge'),final_url=m.get('final_url'))
  results.append(item);(d/'inventory.json').write_text(json.dumps(results,indent=2)+'\n')
  gate=pathlib.Path('/tmp/compliSolv-encodeplus-rate-gate/state.json');state=json.loads(gate.read_text())if gate.exists()else{}
  if state.get('stopped')or state.get('cooldown_until',0)>time.time():break
  continue
 results.append(item);(d/'inventory.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps({k:v for k,v in item.items()if k in ['id','status','bytes','pages','native_pdf','error']},flush=True))
print(json.dumps({'attempted':len(results),'known_entries':len(rows),'pdf_pages':sum(r.get('pages',0)for r in results),'total_bytes':sum(r.get('bytes',0)for r in results),'full_native_layout_parses':0,'publisher_gate_unchanged_policy':True}))
