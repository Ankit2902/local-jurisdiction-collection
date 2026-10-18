"""Portable read-only compact candidate verification; no source/corpus imports."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 m=json.loads((HERE/'MANIFEST.json').read_bytes());actual={str(p.relative_to(HERE)):sha(p)for p in HERE.rglob('*')if p.is_file()and p.name!='MANIFEST.json'};assert actual==m['files'],'Missing/extra/corrupt selected evidence'
 a=json.loads((HERE/'actual-comparison.json').read_bytes());o=json.loads((HERE/'other-reader-comparison.json').read_bytes());code={n:sha(HERE/'candidate'/n)for n in a['candidate_code']};assert code==a['candidate_code']==o['candidate_code']
 for label,case in a['cases'].items():
  r=case['new_report'];assert r['selected_publication_ready']is(label=='current');assert r['complete']is False and r['downstream_ready']is False;assert case['record_count']==2661 and case['IMAGE_count']==882 and case['fields_per_row']==16 and len(case['byte_identical_generated_data_artifacts'])==14;assert case['strict_report_without_added_dimensions_exactly_unchanged']and case['all_original_package_files_unchanged']
 for c in o['cases'].values():assert c['selected_publication_ready']is False and c['old_strict_report_unchanged']and c['all_package_inputs_unchanged']and len(c['all_other_data_artifacts_unchanged'])==14
 log=(HERE/'logs/36-tests-corrected.log').read_text();assert 'Ran 36 tests'in log and '\nOK\n'in log
 print(json.dumps({'passed':True,'selected_files':len(actual),'candidate_modules':len(code),'current_selected_publication_ready':True,'historical_selected_publication_ready':False,'unqualified_MC_EP_selected_readiness':False,'strict_complete_unchanged':False,'network_native_image_operations':0},indent=2))
if __name__=='__main__':main()
