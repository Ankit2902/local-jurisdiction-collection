"""Durable collection and independent source replay; never treats a sample limit as complete."""
from __future__ import annotations
import base64,csv,io,json,shutil,re,copy
from pathlib import Path
from urllib.parse import urlsplit,urljoin
from .common import *
from .adapters import *

VERSION='icc-full-1.0'
_PARSE_CACHE={}
def cached_parse(family,raw,url,expected,base,known):
 key=(family,digest(raw),url,digest(canon(edition(expected))),base,digest(canon(known)) if family=='municipal.codes' else ())
 if key not in _PARSE_CACHE:_PARSE_CACHE[key]=parse_ecode(raw,url,expected) if family=='ecode360' else parse_municipal(raw,url,base,expected,known)
 return copy.deepcopy(_PARSE_CACHE[key])

def code_fingerprint():
 return {p.name:digest(p.read_bytes()) for p in sorted(Path(__file__).parent.glob('*.py'))}

def artifact(out,state,role,raw,meta):
 index=len(state['artifacts']);name=f'raw/{index:05d}-{role}.bin';atomic(out/name,raw)
 item={'path':name,'sha256':digest(raw),'bytes':len(raw),'role':role,**meta};state['artifacts'].append(item);save(out/'checkpoint.json',state);return item

def load_artifact(out,a):
 p=(out/a['path']).resolve()
 if not p.is_relative_to(out.resolve()):raise QualificationError('Artifact path escape')
 raw=p.read_bytes()
 if len(raw)!=a['bytes'] or digest(raw)!=a['sha256']:raise QualificationError('Artifact corruption '+a['path'])
 return raw

