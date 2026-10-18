"""Actual existing historical MC/EP readers do not infer the new qualification."""
import json,socket,sys
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE/'candidate'))
import package
from common import files,sha,encoded,artifacts,load
B=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00');S=B/'outputs/collection-readiness-post1997ee1-2026-10-17/qa/corpus-readers-municode-encodeplus-v1/FINAL-PACKET/fixtures/packages'
def main():
 results={}
 for name,mode,count in [('henderson','municode-html-publication-v1',2122),('charter','encodeplus-html-publication-v1',188)]:
  p=S/name;before=files(p);pb=(p/'evidence/proofs/read-only-proof.json').read_bytes();fb=(p/'evidence/proofs/family-verification.json').read_bytes();b,proof,family,projection=package.binding(p/'evidence/input',pb,fb,mode);new=artifacts(projection);r=json.loads(new['validation-report.json']);base=load(p/'validation-report.json');comparison=dict(r);comparison.pop('selected_publication_ready');comparison.pop('selected_publication_readiness');assert comparison==base;assert r['selected_publication_ready']is False and r['selected_publication_readiness']['reasons']==['reader_has_no_qualified_readiness_evidence'];assert len(projection.rows)==count
  hashes={n:sha(v)for n,v in new.items()if n!='validation-report.json'}
  for n,v in hashes.items():assert sha((p/n).read_bytes())==v
  assert files(p)==before
  results[name]={'package':str(p.relative_to(B)),'source_package_manifest_sha256':sha((p/'run-manifest.json').read_bytes()),'proof_sha256':sha(pb),'family_report_sha256':sha(fb),'records':count,'selected_publication_ready':False,'reasons':r['selected_publication_readiness']['reasons'],'old_strict_report_unchanged':True,'all_other_data_artifacts_unchanged':hashes,'all_package_inputs_unchanged':True}
 result={'passed':True,'candidate_code':package.code(),'cases':results,'scope':'No readiness contract qualified for existing MC/EP HTML reader yet; positive family text/acquisition fields do not imply required nonimage PDF semantics or selected structure readiness. No source normalizer/native/image APIs/network.'};(HERE/'other-reader-comparison.json').write_bytes(encoded(result));print(json.dumps({'passed':True,'case_rows':{k:v['records']for k,v in results.items()},'selected_ready_both':False},indent=2))
if __name__=='__main__':
 with patch.object(socket,'socket',side_effect=AssertionError('Network forbidden')):main()
