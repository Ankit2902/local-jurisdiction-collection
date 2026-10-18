"""Retained whole-native Boston differential; zero acquisition/image decoding."""
import copy,hashlib,importlib.util,json,pathlib,re,socket,sys,time
from unittest.mock import patch
from PIL import Image
OUT=pathlib.Path(__file__).resolve().parent;ROOT=OUT.parents[3];W=json.loads((OUT/'source-witness.json').read_text());RUN=ROOT/W['run_relative_to_project'];TARGET=OUT/'actual-boston-normalization';TARGET.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
base=load('baseline_model',OUT/'baseline-source/model.py');candidate=load('candidate_model',OUT/'candidate-source/model.py');sys.path.insert(0,str(OUT/'candidate-source'));import audit_native
req=json.loads((RUN/'requests.json').read_text());inv=json.loads((RUN/'inventory.json').read_text());raw=(RUN/W['source_receipt']['file']).read_bytes();assert sha(raw)==W['source_native_sha256'];text=raw.decode();identity=W['identity'];toc={n['document_id']:n for n in inv['nodes']};initial_files={name:sha((RUN/name).read_bytes()) for name in ['requests.json','inventory.json','run.json','export-checkpoint.json']};toc_sources={n['document_id']:{'url':req['start:toc:'+n['document_id']]['requested_url'],'sha256':req['start:toc:'+n['document_id']]['sha256']} for n in inv['nodes'] if n['has_children']}
# Independent original raw TOC closure, ID/path/parent based (DFS vs collector BFS).
overview_entry=req['overview-start'];overview=(RUN/overview_entry['file']).read_bytes();assert sha(overview)==overview_entry['sha256'];m=re.search(r'window\._redux_state\s*=\s*JSON\.parse\(("(?:[^"\\]|\\.)*")',overview.decode());codes=json.loads(json.loads(m.group(1)))['codes'];version=codes['selectedVersion'];code=next(c for c in version['toc'] if c['slug']==identity['code_slug']);assert version['uuid']==identity['version_uuid'] and code['uuid']==identity['code_uuid'] and codes['currClient']['slug']==identity['client_slug'];nodes=[];branches=[]
def visit(n,parent=None,path=()):
 item={'document_id':n['doc_id'],'internal_id':n['id'],'heading':n['title'],'parent_id':parent,'path':[*path,n['title']],'has_children':bool(n.get('has_children')),'orig_doc_id':n.get('orig_doc_id') or n['doc_id'],'orig_doc_idx':n.get('orig_doc_idx') or 0,'passthru_doc_id':n.get('passthru_doc_id'),'type':n.get('type','section')};nodes.append(item)
 if item['has_children']:
  e=req['start:toc:'+str(n['doc_id'])];b=(RUN/e['file']).read_bytes();assert sha(b)==e['sha256'];body=json.loads(b);assert body['doc_id']==n['doc_id'] and body['id']==n['id'] and body['code_uuid']==identity['code_uuid'];branches.append(n['doc_id'])
  for child in body['children']:assert child.get('parent_doc_id') in (None,n['doc_id']);visit(child,n['doc_id'],item['path'])