def rebuild(out,state):
 """Recompute graph, ownership and bodies only from hash-checked retained source."""
 cfg=state['config'];family=cfg['family'];base=state.get('publication_url');expected=state.get('identity');nodes={};records={};dispositions={};witnesses={};conflicts=[];duplicates=[];assets={};start=None;end=None;toc_start=None;toc_end=None
 def addnode(n):
  nid=n['id']
  if nid in nodes and nodes[nid]['url']!=n['url']:raise QualificationError('Inventory identity conflict '+nid)
  nodes.setdefault(nid,n)
 image_heads={a['requested_url']:a for a in state['artifacts'] if a['role']=='asset-head' and a.get('status')==200 and a.get('headers',{}).get('content-type','').lower().startswith('image/')}
 municipal_known={}
 if family=='municipal.codes':
  for art in state['artifacts']:
   if art['role']=='contents-start' and art.get('status')==200:
    for n in municipal_inventory(load_artifact(out,art),art['url'],base):addnode(n);municipal_known[n['id']]=n
 for a in state['artifacts']:
  raw=load_artifact(out,a);role=a['role']
  if role not in ['root-start','root-end','contents-start','contents-end','content','native','asset']:continue
  if role=='asset':
   assets[a['requested_url']]=a
   ctype=a.get('headers',{}).get('content-type','').lower();u=a['requested_url']
   if 'html' in ctype or raw.lstrip()[:40].lower().startswith((b'<!doctype html',b'<html')):raise QualificationError('Required attachment returned HTML instead of asset '+u)
   if 'svg' in ctype or u.split('?')[0].lower().endswith('.svg'):
    for ref in asset_refs(raw.decode(errors='replace'),a['url'],u):assets.setdefault(ref['url'],None)
   elif 'text/css' in ctype or u.split('?')[0].lower().endswith('.css'):
    for ref in asset_refs('<style>'+raw.decode(errors='replace')+'</style>',a['url'],u):assets.setdefault(ref['url'],None)
   continue
  if a.get('status',200)!=200 and not (role=='native' and a.get('download_completed') and a.get('status') in [None,200]):continue
  if role in ['root-start','root-end']:
   got=identity(raw,a['url'],family,base)
   if edition(got)!=edition(expected):raise QualificationError('Start/end edition drift')
   if role=='root-start':start=got
   else:end=got
  if role in ['contents-start','contents-end']:
   sp=soup(raw);title=sp.title.get_text(' ',strip=True) if sp.title else ''
   if title!='Contents of '+expected['name']:raise QualificationError('Contents publication title mismatch')
   if not any(clean_url(urljoin(a['url'],x['href']))==base for x in sp.select('a.product.active[href],a.product-name[href]')):raise QualificationError('Contents publication binding missing')
   ns=municipal_inventory(raw,a['url'],base)
   fingerprint=digest(canon(sorted((n['id'],n['heading'],n.get('parent_id'),n.get('source_classes')) for n in ns)))
   if role=='contents-start':toc_start=fingerprint
   else:toc_end=fingerprint
   for n in ns:addnode(n)
   continue
  if role=='root-end':
   if family=='ecode360':
    _,ns=ecode_inventory(raw,a['url']);toc_end=digest(canon(sorted((n['id'],n['heading'],n['kind'],n.get('parent_id')) for n in ns)))
   continue
  if family=='ecode360':
   parsed=cached_parse(family,raw,a['url'],expected,base,{})
   if role=='root-start':toc_start=digest(canon(sorted((n['id'],n['heading'],n['kind'],n.get('parent_id')) for n in parsed['nodes'])))
  else:
   if role=='root-start':
    addnode({'id':base,'url':base,'heading':got['name'],'kind':'publication','observed_on':a['url']});dispositions[base]={'id':base,'classification':'structural_empty','evidence':'Publication navigation wrapper; typed articles separately own content'}
   parsed=cached_parse(family,raw,base if role=='native' else a['url'],expected,base,municipal_known)
  for n in parsed['nodes']:addnode(n)
  for d in parsed['dispositions']:
   nid=d['id'];prior=dispositions.get(nid)
   if prior and prior['classification']=='owned_content' and d['classification']!='owned_content':continue
   dispositions[nid]=d
  for r in parsed['records']:
   nid=r['id'];witnesses.setdefault(nid,[]).append(a['path'])
   if nid in records:
    if records[nid]['body_sha256']!=r['body_sha256']:conflicts.append({'id':nid,'sources':witnesses[nid]})
    else:duplicates.append({'id':nid,'same_body':True,'source':a['path']})
   else:records[nid]=r
 # Attach provenance and resolve logical ancestry from retained descriptors/source URLs.
 for nid,r in records.items():
  r['parent_id']=r.get('parent_id') or nodes.get(nid,{}).get('parent_id') or ((expected.get('customer_id') if family=='ecode360' else base) if nid!=(expected.get('customer_id') if family=='ecode360' else base) else None)
  r['raw_witnesses']=witnesses[nid];r['jurisdiction']=cfg.get('jurisdiction');r['state']=cfg.get('state');r['edition']=edition(expected)
  r['path']=[nodes[nid]['heading']] if nid in nodes else [r['heading']]
  seen={nid};parent=r.get('parent_id')
  while parent and parent not in seen:
   seen.add(parent)
   if parent in nodes:r['path'].insert(0,nodes[parent]['heading'])
   parent=records.get(parent,{}).get('parent_id') or nodes.get(parent,{}).get('parent_id')
  for ref in r['assets']:
   if ref['url'] in image_heads:ref.update({'required':False,'image':True,'policy':'HEAD qualified image; literal [IMAGE] omission; no GET'})
   if ref['required'] and clean_url(ref['url']) not in {clean_url(n['url']) for n in nodes.values()}:assets.setdefault(ref['url'],None)
 external_pubroots=set()
 if family=='municipal.codes':
  for art in state['artifacts']:
   if art['role']=='root-start':external_pubroots.update(p['url'] for p in municipal_publications(load_artifact(out,art),base) if p['url']!=base)
 image_refs=[ref for r in records.values() for ref in r['assets'] if ref.get('image')]
 known_urls={clean_url(n['url']) for n in nodes.values()};image_urls={r['url'] for r in image_refs};ledger=[]
 for r in records.values():
  for link in r.get('links',[]):
   u=link['url'];p=urlsplit(u);cl=None
   if u in image_urls:cl='intentional_image_omission'
   elif u.split('#')[0] in assets:cl='required_nonimage_attachment'
   elif clean_url(u) in known_urls:cl='inventoried_publication_reference'
   elif p.scheme in ['mailto','tel']:cl='contact_reference'
   elif p.netloc=='ecode360.com' and re.fullmatch(r'/(?:[0-9]+|[A-Z]{2}[0-9]{4})',p.path.rstrip('/')) and not p.query:cl='external_publisher_code_reference'
   elif family=='municipal.codes' and any(clean_url(u)==root or clean_url(u).startswith(root+'/') for root in external_pubroots) and not p.query:cl='observed_other_publication_reference'
   elif p.netloc=='municipal.codes' and re.fullmatch(r'/[A-Z]{2}/[A-Z]+/[^/]+',p.path) and not p.query:cl='external_statutory_reference'
   elif p.scheme in ['https','http'] and (p.path in ['', '/'] or p.path.endswith('/') or re.search(r'\.(?:html?|aspx?|jsp)$',p.path,re.I)):cl='external_html_reference'
   else:cl='unresolved_hyperlink'
   ledger.append({**link,'classification':cl})
 return {'nodes':nodes,'records':records,'dispositions':dispositions,'conflicts':conflicts,'duplicate_witnesses':duplicates,'assets':assets,'image_refs':image_refs,'link_ledger':ledger,'start':start,'end':end,'toc_start':toc_start,'toc_end':toc_end}

