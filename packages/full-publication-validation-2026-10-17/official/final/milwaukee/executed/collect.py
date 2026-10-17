#!/usr/bin/env python3
"""Full selected-publication collection. Explicit limits are incomplete; no whole-jurisdiction claims."""
import argparse,csv,hashlib,json,os,pathlib,re,shutil,subprocess,sys,traceback
from urllib.parse import urljoin,urlsplit,quote,unquote
from bs4 import BeautifulSoup
import model,transport
BASE=pathlib.Path(__file__).resolve().parent

def save(p,v):transport.atomic(p,json.dumps(v,ensure_ascii=False,indent=2).encode()+b'\n')
def load(p):return json.loads(pathlib.Path(p).read_text())
def lines(rows):return b''.join(model.encoded(r)+b'\n' for r in rows)
def item(url,heading,kind='html',**extra):return dict(id=model.key(url),url=model.key(url),heading=heading,kind=kind,**extra)
def fetch_raw(run,name,url,config,kind='html',index_url=None,fresh=False):
 key=model.sha(name.encode())[:20];rel='raw/'+key+'.bin';p=run/rel;meta=p.with_suffix('.receipt.json')
 if not fresh and meta.exists():
  m=load(meta)
  if not p.exists() or model.sha(p.read_bytes())!=m.get('sha256'):raise ValueError('Corrupt cached source '+name)
  if m.get('url')!=url or not m.get('success',m.get('status')==200) or m.get('access_stop'):raise ValueError('Cached acquisition failed/mismatched; no automatic retry '+name)
  return p.read_bytes(),m,rel
 if p.exists() or meta.exists():raise ValueError('Refusing overwrite of source request '+name)
 if config.get('transport','http')=='browser':
  job={'url':url,'kind':kind,'wait_ms':config.get('wait_ms',3500)}
  if kind=='pdf':job.update(index_url=index_url or config.get('source_url'),expand_button=config.get('expand_button'))
  if kind=='html' and config.get('wait_selector'):job['wait_selector']=config['wait_selector']
  jf=run/'jobs'/(key+'.json');save(jf,job);node=os.environ.get('NODE','node');subprocess.run([node,str(BASE/'browser_fetch.cjs'),str(jf),str(p)],check=False)
  generated=p.with_name(p.name+'.receipt.json')
  if not generated.exists():raise RuntimeError('Browser failed without receipt')
  m=load(generated);shutil.move(generated,meta)
  if not m.get('success'):raise RuntimeError('Browser acquisition failed; see '+str(meta))
  b=p.read_bytes()
 else:
  b,m=transport.fetch(url,config.get('max_bytes',160_000_000));transport.atomic(p,b);save(meta,m)
  if m.get('status')!=200 or m.get('access_stop'):raise RuntimeError('Access failure retained: '+str(meta))
 m.update(url=url,raw_ref=rel,sha256=model.sha(b));save(meta,m);return b,m,rel

