"""Read-only Notes exposure/differential over actual captured full-run API sources."""
import sys
sys.dont_write_bytecode=True
import json,hashlib,re,socket,importlib.util
from pathlib import Path
from notes import sanitize_notes
base=Path(__file__).resolve().parent;project=base.parents[3]
def deny(*a,**k):raise AssertionError('No network in actual-source audit')
socket.socket.connect=deny;socket.create_connection=deny
sha=lambda raw:hashlib.sha256(raw).hexdigest()
canon=lambda v:json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
spec=importlib.util.spec_from_file_location('baseline_notes',base/'baseline/notes.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
paths=[]
for relative in ['outputs/collection-readiness-2026-10-17/municode','outputs/full-publication-validation-2026-10-17/municode']:
 paths.extend(sorted((project/relative).rglob('checkpoint.json')))
reports=[];source_manifest={};totals={'checkpoints':0,'content_units':0,'documents':0,'documents_with_nonempty_notes':0,'note_strings':0,'note_strings_with_data_image':0,'normalized_note_differences':0,'candidate_boundary_gaps':0}
for path in paths:
 cp=json.loads(path.read_text())
 if not isinstance(cp.get('publications'),dict):continue
 if 'synthetic' in str(cp.get('evidence_kind','')).lower() or '/zz/fixture/' in str(cp.get('source_url','')):continue
 folder=path.parent;source_manifest[str(path.relative_to(project))]=sha(path.read_bytes());report={'source':str(folder.relative_to(project)),'checkpoint_sha256':sha(path.read_bytes()),'expected_identity':cp.get('expected_identity'),'publications':[]};totals['checkpoints']+=1
 for pid,pub in cp['publications'].items():
  item={'product_id':pid,'job_id':pub.get('job_id'),'content_units':0,'documents':0,'nonempty_notes':0,'strings':0,'strings_with_data_image':0,'changed_documents':[],'boundary_gap_documents':[]}
  for name in pub.get('content_units',[]):
   unit=cp['units'][name];receipt_path=folder/unit['receipt'];receipt=json.loads(receipt_path.read_text());body_path=folder/receipt['body_file'];raw=body_path.read_bytes()
   assert sha(raw)==unit['sha256']==receipt['sha256'];assert receipt['status']==200 and not receipt.get('access_stop')
   source_manifest[str(receipt_path.relative_to(project))]=sha(receipt_path.read_bytes());source_manifest[str(body_path.relative_to(project))]=sha(raw)
   data=json.loads(raw);docs=data if isinstance(data,list) else data.get('Docs',[]);item['content_units']+=1
   for doc in docs:
    item['documents']+=1;notes=doc.get('Notes')
    if notes:item['nonempty_notes']+=1
    strings=[]
    def walk(value,loc='Notes'):
     if isinstance(value,str):strings.append((loc,value))
     elif isinstance(value,list):
      for i,v in enumerate(value):walk(v,loc+'['+str(i)+']')
     elif isinstance(value,dict):
      for k,v in value.items():walk(v,loc+'.'+str(k))
    walk(notes);item['strings']+=len(strings);item['strings_with_data_image']+=sum(bool(re.search(r'data:image/',s,re.I)) for _,s in strings)
    previous=old.sanitize_notes(notes,cp['source_url']);current=sanitize_notes(notes,cp['source_url'])
    if previous[:2]!=current[:2]:item['changed_documents'].append({'node_id':str(doc.get('Id')),'unit':name,'body_sha256':sha(raw),'source_notes_sha256':sha(canon(notes)),'old_normalized_sha256':sha(canon(previous[:2])),'new_normalized_sha256':sha(canon(current[:2]))})
    gaps=[o for o in current[1] if o.get('qualification_error')]
    if gaps:item['boundary_gap_documents'].append({'node_id':str(doc.get('Id')),'source_notes_sha256':sha(canon(notes)),'fields':[o['source_field'] for o in gaps]})
    # Serialized normalized Notes+omissions, not original source_markup.
    assert not re.search(r'data:image/',json.dumps(current[:2]),re.I),'Normalized source image URI retained'
  for key,field in [('content_units','content_units'),('documents','documents'),('documents_with_nonempty_notes','nonempty_notes'),('note_strings','strings'),('note_strings_with_data_image','strings_with_data_image')]:totals[key]+=item[field]
  totals['normalized_note_differences']+=len(item['changed_documents']);totals['candidate_boundary_gaps']+=len(item['boundary_gap_documents'])
  report['publications'].append(item)
 reports.append(report)
assert all(sha((project/name).read_bytes())==expected for name,expected in source_manifest.items())
result={'kind':'actual retained-source Notes exposure/differential, no fresh acquisition or semantic promotion','network_requests':0,'source_files_unchanged':True,'source_manifest':source_manifest,'baseline_notes_sha256':sha((base/'baseline/notes.py').read_bytes()),'candidate_notes_sha256':sha((base/'notes.py').read_bytes()),'candidate_model_sha256':sha((base/'model.py').read_bytes()),'totals':totals,'runs':reports,'scope_note':'All committed content_units in these retained full-run checkpoint families, including interrupted and repeated runs; counts include repeated editions. Only Notes normalization is compared. Synthetic quoted/ambiguous regressions provide edge exposure where actual data does not.'}
(base/'actual-source-notes-differential.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(totals,indent=2))
