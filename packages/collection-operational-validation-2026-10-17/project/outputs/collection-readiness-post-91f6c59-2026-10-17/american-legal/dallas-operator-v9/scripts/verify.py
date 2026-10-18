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
 f=Files(path);meta=f.json('run.json');requests=f.json('requests.json');assert meta.get('image_policy')==IMAGE_POLICY,'Superseded image policy; use retained executed verifier for old proof'
 assert meta['status']=='acquired','Run interrupted/failed; not a complete terminal acquisition'
 assets=f.json('assets.json');ledger={a['url']:a for a in assets};resolved_images={a['url'] for a in assets if a['status']=='image-placeholder'}
 for key,e in requests.items():
  assert digest(f.read(e['file']))==e['sha256'],'Corrupt retained raw: '+key
  if e['op']=='binary':assert not image_url(e['requested_url']) and not e['response']['headers'].get('content-type','').startswith('image/'),'Image bytes acquired under forbidden policy'
  for name in ['rendered','scope_html','ready_html']:
   if name+'_sha256' in e['response']:assert digest(f.read(e['response'][name+'_file']))==e['response'][name+'_sha256'],'Corrupt browser evidence'
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
 records=[];pages=[];pdf_owners={};required=set();block_owners={};inventory_ids={n['document_id'] for n in inventory['nodes']};toc_sources={n['document_id']:{'url':requests['start:toc:'+n['document_id']]['requested_url'],'sha256':requests['start:toc:'+n['document_id']]['sha256']} for n in inventory['nodes'] if n['has_children']}
 if meta['strategy']=='native':
  raw,e=read('native-export');payload=e['response']['payload'];job=e['response']['job'];assert payload['version']==identity['version_uuid']==job['version'] and json.loads(payload['scope'])==[{'code_slug':identity['code_slug']}] and payload['output_format']=='html' and payload['for_print'] is False and job['for_print'] is False,'Wrong native publication scope/edition/format';assert e['response']['url']=='https://export.amlegal.com/api/export-requests/'+job['uuid']+'/download/','Native URL/job mismatch';records=native_records(raw,inventory,identity,e['requested_url'],e['sha256'],resolved_images,inventory_sources=toc_sources);required.update(a['url'] for r in records for a in r['assets'] if a['disposition'] in ['required-asset','image-placeholder'])
  try:export_checkpoint=f.json('export-checkpoint.json')
  except (FileNotFoundError,KeyError):export_checkpoint=None
  if export_checkpoint:
   assert export_checkpoint['requested_url']==e['requested_url'] and export_checkpoint['code_uuid']==identity['code_uuid'] and export_checkpoint['code_slug']==identity['code_slug'] and export_checkpoint['version']==identity['version_uuid'],'Export checkpoint publication identity drift'
   assert export_checkpoint['payload']==payload and export_checkpoint['job']==job and export_checkpoint['status']=='downloaded' and export_checkpoint['native_sha256']==e['sha256'],'Export job checkpoint scope/job/bytes drift'
   assert export_checkpoint['scope_html'].encode()==f.read(e['response']['scope_html_file']),'Export checkpoint scope UI source differs'
  for record in records:
   for block in record['body_block_ids']:
    assert block not in block_owners,'Duplicate native owner';block_owners[block]=record['document_id']
 for item in ([] if meta['strategy']=='native' else inventory['nodes']):
  did=item['document_id'];root=f"https://codelibrary.amlegal.com/codes/{identity['client_slug']}/{identity['version_uuid']}/{identity['code_slug']}/{quote(did,safe='')}"
  if item.get('passthru_doc_id'):
   records.append(passthrough_record(item,inventory,identity,toc_sources[did]));continue
  if identity['is_pdf']:
   url=f"https://codelibrary.amlegal.com/api/sec-info/{identity['client_slug']}/{identity['version_uuid']}/{identity['code_slug']}/{quote(did,safe='')}/";raw,e=read('fetch:'+url,url);info=json.loads(raw);assert info['doc_id']==did and info['version_uuid']==identity['version_uuid'] and info['code_uuid']==identity['code_uuid'],'Wrong PDF edition/owner';pdf=info.get('pdf_path')
   if pdf:
    data,pe=read('binary:'+pdf,pdf);required.add(pdf);asset=ledger[pdf];assert asset['file']==pe['file'] and asset['sha256']==pe['sha256'] and asset['validation']==validate_asset(pdf,data,pe['response']['headers'].get('content-type'))
    if pe['sha256'] in pdf_owners:page_ids=[];alias=pdf_owners[pe['sha256']]
    else:
     pp=pdf_pages(data,did,pdf);pages+=pp;page_ids=[x['document_id'] for x in pp];pdf_owners[pe['sha256']]=did;alias=None
    records.append({'document_id':did,'heading':item['heading'],'path':item['path'],'parent_id':item['parent_id'],'kind':'native-pdf','text':'','html':None,'body_block_ids':[],'tables':[],'links':[],'assets':[{'url':pdf,'kind':'native-publication-pdf','disposition':'required-asset'}],'source_url':url,'source_sha256':e['sha256'],'publication_identity':identity,'pdf_asset':asset,'pdf_page_ids':page_ids,'alias_of':alias});continue
  url=f"https://codelibrary.amlegal.com/api/render-section/{identity['client_slug']}/{identity['version_uuid']}/{identity['code_slug']}/{quote(item['orig_doc_id'],safe='')}/{item['orig_doc_idx']}/";raw,e=read('fetch:'+url,url);record=html_record(json.loads(raw),item,identity,root,e['sha256'],resolved_images);records.append(record)
  for block in record['body_block_ids']:
   assert block not in block_owners,'Duplicate body block owner '+block
   assert block not in inventory_ids or block==did,'Descendant content leaked into parent '+block
   block_owners[block]=did
  required.update(a['url'] for a in record['assets'] if a['disposition'] in ['required-asset','image-placeholder'])
 assert len(records)==len({r['document_id'] for r in records}),'Duplicate output identities'
 for url,expected in normalize_pdf_assets(ledger,pages,lambda a:f.read(a['file'])).items():
  assert all(ledger[url].get(k)==v for k,v in expected.items()),'PDF asset normalization/alias metadata drift'
 unresolved_internal=bind_reference_graph(records,inventory)
 for name,data in output_bytes(records,pages).items():assert f.read(name)==data,'Normalized output missing/duplicated/drifted: '+name
 checkpoint=f.json('checkpoint.json');assert checkpoint['inventory_sha256']==meta['inventory_sha256'] and checkpoint['acquired_ids']==[r['document_id'] for r in records],'Interrupted or mismatched checkpoint'
 assets=f.json('assets.json');assert len(assets)==len({a['url'] for a in assets}),'Duplicate asset ledger'
 ledger={a['url']:a for a in assets};pending=list(required);checked=set()
 while pending:
  u=pending.pop(0)
  if u in checked:continue
  checked.add(u);assert u in ledger,'Required asset omitted from ledger: '+u;a=ledger[u]
  if a['status']=='image-placeholder':
   assert a.get('policy')==IMAGE_POLICY and a.get('placeholder')=='[IMAGE]' and not a['required'] and 'file' not in a and 'binary:'+u not in requests,'Invalid image placeholder/no-fetch disposition'
  elif a['status'].startswith('retained'):
   if 'head_unsupported_status' in a:assert requests['head:'+u]['response']['status']==a['head_unsupported_status'] and a['head_unsupported_status'] in [405,501],'HEAD fallback receipt drift'
   assert digest(f.read(a['file']))==a['sha256'],'Asset corruption';assert a['sha256']==requests['binary:'+u]['sha256'],'Asset response binding differs';validation=validate_asset(u,f.read(a['file']),a.get('content_type'));assert validation==a['validation'] and (a['status']=='retained')==validation['qualified'],'Asset qualification drift'
   if 'text/css' in (a.get('content_type') or '') or re.search(r'\.css(?:[?#]|$)',u,re.I):
    for raw in re.findall(r'url\([\s\'"]*([^\)\'\"]+)',f.read(a['file']).decode('utf-8',errors='replace')):
     if not raw.startswith('data:'):pending.append(urljoin(u,raw))
  elif a['status']=='unavailable':
   candidates=[e for e in requests.values() if e['requested_url']==u and e['op'] in ['head','binary'] and e['response']['status']==a['http_status']]
   assert any(e['file']==a['response_file'] and e['sha256']==a['response_sha256'] for e in candidates),'Unavailable asset source receipt mismatch'
   assert a['http_status']>=400 and a['http_status'] not in [403,429],'Access stop cannot be an asset exclusion'
  else:assert a.get('reason'),'Unknown asset exclusion'
 assert checked==set(ledger),'Unjustified extra/unknown asset ledger entries'
 expected={n['document_id'] for n in inventory['nodes']};actual={r['document_id'] for r in records};missing=sorted(expected-actual);extra=sorted(actual-expected);edition=identity==endidentity and inventory==endinventory;unresolved=[a['url'] for a in assets if a['status'] not in ['retained','image-placeholder']];html_only=all(r['kind'] in ['html-renderer-owned-range','publisher-native-html-owned-range','publisher-toc-passthrough-container'] for r in records);complete_inventory=inventory['complete'] and endinventory['complete'] and meta['max_items'] is None
 unqualified=[r['document_id'] for r in records if r.get('content_classification') in ['image-only','unqualified-heading-only']]
 pdf_text_qualified=bool(pages) and all(p.get('source_qualification',{}).get('source_text_qualified',False) for p in pages)
 pdf_tables_qualified=bool(pages) and all(p.get('source_qualification',{}).get('source_tables_qualified',False) for p in pages)
 pdf_order_qualified=bool(pages) and all(p.get('source_qualification',{}).get('source_reading_order_qualified',False) for p in pages)
 pdf_book=identity['is_pdf'] and all(r['kind']=='native-pdf' and (r['pdf_page_ids'] or r.get('alias_of')) for r in records)
 text_complete=not unqualified and complete_inventory and not missing and not extra and edition and (html_only or (pdf_book and pdf_text_qualified and pdf_order_qualified))
 report={'schema_version':1,'publication_identity':identity,'inventory_count':len(expected),'acquired_count':len(records),'unique_id_count':len(actual),'missing_ids':missing,'extra_ids':extra,'duplicate_ids':[],'owned_source_block_count':len(block_owners),'publisher_passthrough_container_count':sum(r['kind']=='publisher-toc-passthrough-container' for r in records),'independently_recomputed_branch_count':len(inventory['expanded']),'inventory_complete':complete_inventory,'pending_inventory_ids':inventory['pending'],'source_consistent_at_end':edition,'edition_complete':edition and complete_inventory,'publication_text_complete':text_complete,'unqualified_text_ids':unqualified,'image_policy':IMAGE_POLICY,'image_reference_placeholder_count':sum(a['status']=='image-placeholder' for a in assets),'image_marker_count':sum(len(r.get('image_placeholders',[])) for r in records)+sum(p.get('image_placeholder_count',p.get('image_xobject_count',0)) for p in pages),'image_binary_download_count':0,'required_asset_count':sum(a['required'] for a in assets),'retained_asset_count':sum(a['status']=='retained' for a in assets),'unresolved_required_assets':unresolved,'attachment_complete':complete_inventory and not unresolved,'native_bulk_html_file_complete':complete_inventory and meta['strategy']=='native' and edition,'native_publication_files_complete':complete_inventory and identity['is_pdf'] and bool(pages) and not unresolved and edition,'pdf_text_layer_pages_parsed':len(pages),'pdf_text_layer_pages_with_text':sum(bool(p['text'].strip()) for p in pages),'pdf_image_xobject_count':sum(p['image_xobject_count'] or 0 for p in pages),'pdf_image_xobject_count_complete':all(p['image_xobject_count'] is not None for p in pages),'pdf_Figure_placeholder_count':sum(p.get('tagged_document',{}).get('qualification',{}).get('source_figure_placeholders',0) for p in pages),'pdf_available_Figure_text_characters':sum(p.get('tagged_document',{}).get('qualification',{}).get('available_figure_text_characters',0) for p in pages),'pdf_text_layer_extraction_complete':bool(pages) and complete_inventory and not unresolved,'pdf_normalized_distinct_document_count':len({p['owner_id'] for p in pages}),'pdf_retained_asset_document_count':sum(a.get('validation',{}).get('kind')=='pdf' and a['status']=='retained' for a in assets),'pdf_semantic_text_completeness_qualified':pdf_text_qualified and pdf_order_qualified,'pdf_legal_provision_segmentation_qualified':False,'pdf_source_qualified_page_count':sum(p.get('source_qualification',{}).get('source_text_qualified',False) for p in pages),'pdf_policy_excluded_no_text_glyph_pages':[p['document_id'] for p in pages if p.get('source_qualification',{}).get('policy_not_applicable_to_text_glyph_fidelity',False)],'pdf_tagged_source_table_count':sum(len(p.get('tagged_document',{}).get('tables',[])) for p in pages),'pdf_tagged_source_cell_count':sum(len(row) for p in pages for t in p.get('tagged_document',{}).get('tables',[]) for row in t['rows']),'pdf_positioned_page_count':sum('layout' in p for p in pages),'pdf_pages_with_agreeing_text_engines':sum(p.get('layout',{}).get('independent_text_characters_equal',False) for p in pages),'pdf_pages_with_qualified_reading_order':sum((p.get('source_qualification',{}).get('source_reading_order_qualified',False) or p.get('layout',{}).get('reading_order_qualified',False)) for p in pages),'pdf_unqualified_reading_order_pages':[p['document_id'] for p in pages if not (p.get('source_qualification',{}).get('source_reading_order_qualified',False) or p.get('layout',{}).get('reading_order_qualified',False))],'pdf_table_candidate_count':sum(len(p.get('layout',{}).get('table_candidates',[])) for p in pages),'pdf_qualified_ruled_table_count':sum(t['qualification']=='ruled-grid-geometry' for p in pages for t in p.get('layout',{}).get('table_candidates',[])),'pdf_table_completeness_qualified':pdf_tables_qualified,'table_count':sum(len(r['tables']) for r in records),'table_cell_count':sum(len(row) for r in records for t in r['tables'] for row in t),'internal_reference_complete':not unresolved_internal,'unresolved_internal_references':unresolved_internal,'publication_complete':text_complete and not unresolved and not unresolved_internal,'jurisdiction_complete':False,'limit':meta['max_items'],'record_unit':'publisher TOC node; PDF pages are separate additional records','limitations':['Independent inventory is recomputed recursively from retained publisher TOC responses, including middle branches.','Images intentionally become [IMAGE] under user policy; this is not a completeness gap. Tagged PDF source order, roles and spans are qualified separately from inferred legal provision segmentation; untagged geometry remains unqualified unless a source-wide profile proves it.','Attachment completeness covers required media/document references discovered in the retained content, not arbitrary external navigation destinations.','One publication never qualifies all independently published jurisdiction families.']}
 if compare_report:assert f.json('coverage.json')==report,'Stored coverage differs from recomputation'
 return report

def main():
 p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('--offline',action='store_true');p.add_argument('--allow-incomplete',action='store_true');a=p.parse_args()
 try:r=verify(a.run);print(json.dumps(r,indent=2));sys.exit(0 if r['publication_complete'] or a.allow_incomplete else 2)
 except Exception as exc:print(json.dumps({'verified':False,'error':str(exc)}));sys.exit(1)
if __name__=='__main__':
 from urllib.parse import quote
 main()