def discover(run,c,resume=False):
 mode=c['mode'];surl=c['source_url'];start,m,ref=fetch_raw(run,'discovery',surl,c)
 if mode in ['pdf','html_single']:
  return [item(surl,c['publication'],'pdf' if mode=='pdf' else 'html',raw_ref=ref)],{'source_ref':ref,'source_sha256':model.sha(start),'source_url':surl,'edition':c.get('edition'),'kind':'native_file','identity':c['id']}
 if mode=='github_archive':
  soup=BeautifulSoup(start,'html.parser');repo=c['repository']
  if not any(repo in a.get('href','') for a in soup.select('a[href]')):raise ValueError('Official hub does not expose configured repository')
  metadata,_,mr=fetch_raw(run,'github-repository','https://api.github.com/repos/'+repo,{'transport':'http'});metadata=json.loads(metadata);branch=metadata['default_branch']
  cb,_,cr=fetch_raw(run,'github-commit','https://api.github.com/repos/'+repo+'/commits/'+quote(branch,safe=''),{'transport':'http'});commit=json.loads(cb)['sha']
  url=metadata['archive_url'].replace('{archive_format}','zipball').replace('{/ref}','/'+commit)
  return [item(url,c['publication'],'zip')],{'source_ref':ref,'source_sha256':model.sha(start),'repo_ref':mr,'commit_ref':cr,'repository':repo,'branch':branch,'commit':commit,'identity':c['id'],'kind':'github_commit','edition':branch,'archive_url':url}
 soup=BeautifulSoup(start,'html.parser');selector=c.get('inventory_selector','main a[href]');links=soup.select(selector);items=[];excluded=[]
 if mode=='portland_titles':
  for a in links:
   title=model.clean(a.get_text(' ',strip=True));url=urljoin(surl,a.get('href',''))
   if not re.match(r'^Title \d+\b',title):continue
   number=int(re.match(r'^Title (\d+)',title)[1])
   if number==33:excluded.append({'url':url,'reason':'Title33 uses separate nativePDF publication/config; unresolved required component of all-city-code scope','required':True});continue
   items.append(item(url.rstrip('/')+'/all',title))
 elif mode=='arlington_portal':
  import base64
  for a in links:
   detail=urljoin(surl,a.get('href',''));token=urlsplit(detail).path.rsplit('/',1)[-1]
   try:url=base64.b64decode(unquote(token)).decode()
   except Exception as error:raise ValueError('Observed portal document URL token invalid') from error
   if not url.startswith('https://www.arlingtonva.us/files/') or not url.lower().endswith('.pdf'):raise ValueError('Unexpected observed portal file identity')
   url=quote(url,safe=':/?&=%');items.append(item(url,model.clean(a.get_text(' ',strip=True)),'pdf',detail_url=detail,source_token=token,listing_context=model.clean(a.parent.get_text(' ',strip=True))))
 elif mode in ['pdf_set','html_graph','legacy_codepublishing']:
  for a in links:
   href=a.get('href') or a.get('value');url=urljoin(surl,href or '');title=model.clean(a.get_text(' ',strip=True)) or a.get('title','')
   if not re.search(c.get('include_url_regex','.'),url):continue
   if c.get('include_text_regex') and not re.search(c['include_text_regex'],title,re.I):continue
   if c.get('exclude_text_regex') and re.search(c['exclude_text_regex'],title,re.I):excluded.append({'url':url,'reason':'Explicit configured historical/alternate publication label','required':False});continue
   items.append(item(url,title or url,'pdf' if mode=='pdf_set' else 'html'))
 else:raise ValueError('Unsupported mode '+mode)
 # Duplicate index links are route aliases, not repeated source documents.
 unique={};aliases=[]
 for i in items:
  if i['id'] in unique:aliases.append({'id':i['id'],'reason':'Duplicate inventory hyperlink to same canonical URL'})
  else:unique[i['id']]=i
 items=list(unique.values())
 if not items:raise ValueError('Empty dynamic publication inventory')
 identity={'source_ref':ref,'source_sha256':model.sha(start),'identity':c['id'],'kind':'html_inventory','inventory_selector':selector,'excluded_components':excluded,'aliases':aliases,'edition':c.get('edition')}
 return items,identity

def discover_graph(data,url,c):
 soup=BeautifulSoup(data,'html.parser');found=[]
 for a in soup.select(c.get('traverse_selector','a[href]')):
  target=model.key(urljoin(url,a.get('href','')))
  if re.search(c.get('include_url_regex','.'),target) and urlsplit(target).hostname==urlsplit(c['source_url']).hostname:found.append(item(target,model.clean(a.get_text(' ',strip=True)) or target))
 return found

def check_edition(data,c):
 if not c.get('edition_tokens'):return
 if data.startswith(b'%PDF-'):
  import pypdfium2
  d=pypdfium2.PdfDocument(data);text=' '.join(d[i].get_textpage().get_text_range() for i in range(min(c.get('edition_pages',2),len(d))));d.close()
 else:text=BeautifulSoup(data,'html.parser').get_text(' ',strip=True)
 for token in c['edition_tokens']:
  if token.lower() not in model.clean(text).lower():raise ValueError('Edition/jurisdiction token mismatch: '+token)

def inventory_projection(data,c):
 soup=BeautifulSoup(data,'html.parser');pairs=set()
 for a in soup.select(c.get('inventory_selector','main a[href]')):
  url=model.key(urljoin(c['source_url'],a.get('href') or a.get('value') or ''));label=model.clean(a.get_text(' ',strip=True))
  if c['mode']=='portland_titles' and not re.match(r'^Title \d+\b',label):continue
  if c.get('include_url_regex') and not re.search(c['include_url_regex'],url):continue
  if c.get('include_text_regex') and not re.search(c['include_text_regex'],label,re.I):continue
  if c.get('exclude_text_regex') and re.search(c['exclude_text_regex'],label,re.I):continue
  pairs.add((url,label))
 return sorted(pairs)