def coverage(state,data):
 ids=set(data['nodes']);done=set(data['dispositions']);missing=sorted(ids-done);extra=sorted(done-ids);unknown=sorted(n for n,d in data['dispositions'].items() if d['classification']=='unresolved_empty')
 required=set(data['assets']);missing_assets=sorted(u for u in required if not data['assets'].get(u));edition_ok=bool(data['start'] and data['end'] and data['toc_start'] and data['toc_start']==data['toc_end']);limited=bool(state.get('limited') or state['config'].get('subtree'));failures=state.get('errors',[])
 text_ok=bool(ids and data['records'] and not missing and not extra and not unknown and not data['conflicts'] and not failures and not limited and edition_ok)
 unresolved_links=[r for r in data.get('link_ledger',[]) if r['classification']=='unresolved_hyperlink']
 attachment_ok=not missing_assets and not failures and edition_ok and not limited and not unresolved_links
 return {'schema_version':VERSION,'acquisition_mode':'retained_source_replay_only' if state.get('network_prohibited') else ('migrated_retained_source_plus_fresh_validation' if state.get('migration') else 'fresh_collection'),'scope':'subtree' if state['config'].get('subtree') else 'whole_publication','publication_url':state.get('publication_url'),'identity':state.get('identity'),'identity_binding':{'jurisdiction_checked':bool(state['config'].get('jurisdiction')),'state_source_verified':bool((state.get('identity') or {}).get('state')),'requested_state':state['config'].get('state')},'inventory_nodes':len(ids),'owned_content_nodes':len(data['records']),'disposition_counts':{k:sum(d['classification']==k for d in data['dispositions'].values()) for k in sorted({d['classification'] for d in data['dispositions'].values()})},'inventory_sha256':digest(canon(sorted(data['nodes'].values(),key=lambda n:n['id']))),'missing_ids':missing,'extra_ids':extra,'unresolved_ids':unknown,'conflicting_duplicate_bodies':data['conflicts'],'identical_duplicate_witnesses':len(data['duplicate_witnesses']),'image_policy':'All images are literal [IMAGE]; no separate image downloads; original source/native files may contain images.','intentional_image_omissions':sum(r.get('image_placeholder_count',0) for r in data['records'].values()),'image_reference_urls':len(data.get('image_refs',[])),'hyperlink_policy':'Inventoried nodes are reconciled. Publisher/explicit HTML and contact links are references; external incorporated texts are outside selected publication certification. Ambiguous extensionless links block attachment completeness.','unresolved_links':unresolved_links,'required_assets':len(required),'acquired_assets':len(required)-len(missing_assets),'missing_assets':missing_assets,'errors':failures,'limits_applied':limited,'start_end_inventory_consistent':edition_ok,'publication_text_complete':text_ok,'attachments_complete':attachment_ok,'edition_complete':edition_ok and text_ok and attachment_ok,'jurisdiction_complete':False,'jurisdiction_limitation':'One selected publication only; other publication tabs, unincorporated ordinances and external adopted codes are not certified.','complete':text_ok and attachment_ok,'resumable':not any(e.get('access_stop') for e in failures)}

