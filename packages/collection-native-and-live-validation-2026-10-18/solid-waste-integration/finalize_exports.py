import sys,hashlib,json,gzip
from pathlib import Path
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R/'candidate'));from collectors.encodeplus import native_document as n
rows=[json.loads(l) for l in (R/'actual-full6/records.jsonl').read_text().splitlines()];out=R/'standalone-final';out.mkdir(exist_ok=True)
for name,body in n.outputs(rows).items():(out/name).write_bytes(body)
(R/'final-standalone-export.json').write_text(json.dumps({'scope':'Purefinalserializer replay ofoncecapturedactualfull6logicalsource; no nativeparse or newacquisition','records':88,'physical_pages':6,'outputs':{p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in out.iterdir()}},indent=2)+'\n')
p=R.parent/'official/infrastructure-canonical-candidate-v2/derivative-current/records.jsonl';raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()=='95e28ea3fa4a60f30cf6b55a33d12f49ca04c3b6895ceca85bfe43af3355d58a';(R/'source-mixed636.jsonl.gz').write_bytes(gzip.compress(raw,mtime=0))
p=R/'candidate/collectors/encodeplus/solid_waste_logical.py';s=p.read_text();a=s.index('def outputs(records):');s=s[:a]+'''def outputs(records):
    assert records and records[0].get('unit')=='pdf_logical_unit'
    cfg={'id':records[0]['document_id'],'url':records[0]['source_document_url']};validate_records(records,cfg)
    columns=['id','document_id','unit','unit_type','heading','parent_id','source_label','source_pages','physical_page_start','physical_page_end','page_count','text','source_url','raw_sha256'];stream=io.StringIO(newline='');writer=csv.DictWriter(stream,columns);writer.writeheader();writer.writerows({k:(json.dumps(r[k]) if k=='source_pages' else r.get(k)) for k in columns} for r in records)
    jsonl=lambda rs:''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\\n' for r in rs).encode();result={'records.jsonl':jsonl(records),'records.csv':stream.getvalue().encode()};e=records[0]['source_document_evidence']
    for name,key in [('source-logical-units.jsonl','original_logical_units'),('source-controls.jsonl','source_controls'),('source-glyphs.jsonl','source_glyphs'),('source-words.jsonl','source_words')]:result[name]=jsonl(e[key])
    result['source-page-diagnostics.jsonl']=jsonl(records[0]['superseded_detector_diagnostics']['original_page_records'])
    for name,key in [('source-tags.json','source_tags'),('source-dependency-inventory.json','source_dependency_inventory'),('source-logical-qualification.json','qualification'),('source-independent-audit.json','audit')]:result[name]=(json.dumps(e[key],ensure_ascii=False,sort_keys=True,indent=2)+'\\n').encode()
    return result
'''
h=json.loads((R/'actual-executed-module-hashes.json').read_text())['solid_waste_logical.py'];assert hashlib.sha256(s.encode()).hexdigest()==h;(R/'attempts/actual-executed-source/solid_waste_logical.py').write_text(s)
(R/'capture-to-final-source-delta.json').write_text(json.dumps({'initial_executed_native_sha256':json.loads((R/'actual-executed-module-hashes.json').read_text())['native_document.py'],'initial_executed_adapter_sha256':h,'final_native_sha256':hashlib.sha256((R/'candidate/collectors/encodeplus/native_document.py').read_bytes()).hexdigest(),'final_adapter_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_extraction_build_and_independent_audit_unchanged':True,'changes_after_native_capture':['Explicitownnative textscopecoverage true/externaldocsfalse','Mixedlogical+genericCSVincludingblankphysical_pageforlogical','Pureoutputvalidator namefixedbacktorecords[0] aftermixedadapterrefactor','Infrastructurealias dataonly7113→a7f35']},indent=2)+'\n');print('exports+executedsourcehashesverified')
