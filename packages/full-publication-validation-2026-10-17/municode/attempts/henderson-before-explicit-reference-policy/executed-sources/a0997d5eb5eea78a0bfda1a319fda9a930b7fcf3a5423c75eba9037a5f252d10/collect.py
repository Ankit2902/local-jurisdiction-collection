"""Full-publication Municode collector. Default unbounded, ordinary headed browser; no direct HTTP."""
import sys
sys.dont_write_bytecode=True
import argparse,base64,json,os,subprocess,uuid,time
from pathlib import Path
from urllib.parse import urlencode,urlparse
from model import atomic,sha,digest,canonical,implementation,flatten,read_response,reconcile_publication,write_outputs
HERE=Path(__file__).resolve().parent
class Browser:
 def __init__(self,url,out):
  self.process=subprocess.Popen([os.environ.get('NODE','node'),str(HERE/'browser.cjs'),url],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=None,text=True,bufsize=1);self.counter=0
  line=self.process.stdout.readline()
  if not line:raise RuntimeError('Browser transport did not start; check Node/Playwright/Chrome')
  self.ready=json.loads(line);atomic(out/'sessions'/(uuid.uuid4().hex+'.json'),self.ready)
  if not self.ready.get('ready'):self.close();raise RuntimeError('Browser access failed: '+str(self.ready))
 def request(self,url,binary=False):
  self.counter+=1;self.process.stdin.write(json.dumps({'id':self.counter,'url':url,'binary':binary,'allowed_hosts':getattr(self,'allowed_hosts',[])})+'\n');self.process.stdin.flush();line=self.process.stdout.readline()
  if not line:raise RuntimeError('Browser transport interrupted')
  r=json.loads(line)
  if r.get('error'):raise RuntimeError(r['error'])
  return r
 def close(self):
  if self.process.poll() is None:
   try:self.process.stdin.write('{"close":true}\n');self.process.stdin.flush();self.process.wait(timeout=30)
   except Exception:self.process.terminate();self.process.wait(timeout=30)
def api(path,**params):return 'https://library.municode.com/api/'+path+('?' +urlencode(params,doseq=True) if params else '')
def target_config(args):
 if args.registry:
  data=json.loads(args.registry.read_text());rows=data.get('targets',data) if isinstance(data,dict) else data;matches=[r for r in rows if str(r.get('id',r.get('sequence')))==str(args.target)]
  if len(matches)!=1:raise ValueError('Expected one registry target ID')
  row=matches[0]
  if row.get('publisher')!='municode':raise ValueError('Registry target publisher is not municode')
  identity=row['expected_identity'];return {'source_url':row['source_url'],'client_names':identity['client_names'],'state':identity['state'],'target_id':str(args.target),'jurisdiction':row['jurisdiction'],'expected_client_id':identity.get('publisher_client_id')}
 if not(args.url and args.client_name and args.state):raise ValueError('Use --registry/--target or --url/--state/--client-name')
 return {'source_url':args.url,'client_names':args.client_name,'state':args.state.upper(),'jurisdiction':args.client_name[0],'target_id':None,'expected_client_id':args.client_id}
