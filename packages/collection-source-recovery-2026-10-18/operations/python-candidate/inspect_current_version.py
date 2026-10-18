"""Actual installed interpreter version read only; no setup/doctor/pip/browser."""
import sys
sys.dont_write_bytecode=True
import hashlib,importlib.util,json,os
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00/github/local-jurisdiction-collection')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 src=HERE/'candidate/collectors/ops/launcher.py';s=importlib.util.spec_from_file_location('candidate_version_probe',src);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 py=ROOT/'.collection-runtime/venv/bin/python';receipt=ROOT/'.collection-runtime/runtime.json';record=json.loads(receipt.read_text());before={'receipt':sha(receipt),'python_binary':sha(py.resolve())}
 os.environ['PYTHONDONTWRITEBYTECODE']='1'
 observed=m.interpreter_version(py)
 assert observed==record['python_version']==[3,12,14]
 assert before=={'receipt':sha(receipt),'python_binary':sha(py.resolve())}
 out={'actual_owned_version':observed,'existing_receipt_version':record['python_version'],'same':True,'receipt_python_before_after':before,'runtime_modified':False,'setup_doctor_pip_browser_executed':False,'publisher_requests':0,'source_sha256':sha(src),'note':'Only Python stdlib sys/json version query executed with bytecode disabled. No dependency installation, browser or publication replay.'}
 (HERE/'current-owned-version.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'passed':True,'owned_version':observed}))
if __name__=='__main__':main()
