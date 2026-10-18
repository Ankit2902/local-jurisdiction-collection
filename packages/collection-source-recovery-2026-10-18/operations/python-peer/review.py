import sys
sys.dont_write_bytecode=True
from pathlib import Path
import importlib.util,hashlib,json,socket,subprocess
p=Path(__file__).resolve().parents[4]
r=p/'github/local-jurisdiction-collection'
c=p/'outputs/collection-readiness-post716cfcb-2026-10-17/qa/owned-python-runtime-candidate-v1'
o=Path(__file__).parent
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('reviewed_launcher',c/'candidate/collectors/ops/launcher.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
rt=r/'.collection-runtime';before={str(x):sha(x) for x in [rt/'runtime.json',rt/'venv/bin/python',Path(m.__file__)]}
calls=[]
def no(*a,**k):calls.append('network');raise AssertionError('No publisher/network requests permitted')
socket.socket.connect=no;socket.create_connection=no
result=m.doctor(rt)
assert result['ready'] and result['runtime_ready'],result
assert before=={x:sha(Path(x)) for x in before} and not calls
(o/'actual-doctor.json').write_text(json.dumps(result,indent=2)+'\n')
q=subprocess.run([sys.executable,'-B',str(c/'test_owned_python.py')],capture_output=True,text=True)
(o/'tests.stdout').write_text(q.stdout);(o/'tests.stderr').write_text(q.stderr);assert q.returncode==0
report={'passed':True,'actual_owned_runtime_doctor_ready':True,'publisher_requests':0,'forbidden_calls':calls,'source_receipt_binary_unchanged':True,'before_after_sha256':before,'candidate_source_sha256':sha(Path(m.__file__)),'candidate_tests_exit':q.returncode,'source_review':'Actual owned interpreter checked before pip installation and on doctor; receipt records actual owned version. Invalid/wrong version preserves incomplete status. Optional bootstrap version does not invalidate existing true receipts.','scope':'Existing owned actual macOS3.12.14 runtime doctor and controlled wrong-version setup; no installation or browser/network invocation.'}
(o/'review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='before_after_sha256'}))
