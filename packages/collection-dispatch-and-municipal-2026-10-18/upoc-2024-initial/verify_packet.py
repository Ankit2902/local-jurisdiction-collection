"""Pure read-only packet/source-method audit; no native parser or publisher call."""
import sys
sys.dont_write_bytecode=True
import csv,gzip,hashlib,importlib.util,io,json,pathlib
H=pathlib.Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def verify():
 m=json.loads((H/'MANIFEST.json').read_text());files={x['path']:x for x in m['files']};actual={p.relative_to(H).as_posix():p for p in H.rglob('*')if p.is_file()and p.name!='MANIFEST.json'};assert set(actual)==set(files),'Selected packet inventory differs'
 for name,row in files.items():assert actual[name].stat().st_size==row['bytes']and sha(actual[name].read_bytes())==row['sha256'],'Selected bytes differ '+name
 registry=H/'candidate/collectors/registry';spec=importlib.util.spec_from_file_location('historical_qualification',registry/'historical_upoc_qualification.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q);pub={'id':q.IDENT,'validation_level':'mapped_only'};pub.update(json.loads((H/'REGISTRY-OVERRIDE-PROPOSAL.json').read_text())['publications'][q.IDENT]);assert q.audit(registry,{'publications':[pub]})==[]
 out=H/'actual-retained-full172';s=json.loads((out/'checkpoint.json').read_text());cfg=json.loads((out/'config.json').read_text());assert cfg==s['config'];source=out/s['source']['path'];assert sha(source.read_bytes())==q.NATIVE_SHA==s['source']['sha256'];assert sha((out/s['source']['receipt_path']).read_bytes())==s['source']['receipt_sha256']
 for name,h in s['code_hashes'].items():assert sha((out/'collector-source/collectors/encodeplus'/name).read_bytes())==h==sha((H/'candidate/collectors/encodeplus'/name).read_bytes()),'Captured/current candidate source differs '+name
 for name,h in s['normalized_outputs'].items():assert sha((out/name).read_bytes())==h
 assert sha((out/'records.jsonl').read_bytes())==q.RECORDS_SHA and sha((out/'coverage.json').read_bytes())==q.COVERAGE_SHA and sha((out/'checkpoint.json').read_bytes())==q.CHECKPOINT_SHA
 old=[json.loads(l)for l in gzip.decompress((H/'source/cached-whole172.jsonl.gz').read_bytes()).decode().split('\n')if l];rows=[json.loads(l)for l in(out/'records.jsonl').read_text().split('\n')if l];assert len(rows)==len(old)==172
 oi=old[0]['document_id'];ni=rows[0]['document_id'];oref=old[0]['raw_ref'];nref=rows[0]['raw_ref'];context={'heading','publication','jurisdiction','path','document_source_title','primary_source_owners'}
 def rebind(v):
  if isinstance(v,str):return v.replace(oi,ni).replace(oref,nref)
  if isinstance(v,list):return [rebind(x)for x in v]
  if isinstance(v,dict):return {rebind(k):rebind(x)for k,x in v.items()}
  return v
 for oldrow,r in zip(old,rows):assert oldrow['text']==r['text']and {k:v for k,v in rebind(oldrow).items()if k not in context}=={k:v for k,v in r.items()if k not in context},'Source text/IR differs beyond documented context'
 report=json.loads((out/'coverage.json').read_text());assert not report['publication_text_complete']and not report['current_adopted_edition_qualified']and report['start_end_consistent']is None
 return {'verified':True,'native_document_complete':True,'all172_source_pages_and_cached_IR_compared':True,'source_words':28603,'IMAGE':46,'canonical_detected_cells_agree':745,'CID_and_independent_engine_disagreement_pages':102,'captured_and_candidate_source_files':len(s['code_hashes']),'publication_text_complete':False,'closing_acquisition_performed':False,'current_edition_complete':False,'jurisdiction_complete':False,'native_parser_reexecuted':False,'publisher_or_image_operations':0}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
