"""Pinned native-document acquisition via the enCodePlus gate. PDF page fidelity remains explicit review."""
import argparse,csv,io,json,pathlib,platform,re,sys
from pypdf import PdfReader
from .collect import code_hashes,HERE,cached,entry,runtime_info,ensure_revision
from .documents import qualify_document
from .util import digest,hash_json,atomic_bytes,atomic_json,read_json,validate_file

def metadata_text(value):
 value=str(value)
 return '[IMAGE]' if 'data:image/' in value.lower() else value

def page_records(data,cfg,raw_ref='raw/start.pdf'):
 from .pdf_structure import pages
 reader=PdfReader(io.BytesIO(data),strict=True)
 records,_=pages(data,{'id':cfg['id'],'heading':cfg['title'],'url':cfg['url'],'raw_ref':raw_ref},{'publication':cfg['title'],'jurisdiction':cfg['jurisdiction'],'state':cfg['state']})
 details={'metadata':{str(k):metadata_text(v) for k,v in (reader.metadata or {}).items()},'pages':len(records),'parser_sha256':digest((HERE/'pdf_structure.py').read_bytes()),'pdf_extractable_text_reconciled':all(r['pdf_qualification']['source_word_ownership_complete'] and r['pdf_qualification']['normalized_source_word_characters_agree'] and r['pdf_qualification']['independent_text_engine_characters_agree'] and not r['pdf_qualification']['unmapped_or_private_use_codepoints'] for r in records),'detected_table_cells_qualified':all(r['pdf_qualification']['detected_table_cells']==r['pdf_qualification']['independent_table_cells_agree'] for r in records),'detected_table_count':sum(r['pdf_qualification']['detected_table_count'] for r in records),'detected_table_cells':sum(r['pdf_qualification']['detected_table_cells'] for r in records),'pdf_table_semantics_complete':False,'reading_order_manual_review_required':True,'review_conditions':{str(r['physical_page']):r['pdf_qualification']['review_conditions'] for r in records if r['pdf_qualification']['review_conditions']}}
 return records,details
def outputs(records):
 buf=io.StringIO(newline='');fields=['id','heading','physical_page','page_count','text','source_url','raw_sha256'];w=csv.DictWriter(buf,fieldnames=fields);w.writeheader();w.writerows({k:r[k] for k in fields} for r in records)
 return {'records.jsonl':''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in records).encode(),'records.csv':buf.getvalue().encode()}
def validate_config(cfg):
 assert cfg['mode']=='native_document' and cfg['url'].startswith('https://'),'Wrong native-document mode/URL'
 assert set(['id','title','jurisdiction','state','url','expected_sha256','expected_pages','qualification']).issubset(cfg),'Native config requires qualified exact identity/source/hash/page pin'
 assert len(cfg['expected_sha256'])==64 and cfg['expected_pages']>0,'Invalid source pin'
