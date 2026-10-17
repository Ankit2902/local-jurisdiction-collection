#!/usr/bin/env python3
"""Read-only offline bundle verification. All regenerated files go to a temporary directory."""
import sys
sys.dont_write_bytecode=True
import hashlib,json,pathlib,tempfile,subprocess,os
BASE=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/'scripts'))
import normalize_all as n

def main():
 manifest=json.loads((BASE/'ARTIFACT-HASHES.json').read_text());checked=0
 for name,digest in manifest['sha256'].items():
  p=BASE/name;assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==digest,('Artifact mismatch',name);checked+=1
 assignment=json.loads((BASE/'assignment.json').read_text());results=json.loads((BASE/'results.json').read_text());assert {r['sequence'] for r in assignment}=={r['sequence'] for r in results} and len(results)==7
 required=['sequence','jurisdiction','state','source_url','source_family','status','acquisition_method','publisher_download','tested_scope','complete_corpus','record_count','checks','command','evidence_paths','script_paths','limitations','next_action']
 for r in results:
  assert all(k in r for k in required) and r['complete_corpus'] is False
  for name in r['evidence_paths']+r['script_paths']+r['publisher_download']['evidence_paths']:assert not pathlib.Path(name).is_absolute() and (BASE/name).is_file(),name
 with tempfile.TemporaryDirectory(prefix='compliSolv-official-replay-') as td:
  replay=pathlib.Path(td)/'parsed';summary=n.run(replay)
  expected={str(p.relative_to(BASE/'parsed')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (BASE/'parsed').rglob('*') if p.is_file()}
  actual={str(p.relative_to(replay)):hashlib.sha256(p.read_bytes()).hexdigest() for p in replay.rglob('*') if p.is_file()}
  assert expected==actual,('Deterministic replay differs',set(expected)^set(actual),[x for x in expected.keys()&actual.keys() if expected[x]!=actual[x]])
  for r in results:
   assert summary[r['sequence']]['record_count']==r['record_count'] and summary[r['sequence']]['table_count']==r['table_count']
  env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
  subprocess.run([sys.executable,str(BASE/'scripts/replay_one.py'),'--sequence','58','--raw',str(BASE/'fresh/58'),'--out',str(pathlib.Path(td)/'fresh58')],check=True,capture_output=True,env=env)
  for f in ['records.jsonl','records.csv']:
   assert (pathlib.Path(td)/'fresh58/58'/f).read_bytes()==(BASE/'fresh/58-parsed/58'/f).read_bytes()
 # Separately qualified native Savannah attachment: observed control, request/poll flow, PDF and all555source cells.
 native_run=subprocess.run([sys.executable,'-B',str(BASE/'savannah-native-export/scripts/verify.py')],check=True,capture_output=True,text=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
 native=json.loads(native_run.stdout);assert native['status']=='passed' and native['native_pdf_pages']==4 and native['source_table_cells']==555
 assert (BASE/'raw/87-impact-fee7137.html').read_bytes()==(BASE/'savannah-native-export/source/87-impact-fee7137.html').read_bytes()
 # Final generic browser collector also has a retained fresh live run.
 generic=json.loads((BASE/'fresh/58/58-alarm-export.meta.json').read_text())
 assert generic['script_sha256']==hashlib.sha256((BASE/'scripts/browser_capture.cjs').read_bytes()).hexdigest()
 assert hashlib.sha256((BASE/'fresh/58'/generic['executed_script']).read_bytes()).hexdigest()==generic['script_sha256']
 # Final portable collector exact bytes were exercised by fresh Chattanooga run.
 receipt=json.loads((BASE/'raw/85-final/receipt.json').read_text())
 assert receipt['script_sha256']==hashlib.sha256((BASE/'scripts/municode/collect_browser.cjs').read_bytes()).hexdigest()==hashlib.sha256((BASE/'raw/85-final/executed-collect_browser.cjs').read_bytes()).hexdigest()
 print(json.dumps({'status':'passed','offline':True,'artifacts_hash_verified':checked,'jurisdictions':7,'normalized_records':sum(r['record_count'] for r in results),'normalized_tables':sum(r['table_count'] for r in results),'deterministic_parsed_files':len(expected),'fresh_final_collector_exercised':True,'source_inputs_modified':False,'savannah_selected_native_pdf_verified':True},indent=2))
if __name__=='__main__':main()
