"""Portable AL refusal review, no acquisitions/native source replay/production edits."""
import ast,hashlib,json,os,shutil,socket,subprocess,sys,tempfile
from pathlib import Path
B=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00');S=B/'outputs/collection-readiness-poste026685-2026-10-17/qa/american-legal-portable-stop-candidate-v1';H=Path(__file__).resolve().parent;PY=B/'github/local-jurisdiction-collection/.collection-runtime/venv/bin/python'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def tree(p):return {str(x.relative_to(p)):sha(x)for x in p.rglob('*')if x.is_file()}
def run(cmd,log,cwd,expected=0,env=None):
 r=subprocess.run([str(x)for x in cmd],cwd=cwd,env=env,text=True,capture_output=True);(H/(log+'.stdout')).write_text(r.stdout);(H/(log+'.stderr')).write_text(r.stderr);assert r.returncode==expected,(log,r.returncode,r.stdout[-500:],r.stderr[-500:]);return r
before=tree(S);assert sha(S/'MANIFEST.json')=='b3ce7e076d2e5fc66e16e1cd9b55c929247d41a58ea0bfa3afb8a55adcb07984';assert {n:d['sha256']for n,d in load(S/'MANIFEST.json')['files'].items()}=={k:v for k,v in before.items()if k!='MANIFEST.json'}
a=load(S/'candidate/collectors/american-legal/access-advisory.json')['advisories'][0];ref=load(S/'evidence/failure-response.json');event=json.loads(ref['error'])['access_stop'];assert ref['op']=='head'and event['status']==403 and {k.lower():v for k,v in event['headers'].items()}['cf-mitigated']=='challenge'and event['body_snippet_bytes']==0;assert event['url']==a['observed_stop']['url']==a['raw_refusal_witness']['url'];assert a['source_sha256']==sha(S/'evidence/browser-stop.json')and a['raw_refusal_witness']['sha256']==sha(S/'evidence/failure-response.json');assert a['observed_stop']==load(S/'evidence/browser-stop.json');assert a['operator_review_required']is True and a['automatic_retry']is False
old=load(S/'baseline/access-advisories.json');new=load(S/'candidate/collectors/registry/access-advisories.json');assert new['advisories'][:-1]==old['advisories']and new['advisories'][-1]==a;assert {k:v for k,v in new.items()if k!='advisories'}=={k:v for k,v in old.items()if k!='advisories'}
original=Path(a['original_gate_path']);assert original.exists()and sha(original)==a['source_sha256'];original_before=original.read_bytes()
with tempfile.TemporaryDirectory(prefix='al-portable-peer-')as td:
 tmp=Path(td);copy=tmp/'candidate';shutil.copytree(S,copy)
 run([PY,'-B','-m','unittest','test_portable_stop','-v'],'ten-packet-tests',copy)
 run([PY,'-B',copy/'candidate/collectors/american-legal/test_access_advisory.py','-v'],'six-shipped-tests',tmp)
 run([PY,'-B',copy/'check_common_and_offline.py'],'common-offline-check',tmp)
 common=load(copy/'common-and-offline.json');assert common['passed']and common['common_catalog_actual_AL_publications']==23 and common['all_receive_exact_new_stop']and common['actual_common_access_state_ast_fresh_absent_gate_refused']and not common['physical_gate_created']and common['production_sources_unchanged'];(H/'common-offline.json').write_text(json.dumps(common,indent=2)+'\n')
 # Independent direct runpy call: fail before path.mkdir, file opening, lock,
 # sleep or process/socket APIs under fresh custom gate, even with -O.
 family=copy/'candidate/collectors/american-legal';custom=tmp/'never-created';trials=[]
 for variant in ['valid','missing','malformed','wrong-source','empty-records']:
  target=tmp/variant;target.mkdir();shutil.copy2(family/'gate.py',target/'gate.py');ad=target/'access-advisory.json'
  if variant=='valid':shutil.copy2(family/'access-advisory.json',ad)
  elif variant=='malformed':ad.write_text('{')
  elif variant=='wrong-source':d=load(family/'access-advisory.json');d['advisories'][0]['source_sha256']='0'*64;ad.write_text(json.dumps(d))
  elif variant=='empty-records':ad.write_text('{"schema_version":1,"advisories":[]}')
  for flags in [[],['-O']]:
   guard='''import os,runpy,sys,socket,time,subprocess\nfrom pathlib import Path\nfrom unittest.mock import patch\nfrom contextlib import ExitStack\ndef no(*a,**k):raise AssertionError("No state/network/process/sleep allowed")\nwith ExitStack()as s:\n for obj,key in [(Path,"mkdir"),(Path,"open"),(socket,"create_connection"),(socket.socket,"connect"),(subprocess,"Popen"),(time,"sleep")]:s.enter_context(patch.object(obj,key,no))\n sys.argv=[sys.argv[1],"reserve","https://codelibrary.amlegal.com/codes/any/latest/overview"]\n runpy.run_path(sys.argv[0],run_name="__main__")\n'''
   env=dict(os.environ,AMLEGAL_GATE_DIR=str(custom));r=subprocess.run([str(PY),'-B',*flags,'-c',guard,str(target/'gate.py')],cwd=tmp,env=env,capture_output=True,text=True);assert r.returncode!=0 and 'portable workflow access stop'in r.stderr and 'No state/network/process/sleep'in r.stderr if variant=='valid' else r.returncode!=0
   # Path.open tripwire also prevents reading advisory; this deliberately checks
   # that failed access to advisory retains source-anchored refusal, not a bypass.
   assert 'portable workflow access stop'in r.stderr,(variant,r.stderr);assert not custom.exists();trials.append({'advisory':variant,'optimized':bool(flags),'refused_before_state_or_request':True})
 assert original.read_bytes()==original_before and tree(S)==before
result={'passed':True,'reviewed_packet_manifest_sha256':sha(S/'MANIFEST.json'),'packet_files':len(before)-1,'source_stop_sha256':a['source_sha256'],'raw_refusal_sha256':a['raw_refusal_witness']['sha256'],'observed_method':'HEAD','observed_status':403,'observed_cf_mitigated':'challenge','observed_external_host':'leginfo.legislature.ca.gov','scope':'Conservative American Legal workflow stop. Other AL route availability untested; not a platformwide unavailability claim.','packet_tests':10,'shipped_portable_tests':6,'additional_state_request_tripwire_trials':trials,'all23ALcatalog_entries_advised':True,'nonAL_catalog_entries_unchanged':common['unchanged_other_publications'],'existing_registry_advisories_unchanged':True,'original_tmp_stop_preserved':True,'freshgate_state_requests_created':False,'readonly_standard_HTML_fixture_verification_available':common['standard_readonly_fixture_verification'],'publisher_native_image_operations':0,'production_and_packet_unchanged':True,'limits':'Common catalog/access_state tested with isolated registry overlay; no live acquisition, actual native replay or jurisdiction availability inferred.'};(H/'review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='additional_state_request_tripwire_trials'},indent=2))
