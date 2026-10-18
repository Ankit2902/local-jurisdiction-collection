"""Independent scoped readiness review: immutable source, no acquisition/native APIs."""
import contextlib,copy,hashlib,io,json,pathlib,socket,subprocess,sys,unittest
from unittest.mock import patch
OUT=pathlib.Path(__file__).resolve().parent
ROOT=OUT.parent.parent.parent
PACKET=ROOT/'outputs/collection-readiness-next-2026-10-17/encodeplus/post-91f6c59/corpus-selected-readiness-candidate-v1'
C=PACKET/'candidate'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(PACKET/'MANIFEST.json')=='720a146033e3ef62cd1668ab3a087d96a1fffd04a3f7131a569cce39fb0f950d'
manifest=json.loads((PACKET/'MANIFEST.json').read_text());before={str(p.relative_to(PACKET)):sha(p) for p in PACKET.rglob('*') if p.is_file()};assert {k:v for k,v in before.items() if k!='MANIFEST.json'}==manifest['files']
sys.path.insert(0,str(C));sys.dont_write_bytecode=True
import package,readiness
from common import artifacts,files,load,FIELDS
calls=[];offline_cli_children=[];original_run=subprocess.run
def allow_verify_child(argv,*args,**kwargs):
 command=list(argv);assert command.pop(0)==sys.executable
 if command and command[0]=='-B':command.pop(0)
 assert len(command)==4 and command[1:3]==['verify','--out']
 script=pathlib.Path(command[0]);target=pathlib.Path(command[3]);assert script==target/'packager-source/package.py' and sha(script)==sha(C/'package.py')
 for name,h in package.code().items():assert sha(target/'packager-source'/name)==h
 offline_cli_children.append({'action':'verify','script_sha256':sha(script),'bytecode_flag':'-B' in argv,'scope':'Temporary fixture package, standardlib-only shipped verifier; no source/native/acquisition operations'})
 return original_run(argv,*args,**kwargs)

def deny(name):
 def stop(*a,**k):calls.append(name);raise AssertionError('Forbidden '+name)
 return stop
