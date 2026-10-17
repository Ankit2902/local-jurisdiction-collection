#!/usr/bin/env python3
"""Independent read-only reconciliation from raw TOC/body/asset evidence, not coverage.json flags."""
import argparse,json,pathlib
from .model import inventory,decode,parse_document,outputs
from .util import digest,hash_json,read_json,validate_file

def verify(out):
 out=pathlib.Path(out);s=read_json(out/'checkpoint.json');errors=[]
 def require(test,reason):
  if not test:errors.append(reason)
 def raw(e):
  p=validate_file(out,e['path'],e['sha256']);m=read_json(p.with_name(p.name+'.receipt.json'));assert m['url']==e['url'] and m['http_status']==200 and m['sha256']==e['sha256'] and not m.get('challenge'),'Receipt identity/status/hash mismatch';return decode(p.read_bytes(),m['headers'])
 try:
  from .collect import TARGETS,code_hashes
  require(s['config']==TARGETS[s['target']] and s['config_sha256']==hash_json(s['config']),'Wrong publication config/edition binding')
  require(s['code_hashes']==code_hashes(),'Collector code version mismatch')
  for name,h in s['code_hashes'].items():validate_file(out,'script-versions/'+h+pathlib.Path(name).suffix,h)
  inv=inventory(raw(s['inventory_raw']),s['config']);require(inv['sha256']==s['inventory_sha256'],'Checkpoint inventory hash mismatch');known={n['id']:n for n in inv['nodes']};records={};duplicate_dispositions=[];requested=[]
  for block in s['blocks']:
   require(block['requested'] not in requested,'Duplicate acquisition block '+block['requested']);requested.append(block['requested']);parsed=parse_document(raw(block),block['requested'],s['config'],known);require([r['id'] for r in parsed]==block['record_ids'],'Checkpoint body ID list mismatch')
   for r in parsed:
    r['raw_path']=block['path'];r['raw_sha256']=block['sha256']
    if r['id'] in records:
     require(records[r['id']]['body_sha256']==r['body_sha256'] and records[r['id']]['path']==r['path'],'Conflicting repeated node '+r['id']);duplicate_dispositions.append({'id':r['id'],'disposition':'identical source body suppressed'});continue
    records[r['id']]=r
  missing=sorted(set(known)-records.keys());embedded=sorted(records.keys()-set(known));require(not missing,'Missing TOC node IDs')
  for r in records.values():
   if r['parent_id']:require(r['parent_id'] in records or any(x.get('id')==r['parent_id'] for x in r['path']),'Unknown parent ownership '+r['id'])
   require(not __import__('bs4').BeautifulSoup(r['body_html'],'html.parser').select('section[data-secid] section[data-secid]'),'Descendant body leaked into owned section '+r['id'])
  # Compare actual delivered rows independently; duplicate/missing CSV/JSONL and edited bodies cannot pass.
  delivered=[json.loads(l) for l in (out/'records.jsonl').read_text().splitlines() if l.strip()];require(len(delivered)==len({r['id'] for r in delivered}),'Duplicate normalized output IDs');require(set(r['id'] for r in delivered)==set(records),'Missing/extra normalized output IDs')
  for name,data in outputs(list(records.values())).items():require((out/name).read_bytes()==data,'Normalized output content differs from raw replay: '+name)
  required={a['url'] for r in records.values() for a in r['assets'] if a['required']};missing_assets=sorted(required-set(s['assets']));extra_assets=sorted(set(s['assets'])-required)
  require(not extra_assets,'Unrelated asset checkpoint entries')
  for url,a in s['assets'].items():
   validate_file(out,a['path'],a['sha256']);require(a['url']==url,'Asset URL binding mismatch')
   if a['kind']=='linked-binary':
    m=read_json(out/(a['path']+'.receipt.json'));require(m['url']==url and m['http_status']==200 and m['sha256']==a['sha256'],'Asset receipt mismatch')
  end_ok=False
  if s.get('end_inventory'):
   endinv=inventory(raw(s['end_inventory']),s['config']);require(endinv['sha256']==inv['sha256']==s['end_inventory_sha256'],'End inventory/edition drift');end={e['requested']:e for e in s['end_blocks']};require(len(end)==len(s['end_blocks']),'Duplicate end-check block')
   for block in s['blocks']:
    require(block['requested'] in end,'Missing end body check '+block['requested'])
    if block['requested'] in end:require(hash_json(parse_document(raw(end[block['requested']]),block['requested'],s['config'],known))==hash_json(parse_document(raw(block),block['requested'],s['config'],known)),'End content/edition drift '+block['requested'])
   end_ok=len(end)==len(s['blocks']) and endinv['sha256']==inv['sha256']
  require(end_ok,'Start/end source consistency not established');require(s['phase']=='finished','Interrupted/failed traversal');require(s['options']['max_items'] is None,'Explicit max-items forces incomplete');text_complete=not errors
  assets_complete=not missing_assets and not s['options']['skip_assets'] and text_complete
  native=s.get('native_export')
  if native:
   validate_file(out,native['path'],native['sha256']);require((out/native['path']).read_bytes().startswith(b'%PDF-'),'Native bytes not PDF')
  return {'schema_version':1,'status':'complete_publication' if text_complete and assets_complete else 'incomplete','target':s['target'],'publication_identity':s['config']['identity'],'publication_scope':s['config']['scope'],'inventory_sha256':inv['sha256'],'edition_pin':{'kind':'observed snapshot','inventory_sha256':inv['sha256'],'block_hashes':[b['sha256'] for b in s['blocks']],'publisher_edition_id':None},'inventory_nodes':len(known),'body_nodes':len(records),'embedded_body_nodes':len(embedded),'acquisition_blocks':len(s['blocks']),'missing_ids':missing,'embedded_ids':embedded,'duplicate_output_ids':len(delivered)-len({r['id'] for r in delivered}),'duplicate_source_dispositions':duplicate_dispositions,'structural_containers':sum(r['kind']=='structural_container' for r in records.values()),'owned_body_count':sum(r['kind']!='structural_container' for r in records.values()),'table_count':sum(len(r['tables']) for r in records.values()),'image_only_nodes':[r['id'] for r in records.values() if r['image_only']],'asset_references':len(required),'assets_acquired':len(s['assets']),'missing_assets':missing_assets,'asset_failures':s.get('asset_failures',{}),'toc_body_heading_differences':[{'id':r['id'],'toc_heading':r['toc_heading'],'body_heading':r['heading'],'disposition':'Stable source ID matches; canonical body heading retained'} for r in records.values() if r['toc_heading_matches'] is False],'start_end_consistent':end_ok and not any('drift' in e for e in errors),'publication_text_complete':text_complete,'attachments_complete':assets_complete,'edition_complete':False,'jurisdiction_complete':False,'native_export':native,'errors':errors,'limits':['Publisher global edition ID unavailable; observed TOC and every acquired body block checked at start/end, no claim of official codewide legal currency','Assets verified as retained binaries; graphic text, model-code content and linked separate publications are not transcribed into legal records','Jurisdiction completeness requires separately published families outside this publication']}
 except Exception as exc:
  return {'status':'incomplete','publication_text_complete':False,'attachments_complete':False,'edition_complete':False,'jurisdiction_complete':False,'errors':errors+[type(exc).__name__+': '+str(exc)]}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('out',type=pathlib.Path);a=p.parse_args();r=verify(a.out);print(json.dumps(r,indent=2));raise SystemExit(0 if r['publication_text_complete'] and r['attachments_complete'] else 2)