def write_outputs(out,state,data):
 rows=[data['records'][k] for k in sorted(data['records'])];atomic(out/'records.jsonl',b''.join(canon(r)+b'\n' for r in rows))
 fields=['id','jurisdiction','state','heading','kind','parent_id','path','text','source_url','body_sha256'];stream=io.StringIO(newline='');w=csv.DictWriter(stream,fieldnames=fields);w.writeheader()
 for r in rows:w.writerow({k:json.dumps(r[k],ensure_ascii=False) if isinstance(r.get(k),(list,dict)) else r.get(k) for k in fields})
 atomic(out/'records.csv',stream.getvalue().encode());save(out/'inventory.json',sorted(data['nodes'].values(),key=lambda n:n['id']));save(out/'dispositions.json',sorted(data['dispositions'].values(),key=lambda n:n['id']));save(out/'link-ledger.json',data.get('link_ledger',[]));save(out/'image-omissions.json',{'placeholders':[im for r in rows for im in r.get('image_references',[])],'references':data.get('image_refs',[])});report=coverage(state,data);save(out/'coverage.json',report);return report

def check_cache(out,state):
 if state.get('schema_version')!=VERSION:raise QualificationError('Unsupported checkpoint version')
 for a in state['artifacts']:load_artifact(out,a)
 for name,h in state.get('code_fingerprint',{}).items():
  p=out/'executed-source'/name
  if not p.is_file() or digest(p.read_bytes())!=h:raise QualificationError('Executed source snapshot corruption '+name)
 if state.get('code_fingerprint')!=code_fingerprint():raise QualificationError('Executed collector changed; resume requires the exact source version')
 if state.get('migration'):
  m=state['migration'];raw=(out/'migration-source-checkpoint.json').read_bytes()
  if digest(raw)!=m['source_checkpoint_sha256']:raise QualificationError('Migration provenance corruption')
  prior=json.loads(raw)
  if prior['code_fingerprint']!=m['original_code_fingerprint']:raise QualificationError('Migration source revision mismatch')
  for name,h in prior['code_fingerprint'].items():
   if digest((out/'prior-executed-source'/name).read_bytes())!=h:raise QualificationError('Prior executed source corruption')
  for a in prior['artifacts']:load_artifact(out,a)
  for rel,h in m.get('ancestry_files',{}).items():
   path=(out/rel).resolve()
   if not path.is_relative_to(out.resolve()) or digest(path.read_bytes())!=h:raise QualificationError('Migration ancestry corruption')
 if state.get('inventory_sha256'):
  bound=state.get('inventory_bound_artifacts',len(state['artifacts']))
  if not isinstance(bound,int) or not 0<=bound<=len(state['artifacts']):raise QualificationError('Invalid checkpoint processed prefix')
  data=rebuild(out,{**state,'artifacts':state['artifacts'][:bound]})
  if digest(canon(sorted(data['nodes'].values(),key=lambda n:n['id'])))!=state['inventory_sha256']:raise QualificationError('Checkpoint inventory binding mismatch')

