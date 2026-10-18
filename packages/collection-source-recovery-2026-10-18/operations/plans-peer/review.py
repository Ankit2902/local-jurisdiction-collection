"""Read-only all-publications CLI review; finite catalog only, no runtime setup."""
import hashlib,importlib.util,json,os,pathlib,subprocess,sys,tempfile
OUT=pathlib.Path(__file__).resolve().parent
PROJECT=OUT.parent.parent.parent
PACKET=PROJECT/'outputs/collection-readiness-post716cfcb-2026-10-17/qa/all-publication-plans-candidate-v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(PACKET/'MANIFEST.json')=='c9d2e6bb967dfd037684c69fbef692d936e9abae57a8e3e684ea04063dc652e7'
manifest=json.loads((PACKET/'MANIFEST.json').read_text());before={str(p.relative_to(PACKET)):sha(p) for p in PACKET.rglob('*') if p.is_file()}
assert {k:v for k,v in before.items() if k!='MANIFEST.json'}=={k:v['sha256'] for k,v in manifest['files'].items()}
C=PACKET/'candidate';baseline=(PACKET/'baseline/launcher.py').read_text();current=(C/'collectors/ops/launcher.py').read_text()
assert sha(PACKET/'baseline/launcher.py')=='a924112d786e1df486389c7b82d7b611e6579e48a9ed007e30395ba4ae07bd0d'
# Remove only three additive planning changes; exact reviewed owned-Python baseline must reappear.
s=current.replace("p.add_argument('--all', action='store_true', help='Plan the primary publication for every selected target')","p.add_argument('--all', action='store_true')").replace("            p.add_argument('--all-publications', action='store_true', help='Plan all inventoried primary/secondary publications, including unqualified discoveries; no acquisition')\n",'').replace("            if args.all_publications:\n                command += ['--all-publications']\n",'')
assert s==baseline,'Other shared runtime/acceptance/owned-Python behavior changed'
# Independently invoke the delivered8-method test file. It guards subprocesses, network and native/app imports and snapshots every sourcefile.
r=subprocess.run([sys.executable,'-B',str(PACKET/'test_all_publications.py')],cwd=OUT,capture_output=True,text=True);(OUT/'eight-tests.stdout').write_text(r.stdout);(OUT/'eight-tests.stderr').write_text(r.stderr);assert r.returncode==0,r.stderr
spec=importlib.util.spec_from_file_location('plan_test',PACKET/'test_all_publications.py');t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t);cat=t.CAT.load_catalog();pb={p['id']:p for p in cat['publications']}
results=[]
with tempfile.TemporaryDirectory(prefix='independent-catalog-plan-') as td:
 work=pathlib.Path(td);guard=work/'guard';guard.mkdir();(guard/'sitecustomize.py').write_text(t.GUARD);events=work/'events.jsonl';runtime=work/'runtime-not-created';env=dict(os.environ,PYTHONPATH=str(guard),PYTHONDONTWRITEBYTECODE='1',PLAN_GUARD_LOG=str(events),HOME=str(work/'fresh-home'))
 def run(args,direct=False):
  argv=[sys.executable,'-B',str(C/('collectors/registry/collect.py' if direct else 'collect.py'))]+args
  done=subprocess.run(argv,cwd=work,env=env,capture_output=True,text=True)
  return done
 def parsed(args,direct=False):
  result=run(args,direct);assert result.returncode==0,result.stderr;return json.loads(result.stdout)
 allplan=parsed(['--runtime',str(runtime),'plan','--all-publications']);assert not runtime.exists();assert allplan['targets']==130 and allplan['publication_count']==225 and allplan['runnable_config_count']==195
 assert {p['publication_id'] for p in allplan['plans']}==set(pb);assert sum(not p['runnable'] for p in allplan['plans'])==30;assert sum(bool(p['observed_access_advisories']) for p in allplan['plans'])==154
 for plan in allplan['plans']:
  p=pb[plan['publication_id']]
  for k,key in [('publication_title','title'),('source_url','source_url'),('publication_role','role'),('publisher','publisher'),('source_family','source_family'),('required_publication_dependencies','required_publication_dependencies')]:assert plan[k]==p.get(key,[])
  assert plan['target_id']==p['target_id'] and plan['runnable']==p['runnable'] and plan['jurisdiction_complete'] is False
  if not p['runnable']:assert plan['unsupported_reason']==p['unsupported_reason'] and 'argv' not in plan
 legacy=parsed(['plan','--all']);assert len(legacy['plans'])==legacy['targets']==130 and 'publication_count' not in legacy;assert {p['publication_id'] for p in legacy['plans']}=={q['primary_publication_id'] for q in cat['targets']}
 for cohort in ['original','expansion']:
  d=parsed(['plan','--all-publications','--cohort',cohort]);expected=t.CAT.load_catalog(cohort);assert {p['publication_id'] for p in d['plans']}=={p['id'] for p in expected['publications']};results.append({'selector':cohort,'targets':d['targets'],'publications':d['publication_count']})
 for target in ['82','original-petaluma-ca']:
  d=parsed(['plan','--all-publications','--target',target]);assert {p['publication_id'] for p in d['plans']}=={p['id'] for p in cat['publications'] if p['target_id']==target};assert d['targets']==1;results.append({'selector':target,'publications':d['publication_count']})
 faults=[]
 for args,direct in [(['plan','--all-publications','--all'],False),(['plan','--all-publications','--publication','82-primary'],False),(['plan','--all-publications','--target','original-petaluma-ca','--cohort','expansion'],False),(['collect','--all-publications','--target','82','--out',str(work/'bad1')],True),(['verify','--all-publications','--target','82','--out',str(work/'bad2')],True),(['status','--all-publications'],True),(['run','--all-publications','--target','82','--out',str(work/'bad3')],False),(['verify','--all-publications','--target','82','--out',str(work/'bad4')],False),(['doctor','--all-publications','--target','82'],False)]:
  result=run(args,direct);assert result.returncode==2,(args,result.stderr);faults.append({'argv_tail':args,'direct_registry':direct,'exit':result.returncode})
 assert not any((work/n).exists() for n in ['bad1','bad2','bad3','bad4']) and not runtime.exists();assert not events.exists(),events.read_text() if events.exists() else ''
 after={str(p.relative_to(PACKET)):sha(p) for p in PACKET.rglob('*') if p.is_file()};assert after==before
 report={'schema_version':1,'status':'PASS','packet_manifest_sha256':sha(PACKET/'MANIFEST.json'),'candidate_files_unchanged':len(before),'eight_existing_focused_tests_passed':True,'actual_root_cli':{'targets':130,'publication_entries':225,'runnable':195,'unqualified':30,'advisory_entries':154,'every_entry_exact_identity_title_role_url_scope_match':True,'optional_nonexistent_runtime_not_created_or_inspected':True},'legacy_primary_all_preserved':130,'selected_filters':results,'illegal_combinations_refused_before_execution':faults,'forbidden_calls':[],'native_or_browser_imports':0,'publisher_requests':0,'owned_python_reviewed_baseline_sha256':sha(PACKET/'baseline/launcher.py'),'owned_python_baseline_exactly_preserved_after_removing_only_plan_delta':True,'plan_launcher_sha256':sha(C/'collectors/ops/launcher.py'),'registry_collect_sha256':sha(C/'collectors/registry/collect.py'),'material_blockers':[],'scope':'Pure catalog planning; no runtime setup/doctor/acquisition/native parsing/readiness change or jurisdiction qualification.'}
 (OUT/'review.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');(OUT/'actual-all-publications.json').write_text(json.dumps(allplan,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['status','actual_root_cli','legacy_primary_all_preserved','owned_python_baseline_exactly_preserved_after_removing_only_plan_delta']}))
if __name__=='__main__':pass