class Run:
 def __init__(self,args):
  self.a=args;self.out=args.out.resolve();config=target_config(args);self.browser=None;self.calls=0
  self.binding={**config,'product_ids':sorted(args.product_id or []),'implementation':implementation()};self.cp_path=self.out/'checkpoint.json'
  if args.resume:
   if not self.cp_path.exists():raise ValueError('Resume requires an existing checkpoint')
   self.cp=json.loads(self.cp_path.read_text())
   if self.cp['binding']!=self.binding:raise ValueError('Resume source/configuration/implementation mismatch')
   if self.cp.get('limit')!=args.max_items:raise ValueError('Resume limit mismatch; use same explicit limit')
   self.validate_committed()
  else:
   if self.out.exists() and any(p.name!='.run.lock' for p in self.out.iterdir()):raise ValueError('Fresh collection requires empty output directory; use --resume explicitly')
   self.out.mkdir(parents=True,exist_ok=True);self.cp={'schema_version':1,'evidence_kind':'live','binding':self.binding,'source_url':config['source_url'],'expected_identity':{'client_names':config['client_names'],'state':config['state']},'units':{},'responses':[],'publications':{},'assets':{},'phase':'initializing','limit':args.max_items,'errors':[]};self.save()
  for name,data in self.binding['implementation'].items():
   dst=self.out/'executed-sources'/data/name
   if dst.exists() and sha(dst.read_bytes())!=data:raise ValueError('Corrupt executed source snapshot')
   if not dst.exists():atomic(dst,(HERE/name).read_bytes())
 def save(self):atomic(self.cp_path,self.cp)
 def validate_committed(self):
  for name,entry in self.cp['units'].items():
   receipt=json.loads((self.out/entry['receipt']).read_text());body=(self.out/receipt['body_file']).read_bytes()
   if sha(body)!=entry['sha256'] or receipt['sha256']!=entry['sha256'] or receipt['request']!=entry['request']:raise ValueError('Corrupt/mismatched committed cache '+name)
 def fetch(self,name,url,binary=False,cache=False):
  if cache and name in self.cp['units']:
   if self.cp['units'][name]['request']!={'url':url,'binary':binary}:raise ValueError('Cache request identity mismatch '+name)
   return read_response(self.out,self.cp['units'][name]) if not binary else None
  request={'url':url,'binary':binary};r=self.browser.request(url,binary);response=r['response'];body=base64.b64decode(response.pop('body'));ident=uuid.uuid4().hex;body_file='raw/'+ident+'.body';receipt_file='raw/'+ident+'.json';atomic(self.out/body_file,body);receipt={'request':request,'url':response['url'],'status':response['status'],'headers':response['headers'],'redirect_hops':response.get('redirect_hops',[]),'body_file':body_file,'sha256':sha(body),'bytes':len(body),'retrieved_at':time.time(),'access_stop':r.get('access_stop')};atomic(self.out/receipt_file,receipt);entry={'request':request,'receipt':receipt_file,'sha256':sha(body)};self.cp['responses'].append(entry)
  if response['status']==200 and not r.get('access_stop'):self.cp['units'][name]=entry
  self.save()
  if response['status']!=200 or r.get('access_stop'):raise RuntimeError('Retained HTTP access/error response '+str(response['status'])+' '+url)
  return None if binary else json.loads(body)
 def signature(self,inventory,product,job,toc):return digest({'inventory':inventory,'product':product,'job':job,'toc':toc})
 def execute(self):
  self.browser=Browser(self.cp['source_url'],self.out);base=getattr(self.browser,'ready',{}).get('runtime',{}).get('document_base_url',self.cp['source_url'])
  if self.cp.get('document_base_url',base)!=base:raise ValueError('Resume document base context changed')
  self.cp['document_base_url']=base;self.browser.allowed_hosts=self.a.allow_asset_host;retried_assets=set()
  try:
   parts=urlparse(self.cp['source_url']).path.split('/');org=self.fetch('org-start','https://library.municode.com/localapi/Organizations/GetByUrlEncodedNames/'+parts[1]+'/'+parts[2]);expected=self.cp['expected_identity']
   if org.get('ClientName') not in expected['client_names'] or org.get('State',{}).get('StateAbbreviation')!=expected['state']:raise ValueError('Organization jurisdiction mismatch')
   cid=org['ClientID']
   if self.binding.get('expected_client_id') is not None and int(cid)!=int(self.binding['expected_client_id']):raise ValueError('Registry publisher client ID mismatch')
   if self.cp.get('client_id',cid)!=cid:raise ValueError('Resume client mismatch')
   self.cp['client_id']=cid;cc=self.fetch('inventory-start',api('ClientContent/'+str(cid)));visible=[p for p in cc.get('codes',[]) if not p.get('hideInLibrary') and p.get('contentTypeId')=='CODES'];selected=[p for p in visible if not self.a.product_id or p['productId'] in self.a.product_id]
   if not selected or (self.a.product_id and set(self.a.product_id)!={p['productId'] for p in selected}):raise ValueError('Requested product is not a visible client publication')
   if self.cp.get('inventory_hash') and self.cp['inventory_hash']!=digest(cc):raise ValueError('Resume visible-publication inventory drift')
   self.cp['inventory_hash']=digest(cc);self.cp['visible_publications']=visible;self.cp['phase']='collecting';self.save()
   for publication in selected:
    pid=str(publication['productId']);product_unit='product-start:'+pid;job_unit='job-start:'+pid;toc_unit='toc-start:'+pid;product=self.fetch(product_unit,api('Products/name',clientId=cid,productName=publication['productName']));model=product.get('Model')
    if not model or model['ProductID']!=int(pid) or model['Client']['ClientID']!=cid or model.get('ExternalCodeLink'):raise ValueError('Publication identity/migration mismatch '+pid)
    job=self.fetch(job_unit,api('Jobs/latest/'+pid));toc=self.fetch(toc_unit,api('codesToc/fullTree',productId=pid,jobId=job['Id'],nodeId=pid));flatten(toc)
    if job['ProductId']!=int(pid):raise ValueError('Job product mismatch')
    pin={'job_id':job['Id'],'toc_hash':digest(toc),'start_signature':self.signature(cc,product,job,toc)}
    if pid in self.cp['publications'] and any(self.cp['publications'][pid][k]!=v for k,v in pin.items()):raise ValueError('Resume edition/inventory drift '+pid)
    if pid not in self.cp['publications']:self.cp['publications'][pid]={**pin,'product_unit':product_unit,'job_unit':job_unit,'toc_unit':toc_unit,'content_units':[]}
    pub=self.cp['publications'][pid];self.save();landing_name='landing:'+pid
    self.fetch(landing_name,api('CodesContent',productId=pid,jobId=job['Id'],nodeId=pid,groupChunks='false'),cache=True);pub['root_landing_unit']=landing_name;self.save()
    # Publisher Print endpoint expands selected container roots into their owned chunks and descendants.
    content_name='content-root:'+pid
    if content_name not in pub['content_units']:
     if self.a.max_items is not None and self.calls>=self.a.max_items:break
     self.fetch(content_name,api('CodesContent/docIds',productId=pid,jobId=job['Id'],docIds=pid,showChanges='false'),cache=True);pub['content_units'].append(content_name);self.calls+=1;self.save()
    records,report=reconcile_publication(self.out,self.cp,pid)
    # Fail closed on unexpected/duplicate ownership. Recover actual omissions in conservative batches.
    if report['duplicate_ids'] or report['extra_ids'] or report['errors']:raise ValueError('Bulk response ownership mismatch: '+str(report['errors'] or report['duplicate_ids'] or report['extra_ids']))
    missing=report['missing_ids']
    for offset in range(0,len(missing),self.a.batch_size):
     if self.a.max_items is not None and self.calls>=self.a.max_items:break
     ids=missing[offset:offset+self.a.batch_size];name='content-batch:'+pid+':'+digest(ids)
     if name not in pub['content_units']:
      self.fetch(name,api('CodesContent/docIds',productId=pid,jobId=job['Id'],docIds=ids,showChanges='false'),cache=True);pub['content_units'].append(name);self.calls+=1;self.save()
    while True:
     records,report=reconcile_publication(self.out,self.cp,pid)
     pending_assets=[a for a in report['asset_ledger'] if a['asset_id'] not in self.cp['assets'] or (getattr(self.a,'retry_assets',False) and a['status']!='acquired' and a['asset_id'] not in retried_assets)]
     if not pending_assets:break
     for asset in pending_assets:
      aid=asset['asset_id'];url=asset['url']
      retry=aid in self.cp['assets'];retried_assets.add(aid)
      if retry:self.cp.setdefault('asset_retry_history',[]).append({'asset_id':aid,'previous':self.cp['assets'][aid]})
      host=urlparse(url).hostname or ''
      if host not in self.a.allow_asset_host and not(host.endswith('.municode.com') or host=='library.municode.com' or host=='mcclibrary.blob.core.usgovcloudapi.net'):
       self.cp['assets'][aid]={'status':'external_required_pending','reason':'Required external asset host not explicitly allowed'};self.save();continue
      name='asset:'+aid
      try:self.fetch(name,url,binary=True,cache=not retry);self.cp['assets'][aid]={'unit':name}
      except Exception as e:self.cp['assets'][aid]={'status':'failed','reason':str(e)};self.save();raise
      self.save()
   end_cc=self.fetch('inventory-end',api('ClientContent/'+str(cid)))
   for pid,pub in self.cp['publications'].items():
    publication=next(p for p in selected if str(p['productId'])==pid);pe='product-end:'+pid;je='job-end:'+pid;te='toc-end:'+pid;product=self.fetch(pe,api('Products/name',clientId=cid,productName=publication['productName']));job=self.fetch(je,api('Jobs/latest/'+pid));toc=self.fetch(te,api('codesToc/fullTree',productId=pid,jobId=job['Id'],nodeId=pid));pub['end_units']={'product':pe,'job':je,'toc':te,'inventory':'inventory-end'};pub['end_signature']=self.signature(end_cc,product,job,toc)
   self.cp['phase']='finished';self.save();return write_outputs(self.out,self.cp)
  except BaseException as e:
   self.cp['phase']='interrupted' if isinstance(e,KeyboardInterrupt) else 'failed';self.cp['errors'].append(str(e));self.save()
   try:write_outputs(self.out,self.cp)
   except Exception:pass
   raise
  finally:
   if self.browser:self.browser.close()
