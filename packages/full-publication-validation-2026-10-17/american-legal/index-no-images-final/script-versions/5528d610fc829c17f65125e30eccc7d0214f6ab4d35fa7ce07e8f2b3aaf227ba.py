#!/usr/bin/env python3
"""Dynamic full-publication American Legal traversal. Defaults to all nodes and required assets."""
import argparse,datetime,json,os,re,sys,traceback
from pathlib import Path
from urllib.parse import quote,urlparse,urljoin
from model import *
from transport import Browser,Cache,atomic,save,BASE

def inventory_live(identity,code,cache,limit=None,phase='start'):
 nodes=[];expanded=[];queue=[(n,None,[]) for n in code['sections']];seen=set()
 while queue and (limit is None or len(nodes)<limit):
  raw,parent,path=queue.pop(0);n=node(raw,parent,path);assert n['document_id'] not in seen,'Duplicate TOC ID';seen.add(n['document_id']);nodes.append(n)
  if n['has_children']:
   url='https://codelibrary.amlegal.com/api/section-toc/'+str(n['internal_id'])+'/'
   b,e=cache.fetch(url,key=phase+':toc:'+n['document_id']);data=json.loads(b);assert data['doc_id']==n['document_id'] and data['id']==n['internal_id'] and data['code_uuid']==identity['code_uuid'];assert isinstance(data.get('children'),list),'Missing children';expanded.append(n['document_id'])
   for child in data['children']:
    assert child.get('parent_doc_id') in [None,n['document_id']];queue.append((child,n['document_id'],n['path']))
 return {'nodes':nodes,'expanded':expanded,'pending':[x[0]['doc_id'] for x in queue],'root_ids':[n['doc_id'] for n in code['sections']],'complete':not queue,'identity':identity}

def asset_fetch(url,cache,assets,policy,kind=None):
 if url in assets:return assets[url]
 item={'url':url,'required':True,'status':'not_acquired','reason':'Explicit reference-only policy'};assets[url]=item
 if kind=='image' or image_url(url) or url.startswith(('inline-image:','inline-svg:')):
  item.update(required=False,status='image-placeholder',reason='User policy: literal [IMAGE], no image acquisition',placeholder='[IMAGE]',policy=IMAGE_POLICY);return item
 if policy=='download':
  try:
   _,head=cache.fetch(url,op='head');mime=head['response']['headers'].get('content-type','')
   if mime.lower().startswith('image/'):
    item.update(required=False,status='image-placeholder',reason='HEAD identified image; no GET/body acquisition',placeholder='[IMAGE]',policy=IMAGE_POLICY);return item
   if not mime or 'text/html' in mime:
    item.update(status='unresolved-type',reason='No verified nonimage download type from HEAD; body not fetched');return item
   b,e=cache.fetch(url,op='binary');validation=validate_asset(url,b,e['response']['headers'].get('content-type'));item.update(status='retained' if validation['qualified'] else 'retained-unqualified',file=e['file'],sha256=e['sha256'],bytes=e['bytes'],content_type=e['response']['headers'].get('content-type'),validation=validation,reason='Verified nonimage bytes retained')
   if validation['kind']=='css':
    for raw in css_links(b):
     if raw.startswith('data:image/') or not re.search(r'\.(?:css|woff2?|ttf|otf|eot)(?:$|[?#])',raw,re.I):childkind='image'
     else:childkind='style-resource'
     asset_fetch(urljoin(e['response']['url'],raw),cache,assets,policy,childkind)
  except Exception as exc:item.update(status='failed',reason=str(exc));raise
 return item

