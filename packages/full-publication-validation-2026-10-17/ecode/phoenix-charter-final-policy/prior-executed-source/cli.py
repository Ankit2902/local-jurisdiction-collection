"""python -m collectors.ecode.cli collect|verify --help"""
import argparse,json,sys
from .adapters import family_of
from .engine import collect,verify,adopt

def main():
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
 c=sub.add_parser('collect');c.add_argument('--url',required=True);c.add_argument('--out',required=True);c.add_argument('--family',choices=['auto','ecode360','municipal.codes'],default='auto');c.add_argument('--jurisdiction');c.add_argument('--state');c.add_argument('--publication');c.add_argument('--resume',action='store_true');c.add_argument('--subtree',action='store_true');c.add_argument('--max-items',type=int);c.add_argument('--gate-dir');c.add_argument('--adopt-from')
 v=sub.add_parser('verify');v.add_argument('--out',required=True)
 a=p.parse_args()
 try:
  if a.command=='collect':
   cfg={k:v for k,v in vars(a).items() if k not in ['command','out','resume','adopt_from']};cfg['family']=family_of(a.url) if a.family=='auto' else a.family
   if cfg['family']!=family_of(a.url):raise ValueError('Family/URL mismatch')
   if a.max_items is not None and a.max_items<0:raise ValueError('max-items must be nonnegative')
   if a.adopt_from and a.resume:raise ValueError('Use either --adopt-from or --resume')
   r=adopt(a.adopt_from,a.out,cfg) if a.adopt_from else collect(cfg,a.out,a.resume)
  else:r=verify(a.out)
  print(json.dumps(r,ensure_ascii=False,indent=2));return 0 if r.get('complete') else 2
 except Exception as e:print(json.dumps({'complete':False,'error':type(e).__name__,'message':str(e)}));return 1
if __name__=='__main__':sys.exit(main())
