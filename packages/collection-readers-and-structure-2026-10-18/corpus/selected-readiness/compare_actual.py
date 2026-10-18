"""Read-only current/historical selected-publication projection differential."""
import argparse,hashlib,json,socket,sys
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE/'candidate'))
import package
from common import files,sha,encoded,artifacts,load
B=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00');P=B/'outputs/collection-readiness-next-2026-10-17/encodeplus/post-91f6c59'
DEFAULTS={'current':P/'corpus-package-current-live-flagstaff-v1/package','historical':P/'corpus-package-composed-flagstaff-bridge-v3/actual/flagstaff-composed-package-v3'}
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=HERE/'actual-comparison.json');args=parser.parse_args();result={'scope':'Actual full source-pinned existing IR projection, no original raw normalizer or family verifier rerun. Current and historical proofs remain immutable.','source_requests':0,'native_or_image_operations':0,'cases':{},'candidate_code':package.code()}
 for label,path in DEFAULTS.items():
  if not path.is_dir():raise ValueError('Missing existing whole actual package '+str(path))
  before=files(path);root=path/'evidence/input';pb=(path/'evidence/proofs/read-only-proof.json').read_bytes();fb=(path/'evidence/proofs/family-verification.json').read_bytes();binding,proof,family,p=package.binding(root,pb,fb,'originals-flagstaff-html-v1');generated=artifacts(p);base=load(path/'validation-report.json');new=json.loads(generated['validation-report.json']);remaining=dict(new);remaining.pop('selected_publication_ready');remaining.pop('selected_publication_readiness');assert remaining==base
  unchanged={n:sha(data)for n,data in generated.items()if n!='validation-report.json'}
  for n,h in unchanged.items():assert hashlib.sha256((path/n).read_bytes()).hexdigest()==h,n
  assert len(p.rows)==2661 and all(len(r)==16 for r in p.rows);assert sum(r['full_text'].count('[IMAGE]')for r in p.rows)==882;assert new['selected_publication_ready']is(label=='current');assert new['complete']is False and new['downstream_ready']is False
  assert files(path)==before
  result['cases'][label]={'original_package':str(path.relative_to(B)),'original_package_manifest_sha256':hashlib.sha256((path/'run-manifest.json').read_bytes()).hexdigest(),'input_file_count':len(binding['input_files']),'input_inventory_sha256':sha(encoded(binding['input_files'])),'proof_sha256':sha(pb),'family_report_sha256':sha(fb),'record_count':len(p.rows),'fields_per_row':16,'IMAGE_count':882,'byte_identical_generated_data_artifacts':unchanged,'new_report':new,'strict_report_without_added_dimensions_exactly_unchanged':True,'all_original_package_files_unchanged':True}
 assert package.code()==result['candidate_code'];args.out.write_bytes(encoded(result));print(json.dumps({'passed':True,'current_selected_publication_ready':result['cases']['current']['new_report']['selected_publication_ready'],'historical_selected_publication_ready':result['cases']['historical']['new_report']['selected_publication_ready'],'strict_complete_both':False,'data_artifacts_each_unchanged':14},indent=2))
if __name__=='__main__':
 with patch.object(socket,'socket',side_effect=AssertionError('Network forbidden')):main()