def adopt(source,out,cfg,offline=False):
 """Explicit new-folder source migration; ordinary --resume never upgrades code."""
 source=Path(source).resolve();out=Path(out).resolve();prior=read(source/'checkpoint.json')
 if out.exists() and any(out.iterdir()):raise QualificationError('Migration requires a fresh output')
 if not prior.get('identity'):raise QualificationError('Migration needs a pinned original identity')
 if not offline and (prior.get('network_prohibited') or any(e.get('access_stop') for e in prior.get('errors',[]))):raise AccessStop('Cannot resume/migrate an access-stopped or read-only replay acquisition')
 old={k:v for k,v in prior['config'].items() if k not in ['max_items','gate_dir']};new={k:v for k,v in cfg.items() if k not in ['max_items','gate_dir']}
 if old!=new:raise QualificationError('Migration source configuration mismatch')
 for name,h in prior['code_fingerprint'].items():
  if digest((source/'executed-source'/name).read_bytes())!=h:raise QualificationError('Original executed source corruption')
 for a in prior['artifacts']:
  load_artifact(source,a)
  if a['role']=='asset' and (a.get('headers',{}).get('content-type','').startswith('image/') or re.search(r'\.(png|jpe?g|gif|svg|webp|tiff?)(?:[?#]|$)',a.get('url',''),re.I)):raise QualificationError('Migration refuses separate historical image assets; use source-document-only evidence')
 out.mkdir(parents=True,exist_ok=True);shutil.copytree(source/'executed-source',out/'prior-executed-source');shutil.copyfile(source/'checkpoint.json',out/'migration-source-checkpoint.json')
 state={**prior,'created_at':now(),'config':cfg,'errors':prior.get('errors',[]) if offline else [],'limited':prior.get('limited',False) if offline else False,'network_prohibited':offline,'code_fingerprint':code_fingerprint(),'migration':{'source_folder_label':source.name,'source_checkpoint_sha256':digest((source/'checkpoint.json').read_bytes()),'original_code_fingerprint':prior['code_fingerprint'],'original_artifact_count':len(prior['artifacts']),'policy':'Hash-verified retained acquisition; new normalization plus fresh resume/closing validation. This is not wholly fresh acquisition by the new revision.'}}
 (out/'executed-source').mkdir()
 for p in Path(__file__).parent.glob('*.py'):shutil.copyfile(p,out/'executed-source'/p.name)
 for a in state['artifacts']:atomic(out/a['path'],load_artifact(source,a))
 ancestry={}
 for name in ['prior-executed-source','migration-source-checkpoint.json','provenance']:
  src=source/name;dst=out/'provenance'/name
  if src.is_dir():shutil.copytree(src,dst)
  elif src.is_file():dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
 for f in (out/'provenance').rglob('*') if (out/'provenance').exists() else []:
  if f.is_file():ancestry[str(f.relative_to(out))]=digest(f.read_bytes())
 state['migration']['ancestry_files']=ancestry
 # Remove old closing receipts so completion always requires new current closing validation.
 if not offline:state['artifacts']=[a for a in state['artifacts'] if a['role'] not in ['root-end','contents-end']]
 state['inventory_bound_artifacts']=len(state['artifacts']);state['inventory_sha256']=digest(canon(sorted(rebuild(out,state)['nodes'].values(),key=lambda n:n['id'])));save(out/'checkpoint.json',state)
 if offline:return write_outputs(out,state,rebuild(out,state))
 return collect(cfg,out,True)

