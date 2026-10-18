#!/usr/bin/env python3
"""Portable stdlib completion receipt/byte binding. Does not parse PDFs or call images/network."""
import argparse,hashlib,json,pathlib
P=pathlib.Path(__file__).resolve().parent
h=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();r=lambda q:json.loads(q.read_text())
def check_manifest(root):
 m=r(root/'MANIFEST.json')
 for name,sha in m.items():
  rel=pathlib.Path(name);assert not rel.is_absolute()and'..'not in rel.parts;assert h(root/rel)==sha,name
 return m
def main():
 p=argparse.ArgumentParser();p.add_argument('--replay-proof',required=True,type=pathlib.Path);p.add_argument('--full-output',type=pathlib.Path);a=p.parse_args();check_manifest(P);R=a.replay_proof.resolve();assert h(R/'MANIFEST.json')=='ae80cea53634c0fd7281c9bc43c8b43b1c1536d500ad6d88f8f500f0642667f7';check_manifest(R)
 rec=r(P/'arlington-tx-current80-guarded-v1-verify-receipt.json');term=r(P/'arlington-tx-current80-guarded-v1-verify-terminal.json');before=r(R/'arlington-tx-current80-guarded-v1-before-readonly.json');after=r(P/'arlington-tx-current80-guarded-v1-after-readonly.json');first=r(R/'arlington-tx-current80-guarded-v1-replay-receipt.json');summary=r(P/'SUMMARY.json');cov=r(R/'run-metadata/coverage.json')
 assert rec['mode']=='verify'and rec['status']==term['observed_exit_code']==term['status']==0 and rec['error']is None and not rec['forbidden_calls']and rec['network_requests']==rec['image_bytes_read']==0
 assert term['driver_receipt_sha256']==h(P/'arlington-tx-current80-guarded-v1-verify-receipt.json')
 assert rec['guard_driver_sha256']==first['guard_driver_sha256']==h(R/'executed/run_guarded.py')=='11d61851c340cf8c1cb7d3fe18f0efa3673b01003390197eda065e1594545f5d'
 assert rec['runtime_source_hashes']==first['runtime_source_hashes']
 for n,s in rec['runtime_source_hashes'].items():assert h(R/'executed'/n)==s
 assert before==after and len(after)==term['full_output_files_unchanged']==336 and term['actual_before_after_files_equal']is True
 assert h(P/'arlington-tx-current80-guarded-v1-after-readonly.json')==term['after_sha256_manifest']==term['before_sha256_manifest']=='d8244d4ad023155822f31a132daa0e5cab08c4076d30c7c0bc60628eb3b5f1bd'
 assert cov['requested_coverage_complete']and cov['requested_level']=='file_pages'and cov['expected_document_count']==cov['acquired_document_count']==61 and cov['parsed_record_count']==9157
 assert cov['legal_semantic_coverage_complete']is False and cov['jurisdiction_complete']is False and cov['manual_review_required']is True
 assert summary['observed_exit']==0 and summary['full_output_files_unchanged']==336 and summary['legal_semantic_coverage_complete']is False and summary['measured_normalization']['qualified_comparison_gap_page_union']==187
 checked=0
 if a.full_output:
  actual={}
  for q in a.full_output.resolve().rglob('*'):
   assert not q.is_symlink()
   if q.is_file():actual[q.relative_to(a.full_output.resolve()).as_posix()]=h(q)
  assert actual==after,'External full output changed';checked=len(actual)
 print(json.dumps({'passed':True,'replay_manifest_sha256':h(R/'MANIFEST.json'),'separate_strict_readonly_exit':0,'captured_runtime':'current80/PDF6ed','actual_observer_before_after_files_equal':336,'external_full_output_files_checked_now':checked,'selected_files':61,'physical_pages':9157,'qualified_comparison_gap_pages':187,'legal_semantic_coverage_complete':False,'forbidden_calls':[],'native_parse_performed_by_this_verifier':False,'separate_strict_source_parser_receipt_credited':True,'scope':'Portable retained terminal/code/hash proof; current source or external bytes are not inferred unless explicitly supplied.'}))
if __name__=='__main__':main()
