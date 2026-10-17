#!/usr/bin/env python3
"""Safe portable plans and explicit single-publication dispatch; no collection by default."""
import sys
sys.dont_write_bytecode=True
import argparse,json,subprocess,tempfile
from pathlib import Path
from dispatch import ROOT,Unsupported,command,qualified,read,bind_run
from catalog import load_catalog
HERE=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',nargs='?',default='status',choices=['plan','status','collect','verify']);p.add_argument('--cohort',choices=['expansion','original','all'],default='all');p.add_argument('--target');p.add_argument('--publication');p.add_argument('--all',action='store_true');p.add_argument('--out');p.add_argument('--resume',action='store_true');p.add_argument('--upgrade-code',action='store_true');p.add_argument('--native-export',action='store_true');p.add_argument('--retry-native-export',action='store_true');p.add_argument('--max-items',type=int);p.add_argument('--python',default=sys.executable);a=p.parse_args()
 catalog=load_catalog(getattr(a,'cohort','all'));targets=catalog['targets'];pubs={x['id']:x for x in catalog['publications']};matches=[t for t in targets if not a.target or t['id']==a.target]
 if a.target and len(matches)!=1:p.error('Unknown target ID')
 if a.action in ['collect','verify'] and (not a.target or not a.out or a.all):p.error('Explicit single --target and --out required; no all-target execution is provided')
 if a.action=='plan' and not(a.target or a.all or a.publication):p.error('Plan requires --target or --all')
 if a.out:a.out=str(Path(a.out).resolve())
 selected=[]
 if a.publication:
  if a.publication not in pubs:p.error('Unknown publication ID')
  pub=pubs[a.publication];target=next(t for t in targets if t['id']==pub['target_id'])
  if a.target and target['id']!=a.target:p.error('Publication belongs to a different target')
  matches=[target]
 for t in matches:
  pub=pubs[a.publication or t['primary_publication_id']]
  try:
   plan=command(pub,t,a.out or ('{OUT}/'+pub['id']),a.python,a.resume,a.max_items,a.action=='verify',a.upgrade_code,a.native_export,a.retry_native_export);plan.update(target_id=t['id'],jurisdiction=t['jurisdiction'],state=t['state'],runnable=True)
  except Unsupported as e:plan={'target_id':t['id'],'publication_id':pub['id'],'runnable':False,'unsupported_reason':str(e)}
  plan['observed_access_advisories']=pub.get('observed_access_advisories',[])
  selected.append(plan)
 if a.action in ['status','plan']:
  print(json.dumps({'schema_version':1,'network_requests_sent':0,'action':a.action,'cohort':a.cohort,'targets':len(selected),'runnable_config_count':sum(x['runnable'] for x in selected),'plans':selected,'validation_note':'Mapped/runnable configuration is not a full live publication pass. Primary scope is not jurisdiction scope.'},indent=2));return
 plan=selected[0]
 if not plan['runnable']:raise SystemExit(json.dumps(plan))
 if a.action=='collect' and plan.get('observed_access_advisories'):p.error('Observed publisher workflow access stop requires operator review; no automatic retry. Planning and offline verification remain available. See observed_access_advisories in plan.')
 out=Path(a.out).resolve()
 if a.action=='verify':
  try:bind_run(pubs[a.publication or matches[0]['primary_publication_id']],matches[0],out)
  except (Unsupported,KeyError,ValueError,OSError) as exc:p.error(str(exc))
 if a.action=='collect' and not a.resume and out.exists() and any(out.iterdir()):p.error('Fresh output must be empty; --resume is explicit')
 argv=plan['argv']
 # Stage synthesized configs outside the fresh run directory. Adapter receives actual JSON data, never shell fragments.
 with tempfile.TemporaryDirectory(prefix='complisolv-registry-config-') as td:
  if plan['staged_config']:
   cfg=Path(td)/'publication.json';cfg.write_text(json.dumps(plan['staged_config'],indent=2));argv=[str(cfg) if x=='{CONFIG}' else x for x in argv]
  result=subprocess.run(argv,cwd=ROOT);raise SystemExit(result.returncode)
if __name__=='__main__':main()
