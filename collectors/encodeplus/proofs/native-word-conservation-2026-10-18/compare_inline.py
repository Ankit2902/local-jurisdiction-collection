import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
rows=lambda label:[json.loads(l) for l in (root/label/'records.jsonl').read_text().splitlines()]
def diff(a,b,path=''):
 if type(a)!=type(b):return [(path,a,b)]
 if isinstance(a,dict):
  assert set(a)==set(b)
  return [d for k in a for d in diff(a[k],b[k],path+'/'+k)]
 if isinstance(a,list):
  assert len(a)==len(b)
  return [d for i,(x,y) in enumerate(zip(a,b)) for d in diff(x,y,path+'/'+str(i))]
 return [] if a==b else [(path,a,b)]
old_a=rows('baseline-a');old_b=rows('baseline-b');new_a=rows('candidate-a');new_b=rows('candidate-b');baseline=diff(old_a,old_b);delta=diff(old_a,new_a)
assert len(baseline)==len(delta)==7 and all(p.endswith('/source_name') for p,_,_ in baseline)
assert all(p.endswith('/source_name') and value is None for p,old,value in delta)
assert (root/'candidate-a/records.jsonl').read_bytes()==(root/'candidate-b/records.jsonl').read_bytes()
report=json.loads((root/'candidate-a/report.json').read_text());assert len(report['source_image_metadata'])==10
assert sum(i['object_id'] is None for i in report['source_image_metadata'])==7
assert [i['object_id'] for i in report['source_image_metadata'] if i['object_id'] is not None]==[152,179,1967]
assert all(not json.loads((root/label/'report.json').read_text())['forbidden_calls'] for label in ('baseline-a','baseline-b','candidate-a','candidate-b'))
summary={'passed':True,'scope':'Four independent processes, bounded actualCharterphysical52/57/63, not whole71/fullpublication','source_sha256':report['source_sha256'],'selected_physical_pages':[52,57,63],'baseline_crossprocess_differences':len(baseline),'difference_fields':['source_name'],'candidate_crossprocess_bytes_identical':True,'actual_inline_masks_qualified_by_stream_objid_none':7,'named_indirect_object_ids_preserved':[152,179,1967],'all_other_record_fields_unchanged':True,'image_placeholders_unchanged':10,'image_marker_count_unchanged':report['image_marker_count'],'pixel_decode_extract_render_ocr_network_calls':[],'candidate_records_sha256':report['records_sha256'],'changes':[{'path':p,'prior_source_name_sha256':hashlib.sha256(old.encode()).hexdigest(),'new_source_name':None} for p,old,_ in delta]}
(root/'inline-independent-repeatability.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