def collect(cfg,out,resume=False):
 from .browser import Browser
 out=Path(out).resolve()
 if out.exists() and any(out.iterdir()) and not resume:raise QualificationError('Output is nonempty; choose a fresh directory or --resume')
 out.mkdir(parents=True,exist_ok=True)
 if resume:
  state=read(out/'checkpoint.json');check_cache(out,state)
  if state.get('network_prohibited'):raise AccessStop('This derivative is read-only; collection resume is prohibited')
  old={k:v for k,v in state['config'].items() if k not in ['max_items','gate_dir']};new={k:v for k,v in cfg.items() if k not in ['max_items','gate_dir']}
  if old!=new:raise QualificationError('Resume configuration/identity mismatch')
  if any(e.get('access_stop') for e in state.get('errors',[])):raise AccessStop('Retained access stop requires operator review; no automatic resume')
  state['errors']=[];state['limited']=False;state['config']=cfg
 else:
  state={'schema_version':VERSION,'created_at':now(),'config':cfg,'artifacts':[],'errors':[],'limited':False,'code_fingerprint':code_fingerprint()};save(out/'checkpoint.json',state)
  snap=out/'executed-source';snap.mkdir()
  for p in Path(__file__).parent.glob('*.py'):shutil.copyfile(p,snap/p.name)
 data=None
 try:
  with Browser(cfg['family'],out,cfg.get('gate_dir')) as browser:
   def get(role,url,bootstrap=False,method='GET'):
    raw,meta=browser.bootstrap(url) if bootstrap else (browser.fetch(url,method=method) if method!='GET' else browser.fetch(url));a=artifact(out,state,role,raw,meta);browser.check(raw,meta);return raw,a
   if not state.get('identity'):
    raw,a=get('discovery',cfg['url'],True);base=clean_url(a['url'])
    if family_of(base)!=cfg['family']:raise QualificationError('Publisher migration requires explicit source review')
    if cfg['family']=='ecode360':
     got=identity(raw,base,cfg['family']);alias='https://ecode360.com/'+str(got['customer_id'])
     if not cfg.get('subtree') and base!=alias:raw,a=get('discovery',alias,True);base=alias;got=identity(raw,base,cfg['family'])
    else:
     pubs=municipal_publications(raw,base);save(out/'publications.json',pubs)
     selected=cfg.get('publication')
     if selected:
      target=clean_url(selected if selected.startswith('https://') else 'https://'+urlsplit(base).netloc+'/'+selected.strip('/'))
      if target not in {p['url'] for p in pubs} and target!=base:raise QualificationError('Publication selector not observed on publisher page')
      if target!=base:raw,a=get('discovery',target,True);base=target
     elif len(urlsplit(base).path.strip('/').split('/'))!=1 or base.endswith('/'):
      raise QualificationError('Select an observed publication root with --publication')
     else:base='https://'+urlsplit(base).netloc+'/'+urlsplit(base).path.strip('/').split('/')[0]
     if clean_url(a['url'])!=base:raw,a=get('discovery',base,True)
     got=identity(raw,base,cfg['family'],base)
    jurisdiction_check(got,cfg.get('jurisdiction'),cfg.get('state'));state['identity']=got;state['publication_url']=base;save(out/'checkpoint.json',state)
    # Preserve exact independent start source even when bootstrap served as discovery.
    artifact(out,state,'root-start',raw,{k:v for k,v in a.items() if k not in ['role','path','sha256','bytes']})
   else:
    # Browser needs an ordinary document origin; retained source is not network authority for a new session.
    raw,a=get('resume-bootstrap',state['publication_url'],True)
    if edition(identity(raw,a['url'],cfg['family'],state['publication_url']))!=edition(state['identity']):raise QualificationError('Resume edition drift')
   base=state['publication_url']
   if cfg['family']=='municipal.codes':
    if not any(a['role']=='contents-start' for a in state['artifacts']):
     # The contents route must be present in the retained root DOM.
     root=next(a for a in state['artifacts'] if a['role']=='root-start');sp=soup(load_artifact(out,root));candidates=[urljoin(base,x.get('href') or x.get('data-source')) for x in sp.select('[href],[data-source]') if (x.get('href') or x.get('data-source') or '').split('?')[0].rstrip('/').endswith('/contents')]
     contents=next((u.split('?')[0] for u in candidates if clean_url(u).startswith(base+'/contents')),None)
     if not contents:raise QualificationError('Independent complete contents route not observed')
     state['contents_url']=contents;save(out/'checkpoint.json',state);get('contents-start',contents)
    if 'native_export' not in state:
     root=next(a for a in state['artifacts'] if a['role']=='root-start');sp=soup(load_artifact(out,root));link=next((x for x in sp.select('.sitenavbar-share a') if x.get_text(' ',strip=True)=='This Page'),None)
     enabled=bool(link and link.get('href') and 'disabled' not in link.get('class',[]));state['native_export']={'whole_publication_control_enabled':enabled,'observed_href':link.get('href') if link else None,'method':'Ordinary chapter bulk HTML traversal' if not enabled else 'Observed publisher root Share/Save HTML export'};save(out/'checkpoint.json',state)
     if enabled:
      try:
       raw,meta=browser.native_html();artifact(out,state,'native',raw,{**meta,'status':meta.get('http_status'),'headers':{'content-type':'text/html'}});browser.check(raw,{**meta,'status':200,'headers':{'content-type':'text/html'}})
      except AccessStop:raise
      except Exception as e:
       if browser.blocked:raise AccessStop('Native export access stop')
       state['native_export']['optional_transport_error']=str(e);save(out/'checkpoint.json',state)
   data=rebuild(out,state);count=0
   if cfg['family'] in ['ecode360','municipal.codes']:
    while True:
     pending=[n for nid,n in data['nodes'].items() if nid not in data['dispositions']]
     if not pending:break
     if cfg.get('max_items') is not None and count>=cfg['max_items']:state['limited']=True;break
     n=pending[0];get('content',n['url']);count+=1;data=rebuild(out,state);state['inventory_bound_artifacts']=len(state['artifacts']);state['inventory_sha256']=digest(canon(sorted(data['nodes'].values(),key=lambda n:n['id'])));save(out/'checkpoint.json',state);print(json.dumps({'event':'progress','pages':count,'inventory':len(data['nodes']),'owned':len(data['records']),'remaining':len(set(data['nodes'])-set(data['dispositions']))}),flush=True)
   if not state['limited']:
    # Required assets are individually hash-bound. Access stops terminate all subsequent traffic.
    while True:
     pending_assets=[u for u,a in data['assets'].items() if not a]
     if not pending_assets:break
     u=pending_assets[0]
     if u.startswith('data:'):
      head,payload=u.split(',',1);raw=base64.b64decode(payload,validate=True) if ';base64' in head else __import__('urllib.parse').parse.unquote_to_bytes(payload);artifact(out,state,'asset',raw,{'url':u,'requested_url':u,'status':200,'headers':{'content-type':head[5:].split(';')[0]},'retrieved_at':now(),'transport':'embedded data URI'})
     elif urlsplit(u).scheme not in ['https','http']:raise QualificationError('Unsupported required asset '+u[:100])
     else:
      head=next((a for a in state['artifacts'] if a['role']=='asset-head' and a['requested_url']==u and a.get('status')==200),None)
      if not head:_,head=get('asset-head',u,method='HEAD')
      if not head['headers'].get('content-type','').lower().startswith('image/'):get('asset',u)
     data=rebuild(out,state)
    get('root-end',base)
    if cfg['family']=='municipal.codes':get('contents-end',state['contents_url'])
 except Exception as e:
  state['errors'].append({'type':type(e).__name__,'message':str(e),'at':now(),'access_stop':isinstance(e,AccessStop) or ('browser' in locals() and getattr(browser,'blocked',False))});save(out/'checkpoint.json',state)
 try:
  data=rebuild(out,state) if state.get('identity') else {'nodes':{},'records':{},'dispositions':{},'conflicts':[],'duplicate_witnesses':[],'assets':{},'start':None,'end':None,'toc_start':None,'toc_end':None}
  state['inventory_bound_artifacts']=len(state['artifacts']);state['inventory_sha256']=digest(canon(sorted(data['nodes'].values(),key=lambda n:n['id'])));save(out/'checkpoint.json',state);report=write_outputs(out,state,data)
 except Exception as e:
  state['errors'].append({'type':type(e).__name__,'message':str(e),'at':now(),'access_stop':False});save(out/'checkpoint.json',state);report={'complete':False,'publication_text_complete':False,'attachments_complete':False,'edition_complete':False,'jurisdiction_complete':False,'errors':state['errors']};save(out/'coverage.json',report)
 return report

