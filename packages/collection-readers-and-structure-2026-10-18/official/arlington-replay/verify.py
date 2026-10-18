#!/usr/bin/env python3
"""Read-only compact replay proof binding; optional full-output byte hashes, no native parse."""
import argparse,json,pathlib,hashlib
P=pathlib.Path(__file__).resolve().parent
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();r=lambda p:json.loads(p.read_text())
def main():
 a=argparse.ArgumentParser();g=a.add_mutually_exclusive_group(required=True);g.add_argument('--receipts-only',action='store_true');g.add_argument('--full-output',type=pathlib.Path);args=a.parse_args()
 m=r(P/'MANIFEST.json')
 for n,s in m.items():
  rel=pathlib.Path(n);assert not rel.is_absolute()and'..'not in rel.parts;assert h(P/rel)==s,n
 receipt=r(P/'arlington-tx-current80-guarded-v1-replay-receipt.json');terminal=r(P/'arlington-tx-current80-guarded-v1-replay-terminal.json');before=r(P/'arlington-tx-current80-guarded-v1-before-readonly.json');summary=r(P/'SUMMARY.json');cov=r(P/'run-metadata/coverage.json')
 assert receipt['status']==terminal['observed_exit_code']==0 and receipt['error']is None and receipt['mode']=='replay'and receipt['forbidden_calls']==[]and receipt['network_requests']==receipt['image_bytes_read']==0
 assert terminal['receipt_sha256']==h(P/'arlington-tx-current80-guarded-v1-replay-receipt.json')and terminal['output_files']==len(before)==336 and terminal['output_sha256_manifest_sha256']==h(P/'arlington-tx-current80-guarded-v1-before-readonly.json')
 assert h(P/'executed/run_guarded.py')==receipt['guard_driver_sha256']=='11d61851c340cf8c1cb7d3fe18f0efa3673b01003390197eda065e1594545f5d'
 assert r(P/'executed/GUARDED-SOURCE-HASHES.json')==receipt['runtime_source_hashes']
 for n,s in receipt['runtime_source_hashes'].items():assert h(P/'executed'/n)==s
 for f in(P/'run-metadata').iterdir():assert before[f.name]==h(f)
 assert cov['requested_level']=='file_pages'and cov['requested_coverage_complete']and cov['publication_file_coverage_complete']and cov['pdf_page_extraction_complete']and cov['expected_document_count']==cov['acquired_document_count']==61 and cov['parsed_record_count']==9157 and cov['table_count']==691
 assert cov['legal_semantic_coverage_complete']is False and cov['jurisdiction_complete']is False and cov['manual_review_required']is True
 assert len(cov['pdf_files'])==61 and sum(x['expected_pages']for x in cov['pdf_files'].values())==9157
 for v in cov['pdf_files'].values():assert v['acquired_page_ids']==list(range(1,v['expected_pages']+1))and not v['page_gaps']and v['duplicates']==0
 assert summary['counts']=={'pages':9157,'tables':691,'cells':28297,'agree_cells':26458,'image_placeholders':46451}
 assert summary['coverage_flags']['legal_semantic_coverage_complete']is False and r(P/'PROVENANCE.json')['separate_readonly_pending']is True
 checked=0
 if args.full_output:
  tree=args.full_output.resolve();actual={}
  for f in tree.rglob('*'):
   assert not f.is_symlink()
   if f.is_file():actual[f.relative_to(tree).as_posix()]=h(f)
  assert actual==before,'Full output bytes/file set changed';checked=len(actual)
 print(json.dumps({'passed':True,'packet_files':len(m),'full_output_files_byte_verified':checked,'source_semantic_coverage_complete':False,'file_page_request_complete':True,'physical_pages':9157,'native_parse_performed':False,'new_readonly_parser_result_credited':False,'scope':'Replay terminal and exact executed sources; full bytes checked only when supplied. Separate strict parser verification remains pending in this immutable packet.'}))
if __name__=='__main__':main()
