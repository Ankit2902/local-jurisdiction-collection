"""Serial full-publication readiness jobs. Source-bound resume/revision reuse; never sample fallback."""
import sys
sys.dont_write_bytecode=True
import argparse,hashlib,json,os,re,subprocess,time,fcntl
from pathlib import Path
from model import atomic,implementation,read_response
from runtime import check
from collect import load_policy
HERE=Path(__file__).resolve().parent
def load(path):
 d=json.loads(path.read_text());rows=d.get('publications',d.get('targets',[])) if isinstance(d,dict) else d;out=[]
 for source in rows:
  if source.get('publisher')!='municode' or source.get('runnable') is False:continue
  row=dict(source)
  if 'primary_publication' in row:row.update(publisher_product_id=row['primary_publication'].get('publisher_product_id'),role='primary',target_id=str(row['id']),id=str(row['id'])+'-primary')
  if not row.get('publisher_product_id'):raise ValueError('No source-qualified productID '+str(row.get('id')))
  row={k:row.get(k) for k in ['id','target_id','role','source_url','publisher_product_id','title']};row['expected_identity']={k:source['expected_identity'].get(k) for k in ['client_names','state','publisher_client_id']};out.append(row)
 return out
def verify(out,report):
 cmd=[sys.executable,'-B',str(HERE/'verify.py'),str(out),'--offline'];r=subprocess.run(cmd,capture_output=True,text=True);atomic(report,{'command':cmd,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr});return r.returncode==0
def reuse(row,old,previous,out):
 run=(previous.parent/old['run_path']).resolve();cp=json.loads((run/'checkpoint.json').read_text());identity=row['expected_identity'];pid=str(row['publisher_product_id'])
 if cp.get('evidence_kind')!='live' or cp['source_url']!=row['source_url'] or set(cp['publications'])!={pid}:return None
 expected_policy=load_policy([int(pid)],HERE/'policies/henderson-14896.json' if pid=='14896' else None)
 if cp['binding'].get('reference_policy',{})!=expected_policy:return None
 pub=cp['publications'][pid];product=read_response(run,cp['units'][pub['product_unit']])['Model'];client=product['Client']
 if client['ClientName'] not in identity['client_names'] or client['State']['StateAbbreviation']!=identity['state'] or (identity.get('publisher_client_id') is not None and client['ClientID']!=identity['publisher_client_id']):return None
 if not verify(run,out/'verification'/(row['id']+'-prior.json')):return None
 result=dict(old);result.update(run_path=os.path.relpath(run,out),status='complete',full_publication_live_verified=True,evidence_origin='earlier-readiness-batch-live-proof-with-current-read-only-verification',reused_from=os.path.relpath(previous,out));return result
