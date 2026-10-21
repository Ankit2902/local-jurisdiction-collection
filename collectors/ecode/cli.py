"""python -m collectors.ecode.cli collect|verify --help"""
import sys
from pathlib import Path
_root = Path(__file__).resolve().parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
from collectors.winboot import boot, ensure_fcntl
if __name__ == '__main__':
    boot('collectors.ecode.cli')
else:
    ensure_fcntl()
import argparse,json
from .adapters import family_of
from .common import read
from pathlib import Path
from .engine import collect,verify,adopt

def main():
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
 c=sub.add_parser('collect');c.add_argument('--url',required=True);c.add_argument('--out',required=True);c.add_argument('--family',choices=['auto','ecode360','municipal.codes'],default='auto');c.add_argument('--jurisdiction');c.add_argument('--state');c.add_argument('--publication');c.add_argument('--resume',action='store_true');c.add_argument('--subtree',action='store_true');c.add_argument('--max-items',type=int);c.add_argument('--gate-dir');c.add_argument('--adopt-from')
 r=sub.add_parser('replay');r.add_argument('--source',required=True);r.add_argument('--out',required=True)
 v=sub.add_parser('verify');v.add_argument('--out',required=True)
 d=sub.add_parser('doctor');d.add_argument('--url',required=True);d.add_argument('--source');d.add_argument('--gate-dir')
 e=sub.add_parser('export-plan');e.add_argument('--source',required=True);e.add_argument('--out',required=True)
 b=sub.add_parser('import-bundle');b.add_argument('--source');b.add_argument('--manifest',required=True);b.add_argument('--out',required=True)
 i=sub.add_parser('inspect-download');i.add_argument('--file',required=True);i.add_argument('--witness',required=True);i.add_argument('--source-url',required=True);i.add_argument('--publication');i.add_argument('--identity-term',action='append');i.add_argument('--out',required=True)
 a=p.parse_args()
 try:
  if a.command=='collect':
   cfg={k:v for k,v in vars(a).items() if k not in ['command','out','resume','adopt_from']};cfg['family']=family_of(a.url) if a.family=='auto' else a.family
   if cfg['family']!=family_of(a.url):raise ValueError('Family/URL mismatch')
   if a.max_items is not None and a.max_items<0:raise ValueError('max-items must be nonnegative')
   if a.adopt_from and a.resume:raise ValueError('Use either --adopt-from or --resume')
   r=adopt(a.adopt_from,a.out,cfg) if a.adopt_from else collect(cfg,a.out,a.resume)
  elif a.command=='replay':r=adopt(a.source,a.out,read(Path(a.source)/'checkpoint.json')['config'],True)
  elif a.command=='verify':r=verify(a.out)
  else:
   from .operator import doctor,export_plan,import_bundle,inspect_download
   if a.command=='doctor':r=doctor(a.url,a.source,a.gate_dir)
   elif a.command=='export-plan':r=export_plan(a.source,a.out)
   elif a.command=='import-bundle':r=import_bundle(a.source,a.manifest,a.out)
   else:r=inspect_download(a.file,a.witness,a.source_url,a.out,a.publication,a.identity_term)
  print(json.dumps(r,ensure_ascii=False,indent=2))
  if a.command=='doctor':return 0 if r['ready'] else 2
  if a.command=='export-plan':return 0
  if a.command=='inspect-download':return 0 if r.get('native_file_qualified') else 1
  return 0 if r.get('complete') else 2
 except Exception as e:
  result={'complete':False,'error':type(e).__name__,'message':str(e)}
  if isinstance(e,__import__('collectors.ecode.common',fromlist=['AccessStop']).AccessStop):result['operator_action']='Access stop retained. Do not retry, clear the gate, or change routes. Run doctor and export-plan for offline genuine publisher file recovery; no credentials are accepted by this collector.'
  print(json.dumps(result));return 1
if __name__=='__main__':sys.exit(main())