def main():
 p=argparse.ArgumentParser();p.add_argument('--registry',type=Path);p.add_argument('--target');p.add_argument('--url');p.add_argument('--client-id',type=int);p.add_argument('--state');p.add_argument('--client-name',action='append');p.add_argument('--out',type=Path,required=True);p.add_argument('--product-id','--publication-id',action='append',type=int);p.add_argument('--resume',action='store_true');p.add_argument('--retry-assets',action='store_true',help='With explicit resume, retry failed/deferred assets once; never clears shared access stops');p.add_argument('--max-items',type=int,help='Diagnostic content-request limit; any value forces incomplete');p.add_argument('--batch-size',type=int,default=25);p.add_argument('--allow-asset-host',action='append',default=[]);a=p.parse_args()
 if a.max_items is not None and a.max_items<1:p.error('--max-items must be positive')
 if a.batch_size<1:p.error('--batch-size must be positive')
 try:
  import fcntl
  if not a.resume and a.out.exists() and any(a.out.iterdir()):raise ValueError('Fresh collection requires empty output directory')
  a.out.mkdir(parents=True,exist_ok=True)
  with (a.out/'.run.lock').open('a+') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   report=Run(a).execute();print(json.dumps(report,indent=2));return 0 if report['publication_complete'] else 2
 except Exception as e:print(str(e),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