for n in code['sections']:visit(n)
assert {n['document_id']:n for n in nodes}==toc and len(nodes)==len(toc);assert len(branches)==len(set(branches)) and set(branches)==set(inv['expanded'])
# A diagnostic projection removes ONLY this exactly located original Notes heading
# and typed source note table. It is not a final normalized corpus or acquisition.
notes='<p>Notes</p>';table='<table class="footnote">';assert text.count(notes)==text.count(table)==1;a=text.index(notes);b=text.index('</table>',text.index(table,a))+len('</table>');removed=text[a:b];assert removed.startswith(notes+table);projection=(text[:a]+text[b:]).encode();projection_sha=sha(projection);(OUT/'projection-witness.json').write_text(json.dumps({'kind':'Diagnostic source projection only','original_native_sha256':sha(raw),'projection_sha256':projection_sha,'removed_char_range':[a,b],'removed_fragment_sha256':sha(removed.encode()),'removed_fragment_bytes':len(removed.encode()),'removed_elements':['p Notes','table.footnote'],'original_source_unchanged':True},indent=2)+'\n')
with patch.object(socket,'socket',side_effect=AssertionError('Network forbidden')) as network,patch.object(Image,'open',side_effect=AssertionError('Image decoder forbidden')) as decoder:
 try:base.native_records(raw,inv,identity,W['source_receipt']['requested_url'],sha(raw),inventory_sources=toc_sources)
 except AssertionError as e:baseline_failure=str(e);assert 'Footnote marker/backlink binding absent' in baseline_failure
 else:raise AssertionError('Expected exact old-profile source-key/printed-label failure absent')
 print('Baseline full native rejected source anchor/printed-label mismatch:',baseline_failure,flush=True)
 records=candidate.native_records(raw,inv,identity,W['source_receipt']['requested_url'],sha(raw),inventory_sources=toc_sources);print('Candidate full native parsed',len(records),flush=True)
 baseline=base.native_records(projection,inv,identity,W['source_receipt']['requested_url'],projection_sha,inventory_sources=toc_sources);print('Diagnostic baseline projection parsed',len(baseline),flush=True)
 changes=[]
 for old,new in zip(baseline,records):
  assert old['document_id']==new['document_id'];old=copy.deepcopy(old);new=copy.deepcopy(new);old.pop('source_sha256');new.pop('source_sha256');fields=[k for k in sorted(set(old)|set(new)) if old.get(k)!=new.get(k)]
  if fields:changes.append({'document_id':new['document_id'],'changed_fields':fields})
 assert len(changes)==1 and changes[0]['document_id']=='0-0-0-475',changes
 record=next(r for r in records if r['document_id']=='0-0-0-475');assert len(record['native_auxiliary_fragments'])==2
 expected=[{'printed_label':str(n+5),'source_anchor_key':str(n),'note_anchor':'foot--'+str(n),'inline_anchor':'text--'+str(n)} for n in [1,2,3]]
 for aux in record['native_auxiliary_fragments']:assert aux['marker_labels']==['6','7','8'] and aux['marker_anchor_bindings']==expected
 assert record['text'].count('Plan A, as noted in the ballot question')==1 and record['text'].count('Plan D, as noted in the ballot question')==1 and record['text'].count('Plan E, as noted in the ballot question')==1
 data=candidate.output_bytes(records,[])
 for name,content in data.items():
  if name!='pdf-pages.jsonl':(TARGET/name).write_bytes(content)
 print('Output saved; independent original raw-DOM table audit starting',flush=True);table_audit=audit_native.audit(raw,records);assert table_audit['passed'],table_audit
 (OUT/'original-native-table-audit.json').write_text(json.dumps(table_audit,indent=2)+'\n')
 assets=[{'owner_id':r['document_id'],**a} for r in records for a in r['assets'] if a['disposition']=='required-asset'];(OUT/'required-nonimage-references.json').write_text(json.dumps(assets,indent=2,ensure_ascii=False)+'\n')
 assert initial_files=={name:sha((RUN/name).read_bytes()) for name in initial_files} and sha((RUN/W['source_receipt']['file']).read_bytes())==sha(raw)
 result={'passed':True,'scope':'Whole retained native HTML parse+independent raw TOC inventory, original raw-DOM tables and narrow source-projection differential. No closing source refresh/attachment/PDF qualification.','source_native_sha256':sha(raw),'source_native_bytes':len(raw),'publication_identity':identity,'baseline_model_sha256':sha((OUT/'baseline-source/model.py').read_bytes()),'candidate_model_sha256':sha((OUT/'candidate-source/model.py').read_bytes()),'baseline_full_native_failure':baseline_failure,'independent_raw_TOC_nodes':len(nodes),'independent_raw_TOC_branches':len(branches),'normalized_records':len(records),'rich_blocks_owned_once':sum(len(r['body_block_ids']) for r in records),'unique_source_owned_blocks':len({x for r in records for x in r['body_block_ids']}),'passthrough_containers':sum(r['kind']=='publisher-toc-passthrough-container' for r in records),'auxiliary_fragments':sum(len(r.get('native_auxiliary_fragments',[])) for r in records),'full_native_projection_changes':changes,'all_other_records_equal_except_explicit_projection_source_hash':True,'note_marker_anchor_bindings':expected,'note_bodies_occurrence_count_each':1,'original_raw_table_audit':table_audit,'original_raw_table_audit_sha256':sha((OUT/'original-native-table-audit.json').read_bytes()),'required_nonimage_URL_count':len({a['url'] for a in assets}),'unqualified_HTML_units':[r['document_id'] for r in records if r['content_classification']=='unqualified-heading-only'],'output_SHA256':{name:sha((TARGET/name).read_bytes()) for name in ['sections.jsonl','sections.csv']},'original_inputs_unchanged':True,'socket_calls':network.call_count,'Image_open_calls':decoder.call_count,'publication_complete':False,'new_acquisition':False,'source_end_inventory_refreshed':False,'script_sha256':sha(pathlib.Path(__file__).read_bytes())};(TARGET/'receipt.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(json.dumps({k:result[k] for k in ['passed','normalized_records','rich_blocks_owned_once','auxiliary_fragments','required_nonimage_URL_count','unqualified_HTML_units','publication_complete']},indent=2))
