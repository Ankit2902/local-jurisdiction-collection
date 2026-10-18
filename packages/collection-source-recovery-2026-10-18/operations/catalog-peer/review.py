import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib,importlib.util,socket,subprocess
p=Path(__file__).resolve().parents[4];r=p/'github/local-jurisdiction-collection';c=p/'outputs/collection-readiness-post716cfcb-2026-10-18/core/ledger-candidate';o=Path(__file__).parent
sys.path[:0]=[str(r/'collectors/registry'),str(r/'collectors/qa')]
from catalog import load_catalog
spec=importlib.util.spec_from_file_location('candidate_ledger',c/'build_followup_ledger.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.ROOT=r;m.PROJECT=p;m.HERE=r/'collectors/qa'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
before=sha(r/'collectors/qa/followup-requirements.json');old=json.loads((r/'collectors/qa/followup-requirements.json').read_text());prior=json.loads((r/'collectors/qa/readiness-requirements.json').read_text());priorby={x['publication_id']:x for x in prior['publications']};catalog=load_catalog();pubs={x['id']:x for x in catalog['publications']};calls=[]
def no(*a,**k):calls.append('network');raise AssertionError('Offline ledger review')
socket.socket.connect=no;socket.create_connection=no
new=m.build();assert len(new['publications'])==225
oldby={x['publication_id']:x for x in old['publications']};changes=[]
for row in new['publications']:
 ident=row['publication_id'];pub=pubs[ident];previous=oldby[ident]
 assert row['dispatchable_config']==pub['runnable']==row['configuration_qualified']
 assert row['operational_access_prohibited']==bool(pub['observed_access_advisories'])
 assert row['access_stop_evidence']==pub['observed_access_advisories']
 for k in ['requirements','readiness_verified','active_readiness_binding']:assert row[k]==previous[k],(ident,k)
 priorfields={k:v for k,v in priorby.get(ident,{}).items() if k in ['dispatchable_config','operational_access_prohibited','access_stop_evidence']}
 if priorfields:assert row['historical_operational_state']['values']==priorfields
 else:assert 'historical_operational_state' not in row
 if any(row.get(k)!=previous.get(k) for k in ['dispatchable_config','operational_access_prohibited','access_stop_evidence']):changes.append(ident)
assert before==sha(r/'collectors/qa/followup-requirements.json') and not calls
(o/'generated-current-ledger.json').write_text(json.dumps(new,indent=2)+'\n')
q=subprocess.run([sys.executable,'-B',str(c/'test_current_status.py')],capture_output=True,text=True);(o/'tests.stdout').write_text(q.stdout);(o/'tests.stderr').write_text(q.stderr);assert q.returncode==0
report={'passed':True,'actual_rows':225,'runnable':sum(x['dispatchable_config'] for x in new['publications']),'catalog_stopped':sum(x['operational_access_prohibited'] for x in new['publications']),'changed_status_publications':changes,'all_readiness_requirements_and_active_bindings_unchanged':True,'prior_history_matches_actual_sealed_ledger':True,'production_unchanged':True,'candidate_sha256':sha(c/'build_followup_ledger.py'),'tests_exit':q.returncode,'publisher_requests':0,'scope':'Full actual build, all225row catalog reconciliation and sealed prior history; catalog advisories are distinct from physical/runtime external gates.'};(o/'review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