report={'candidate_manifest_sha256':sha(PACKET/'MANIFEST.json'),'candidate_files':len(before),'scope':'Independent current/historical projection and failclosed contract review; no acquisition/normalizer/native parse/image operations','python':sys.version,'cases':{},'faults':[]}
with contextlib.ExitStack() as stack:
 import pypdf,pdfplumber,pypdfium2,fitz
 from PIL import Image
 for obj,name in [(socket,'socket'),(pypdf,'PdfReader'),(pdfplumber,'open'),(pypdfium2,'PdfDocument'),(fitz,'open'),(Image,'open')]:stack.enter_context(patch.object(obj,name,deny(name)))
 stack.enter_context(patch.object(subprocess,'run',allow_verify_child))
 suite=unittest.defaultTestLoader.loadTestsFromNames(['test_package','test_readiness']);stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite);(OUT/'tests.log').write_text(stream.getvalue());assert result.wasSuccessful();report['tests']={'run':result.testsRun,'errors':len(result.errors),'failures':len(result.failures)}
 comparison=json.loads((PACKET/'actual-comparison.json').read_text())
 for label,case in comparison['cases'].items():
  path=ROOT/case['original_package'];oldfiles=files(path);pb=(path/'evidence/proofs/read-only-proof.json').read_bytes();fb=(path/'evidence/proofs/family-verification.json').read_bytes();b,proof,family,p=package.binding(path/'evidence/input',pb,fb,'originals-flagstaff-html-v1');generated=artifacts(p);r=json.loads(generated['validation-report.json']);old=load(path/'validation-report.json');rbase=dict(r);rbase.pop('selected_publication_ready');rbase.pop('selected_publication_readiness');assert rbase==old
  assert r['selected_publication_ready'] is (label=='current') and r['complete'] is False and r['downstream_ready'] is False and r['status']=='incomplete'
  unchanged={n:hashlib.sha256(data).hexdigest() for n,data in generated.items() if n!='validation-report.json'}
  assert len(unchanged)==14
  for n,h in unchanged.items():assert sha(path/n)==h
  assert len(p.rows)==2661 and all(set(row)==set(FIELDS) and len(row)==16 for row in p.rows)
  assert sum(row['full_text'].count('[IMAGE]') for row in p.rows)==882
  assert p.inherited_coverage['whole_jurisdiction_complete'] is False and p.inherited_coverage['external_adopted_legal_dependency_closure_complete'] is False and p.inherited_coverage['independent_final_review_complete'] is False
  e=p.readiness_evidence;binding=e['binding']
  assert binding['common_receipt_canonical_sha256']==readiness.digest(proof) and binding['family_report_canonical_sha256']==readiness.digest(family) and binding['source_input_inventory_sha256']==readiness.digest(proof['evidence_sha256_before'])
  assert binding['coverage_raw_sha256']==sha(path/'evidence/input/coverage.json')
  assert r['selected_publication_readiness']['independent_legal_review_inferred'] is False and r['selected_publication_readiness']['jurisdiction_readiness_inferred'] is False
  assert files(path)==oldfiles
  report['cases'][label]={'source_package_manifest_sha256':sha(path/'run-manifest.json'),'source_files_unchanged':True,'records':len(p.rows),'fields':16,'image_placeholders':882,'data_artifacts_byte_identical':unchanged,'selected_publication_ready':r['selected_publication_ready'],'strict_complete':r['complete'],'downstream_ready':r['downstream_ready'],'scope_gates_unchanged':True,'common_family_inventory_bindings_recomputed':True}
  if label=='current':
   # Consumer contract faults: explicit source-consistency, sourceepoch and foreignpublication cannot borrow scoped readiness.
   mutations=[('source_epoch',lambda q:q.metadata['source_version'].update(snapshot_id='other')),('source_consistency',lambda q:q.readiness_evidence['gates'].update(source_consistency_complete=False)),('wrong_publication',lambda q:setattr(q,'publication_id','original-flagstaff-az-secondary')),('unresolved_source',lambda q:q.dispositions[0].update(disposition='unresolved')),('no_evidence',lambda q:setattr(q,'readiness_evidence',None))]
   for name,change in mutations:
    q=copy.deepcopy(p);change(q)
    # Reader/Projection validates foreign publication dispositions before report if applicable.
    try:rr=json.loads(artifacts(q)['validation-report.json']);refused=rr['selected_publication_ready'] is False
    except ValueError:refused=True
    assert refused,name;report['faults'].append({'case':name,'selected_readiness_refused':True})
 # Other published adapters lack this qualified contract; compare their full retained projections too.
 other=json.loads((PACKET/'other-reader-comparison.json').read_text())
 report['other_readers']={}
 for name,case in other['cases'].items():
  path=ROOT/case['package'];oldfiles=files(path);pb=(path/'evidence/proofs/read-only-proof.json').read_bytes();fb=(path/'evidence/proofs/family-verification.json').read_bytes();reader=load(path/'run-manifest.json')['reader'];_,proof,family,p=package.binding(path/'evidence/input',pb,fb,reader);generated=artifacts(p);r=json.loads(generated['validation-report.json']);base=dict(r);base.pop('selected_publication_ready');base.pop('selected_publication_readiness');assert base==load(path/'validation-report.json');assert r['selected_publication_ready'] is False
  for n,data in generated.items():
   if n!='validation-report.json':assert (path/n).read_bytes()==data
  assert files(path)==oldfiles
  report['other_readers'][name]={'rows':len(p.rows),'selected_publication_ready':False,'other14artifacts_identical':True,'input_unchanged':True}
assert not calls
assert before=={str(p.relative_to(PACKET)):sha(p) for p in PACKET.rglob('*') if p.is_file()}
report['allowed_offline_fixture_cli_children']=offline_cli_children
assert len(offline_cli_children)==2
report.update(status='PASS',candidate_files_unchanged=True,forbidden_calls=calls,material_blockers=[],code_review={'operational_changes_only':['common.py','flagstaff.py','package.py','readiness.py'],'global_ops_registry_acceptance_modified':False,'strict_gate_logic_status_cli_exits_unchanged':True,'allowed_publication_only':'original-flagstaff-az-primary','semantic_scope':'Existing bound selected codified publication acceptance; no independent legal review/edition/native semantics/jurisdiction-discovery inference'})
(OUT/'review.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':report['status'],'tests':report['tests'],'current':report['cases']['current']['selected_publication_ready'],'historical':report['cases']['historical']['selected_publication_ready'],'forbidden_calls':calls,'noops':14}))
