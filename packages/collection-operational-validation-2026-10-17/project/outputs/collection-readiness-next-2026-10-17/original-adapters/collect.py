"""Standalone full-publication entry point; exact-version durable resume, no automatic access retries."""
import argparse,json,sys
from pathlib import Path
from source_common import *
from publication_source_verify import validate
def main(target,out,resume=False):
 out=Path(out).resolve();root=Path(__file__).parent
 from doctor import run as preflight
 readiness=preflight(target)
 if not readiness['ready_to_attempt_collection']:raise ValueError('Read-only preflight blocked collection before transport/browser startup: '+json.dumps(readiness))
 versions={p.name:sha(p.read_bytes()) for p in root.iterdir() if p.is_file() and (p.suffix=='.py' or p.name in ['configs.json','source_dispositions.json','source_character_dispositions.json','requirements.txt'])}
 if resume:
  marker=load(out/'collection-start.json')
  if marker['target']!=target or marker['code_fingerprint']!=versions:raise ValueError('Target or collector revision drift. Resume with exact executed revision; no automatic version migration.')
 else:
  if out.exists() and any(out.iterdir()):raise ValueError('Fresh output required unless explicit --resume')
  out.mkdir(parents=True,exist_ok=True);save(out/'collection-start.json',{'target':target,'started_at':stamp(),'code_fingerprint':versions})
  source_snapshot(out,list(versions))
 def normalized(family,source,destination,run):
  if destination.exists() and any(destination.iterdir()):
   from verify import verify
   return verify(family,source,destination)
  return run(source,destination)
 if target=='original-king-county-wa':
  from king_acquire import collect
  from king_native import run as native
  from king_normalize import run as normalize
  from king_native_audit import run as parity
  a=collect(out/'html-source',resume=resume and (out/'html-source/checkpoint.json').is_file())
  if a['errors']:return {'complete':False,'stage':'html-acquisition','errors':a['errors']}
  b=native(out/'html-source',out/'native-source',resume=resume and (out/'native-source/checkpoint.json').is_file())
  if b['errors']:return {'complete':False,'stage':'native-acquisition','errors':b['errors']}
  from king_word_import import run as word_import
  validate('king',out/'html-source');validate('king-word',out/'native-source')
  word=normalized('king-word',out/'native-source',out/'native-normalized',word_import)
  n=normalized('king',out/'html-source',out/'normalized',normalize);q=parity(out/'html-source',out/'native-source');save(out/'native-parity.json',q)
  n.update(raw_w_t_diagnostic=q['complete'],raw_w_t_diagnostic_scope='Supplemental literal XML/HTML string diagnostic; layout, symbols and notes differ between formats. Not a semantic completeness gate.',native_word_complete=word['complete'],complete=n['complete'] and word['complete']);save(out/'collection-result.json',n);return n
 from flagstaff_html import collect as run
 from flagstaff_html_normalize import run as normalize
 a=run(out/'source',resume=resume and (out/'source/checkpoint.json').is_file())
 if a.get('errors') or a.get('blocked'):return {'complete':False,'stage':'full-html-acquisition','errors':[a.get('errors'),a.get('blocked')]}
 validate('flagstaff-html',out/'source')
 n=normalized('flagstaff-html',out/'source',out/'normalized',normalize);save(out/'collection-result.json',n);return n
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--target',choices=['original-flagstaff-az','original-king-county-wa'],required=True);p.add_argument('--out',required=True);p.add_argument('--resume',action='store_true');a=p.parse_args()
 try:r=main(a.target,a.out,a.resume);print(json.dumps(r,indent=2));sys.exit(0 if r['complete'] else 2)
 except Exception as e:print(json.dumps({'complete':False,'error':type(e).__name__,'message':str(e)}));sys.exit(1)
