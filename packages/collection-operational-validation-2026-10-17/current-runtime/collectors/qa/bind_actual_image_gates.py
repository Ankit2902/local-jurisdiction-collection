"""Run current no-image audits/tests against an actual verified artifact tuple.
No requirement statuses are granted by this tool.
"""
import argparse,hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path
from readiness_binding import current_components,gate_qa_sources,canonical
ROOT=Path(__file__).resolve().parents[2];PROJECT=ROOT.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--proof',type=Path,required=True);p.add_argument('--run',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 if a.out.exists():raise ValueError('Fresh proof directory required')
 proof=json.loads(a.proof.read_text());selection=proof['selected_configuration'];pub=selection['publication'];assert pub.get('adapter_family',pub['publisher'])=='originals'
 assert proof['component_sources']==current_components(ROOT,pub);manifestpath=PROJECT/proof['artifact_manifest'];assert sha(manifestpath)==proof['artifact_manifest_sha256'];manifest=json.loads(manifestpath.read_text())
 run=a.run.resolve();assert run.is_relative_to(PROJECT.resolve())
 before={str(x.relative_to(run)):sha(x) for x in run.rglob('*') if x.is_file()}
 for item in manifest['files']:
  f=PROJECT/item['path'];assert f.is_relative_to(run) and sha(f)==item['sha256']
 assert len(before)==len(manifest['files'])
 a.out.mkdir(parents=True);commands=[('normalized_image_audit',['collectors/qa/audit_normalized_images.py',str(run)]),('acquired_bytes_image_audit',['collectors/qa/audit_images.py',str(run)]),('image_transport_regression',['collectors/qa/test_originals_image_transport.py'])]
 with tempfile.TemporaryDirectory() as td:
  Path(td,'sitecustomize.py').write_text("import socket\ndef deny(*a,**k):raise RuntimeError('QA_NETWORK_FORBIDDEN')\nsocket.socket.connect=deny\nsocket.create_connection=deny\n")
  for key,args in commands:
   r=subprocess.run([sys.executable,'-B',*args],cwd=ROOT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=td+os.pathsep+str(ROOT)),capture_output=True,text=True);(a.out/(key+'.stdout')).write_text(r.stdout);(a.out/(key+'.stderr')).write_text(r.stderr)
   report=json.loads(r.stdout) if key!='image_transport_regression' and r.returncode==0 else {'passed':r.returncode==0,'tests':'Three actual original-source transport/Word-media/HTML-cell entrypoint tests','stderr':r.stderr}
   assert r.returncode==0 and report['passed']
   report.update(proof_scope_id=proof['scope_id'],component_sources=proof['component_sources'],executed_qa_sources=gate_qa_sources(ROOT,pub,key),actual_run=str(run.relative_to(PROJECT)),artifact_manifest_sha256=proof['artifact_manifest_sha256'],network_requests_sent=0)
   path=a.out/(key+'.json');path.write_text(json.dumps(report,indent=2)+'\n');proof[key]={'path':str(path.relative_to(PROJECT)),'sha256':sha(path)}
 after={str(x.relative_to(run)):sha(x) for x in run.rglob('*') if x.is_file()};assert before==after and proof['component_sources']==current_components(ROOT,pub)
 proof['actual_image_gates_read_only']=True;proof['actual_image_gates_evidence_unchanged']=True;(a.out/'active-proof-images.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'passed':True,'scope_id':proof['scope_id'],'evidence_files':len(before),'proof':str(a.out/'active-proof-images.json'),'network_requests_sent':0}));return 0
if __name__=='__main__':raise SystemExit(main())
