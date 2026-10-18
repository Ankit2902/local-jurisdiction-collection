#!/usr/bin/env python3
"""Run exact retained verifier; retain bounded structural diff on actual cache failure."""
import argparse,hashlib,json,pathlib,sys,traceback,datetime
p=argparse.ArgumentParser();p.add_argument('--run',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();sys.dont_write_bytecode=True;run=a.run.resolve();sys.path.insert(0,str(run/'executed'));import verify
sha=lambda b:hashlib.sha256(b).hexdigest()
def scalar(v):
 if isinstance(v,str):return {'type':'str','length':len(v),'sha256':sha(v.encode())}
 if v is None or isinstance(v,(int,float,bool)):return v
 return {'type':type(v).__name__,'length':len(v)if hasattr(v,'__len__')else None}
def differences(x,y,path='',out=None):
 out=[]if out is None else out
 if len(out)>=100:return out
 if type(x)!=type(y):out.append({'path':path,'before':scalar(x),'after':scalar(y)});return out
 if isinstance(x,dict):
  for k in sorted(set(x)|set(y)):
   if k not in x or k not in y:out.append({'path':path+'/'+str(k),'missing_from':'stored'if k not in x else'recomputed'})
   else:differences(x[k],y[k],path+'/'+str(k),out)
 elif isinstance(x,list):
  if len(x)!=len(y):out.append({'path':path,'stored_length':len(x),'recomputed_length':len(y)})
  for i,(u,v)in enumerate(zip(x,y)):differences(u,v,path+'/'+str(i),out)
 elif x!=y:out.append({'path':path,'before':scalar(x),'after':scalar(y)})
 return out
state=json.loads((run/'checkpoint.json').read_text());report={'schema':1,'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'run_path_provenance':str(run),'executed_scripts':state['scripts'],'script_sha256':sha(pathlib.Path(__file__).read_bytes()),'readonly':True,'network':False,'pixel_operations':0}
assert all(sha((run/'executed'/n).read_bytes())==h for n,h in state['scripts'].items())
try:
 result=verify.verify(run);report.update(status='terminal_recomputed',requested_complete=result['requested_coverage_complete'],result=result)
except Exception as e:
 report.update(status='terminal_error',error=str(e),exception_type=type(e).__name__)
 tb=e.__traceback__
 while tb:
  f=tb.tb_frame
  if f.f_code.co_name=='validate_cached':
   local=f.f_locals;record=local.get('record');recomputed=local.get('recomputed')
   if record and recomputed is not None:report['failure_item']=record['item'];report['stored_source_sha256']=record.get('raw_sha256');report['record_differences']=differences(record['records'],recomputed);report['disposition_differences']=differences(record['dispositions'],local.get('disp'))
  tb=tb.tb_next
report['finished_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k not in ['result','executed_scripts']},ensure_ascii=False,indent=2));raise SystemExit(3 if report['status']=='terminal_error'or not report.get('requested_complete')else 0)
