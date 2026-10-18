"""Build a compact documentary proof subset; never calls source transport/native parser."""
from pathlib import Path
import json,hashlib,shutil,difflib,importlib.util,sys
P=Path(__file__).resolve().parent;C=P/'candidate';R=Path(json.loads((P/'source-binding.json').read_text())['repository']);PROOF=R/'packages/collection-source-recovery-2026-10-18/clark/full30';PEER=R/'packages/collection-source-recovery-2026-10-18/clark/peer'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cp=read(PROOF/'run/checkpoint.json');names=['config.json','source-inventory.json','SUMMARY.json','source-binding.json','verification-source-binding.json','verify.stdout','run/config.json','run/checkpoint.json','run/coverage.json','run/'+cp['identity']['source_ref']];names += ['run/executed/'+n for n in cp['scripts']]
E=P/'evidence/full30'
for n in names:
 d=E/n;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(PROOF/n,d)
shutil.copyfile(PROOF/'MANIFEST.json',E/'sealed-full30-MANIFEST.json')
for name in ['review.json','MANIFEST.json']:
 d=P/'evidence/peer'/name;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(PEER/name,d)
source_receipts=[]
for f in(PROOF/'run/raw').glob('*.receipt.json'):
 d=E/'run/raw'/f.name;shutil.copyfile(f,d);source_receipts.append(str(d.relative_to(P)))
bridge={'schema':1,'qualification':'Retained sealed full30 proof bridged by exact configuration bytes and all16executed runtime module hashes. Current common CLI verification NOT executed; no fresh live/common pass inferred.','sealed_full30_manifest_sha256':sha(PROOF/'MANIFEST.json'),'sealed_peer_review_sha256':sha(PEER/'review.json'),'configuration_sha256':sha(PROOF/'config.json'),'candidate_config_sha256':sha(C/'collectors/official/configs/clark-title30-current-associated-documents.json'),'executed_scripts':{n:{'sealed':h,'current_candidate':sha(C/'collectors/official'/n),'unchanged':h==sha(C/'collectors/official'/n)}for n,h in cp['scripts'].items()},'new_component_metadata':'One catalog qualification overlay and the byte-identical tested official configuration are new selected-component inputs, not an existing common job binding. No migration or fabricated job receipt.','evidence_subset_policy':'Only metadata, receipts, original HTML, executed source modules and prior proof reports duplicated here. All native PDFs and canonical outputs remain in the sealed repository package; this subset is not a substitute full-native evidence package.','receipt_witness_count':len(source_receipts),'full381_reparse_count':0,'publisher_requests':0,'images_native_render_calls':0}
assert all(v['unchanged']for v in bridge['executed_scripts'].values());assert bridge['configuration_sha256']==bridge['candidate_config_sha256']
(P/'proof-bridge.json').write_text(json.dumps(bridge,indent=2)+'\n')
spec=importlib.util.spec_from_file_location('ops_candidate',C/'collectors/ops/launcher.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);sys.path.insert(0,str(C/'collectors/registry'));from catalog import load_catalog
pub=next(p for p in load_catalog()['publications']if p['id']=='96-7e8795b1baee');accept=m.publication_acceptance(pub,PROOF/'run');(P/'common-acceptance-projection.json').write_text(json.dumps({'method':'Pure current common acceptance interpretation of sealed coverage; no common verifier/collector invocation','publication_id':pub['id'],'result':accept},indent=2)+'\n')
whitelist=['collectors/registry/followup-qualified-configs.json','collectors/official/configs/clark-title30-current-associated-documents.json','collectors/registry/test_clark_title30_config.py']
source=read(P/'source-binding.json');source.update(whitelist=whitelist,before={n:sha(R/n)if(R/n).is_file()else None for n in whitelist},after={n:sha(C/n)for n in whitelist});(P/'source-binding.json').write_text(json.dumps(source,indent=2)+'\n')
patch=''
for n in whitelist:
 old=(R/n).read_text().splitlines(True)if(R/n).is_file()else [];new=(C/n).read_text().splitlines(True);patch+=''.join(difflib.unified_diff(old,new,fromfile='a/'+n,tofile='b/'+n))
(P/'candidate.patch').write_text(patch)
(P/'PROMOTION-PLAN.json').write_text(json.dumps({'baseline':'9ef7220','changes':[{'path':n,'before_sha256':source['before'][n],'after_sha256':source['after'][n]}for n in whitelist],'scope':'Data/config/test only; no shared dispatcher, runtime, producer or native parser code changes. Root owns ledger/docs regeneration after promotion.','counts':{'publications':225,'runnable':196,'unqualified':29,'advisories':154,'governments':130},'new_family_verify_or_publisher_requests':False},indent=2)+'\n')
print(json.dumps(source['after'],indent=2))
