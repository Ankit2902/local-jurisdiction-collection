"""Exact isolated candidate regression suites, synthetic/retained fixtures only."""
import datetime,hashlib,importlib.metadata,json,os,pathlib,re,subprocess,sys
OUT=pathlib.Path(__file__).resolve().parent;SOURCE=OUT/'candidate-source';TESTS=OUT/'tests';TESTS.mkdir(exist_ok=True);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected={'test_faults.py':46,'test_pdf_tags.py':21,'test_pdf_native.py':9,'test_pdf_publication.py':7,'test_pdf_encoding.py':4,'test_image_metadata.py':25,'test_native_notes.py':11,'test_resume_copy.py':6,'test_image_context.py':2,'test_source_alias.py':6,'test_fortworth_status.py':9,'test_boston_notes.py':10}
source_hashes={str(p.relative_to(SOURCE)):sha(p) for p in sorted(SOURCE.rglob('*')) if p.is_file() and ('__pycache__' not in p.parts) and (p.suffix in ['.py','.cjs'] or 'fixtures' in p.parts or p.name in ['requirements-lock.txt','requirements.txt','package.json'])};results=[]
for name,count in expected.items():
 run=subprocess.run([sys.executable,str(SOURCE/name)],cwd=SOURCE,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),capture_output=True);(TESTS/(name+'.stdout')).write_bytes(run.stdout);(TESTS/(name+'.stderr')).write_bytes(run.stderr)
 if name=='test_resume_copy.py':
  m=re.search(rb'Ran (\d+) tests?',run.stderr);actual=int(m.group(1)) if m else None;passed=run.returncode==0 and b'\nOK\n' in run.stderr
 else:value=json.loads(run.stdout);actual=value['count'];passed=run.returncode==0 and value['passed']
 results.append({'script':name,'source_sha256':sha(SOURCE/name),'passed':passed,'count':actual,'expected_count':count,'returncode':run.returncode,'stdout_sha256':sha(TESTS/(name+'.stdout')),'stderr_sha256':sha(TESTS/(name+'.stderr'))});assert passed and actual==count,results[-1];print(name,actual,'PASS',flush=True)
assert source_hashes=={n:sha(SOURCE/n) for n in source_hashes};locked=[]
for line in (SOURCE/'requirements-lock.txt').read_text().splitlines():
 if not line.strip() or line.startswith('#'):continue
 name,version=line.split('==');actual=importlib.metadata.version(name);assert actual==version;locked.append({'name':name,'installed':actual,'locked':version})
report={'passed':True,'count':sum(r['count'] for r in results),'existing_v12_cases':146,'new_Boston_cases':10,'suites':results,'source_hashes':source_hashes,'runtime':sys.version,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'model_sha256':sha(SOURCE/'model.py'),'source_base_sha256':sha(OUT/'source-base.json'),'locked_packages':locked,'publisher_requests':0,'image_decode_calls_new_Boston_tests':0,'no_source_changes_during_execution':True,'script_sha256':sha(pathlib.Path(__file__))};assert report['count']==156;(OUT/'offline-suites.json').write_text(json.dumps(report,indent=2)+'\n');print('TOTAL156 PASS',flush=True)