def consistency(run,c,identity):
 if identity['kind']=='github_commit':
  url='https://api.github.com/repos/'+identity['repository']+'/commits/'+quote(identity['branch'],safe='');b,_,ref=fetch_raw(run,'consistency-end-'+transport.now(),url,{'transport':'http'},fresh=True);end={'kind':'github_commit','commit':json.loads(b)['sha'],'raw_ref':ref};return dict(end,consistent=end['commit']==identity['commit'])
 b,_,ref=fetch_raw(run,'consistency-end-'+transport.now(),c['source_url'],c,kind='html',fresh=True)
 if identity['kind']=='native_file':same=model.sha(b)==identity['source_sha256']
 else:
  same=inventory_projection((run/identity['source_ref']).read_bytes(),c)==inventory_projection(b,c)
 return {'kind':identity['kind'],'raw_ref':ref,'sha256':model.sha(b),'consistent':same,'comparison':'Native bytes or selected full inventory link URL+label projection; no codewide effective-date assertion'}

def parse_item(data,i,c):
 if i['kind']=='pdf':return model.pdf_records(data,i,c)
 if i['kind']=='zip':
  rows,archive=model.archive_records(data,c,i['raw_ref']);return rows,[{'archive':archive}]
 return model.html_records(data,i,c)

def collect(config,out,resume=False,max_items=None,interrupt_after=None):
 c=load(config);out=pathlib.Path(out).resolve();binding=model.sha(model.encoded(c));cp=out/'checkpoint.json'
 if out.exists() and any(out.iterdir()) and not resume:raise ValueError('Output must be empty unless --resume')
 out.mkdir(parents=True,exist_ok=True);(out/'raw').mkdir(exist_ok=True);(out/'items').mkdir(exist_ok=True)
 scripts={name:model.sha((BASE/name).read_bytes()) for name in ['collect.py','model.py','transport.py','legacy_html.py','browser_fetch.cjs']};codebinding=model.sha(model.encoded(scripts))
 if cp.exists():
  state=load(cp)
  if state['config_sha256']!=binding or state['code_binding']!=codebinding:raise ValueError('Resume config/code identity mismatch')
  c=load(out/'config.json');validate_cached(out,state,c)
 else:
  save(out/'config.json',c);(out/'executed').mkdir(exist_ok=True)
  for n in scripts:shutil.copyfile(BASE/n,out/'executed'/n)
  state={'schema':1,'config_sha256':binding,'code_binding':codebinding,'scripts':scripts,'started_at':transport.now(),'items':[],'done':[],'completed':False,'identity':None,'consistency':None,'limits_history':[]};save(cp,state)
 try:
  if not state['identity']:
   state['items'],state['identity']=discover(out,c);state['inventory_sha256']=model.sha(model.encoded(state['items']));save(out/'inventory.json',state['items']);save(cp,state)
  else:
   # Fresh source identity check before trusting cached completion/resuming network.
   check=consistency(out,c,state['identity']);state['resume_consistency']=check;save(cp,state)
   if not check['consistent']:raise ValueError('Source drift on resume; use a new run')
  if max_items is not None:state['limits_history'].append(max_items)
  count=0;cursor=0
  while cursor<len(state['items']):
   i=state['items'][cursor];cursor+=1
   if i['id'] in state['done']:continue
   if max_items is not None and count>=max_items:break
   key=model.sha(i['id'].encode())[:24]
   try:
    b,m,raw=fetch_raw(out,'item:'+i['id'],i['url'],c,kind=i['kind'],index_url=i.get('detail_url',c.get('source_url')));i['raw_ref']=raw;check_edition(b,c);rows,disp=parse_item(b,i,c)
    asset_ledger=[]
    if i['kind']!='pdf':
     archive_assets=next((d['archive']['assets'] for d in disp if 'archive' in d),None)
     candidates=archive_assets if archive_assets is not None else [dict(a,owner=r['id']) for r in rows for a in r.get('assets',[])+r.get('document_assets',[])]
     retained={a['url'] for a in candidates if a.get('status') in ['retained_in_archive','retained_inline','retained_inline_reference'] or not a.get('required',True)};asset_ledger += [dict(a,status=a.get('status','independent_legal_layer_reference')) for a in candidates if not a.get('required',True)]
     for url in sorted({a['url'] for a in candidates}-retained):
      if any(a.get('requires_manual_review') for a in candidates if a['url']==url):asset_ledger.append({'url':url,'status':'unresolved','reason':'Source reference requires manual review'});continue
      if not re.search(r'\.(?:pdf|docx?|xlsx?|zip|xml|csv|txt|html?)(?:$|[?#])',url,re.I):asset_ledger.append({'url':url,'status':'unresolved','reason':'Extensionless/opaque nonimage attachment requires qualification; no automatic fetch that could acquire an image'});continue
      if not url.startswith('https://'):asset_ledger.append({'url':url,'status':'unresolved','reason':'NonHTTPS referenced asset requires manual review'});continue
      try:
       ab,am,ar=fetch_raw(out,'asset:'+url,url,c,kind='pdf' if urlsplit(url).path.lower().endswith('.pdf') else 'asset',index_url=i['url'])
       if urlsplit(url).path.lower().endswith('.pdf') and not ab.startswith(b'%PDF-'):raise ValueError('Referenced PDF asset is not nativePDF')
       if urlsplit(url).path.lower().endswith('.svg') and urlsplit(url).fragment and not BeautifulSoup(ab,'html.parser').find(id=urlsplit(url).fragment):raise ValueError('Required SVG fragment target absent')
       asset_ledger.append({'url':url,'status':'acquired_requires_nested_review' if any(a.get('requires_nested_asset_review') for a in candidates if a['url']==url) else 'acquired','raw_ref':ar,'sha256':model.sha(ab),'bytes':len(ab)})
      except Exception as asset_error:
       asset_ledger.append({'url':url,'status':'failed','error':str(asset_error)});break
    save(out/'items'/(key+'.json'),{'item':i,'raw_sha256':model.sha(b),'records':rows,'dispositions':disp,'asset_downloads':asset_ledger});state['done'].append(i['id'])
    if c['mode'] in ['legacy_codepublishing','html_graph']:
     known={x['id'] for x in state['items']}
     for extra in discover_graph(b,i['url'],c):
      if extra['id'] not in known:state['items'].append(extra);known.add(extra['id'])
    state['inventory_sha256']=model.sha(model.encoded(state['items']));save(out/'inventory.json',state['items']);save(cp,state);count+=1
   except Exception as error:state.setdefault('failures',[]).append({'id':i['id'],'error':str(error)});save(cp,state);raise
   if interrupt_after is not None and count>=interrupt_after:raise InterruptedError('Explicit interruption injection after durable item boundary')
  state['consistency']=consistency(out,c,state['identity']);state['completed']=len(state['done'])==len(state['items']) and max_items is None;state['finished_at']=transport.now();save(cp,state)
 except Exception as error:
  state['last_error']=str(error);state['completed']=False;save(cp,state)
 rows=[]
 for i in state['items']:
  p=out/'items'/(model.sha(i['id'].encode())[:24]+'.json')
  if p.exists():rows+=load(p)['records']
 transport.atomic(out/'records.jsonl',lines(rows))
 with (out/'records.csv').open('w',newline='') as cf:
  fields=['id','document_id','unit','jurisdiction','state','publication','heading','source_url','text','raw_ref','raw_sha256'];writer=csv.DictWriter(cf,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
 report=reconcile(out);save(out/'coverage.json',report);print(json.dumps(brief(report),indent=2));return 0 if report['requested_coverage_complete'] else 3

def validate_cached(out,state,c):
 # Re-derive dynamic expected IDs from retained source, with a fail-closed offline cache accessor.
 global fetch_raw
 original=fetch_raw
 def offline_fetch(run,name,url,config,**kwargs):
  stem=model.sha(name.encode())[:20];p=run/'raw'/(stem+'.bin');meta=p.with_suffix('.receipt.json')
  if not p.exists() or not meta.exists():raise ValueError('Missing discovery cache; offline verifier never requests network')
  return original(run,name,url,config,**kwargs)
 fetch_raw=offline_fetch
 try:initial,identity=discover(out,c)
 finally:fetch_raw=original
 if identity!=state['identity']:raise ValueError('Pinned publication/edition/source discovery mismatch')
 expected={i['id'] for i in initial}
 for ident in state['done']:
  p=out/'items'/(model.sha(ident.encode())[:24]+'.json')
  if p.exists() and c['mode'] in ['legacy_codepublishing','html_graph']:
   doc=load(p);expected.update(i['id'] for i in discover_graph((out/doc['item']['raw_ref']).read_bytes(),doc['item']['url'],c))
 if expected!={i['id'] for i in state['items']}:raise ValueError('Missing/extra dynamic inventory IDs versus source graph')
 for meta in (out/'raw').glob('*.receipt.json'):
  m=load(meta);p=meta.with_name(meta.name.replace('.receipt.json','.bin'))
  if not p.exists() or model.sha(p.read_bytes())!=m.get('sha256'):raise ValueError('Raw source/receipt hash mismatch '+str(meta))
 for name,digest in state['scripts'].items():
  if model.sha((out/'executed'/name).read_bytes())!=digest:raise ValueError('Executed source snapshot mismatch')
 if model.sha(model.encoded(load(out/'config.json')))!=state['config_sha256']:raise ValueError('Config corrupt')
 if model.sha(model.encoded(load(out/'inventory.json')))!=state['inventory_sha256']:raise ValueError('Inventory corrupt')
 if len(state['done'])!=len(set(state['done'])):raise ValueError('Duplicate checkpoint completion IDs')
 for ident in state['done']:
  p=out/'items'/(model.sha(ident.encode())[:24]+'.json');record=load(p);data=(out/record['item']['raw_ref']).read_bytes()
  if model.sha(data)!=record['raw_sha256']:raise ValueError('Corrupt source cache')
  for asset in record.get('asset_downloads',[]):
   if asset.get('status')=='acquired' and model.sha((out/asset['raw_ref']).read_bytes())!=asset['sha256']:raise ValueError('Corrupt required asset')
  recomputed,disp=parse_item(data,record['item'],c)
  if recomputed!=record['records'] or disp!=record['dispositions']:raise ValueError('Cached parsed output/source mismatch')
 return True

def recompute_consistency(out,c,state):
 end=state.get('consistency');identity=state.get('identity')
 if not end or not identity:return False
 b=(out/end['raw_ref']).read_bytes()
 if identity['kind']=='github_commit':return json.loads(b)['sha']==identity['commit']
 if identity['kind']=='native_file':return model.sha(b)==identity['source_sha256']
 return inventory_projection((out/identity['source_ref']).read_bytes(),c)==inventory_projection(b,c)

def reconcile(out):
 out=pathlib.Path(out);c=load(out/'config.json');s=load(out/'checkpoint.json');validate_cached(out,s,c);inventory=load(out/'inventory.json');expected=[i['id'] for i in inventory];done=set(s['done']);records=[];assets=[];exclusions=[];page_files={};unknown=[];archive_summaries=[]
 for i in inventory:
  p=out/'items'/(model.sha(i['id'].encode())[:24]+'.json')
  if not p.exists():continue
  doc=load(p);records+=doc['records']
  if i['kind']=='pdf':
   pages=[r['physical_page'] for r in doc['records']];expected_pages=doc['records'][0]['page_count'] if doc['records'] else 0;page_files[i['id']]={'expected_pages':expected_pages,'acquired_page_ids':pages,'page_gaps':sorted(set(range(1,expected_pages+1))-set(pages)),'duplicates':len(pages)-len(set(pages)),'semantic_review_required':True}
  for d in doc['dispositions']:
   if 'archive' in d:
    ar=d['archive'];assets+=ar['assets'];exclusions+=ar['owners'];unknown +=[o['id'] for o in ar['owners'] if o['disposition']=='unresolved'];unknown+=ar['missing_internal_nav_targets'];archive_summaries.append({'members':len(ar['members']),'canonical_members':ar['canonical_member_count'],'aggregate_alternates_excluded':ar['alternate_aggregate_members_excluded'],'missing_internal_nav_targets':ar['missing_internal_nav_targets'],'member_inventory_sha256':model.sha(model.encoded(ar['members']))})
   elif d.get('disposition') in ['structural','reserved_or_repealed']:exclusions.append(d)
   elif d.get('disposition')=='unresolved':unknown.append(d['node_id'])
  downloaded={a['url']:a for a in doc.get('asset_downloads',[])}
  for a in assets:
   if a.get('url') in downloaded:a.update(downloaded[a['url']])
  if i['kind']=='html':
   for r in doc['records']:
    for a in r.get('assets',[])+r.get('document_assets',[]):assets.append({**a,'owner':r['id'],**downloaded.get(a['url'],{'status':'unresolved','reason':'Referenced legal image/attachment missing acquisition'})})
 ids=[r['id'] for r in records];record_counts=__import__('collections').Counter(ids);duplicate_records=sorted(i for i,n in record_counts.items() if n>1);missing=sorted(set(expected)-done);extra=sorted(done-set(expected));limited=not s.get('completed');consistent=recompute_consistency(out,c,s)
 document_complete=not missing and not extra and len(expected)==len(set(expected)) and not limited and consistent
 pages_complete=bool(page_files) and document_complete and all(not x['page_gaps'] and not x['duplicates'] for x in page_files.values())
 body_complete=document_complete and not duplicate_records and not unknown and not page_files
 unresolved_assets=[a for a in assets if a.get('required') and a.get('status') not in ['retained_in_archive','retained_inline','retained_inline_reference','acquired']]
 required_components=[x for x in (s['identity'] or {}).get('excluded_components',[]) if x.get('required')]
 requested=c.get('coverage_level','publication_text');complete=(pages_complete if requested=='file_pages' else body_complete) and not unresolved_assets and not required_components
 if c.get('mode')=='pdf' and not page_files:complete=False
 return {'schema':1,'publication_identity':{'id':c['id'],'jurisdiction':c['jurisdiction'],'state':c['state'],'publication':c['publication'],'source_url':c['source_url'],'pinned_source':s['identity']},'requested_level':requested,'requested_coverage_complete':complete,'publication_file_coverage_complete':document_complete,'pdf_page_extraction_complete':pages_complete,'publication_html_text_coverage_complete':body_complete,'legal_semantic_coverage_complete':body_complete and not unresolved_assets and not required_components and not any(r.get('semantic_review_required') or r['unit'] in ['publication_html_document','image_only_publication'] for r in records),'jurisdiction_complete':False,'manual_review_required':bool(page_files) or any(r.get('semantic_review_required') or r['unit'] in ['publication_html_document','image_only_publication'] for r in records),'expected_document_count':len(expected),'acquired_document_count':len(done),'parsed_record_count':len(records),'table_count':sum(len(r.get('tables',[])) for r in records),'record_units':dict(__import__('collections').Counter(r['unit'] for r in records)),'missing_document_ids':missing,'extra_document_ids':extra,'duplicate_inventory_ids':len(expected)-len(set(expected)),'duplicate_record_ids':duplicate_records,'unknown_ownership_or_nav_ids':unknown,'pdf_files':page_files,'archive_reconciliation':archive_summaries,'required_assets_count':sum(bool(a.get('required')) for a in assets),'policy_omitted_image_count':sum(a.get('status')=='policy_omitted_image' for a in assets),'image_placeholder_count':sum(r.get('image_placeholder_count',0) for r in records),'image_policy':'No image fetch or pixel extraction; literal[IMAGE] placeholders, references retained as deliberate omissions','required_assets_unresolved':unresolved_assets,'assets':assets,'dispositions':exclusions,'required_components_unresolved':required_components,'source_consistency':s.get('consistency'),'interrupted_or_limited':limited,'failures':s.get('failures',[]),'limitations':['Selected publication scope only; external incorporated standards and other families require separate configs.','Full native PDF/page extraction does not establish all visible text, legal sections, tables/spans, diagrams or semantics.','Edition pinned to source metadata/bytes; it is not a jurisdiction-wide current-law opinion.']}
def brief(report):
 keys=['requested_level','requested_coverage_complete','publication_file_coverage_complete','pdf_page_extraction_complete','publication_html_text_coverage_complete','legal_semantic_coverage_complete','jurisdiction_complete','manual_review_required','expected_document_count','acquired_document_count','parsed_record_count','record_units','table_count','required_assets_count','policy_omitted_image_count','image_placeholder_count','interrupted_or_limited','failures']
 return dict(publication_id=report['publication_identity']['id'],**{k:report[k] for k in keys},missing_document_count=len(report['missing_document_ids']),unknown_ownership_count=len(report['unknown_ownership_or_nav_ids']),unresolved_required_asset_count=len(report['required_assets_unresolved']))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--config',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--resume',action='store_true');p.add_argument('--max-items',type=int);p.add_argument('--interrupt-after',type=int);a=p.parse_args()
 try:raise SystemExit(collect(a.config,a.out,a.resume,a.max_items,a.interrupt_after))
 except Exception as e:print(str(e),file=sys.stderr);raise SystemExit(3)
