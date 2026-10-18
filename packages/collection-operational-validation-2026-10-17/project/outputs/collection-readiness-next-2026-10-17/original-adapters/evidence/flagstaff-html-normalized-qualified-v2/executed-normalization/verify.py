"""Read-only full raw replay: source and normalized inputs never modified; scratch is temporary."""
import argparse,json,tempfile,sys
from pathlib import Path
from source_common import *
def verify(family,source,normalized):
 source=Path(source).resolve();normalized=Path(normalized).resolve();old=load(normalized/'summary.json')
 if family in ['king','king-word','flagstaff-html']:
  from publication_source_verify import validate
  source_receipt=validate(family,source)
 else:source_receipt={}
 for n,h in old['code_fingerprint'].items():
  if sha((Path(__file__).parent/n).read_bytes())!=h:raise ValueError('Normalization version mismatch: use exact executed parser or explicit new replay '+n)
 with tempfile.TemporaryDirectory(prefix='original-official-replay-') as tmp:
  fresh=Path(tmp)/'normalized'
  if family=='king-word':
   from king_word_import import run
   files=['records.jsonl','document-audits.json','relationships.json']
  elif family=='flagstaff-html':
   from flagstaff_html_normalize import run
   files=['records.jsonl','records.csv','document-audits.json','dependencies.json','source-inventory.json']
  elif family=='king':
   from king_normalize import run
   files=['records.jsonl','records.csv','document-audits.json','dependencies.json']
  else:
   from flagstaff_normalize import run
   files=['records.jsonl','records.csv','source-toc.json','toc-mapping.json','missing-toc.json','extra-headings.json','dependencies.json']
  result=run(source,fresh);mismatches=[name for name in files if not (normalized/name).is_file() or sha((normalized/name).read_bytes())!=sha((fresh/name).read_bytes())]
  if mismatches:raise ValueError('Full raw replay differs from normalized evidence: '+','.join(mismatches))
  result.update(full_raw_replay_equal=True,input_files_modified=False,**source_receipt)
  return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--family',choices=['king','king-word','flagstaff','flagstaff-html'],required=True);p.add_argument('--source',required=True);p.add_argument('--normalized',required=True);a=p.parse_args()
 try:r=verify(a.family,a.source,a.normalized);print(json.dumps(r,indent=2));sys.exit(0 if r['complete'] else 2)
 except Exception as e:print(json.dumps({'complete':False,'verified':False,'error':type(e).__name__,'message':str(e)}));sys.exit(1)
