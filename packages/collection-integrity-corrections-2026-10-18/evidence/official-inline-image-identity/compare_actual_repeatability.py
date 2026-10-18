#!/usr/bin/env python3
"""Require source-proven7inline metadata-only changes and whole71page repeatability."""
import ast,hashlib,json,pathlib,datetime
root=pathlib.Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(case):return [json.loads(line)for line in(root/case/'records.jsonl').read_text().splitlines()]
def diffs(x,y,path=()):
 if type(x)!=type(y):return [path]
 if isinstance(x,dict):
  if set(x)!=set(y):return [path+('KEYS',)]
  return [v for k in x for v in diffs(x[k],y[k],path+(k,))]
 if isinstance(x,list):
  if len(x)!=len(y):return[path+('LENGTH',)]
  return[v for i,(u,v)in enumerate(zip(x,y))for v in diffs(u,v,path+(i,))]
 return []if x==y else[path]
def at(rows,path):
 for x in path:rows=rows[x]
 return rows
cases=json.loads((root/'process-progress.json').read_text());assert len(cases)==4 and all(x['returncode']==0 for x in cases)
a,b,c,d=map(load,['baseline-a','baseline-b','candidate-a','candidate-b']);reports={n:json.loads((root/n/'report.json').read_text())for n in ['baseline-a','baseline-b','candidate-a','candidate-b']};assert len(a)==len(b)==len(c)==len(d)==71;assert all(r['source_sha256']=='b2cf3f57150581560328494e4a59b2bf6bac1ceb05ba87e7940f0f27f4f14360'and not r['forbidden_calls']for r in reports.values())
repeat=diffs(a,b);delta=diffs(a,c);assert repeat and all(p[-1]=='source_name'for p in repeat);assert len(delta)==7 and all(p[-1]=='source_name'for p in delta);assert not diffs(c,d);assert(root/'candidate-a/records.jsonl').read_bytes()==(root/'candidate-b/records.jsonl').read_bytes()
inline={str(im['physical_page'])+':'+str(im['source_image_ordinal']):im for im in reports['candidate-a']['source_images']if im['object_id']is None};changed=[]
for path in delta:
 before,after=at(a,path[:-1]),at(c,path[:-1]);assert before['kind']=='image_placeholder'and after['source_name']is None and before['id']==after['id']and before['bbox']==after['bbox'];page=path[0]+1;ordinal=int(before['id'].rsplit(':',1)[1]);assert str(page)+':'+str(ordinal)in inline;changed.append({'physical_page':page,'image_id':before['id'],'bbox':before['bbox'],'path':'/'+('/'.join(map(str,path))),'old_source_name_sha256':hashlib.sha256(before['source_name'].encode()).hexdigest(),'new_source_name':None})
assert len(inline)==7 and{r['physical_page']for r in changed}=={52,57,63}
baseline=(root/'baseline-runtime/pdf_structure.py').read_text();candidate=(root/'pdf_structure.py').read_text();func=lambda s:{f.name:ast.dump(f,include_attributes=False)for f in ast.parse(s).body if isinstance(f,ast.FunctionDef)};bf,cf=func(baseline),func(candidate);assert sorted(k for k in set(bf)|set(cf)if bf.get(k)!=cf.get(k))==['image_source_name','pages'];reversed_candidate=candidate.replace("'source_name':image_source_name(im)","'source_name':str(im.get('name',''))");assert func(reversed_candidate)['pages']==bf['pages']
report={'schema':1,'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pass':True,'native_pdf_scope':'Whole exact71pageArlingtonCharter, notwhole61filepublication','source_sha256':reports['candidate-a']['source_sha256'],'baseline_runtime_sha256':sha(root/'baseline-runtime/pdf_structure.py'),'candidate_runtime_sha256':sha(root/'pdf_structure.py'),'baseline_cross_process_differences':len(repeat),'baseline_difference_fields':['source_name'],'candidate_cross_process_bytes_identical':True,'candidate_records_sha256':reports['candidate-a']['records_sha256'],'source_bound_delta':changed,'all_other_legal_text_html_tables_qualifications_geometry_order_markers_citations_unchanged':True,'pages':71,'table_count':reports['candidate-a']['table_count'],'image_placeholder_count':reports['candidate-a']['image_placeholder_count'],'image_payload_reads':0,'bitmap_extract_render_ocr_network_calls':0,'source_ast_delta':'Only pages() source_name expression plus new metadata-onlyhelper; allotherfunctionASTexactunchanged. No cachecomparison waiver.','processes':cases,'reports':{n:sha(root/n/'report.json')for n in reports},'limitations':['Original61fileTXrunremainsfailed/no finalcoverage.','Newcandidateisnotpromoted; wholepublicationcurrentreplaystillrequired.','Existingtext/table/readingorder qualification limits unchanged.']};(root/'actual-repeatability.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'pass':True,'baseline_cross_process_differences':len(repeat),'candidate_bytes_identical':True,'metadata_only_source_bound_changes':len(changed),'pages':71},indent=2))
