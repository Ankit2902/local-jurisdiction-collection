#!/usr/bin/env python3
"""Network-disabled registry/family fault suite. Default is read-only; optional logs --out."""
import argparse,hashlib,json,os,platform,re,subprocess,sys,tempfile,importlib.metadata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
COMMANDS=[
 ('registry', ['collectors/registry/verify.py']),
 ('registry_faults',['collectors/registry/test_registry.py']),
 ('independent_municode',['collectors/qa/test_municode_edges.py']),
 ('independent_cross_family',['collectors/qa/test_cross_family_edges.py']),
 ('independent_image_policy',['collectors/qa/test_image_policy.py']),
 ('independent_official_no_image_transport',['collectors/qa/test_official_image_transport.py']),
 ('independent_american_no_image_transport',['collectors/qa/test_american_image_transport.py']),
 ('independent_image_byte_audit',['collectors/qa/test_image_audit.py']),
 ('municode_faults',['collectors/municode/test_faults.py']),
 ('american_legal_faults',['collectors/american-legal/test_faults.py']),
 ('ecode_faults',['-m','unittest','collectors.ecode.tests.test_faults']),
 ('encodeplus_faults',['-m','collectors.encodeplus.tests']),
 ('official_faults',['collectors/official/test_offline.py'])]
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,help='Fresh external log directory; omitted means no saved reports');a=p.parse_args()
 if a.out:
  a.out=a.out.resolve()
  if a.out.exists() and any(a.out.iterdir()):p.error('--out must be fresh/empty')
  a.out.mkdir(parents=True,exist_ok=True)
 results=[]
 # A test regression cannot silently turn a retained-source test into a network run.
 with tempfile.TemporaryDirectory(prefix='complisolv-offline-guard-') as td:
  guard=Path(td)/'sitecustomize.py';guard.write_text("import socket\ndef denied(*a,**k):\n raise RuntimeError('Network disabled by independent offline QA')\nsocket.socket.connect=denied\nsocket.socket.connect_ex=denied\nsocket.create_connection=denied\n")
  env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=td+os.pathsep+str(ROOT));env.pop('PYTHONSTARTUP',None)
  for name,args in COMMANDS:
   cmd=[sys.executable,'-B',*args];r=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True);stdout=r.stdout.encode();stderr=r.stderr.encode();entry={'name':name,'command':['python3','-B',*args],'exit_code':r.returncode,'passed':r.returncode==0,'stdout_sha256':sha(stdout),'stderr_sha256':sha(stderr)}
   match=re.search(r'Ran (\d+) tests?',r.stderr)
   if match:entry['unittest_cases']=int(match[1])
   try:
    body=json.loads(r.stdout)
    if 'passed' in body:entry['passed']=entry['passed'] and body['passed']
    if 'count' in body:entry['reported_cases']=body['count']
    if 'probes' in body:entry['reported_cases']=len(body['probes'])
   except (ValueError,TypeError):pass
   if not entry['passed']:entry['failure_tail']=(r.stdout+'\n'+r.stderr)[-5000:]
   results.append(entry)
   if a.out:(a.out/(name+'.stdout.txt')).write_bytes(stdout);(a.out/(name+'.stderr.txt')).write_bytes(stderr)
 hashes={str(p.relative_to(ROOT)):sha(p.read_bytes()) for folder in ['registry','qa','municode','american-legal','ecode','encodeplus','official'] for p in sorted((ROOT/'collectors'/folder).rglob('*')) if p.is_file() and p.suffix in ['.py','.cjs'] and '__pycache__' not in p.parts}
 report={'schema_version':1,'test_kind':'Independent network-disabled offline replay and synthetic faults; not live publication proof','network_disabled':True,'network_guard':'Python child socket connections disabled; adapter transports are mocked in production-path tests','read_only_sources':True,'passed':all(x['passed'] for x in results),'runtime':{'python':platform.python_version(),'os':platform.platform(),'dependencies':{n:importlib.metadata.version(n) for n in ['beautifulsoup4','requests','brotli','pypdf','pypdfium2','fonttools','Pillow']}},'image_policy':'No separate image requests/downloads. Literal [IMAGE] in normalized HTML/text; original native files remain source evidence. Required nonimage documents separate.','results':results,'source_sha256':hashes}
 if a.out:(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2));return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
