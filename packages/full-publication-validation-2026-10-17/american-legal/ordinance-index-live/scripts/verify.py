#!/usr/bin/env python3
"""Read-only recomputing verifier. A run directory or compressed fixture ZIP; no extraction/network."""
import argparse,json,sys,zipfile
sys.dont_write_bytecode=True
from pathlib import Path
from urllib.parse import quote
from model import *
class Files:
 def __init__(self,path):
  self.path=Path(path);self.zip=zipfile.ZipFile(self.path) if self.path.is_file() else None
 def read(self,name):
  assert not name.startswith('/') and '..' not in Path(name).parts,'Unsafe retained path'
  return self.zip.read(name) if self.zip else (self.path/name).read_bytes()
 def json(self,name):return json.loads(self.read(name))

def verify(path,compare_report=True):
 f=Files(path);meta=f.json('run.json');requests=f.json('requests.json');assert meta['status']=='acquired','Run interrupted/failed; not a complete terminal acquisition'
 for key,e in requests.items():assert digest(f.read(e['file']))==e['sha256'],'Corrupt retained raw: '+key
 def read(key,url=None):
  e=requests[key];assert e['response']['status']==200,'Non200 source'
  if url:assert e['requested_url']==url,'Source request identity mismatch'
  return f.read(e['file']),e
 start,se=read('overview-start',meta['overview_url']);identity,code,publications=select(start,meta['source_url'],meta['expected_jurisdiction'],meta['expected_state'],meta.get('publication_selector'),meta.get('identity_aliases',[]));assert meta['identity']==identity,'Wrong pinned edition identity';assert meta['publication_inventory']==publications,'Publication inventory differs from source'
 for key in requests:
  if key.startswith('resume-overview:'):
   data,e=read(key,meta['overview_url']);current,_,_=select(data,meta['source_url'],meta['expected_jurisdiction'],meta['expected_state'],meta.get('publication_selector'),meta.get('identity_aliases',[]));assert current==identity,'Wrong-edition resumed source'
 def inv(c,ident,phase):
  nodes=[];seen=set();expanded=[];queue=[(n,None,[]) for n in c['sections']]
  while queue and (meta['max_items'] is None or len(nodes)<meta['max_items']):
   raw,parent,path=queue.pop(0);n=node(raw,parent,path);assert n['document_id'] not in seen,'Duplicate independent inventory ID';seen.add(n['document_id']);nodes.append(n)
   if n['has_children']:
    url='https://codelibrary.amlegal.com/api/section-toc/'+str(n['internal_id'])+'/'
    b,e=read(phase+':toc:'+n['document_id'],url);data=json.loads(b);assert data['doc_id']==n['document_id'] and data['id']==n['internal_id'] and data['code_uuid']==ident['code_uuid'],'Wrong branch identity';assert isinstance(data.get('children'),list),'Missing independent branch children';expanded.append(n['document_id'])
    for child in data['children']:
     assert child.get('parent_doc_id') in [None,n['document_id']],'Wrong branch parent';queue.append((child,n['document_id'],n['path']))
  return {'nodes':nodes,'expanded':expanded,'pending':[n[0]['doc_id'] for n in queue],'root_ids':[n['doc_id'] for n in c['sections']],'complete':not queue,'identity':ident}
 inventory=inv(code,identity,'start');assert inventory==f.json('inventory.json'),'Stored inventory does not match independent raw TOC';assert digest(canonical(inventory))==meta['inventory_sha256'],'Inventory checkpoint binding mismatch'
 end,ee=read('overview-end:'+str(meta['resume_count']),meta['overview_url']);endidentity,endcode,_=select(end,meta['source_url'],meta['expected_jurisdiction'],meta['expected_state'],meta.get('publication_selector'),meta.get('identity_aliases',[]));endinventory=inv(endcode,endidentity,'end:'+str(meta['resume_count']));assert endinventory==f.json('inventory-end.json');assert digest(canonical(endinventory))==meta['inventory_end_sha256'];assert meta['end_identity']==endidentity
 records=[];pages=[];pdf_owners={};required=set();block_owners={};inventory_ids={n['document_id'] for n in inventory['nodes']}
 for item in inventory['nodes']:
  did=item['document_id'];root=f"https://codelibrary.amlegal.com/codes/{identity['client_slug']}/{identity['version_uuid']}/{identity['code_slug']}/{quote(did,safe='')}"
  if identity['is_pdf']:
   url=f"https://codelibrary.amlegal.com/api/sec-info/{identity['client_slug']}/{identity['version_uuid']}/{identity['code_slug']}/{quote(did,safe='')}/";raw,e=read('fetch:'+url,url);info=json.loads(raw);assert info['doc_id']==did and info['version_uuid']==identity['version_uuid'] and info['code_uuid']==identity['code_uuid'],'Wrong PDF edition/owner';pdf=info.get('pdf_path')
   if pdf:
    data,pe=read('binary:'+pdf,pdf);required.add(pdf);asset={'url':pdf,'required':True,'status':'retained','file':pe['file'],'sha256':pe['sha256'],'bytes':pe['bytes'],'content_type':pe['response']['headers'].get('content-type')}
    if pe['sha256'] in pdf_owners:page_ids=[];alias=pdf_owners[pe['sha256']]
    else:
     pp=pdf_pages(data,did,pdf);pages+=pp;page_ids=[x['document_id'] for x in pp];pdf_owners[pe['sha256']]=did;alias=None
    records.append({'document_id':did,'heading':item['heading'],'path':item['path'],'parent_id':item['parent_id'],'kind':'native-pdf','text':'','html':None,'body_block_ids':[],'tables':[],'links':[],'assets':[{'url':pdf,'kind':'native-publication-pdf','disposition':'required-asset'}],'source_url':url,'source_sha256':e['sha256'],'publication_identity':identity,'pdf_asset':asset,'pdf_page_ids':page_ids,'alias_of':alias});continue
  url=f"https://codelibrary.amlegal.com/api/render-section/{identity['client_slug']}/{identity['version_uuid']}/{identity['code_slug']}/{quote(item['orig_doc_id'],safe='')}/{item['orig_doc_idx']}/";raw,e=read('fetch:'+url,url);record=html_record(json.loads(raw),item,identity,root,e['sha256']);records.append(record)
  for block in record['body_block_ids']:
   assert block not in block_owners,'Duplicate body block owner '+block
   assert block not in inventory_ids or block==did,'Descendant content leaked into parent '+block
   block_owners[block]=did
  required.update(a['url'] for a in record['assets'] if a['disposition']=='required-asset')
 assert len(records)==len({r['document_id'] for r in records}),'Duplicate output identities'
 for name,data in output_bytes(records,pages).items():assert f.read(name)==data,'Normalized output missing/duplicated/drifted: '+name
 checkpoint=f.json('checkpoint.json');assert checkpoint['inventory_sha256']==meta['inventory_sha256'] and checkpoint['acquired_ids']==[r['document_id'] for r in records],'Interrupted or mismatched checkpoint'
 assets=f.json('assets.json');assert len(assets)==len({a['url'] for a in assets}),'Duplicate asset ledger'
 ledger={a['url']:a for a in assets};pending=list(required);checked=set()
 while pending:
  u=pending.pop(0)
  if u in checked:continue
  checked.add(u);assert u in ledger,'Required asset omitted from ledger: '+u;a=ledger[u]
  if a['status']=='retained':
   assert digest(f.read(a['file']))==a['sha256'],'Asset corruption';assert a['sha256']==requests['binary:'+u]['sha256'],'Asset response binding differs'
   if 'text/css' in (a.get('content_type') or '') or re.search(r'\.css(?:[?#]|$)',u,re.I):
    for raw in re.findall(r'url\([\s\'"]*([^\)\'\"]+)',f.read(a['file']).decode('utf-8',errors='replace')):
     if not raw.startswith('data:'):pending.append(urljoin(u,raw))
  else:assert a.get('reason'),'Unknown asset exclusion'
 assert checked==set(ledger),'Unjustified extra/unknown asset ledger entries'
 expected={n['document_id'] for n in inventory['nodes']};actual={r['document_id'] for r in records};missing=sorted(expected-actual);extra=sorted(actual-expected);edition=identity==endidentity and inventory==endinventory;unresolved=[a['url'] for a in assets if a['status']!='retained'];html_only=all(r['kind']=='html-renderer-owned-range' for r in records);complete_inventory=inventory['complete'] and endinventory['complete'] and meta['max_items'] is None
 text_complete=complete_inventory and not missing and not extra and edition and html_only
 report={'schema_version':1,'publication_identity':identity,'inventory_count':len(expected),'acquired_count':len(records),'unique_id_count':len(actual),'missing_ids':missing,'extra_ids':extra,'duplicate_ids':[],'owned_source_block_count':len(block_owners),'independently_recomputed_branch_count':len(inventory['expanded']),'inventory_complete':complete_inventory,'pending_inventory_ids':inventory['pending'],'source_consistent_at_end':edition,'edition_complete':edition and complete_inventory,'publication_text_complete':text_complete,'required_asset_count':len(assets),'retained_asset_count':sum(a['status']=='retained' for a in assets),'unresolved_required_assets':unresolved,'attachment_complete':complete_inventory and not unresolved,'native_publication_files_complete':complete_inventory and identity['is_pdf'] and bool(pages) and not unresolved and edition,'pdf_text_layer_pages_parsed':len(pages),'pdf_text_layer_pages_with_text':sum(bool(p['text'].strip()) for p in pages),'pdf_image_xobject_count':sum(p['image_xobject_count'] for p in pages),'pdf_text_layer_extraction_complete':bool(pages) and complete_inventory,'pdf_semantic_text_completeness_qualified':False,'table_count':sum(len(r['tables']) for r in records),'table_cell_count':sum(len(row) for r in records for t in r['tables'] for row in t),'publication_complete':text_complete and not unresolved,'jurisdiction_complete':False,'limit':meta['max_items'],'record_unit':'publisher TOC node; PDF pages are separate additional records','limitations':['Independent inventory is recomputed recursively from retained publisher TOC responses, including middle branches.','PDF searchable layer extraction and retained native bytes do not qualify semantic/OCR text completeness.','Attachment completeness covers required media/document references discovered in the retained content, not arbitrary external navigation destinations.','One publication never qualifies all independently published jurisdiction families.']}
 if compare_report:assert f.json('coverage.json')==report,'Stored coverage differs from recomputation'
 return report

def main():
 p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('--offline',action='store_true');p.add_argument('--allow-incomplete',action='store_true');a=p.parse_args()
 try:r=verify(a.run);print(json.dumps(r,indent=2));sys.exit(0 if r['publication_complete'] or a.allow_incomplete else 2)
 except Exception as exc:print(json.dumps({'verified':False,'error':str(exc)}));sys.exit(1)
if __name__=='__main__':
 from urllib.parse import quote
 main()