def run(a):
 folder=a.out.resolve();old=None
 if a.resume:
  assert (folder/'run.json').exists(),'Resume requires owned run.json';old=json.loads((folder/'run.json').read_text());assert old['source_url']==a.url and old['expected_jurisdiction']==a.jurisdiction and old['expected_state']==a.state.upper() and old.get('publication_selector')==a.publication and old.get('identity_aliases',[])==a.identity_alias,'Resume identity parameters differ'
 else:
  assert not folder.exists(),'Fresh --out must not exist';folder.mkdir(parents=True)
 for name in ['collect.py','model.py','verify.py','transport.py','browser.cjs','gate.py']:
  p=BASE/name;atomic(folder/'scripts'/name,p.read_bytes());atomic(folder/'script-versions'/(digest(p.read_bytes())+p.suffix),p.read_bytes())
 a.assets=a.assets or (old['assets_policy'] if old else 'download');a.strategy=a.strategy or (old['strategy'] if old else 'traverse')
 if old:assert a.assets==old['assets_policy'] and a.strategy==old['strategy'] and old.get('image_policy')==IMAGE_POLICY,'Resume policy differs; choose fresh output after image-policy change'
 browser=Browser()
 try:cache=Cache(folder,browser)
 except BaseException:browser.close();raise
 runmeta=old or {'schema_version':1,'source_url':a.url,'expected_jurisdiction':a.jurisdiction,'expected_state':a.state.upper(),'publication_selector':a.publication,'identity_aliases':a.identity_alias,'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'assets_policy':a.assets,'strategy':a.strategy,'resume_count':0,'executions':[],'image_policy':IMAGE_POLICY}
 runmeta['executions'].append({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'python':sys.version,'platform':sys.platform,'script_sha256':{p.name:digest(p.read_bytes()) for p in BASE.iterdir() if p.suffix in ['.py','.cjs']},'max_items':a.max_items});runmeta['max_items']=a.max_items;runmeta['status']='collecting';save(folder/'run.json',runmeta)
 try:
  parts=urlparse(a.url).path.split('/');assert urlparse(a.url).hostname=='codelibrary.amlegal.com' and len(parts)>3 and parts[1]=='codes','Requires ALP codes URL';overview='https://codelibrary.amlegal.com/codes/'+parts[2]+'/latest/overview'
  if old:
   runmeta['resume_count']+=1;fresh,e=cache.fetch(overview,op='navigate',key='resume-overview:'+str(runmeta['resume_count']));ident,c,codes=select(fresh,a.url,a.jurisdiction,a.state,a.publication,a.identity_alias);assert not old.get('identity') or ident==old['identity'],'Publication edition drift on resume'
  start,e=cache.fetch(overview,op='navigate',key='overview-start');identity,code,codes=select(start,a.url,a.jurisdiction,a.state,a.publication,a.identity_alias)
  if old:assert identity==ident and (not old.get('identity') or identity==old['identity'])
  runmeta['identity']=identity;runmeta['publication_inventory']=codes;runmeta['overview_url']=overview;save(folder/'run.json',runmeta)
  inv=inventory_live(identity,code,cache,a.max_items);save(folder/'inventory.json',inv);runmeta['inventory_sha256']=digest(canonical(inv));save(folder/'run.json',runmeta)
  records=[];pages=[];assets={};pdf_owners={}
  # Native bulk is optional. Independent inventory above still gates completeness. Traversal is default.
  if a.strategy=='native':
   assert not identity['is_pdf'],'For PDF publications use traverse';url=f"https://codelibrary.amlegal.com/codes/{identity['client_slug']}/{identity['version_uuid']}/{identity['code_slug']}/{code['sections'][0]['doc_id']}";data,e=cache.fetch(url,op='export',key='native-export',code_uuid=identity['code_uuid'],code_slug=identity['code_slug'],version=identity['version_uuid']);records=native_records(data,inv,identity,url,e['sha256'])
   for record in records:
    for asset in record['assets']:
     if asset['disposition'] in ['required-asset','image-placeholder']:asset_fetch(asset['url'],cache,assets,a.assets,asset.get('kind'))
   records=native_records(data,inv,identity,url,e['sha256'],{u for u,v in assets.items() if v['status']=='image-placeholder'})
   save(folder/'checkpoint.json',{'inventory_sha256':runmeta['inventory_sha256'],'acquired_ids':[r['document_id'] for r in records]})
  for item in ([] if a.strategy=='native' else inv['nodes']):
   did=item['document_id'];root=f"https://codelibrary.amlegal.com/codes/{identity['client_slug']}/{identity['version_uuid']}/{identity['code_slug']}/{quote(did,safe='')}"
   if identity['is_pdf']:
    url=f"https://codelibrary.amlegal.com/api/sec-info/{identity['client_slug']}/{identity['version_uuid']}/{identity['code_slug']}/{quote(did,safe='')}/";raw,e=cache.fetch(url);info=json.loads(raw);assert info['doc_id']==did and info['version_uuid']==identity['version_uuid'] and info['code_uuid']==identity['code_uuid'],'PDF source identity mismatch'
    pdf=info.get('pdf_path')
    if pdf:
     asset=asset_fetch(pdf,cache,assets,'download','native-pdf');assert asset['status']=='retained','Native PDF format not verified';data,pe=cache.fetch(pdf,op='binary')
     if pe['sha256'] in pdf_owners:page_ids=[];alias=pdf_owners[pe['sha256']]
     else:
      pp=pdf_pages(data,did,pdf);pages+=pp;page_ids=[x['document_id'] for x in pp];pdf_owners[pe['sha256']]=did;alias=None
     records.append({'document_id':did,'heading':item['heading'],'path':item['path'],'parent_id':item['parent_id'],'kind':'native-pdf','text':'','html':None,'body_block_ids':[],'tables':[],'links':[],'assets':[{'url':pdf,'kind':'native-publication-pdf','disposition':'required-asset'}],'source_url':url,'source_sha256':e['sha256'],'publication_identity':identity,'pdf_asset':asset,'pdf_page_ids':page_ids,'alias_of':alias});save(folder/'checkpoint.json',{'inventory_sha256':runmeta['inventory_sha256'],'acquired_ids':[r['document_id'] for r in records]});continue
   url=f"https://codelibrary.amlegal.com/api/render-section/{identity['client_slug']}/{identity['version_uuid']}/{identity['code_slug']}/{quote(item['orig_doc_id'],safe='')}/{item['orig_doc_idx']}/";data,e=cache.fetch(url);record=html_record(json.loads(data),item,identity,root,e['sha256']);records.append(record)
   for asset in record['assets']:
    if asset['disposition'] in ['required-asset','image-placeholder']:asset_fetch(asset['url'],cache,assets,a.assets,asset.get('kind'))
   records[-1]=html_record(json.loads(data),item,identity,root,e['sha256'],{u for u,v in assets.items() if v['status']=='image-placeholder'})
   save(folder/'checkpoint.json',{'inventory_sha256':runmeta['inventory_sha256'],'acquired_ids':[r['document_id'] for r in records]})
  end,ee=cache.fetch(overview,op='fetch',key='overview-end:'+str(runmeta['resume_count']));endidentity,endcode,_=select(end,a.url,a.jurisdiction,a.state,a.publication,a.identity_alias);endinv=inventory_live(endidentity,endcode,cache,a.max_items,phase='end:'+str(runmeta['resume_count']));save(folder/'inventory-end.json',endinv)
  runmeta.update(end_identity=endidentity,inventory_end_sha256=digest(canonical(endinv)),status='acquired',finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat());save(folder/'assets.json',list(assets.values()))
  for name,b in output_bytes(records,pages).items():atomic(folder/name,b)
  save(folder/'run.json',runmeta)
  from verify import verify
  coverage=verify(folder,compare_report=False);save(folder/'coverage.json',coverage);print(json.dumps(coverage,indent=2));return 0 if coverage['publication_complete'] else 2
 except BaseException as exc:
  runmeta.update(status='interrupted' if isinstance(exc,KeyboardInterrupt) else 'failed',error=str(exc),finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat());save(folder/'run.json',runmeta);traceback.print_exc();return 2
 finally:browser.close()

def main():
 p=argparse.ArgumentParser();p.add_argument('--url',required=True);p.add_argument('--jurisdiction',required=True);p.add_argument('--state',required=True);p.add_argument('--publication');p.add_argument('--identity-alias',action='append',default=[]);p.add_argument('--out',required=True,type=Path);p.add_argument('--resume',action='store_true');p.add_argument('--max-items',type=int);p.add_argument('--assets',choices=['download','reference-only']);p.add_argument('--strategy',choices=['traverse','native']);a=p.parse_args();assert a.max_items is None or a.max_items>0;sys.exit(run(a))
if __name__=='__main__':main()