def policy_hashes():return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((HERE/'policies').glob('*.json'))}
def execute(a,runtime,rows):
 binding={'configs':rows,'implementation':implementation(),'policy_hashes':policy_hashes(),'batch_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()};index=a.out/'status.json'
 if index.exists():
  if not a.resume:raise ValueError('Existing batch requires --resume')
  status=json.loads(index.read_text())
  if status['binding']!=binding:raise ValueError('Batch configuration/revision mismatch; use fresh output plus --previous-batch to independently reverify earlier full proofs')
 else:
  if any(p.name!='.batch.lock' for p in a.out.iterdir()):raise ValueError('Fresh batch requires empty output')
  status={'schema_version':1,'binding':binding,'runtime':runtime,'phase':'running','jobs':{r['id']:{'status':'pending','publication_id':r['id'],'target_id':r.get('target_id'),'product_id':r['publisher_product_id'],'role':r.get('role'),'source_url':r['source_url'],'run_path':'runs/'+r['id'],'full_publication_live_verified':False} for r in rows}}
  for previous in a.previous_batch:
   old=json.loads(previous.read_text())
   for row in rows:
    prior=old['jobs'].get(row['id']);job=status['jobs'][row['id']]
    if not prior or prior['status'] not in ['complete','incomplete']:continue
    if prior['status']=='complete':
     try:accepted=reuse(row,prior,previous,a.out)
     except Exception:accepted=None
     if accepted:status['jobs'][row['id']]=accepted
    elif not a.retry_incomplete and row['id'] not in a.retry_publication:
     result=dict(prior);result.update(run_path=os.path.relpath((previous.parent/prior['run_path']).resolve(),a.out),full_publication_live_verified=False,evidence_origin='earlier-readiness-batch-incomplete-attempt');status['jobs'][row['id']]=result
    else:job['prior_attempts']=[{'run_path':os.path.relpath((previous.parent/prior['run_path']).resolve(),a.out),'status':prior['status']}]
  atomic(a.out/'executed-batch'/binding['batch_sha256']/'batch.py',Path(__file__).read_bytes());atomic(index,status)
 gate=Path(os.environ.get('MUNICODE_GATE_DIR','/tmp/compliSolv-municode-rate-gate'))
 for row in rows:
  if implementation()!=binding['implementation'] or policy_hashes()!=binding['policy_hashes']:status['phase']='implementation_changed';atomic(index,status);break
  job=status['jobs'][row['id']]
  if job['status']=='complete' or (job['status']=='incomplete' and not a.retry_incomplete and row['id'] not in a.retry_publication):continue
  if (gate/'browser-stop.json').exists():status['phase']='access_stopped';atomic(index,status);break
  out=a.out/job['run_path'];identity=row['expected_identity'];cmd=[sys.executable,'-B',str(HERE/'collect.py'),'--url',row['source_url'],'--state',identity['state'],'--product-id',str(row['publisher_product_id']),'--out',str(out)]
  for name in identity['client_names']:cmd+=['--client-name',name]
  if identity.get('publisher_client_id') is not None:cmd+=['--client-id',str(identity['publisher_client_id'])]
  if row['publisher_product_id']==14896:cmd+=['--reference-policy',str(HERE/'policies/henderson-14896.json')]
  if (out/'checkpoint.json').exists():cmd+=['--resume']
  job.update(status='running',started_at=time.time(),command=cmd,evidence_origin='fresh-live-publication-wide-acquisition');atomic(index,status);out.parent.mkdir(parents=True,exist_ok=True);log=a.out/'logs';log.mkdir(exist_ok=True)
  with (log/(row['id']+'.stdout')).open('w') as stdout,(log/(row['id']+'.stderr')).open('w') as stderr:r=subprocess.run(cmd,stdout=stdout,stderr=stderr)
  job.update(exit_code=r.returncode,finished_at=time.time());coverage=out/'coverage.json'
  if coverage.exists():job['coverage']=json.loads(coverage.read_text())
  verified=verify(out,a.out/'verification'/(row['id']+'.json'));job['verification_exit_code']=0 if verified else 2;job['full_publication_live_verified']=bool(r.returncode==0 and verified and job.get('coverage',{}).get('publication_complete'));job['status']='complete' if job['full_publication_live_verified'] else 'incomplete';atomic(index,status);print(json.dumps({k:job[k] for k in ['publication_id','status','exit_code','verification_exit_code']}),flush=True)
  if (gate/'browser-stop.json').exists():status['phase']='access_stopped';atomic(index,status);break
 else:status['phase']='finished'
 status['counts']={name:sum(j['status']==name for j in status['jobs'].values()) for name in ['pending','running','complete','incomplete']};atomic(index,status);print(json.dumps(status['counts'],indent=2));return 0 if status['counts']['complete']==len(rows) else 2
def main():
 p=argparse.ArgumentParser();p.add_argument('--registry',type=Path,required=True);p.add_argument('--additional-registry',action='append',type=Path,default=[]);p.add_argument('--out',type=Path,required=True);p.add_argument('--scope',choices=['all','primary','secondary'],default='all');p.add_argument('--publication',action='append');p.add_argument('--prioritize',action='append',default=[]);p.add_argument('--previous-batch',action='append',type=Path,default=[]);p.add_argument('--retry-publication',action='append',default=[]);p.add_argument('--resume',action='store_true');p.add_argument('--retry-incomplete',action='store_true');a=p.parse_args();runtime=check()
 if not runtime['passed']:raise ValueError('Runtime preflight: '+ '; '.join(runtime['errors']))
 rows=[]
 for registry in [a.registry]+a.additional_registry:rows+=load(registry)
 rows=[r for r in rows if (a.scope=='all' or r.get('role')==a.scope) and (not a.publication or r['id'] in a.publication)];rows.sort(key=lambda r:a.prioritize.index(r['id']) if r['id'] in a.prioritize else len(a.prioritize));ids=[r['id'] for r in rows]
 if not rows or len(set(ids))!=len(ids) or any(not re.fullmatch(r'[\w-]+',ident) for ident in ids):raise ValueError('Empty/duplicate/unsafe publication config IDs')
 a.out.mkdir(parents=True,exist_ok=True)
 with (a.out/'.batch.lock').open('a+') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);return execute(a,runtime,rows)
if __name__=='__main__':
 try:raise SystemExit(main())
 except Exception as e:print(str(e),file=sys.stderr);raise SystemExit(2)
