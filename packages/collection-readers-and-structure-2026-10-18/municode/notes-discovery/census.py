from pathlib import Path
import json,hashlib,collections
B=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00');O=Path(__file__).resolve().parent
old=json.loads((B/'outputs/collection-readiness-next-2026-10-17/municode/isolated-multiline-notes-candidate-v2/actual-source-notes-differential.json').read_text())
roots={B/p for p in old['source_manifest'] if p.endswith('/checkpoint.json')}
for base in [B/'outputs/collection-readiness-2026-10-17/municode',B/'outputs/collection-readiness-2026-10-17/ops']:
 for p in base.rglob('checkpoint.json'):
  if 'fixtures' not in p.parts and ('runs' in p.parts or p.parent.name.startswith('live-henderson')):roots.add(p)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();witness={};cache={};runs=[];samples=[];unique_pop={};tot=collections.Counter()
for p in sorted(roots):
 cp=json.loads(p.read_text());root=p.parent
 if 'publications' not in cp or 'units' not in cp:continue
 witness[str(p.relative_to(B))]=sha(p);entry={'root':str(root.relative_to(B)),'checkpoint_sha256':sha(p),'phase':cp.get('phase'),'expected_identity':cp.get('expected_identity'),'publications':[]}
 for pid,pub in cp['publications'].items():
  stats=collections.Counter();sourceunits=list(pub.get('content_units',[]));landing=pub.get('root_landing_unit')
  if landing and landing not in sourceunits:sourceunits.append(landing)
  for name in sourceunits:
   u=cp['units'][name];rpath=root/u['receipt'];rec=json.loads(rpath.read_text());body=root/rec['body_file'];bh=sha(body);assert bh==rec['sha256']==u['sha256'];witness[str(rpath.relative_to(B))]=sha(rpath);witness[str(body.relative_to(B))]=bh
   if bh not in cache:cache[bh]=json.loads(body.read_bytes())
   raw=cache[bh];docs=raw if isinstance(raw,list) else raw.get('Docs',[])
   for idx,d in enumerate(docs):
    stats['doc_occurrences']+=1
    for key,value in d.items():
     if key.lower() not in ['notes','footnotes']:continue
     stats[key+'_schema_'+type(value).__name__]+=1
     if value:
      stats['populated_'+key]+=1;unique_pop[(bh,str(d.get('Id')),key)]={'raw_sha256':bh,'doc_id':str(d.get('Id')),'field':key,'value_sha256':hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode()).hexdigest()}
      samples.append({'root':entry['root'],'product_id':pid,'job_id':pub.get('job_id'),'source_unit':name,'receipt':u['receipt'],'raw_body':rec['body_file'],'raw_sha256':bh,'array_ordinal':idx,'doc_id':str(d.get('Id')),'doc_type':d.get('DocType'),'title':d.get('Title'),'field':key,'schema':type(value).__name__,'value_length':len(value) if hasattr(value,'__len__') else None,'sample':str(value)[:1200]})
  covpath=root/'publications'/pid/'coverage.json';cov=json.loads(covpath.read_text())if covpath.exists()else None
  entry['publications'].append({'product_id':pid,'job_id':pub.get('job_id'),'counts':dict(stats),'coverage_present':cov is not None,'publication_complete':cov.get('publication_complete')if cov else None});tot.update(stats)
 runs.append(entry)
assert all(sha(B/p)==h for p,h in witness.items())
result={'source_files_unchanged':True,'network_requests':0,'source_parser_or_image_api_calls':0,'runs':runs,'totals':dict(tot),'unique_source_bodies':len(cache),'unique_populated_fields':list(unique_pop.values()),'samples':samples,'source_manifest':witness};(O/'census.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'runs':len(runs),'unique_bodies':len(cache),'totals':dict(tot),'unique_populated_fields':len(unique_pop),'samples':samples[:3]}))