def verify(out):
 out=Path(out).resolve();state=read(out/'checkpoint.json');check_cache(out,state);data=rebuild(out,state);report=coverage(state,data)
 expected=[data['records'][k] for k in sorted(data['records'])];actual=[json.loads(line) for line in (out/'records.jsonl').read_text().splitlines()]
 if len({r['id'] for r in actual})!=len(actual):raise QualificationError('Duplicate normalized IDs')
 if actual!=expected:raise QualificationError('Normalized records disagree with retained source')
 if read(out/'inventory.json')!=sorted(data['nodes'].values(),key=lambda n:n['id']):raise QualificationError('Published inventory disagrees with source')
 if read(out/'dispositions.json')!=sorted(data['dispositions'].values(),key=lambda n:n['id']):raise QualificationError('Published dispositions disagree with source')
 if read(out/'link-ledger.json')!=data.get('link_ledger',[]):raise QualificationError('Link ledger disagrees with source')
 if read(out/'image-omissions.json')!={'placeholders':[im for r in expected for im in r.get('image_references',[])],'references':data.get('image_refs',[])}:raise QualificationError('Image omission ledger disagrees with source')
 if read(out/'coverage.json')!=report:raise QualificationError('Coverage claim disagrees with independent recomputation')
 fields=['id','jurisdiction','state','heading','kind','parent_id','path','text','source_url','body_sha256'];stream=io.StringIO(newline='');w=csv.DictWriter(stream,fieldnames=fields);w.writeheader()
 for r in expected:w.writerow({k:json.dumps(r[k],ensure_ascii=False) if isinstance(r.get(k),(list,dict)) else r.get(k) for k in fields})
 if (out/'records.csv').read_bytes()!=stream.getvalue().encode():raise QualificationError('CSV disagrees with source')
 return {'verified':True,**report}
