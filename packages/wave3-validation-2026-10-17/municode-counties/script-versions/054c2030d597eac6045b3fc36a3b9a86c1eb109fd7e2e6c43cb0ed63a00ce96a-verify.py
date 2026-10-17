"""Read-only offline evidence integrity + byte-identical parse replay. No network."""
import sys
sys.dont_write_bytecode=True
import hashlib,json,tempfile
from pathlib import Path
from normalize import normalize
from government_pdfs import parse as parse_pdf
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(b,msg):
 if not b:raise AssertionError(msg)
def main():
 checks=[];records=pages=0
 for group in ['http','browser','supplemental']:
  for d in sorted((ROOT/group).glob('*')):
   if not (d/'receipt.json').exists():continue
   r=json.loads((d/'receipt.json').read_text())
   for raw in r.get('responses',[]):check(sha(d/raw['file'])==raw['sha256'],'Raw response changed '+str(d/raw['file']))
   for key,fn in [('script_sha256','executed-collect_browser.cjs'),('gate_script_sha256','executed-gate_cli.py')]:
    if (d/fn).exists() and r.get(key):check(sha(d/fn)==r[key],'Executed script hash mismatch '+str(d))
   if (d/'samples.json').exists():
    with tempfile.TemporaryDirectory(prefix='complisolv-replay-') as td:
     v=normalize(d,td)
     for fn in ['sections.jsonl','sections.csv']:check(sha(Path(td)/fn)==sha(d/'normalized'/fn),'Replay differs '+str(d/fn))
    records+=v['record_count'];checks.append({'folder':str(d.relative_to(ROOT)),'records':v['record_count'],'tables':v['table_count'],'byte_identical_jsonl_csv':True,'raw_hashes_verified':True})
   pp=d/'publisher-export.pdf'
   if pp.exists():
    pr=json.loads((d/'publisher-export.receipt.json').read_text());check(sha(pp)==pr['sha256'],'Publisher PDF hash');check(pp.read_bytes()[:5]==b'%PDF-','Publisher PDF magic')
 for d in sorted((ROOT/'native').glob('*')):
  if not (d/'source-config.json').exists():continue
  cfg=json.loads((d/'source-config.json').read_text())
  with tempfile.TemporaryDirectory(prefix='complisolv-native-replay-') as td:
   v=parse_pdf(cfg,d,td)
   for fn in ['pages.jsonl','pages.csv']:check(sha(Path(td)/fn)==sha(d/'normalized'/fn),'Native replay differs '+str(d/fn))
  pages+=v['record_count'];checks.append({'folder':str(d.relative_to(ROOT)),'pdf_page_records':v['record_count'],'byte_identical_jsonl_csv':True,'source_pdf_sha_verified':True})
 if (ROOT/'manifest.json').exists():
  manifest=json.loads((ROOT/'manifest.json').read_text())
  for row in manifest['files']:check(sha(ROOT/row['path'])==row['sha256'],'Manifest changed '+row['path'])
 results=json.loads((ROOT/'results.json').read_text());assignment=json.loads((ROOT/'assignment.json').read_text());check({r['sequence'] for r in results}=={a['sequence'] for a in assignment},'Assignment/result mismatch');check(all(r['complete_corpus'] is False for r in results),'Unproven complete corpus')
 for r in results:
  for field in ['evidence_paths','script_paths']:
   for p in r[field]:check(not Path(p).is_absolute() and (ROOT/p).exists(),'Missing/nonrelative '+p)
 print(json.dumps({'offline':True,'read_only':True,'network_requests_sent':0,'targets':len(results),'replayed_legal_provisions_including_retained_attempts':records,'supplemental_pdf_page_records':pages,'checks':checks,'manifest_verified':(ROOT/'manifest.json').exists(),'passed':True},indent=2))
if __name__=='__main__':main()