def verify(out):
 out=pathlib.Path(out);errors=[]
 try:
  s=read_json(out/'checkpoint.json');cfg=s['config'];validate_config(cfg);assert hash_json(cfg)==s['config_sha256'],'Config binding mismatch'
  for name,h in s['code_hashes'].items():validate_file(out,'script-versions/'+h+pathlib.Path(name).suffix,h)
  bodies=[]
  for key in ['start','end']:
   e=s[key];p=validate_file(out,e['path'],e['sha256']);m=read_json(p.with_name(p.name+'.receipt.json'));assert e['url']==cfg['url']==m['url'] and m['http_status']==200 and not m.get('challenge') and m['sha256']==e['sha256'],'Native receipt/source binding mismatch';data=p.read_bytes();qualify_document(data,cfg['url'],'application/pdf');assert digest(data)==cfg['expected_sha256'],'Native file differs from qualified edition/hash';bodies.append(data)
  assert bodies[0]==bodies[1],'Native start/end bytes changed';records,details=page_records(bodies[0],cfg,s['start']['path']);assert details['pages']==cfg['expected_pages'],'Native page-count pin mismatch';assert s['phase']=='finished','Interrupted native-document collection'
  for name,data in outputs(records).items():assert (out/name).read_bytes()==data,'Native normalized output differs from source replay: '+name
  return {'schema_version':1,'status':'native_captured_semantic_review_required','target':cfg['id'],'publication_identity':cfg['title'],'source_url':cfg['url'],'native_document_complete':True,'source_page_traversal_complete':True,'physical_pages':len(records),'source_sha256':cfg['expected_sha256'],'start_end_consistent':True,'publication_text_complete':False,'attachments_complete':False,'edition_complete':False,'jurisdiction_complete':False,'image_policy':'[IMAGE]; original native PDFs allowed, no separate image extraction','pdf_details':details,'errors':[],'limits':['Whole original PDF and every page are retained/replayed. Coordinate text/word ownership and detected table cells are checked, but all tables, reading order and legal semantics remain explicitly qualified; do not promote this native-only result to full publication semantic completeness.']}
 except Exception as exc:return {'schema_version':1,'status':'incomplete','native_document_complete':False,'source_page_traversal_complete':False,'publication_text_complete':False,'attachments_complete':False,'edition_complete':False,'jurisdiction_complete':False,'errors':[type(exc).__name__+': '+str(exc)]}
def collect(cfg,out,resume=False,interrupt_after_start=False):
 validate_config(cfg);out=pathlib.Path(out)
 if resume:
  s=read_json(out/'checkpoint.json');assert s['config']==cfg and s['config_sha256']==hash_json(cfg) and s['code_hashes']==code_hashes(),'Wrong config or collector revision for native resume'
  if s['phase']=='finished':return verify(out)
 else:
  assert not out.exists() or not any(out.iterdir()),'Native output must be new';out.mkdir(parents=True,exist_ok=True);versions=code_hashes()
  for name,h in versions.items():atomic_bytes(out/'script-versions'/(h+pathlib.Path(name).suffix),(HERE/name).read_bytes())
  s={'native_schema_version':1,'config':cfg,'config_sha256':hash_json(cfg),'code_hashes':versions,'command':sys.argv,'runtime':runtime_info(),'phase':'start','failures':[]};atomic_json(out/'checkpoint.json',s)
 try:
  ensure_revision(s);data,meta=cached(out,cfg['url'],'raw/start.pdf');s['start']=entry('raw/start.pdf',meta);ensure_revision(s);qualify_document(data,cfg['url'],'application/pdf');assert digest(data)==cfg['expected_sha256'],'Wrong source edition/hash';records,details=page_records(data,cfg,s['start']['path']);assert details['pages']==cfg['expected_pages'],'Wrong page-count pin';s['phase']='normalized';atomic_json(out/'checkpoint.json',s)
  for name,b in outputs(records).items():atomic_bytes(out/name,b)
  if interrupt_after_start:raise InterruptedError('Intentional native checkpoint interruption')
  ensure_revision(s);end,em=cached(out,cfg['url'],'raw/end.pdf');s['end']=entry('raw/end.pdf',em);ensure_revision(s);assert end==data,'Native source changed during collection';s['phase']='finished';atomic_json(out/'checkpoint.json',s)
 except Exception as exc:s['phase']='interrupted' if isinstance(exc,InterruptedError) else 'failed';s['failures'].append({'type':type(exc).__name__,'reason':str(exc)});atomic_json(out/'checkpoint.json',s)
 report=verify(out);atomic_json(out/'coverage.json',report);return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--config',type=pathlib.Path);p.add_argument('--out',type=pathlib.Path);p.add_argument('--resume',action='store_true');p.add_argument('--verify',type=pathlib.Path);a=p.parse_args()
 if a.verify:r=verify(a.verify)
 else:
  p.error('--config and --out required') if not a.config or not a.out else None;r=collect(read_json(a.config),a.out,a.resume)
 print(json.dumps(r,indent=2));raise SystemExit(0 if r.get('native_document_complete') else 2)
