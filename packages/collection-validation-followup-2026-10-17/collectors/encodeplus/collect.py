#!/usr/bin/env python3
"""Full dynamic publication traversal by default. Limits always force incomplete."""
import argparse,base64,datetime,importlib.metadata,json,pathlib,platform,re,shutil,sys,time,urllib.parse
from bs4 import BeautifulSoup
from .util import atomic_bytes,atomic_json,digest,hash_json,read_json,validate_file
from .model import inventory,decode,parse_document,outputs
from .transport import fetch
from .documents import qualify_document
HERE=pathlib.Path(__file__).resolve().parent
TARGETS=read_json(HERE/'targets.json')
def code_hashes():return {p.name:digest(p.read_bytes()) for p in sorted(HERE.glob('*.py')) if p.name!='tests.py'}|{name:digest((HERE/name).read_bytes()) for name in ['targets.json','requirements.txt']}
def runtime_info():
 packages={}
 for name in ['beautifulsoup4','brotli','pypdf','fonttools','pdfplumber','pypdfium2','pdfminer.six','cryptography']:
  try:packages[name]=importlib.metadata.version(name)
  except importlib.metadata.PackageNotFoundError:packages[name]=None
 return {'python':platform.python_version(),'os':platform.platform(),'packages':packages}
def ensure_revision(state):
 if 'code_hashes' in state:
  assert code_hashes()==state['code_hashes'],'Collector source changed during run; explicit upgrade/revalidation required'
  assert runtime_info()==state['runtime'],'Collector runtime/dependencies changed during run; explicit upgrade/revalidation required'
def cached(out,url,path,timeout=120):
 original=pathlib.Path(path);attempt=0
 while True:
  candidate=original if not attempt else original.with_name(original.stem+'.attempt-'+str(attempt)+original.suffix);raw=out/candidate;meta=raw.with_name(raw.name+'.receipt.json')
  if not raw.exists() and not meta.exists():
   try:data,m=fetch(url,raw,timeout=timeout)
   except Exception as exc:exc.evidence_path=str(candidate);raise
   return data,m|{'_retained_path':str(candidate)}
  m=read_json(meta);assert m['url']==url,'Mismatched cached URL';data=raw.read_bytes();assert digest(data)==m['sha256'],'Corrupt cached request'
  if m['http_status']==200 and not m.get('challenge'):return data,m|{'_retained_path':str(candidate)}
  # Only an explicit later cache invocation/resume can create ONE new attempt.
  # Failed bytes/receipts remain immutable. 403/challenges/stops never become retryable.
  retryable=m['http_status'] in [None,429] and not m.get('challenge') and not m.get('preexisting_stop') and not m.get('blocked_by_stop') and not m.get('redirect_failure')
  assert retryable,'Mismatched/failed cached request; retained refusal or nontransient HTTP failure'
  attempt+=1

def entry(path,meta):return {'path':meta.get('_retained_path',path),'sha256':meta['sha256'],'url':meta['url']}
def get_inventory(out,url,path,cfg):
 data,m=cached(out,url,path);return inventory(decode(data,m['headers']),cfg),entry(path,m)
def checkpoint(out,state):atomic_json(out/'checkpoint.json',state)
def assemble(out,state,inv):
 known={n['id']:n for n in inv['nodes']};records={};duplicates=[]
 for block in state['blocks']:
  p=validate_file(out,block['path'],block['sha256']);m=read_json(p.with_name(p.name+'.receipt.json'));parsed=parse_document(decode(p.read_bytes(),m['headers']),block['requested'],state['config'],known,state.get('image_skips',{}))
  for r in parsed:
   r['raw_path']=block['path'];r['raw_sha256']=block['sha256']
   if r['id'] in records:
    # Same canonical owned content may be repeated by another container response; suppress, record disposition.
    if records[r['id']]['body_sha256']!=r['body_sha256'] or records[r['id']]['path']!=r['path']:raise ValueError('Conflicting repeated source body '+r['id'])
    duplicates.append({'id':r['id'],'disposition':'identical source body suppressed','block':block['path']});continue
   records[r['id']]=r
 return records,duplicates

def merge_parsed(records,duplicates,parsed,block):
 for r in parsed:
  r['raw_path']=block['path'];r['raw_sha256']=block['sha256']
  if r['id'] in records:
   previous=records[r['id']]
   if previous['body_sha256']!=r['body_sha256'] or previous['path']!=r['path']:raise ValueError('Conflicting repeated source body '+r['id'])
   duplicates.append({'id':r['id'],'disposition':'identical source body suppressed','block':block['path']})
  else:records[r['id']]=r

def full_export_candidates(blocks,records,known):
 """A root may emit only its own HTML while its observed body-key subtree spans the whole publication."""
 if not set(known).issubset(records):return []
 result=[]
 for block in blocks:
  root=records.get(block['requested']);key=root.get('canonical_body_key') if root else None
  if key and all(r.get('canonical_body_key') and (r['canonical_body_key']==key or r['canonical_body_key'].startswith(key+'-')) for r in records.values()):result.append(block)
 return result

def native_export(out,state,start_html):
 ensure_revision(state);attempt=state.get('native_attempt',0);state['native_attempt']=attempt+1;checkpoint(out,state);prefix='native/attempt-'+str(attempt)+'/'
 soup=BeautifulSoup(start_html,'html.parser');control=soup.find('a',title='Export PDF');assert control,'No visible native export control';m=re.search(r'OpenPDF\("([^\"]+)",false',control.get('onclick',''));assert m,'Unsupported native export control'
 script=next((s['src'] for s in soup.find_all('script',src=True) if urllib.parse.urlparse(s['src']).path.endswith('/doc-view.js')),None);assert script,'No observed application script'
 js,meta=cached(out,urllib.parse.urljoin(state['config']['base'],script),'native/observed-doc-view.js');assert 'var mURL = "export2doc.aspx?pdf=1&tocid=" + id' in decode(js,meta['headers']),'Export mapping changed'
 url=state['config']['base']+'export2doc.aspx?'+urllib.parse.urlencode({'pdf':1,'tocid':m.group(1)});raw,meta=cached(out,url,prefix+'status.html');text=decode(raw,meta['headers']) if not raw.startswith(b'%PDF-') else '';poll=re.search(r"\$\.get\('([^']+)'",text)
 if raw.startswith(b'%PDF-'):
  pdf=raw;pm=meta;path=prefix+'publication.pdf';atomic_bytes(out/path,pdf);atomic_json(out/(path+'.receipt.json'),meta)
 else:
  assert poll,'No observed export polling URL';pollurl=urllib.parse.urljoin(url,poll.group(1));result=None
  # Each explicit collection/resume attempt has separate poll evidence. Failed/timeout receipts are immutable.
  deadline=time.monotonic()+600
  for i in range(30):
   ensure_revision(state)
   if time.monotonic()>=deadline:raise ValueError('Native full export not ready within600second bounded wait')
   if i:time.sleep(5)
   data,pr=cached(out,pollurl,prefix+'poll-'+str(i)+'.json',timeout=max(1,min(600,deadline-time.monotonic())));ensure_revision(state);result=json.loads(decode(data,pr['headers']));assert not result.get('Failed'),result.get('Msg')
   if result.get('Ready'):break
  else:raise ValueError('Native full export not ready within30bounded polls')
  final=url+'&'+urllib.parse.urlencode({'file':result['File']});pdf,pm=cached(out,final,prefix+'publication.pdf');path=pm.get('_retained_path',prefix+'publication.pdf')
 integrity=qualify_document(pdf,pm['url'],'application/pdf')
 return {'status':'downloaded','document_integrity':integrity,'path':path,'sha256':digest(pdf),'bytes':len(pdf),'url':pm['url'],'scope':'Entire observed TOCroot control '+m.group(1),'tocid':m.group(1),'content_completeness':'Unverified native file: transport alone does not establish text/asset completeness'}
def collect(target,out,resume=False,max_items=None,skip_assets=False,want_native=False,interrupt_after=None,config=None,upgrade_code=False,retry_native=False):
 from .verify import verify
 assert not retry_native or (resume and want_native),'--retry-native-export requires --resume and --native-export'
 cfg=config if config is not None else TARGETS[target];assert set(['identity','base','jurisdiction','scope']).issubset(cfg),'Config requires explicit identity/base/jurisdiction/scope';assert cfg['base'].startswith('https://') and cfg['base'].endswith('/'),'Config base must be canonical HTTPS publication directory';out=pathlib.Path(out)
 if resume:
  state=read_json(out/'checkpoint.json');assert state['config']==cfg and state['config_sha256']==hash_json(cfg),'Wrong target/config checkpoint';assert state['options']=={'max_items':max_items,'skip_assets':skip_assets,'native_export':want_native},'Resume options must match checkpoint'
  if state['code_hashes']!=code_hashes() or state.get('runtime')!=runtime_info():
   assert upgrade_code,'Wrong collector version checkpoint; use explicit --upgrade-code after reviewing retained evidence'
   for name,h in state['code_hashes'].items():validate_file(out,'script-versions/'+h+pathlib.Path(name).suffix,h)
   for raw in out.rglob('*.receipt.json'):
    meta=read_json(raw);source=raw.with_name(raw.name[:-len('.receipt.json')]);assert digest(source.read_bytes())==meta['sha256'],'Corrupt retained request during upgrade'
   old_hash=digest((out/'checkpoint.json').read_bytes());atomic_bytes(out/'checkpoint-history'/(old_hash+'.json'),(out/'checkpoint.json').read_bytes());old_versions=state['code_hashes'];current=code_hashes()
   for name,h in current.items():
    destination=out/'script-versions'/(h+pathlib.Path(name).suffix)
    if not destination.exists():shutil.copy2(HERE/name,destination)
   state.setdefault('code_upgrades',[]).append({'prior_checkpoint_sha256':old_hash,'prior_code_hashes':old_versions,'current_code_hashes':current,'command':sys.argv,'reason':'Explicit parser/collector upgrade; retained requests hashes verified; all source reparsed and closing checks refreshed'});state['code_hashes']=current;state.setdefault('runtime_history',[]).append(state.get('runtime'));state['runtime']=runtime_info();state['code_upgrades'][-1]['runtime']=state['runtime']
   # Reconstruct all records under the new parser; never keep a prior complete flag or end check.
   state['phase']='upgrade-revalidation';state['rebuild_block_ids']=True;checkpoint(out,state)
  if state['phase']=='finished' and not retry_native:
   from .verify import verify
   return verify(out)
  if retry_native:
   prior=(out/'checkpoint.json').read_bytes();prior_hash=digest(prior);atomic_bytes(out/'native-retry-history'/(prior_hash+'.json'),prior)
   state.setdefault('native_export_retries',[]).append({'prior_checkpoint_sha256':prior_hash,'prior_native_export':state.get('native_export'),'command':sys.argv,'reason':'Explicit native export retry; earlier attempt/result retained and all closing checks refreshed'})
   state['phase']='native-retry-requested';checkpoint(out,state)
  state['generation']=state.get('generation',0)+1;state['end_blocks']=[];state.pop('end_inventory',None);state.pop('end_inventory_sha256',None);checkpoint(out,state)
 else:
  assert not upgrade_code,'--upgrade-code requires --resume'
  assert not out.exists() or not any(out.iterdir()),'Fresh output must be unpopulated';out.mkdir(parents=True,exist_ok=True)
  versions=out/'script-versions';versions.mkdir();hashes=code_hashes()
  for name,h in hashes.items():shutil.copy2(HERE/name,versions/(h+pathlib.Path(name).suffix))
  state={'schema_version':1,'target':target,'config':cfg,'custom_config':config is not None,'config_sha256':hash_json(cfg),'code_hashes':hashes,'command':sys.argv,'runtime':runtime_info(),'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'options':{'max_items':max_items,'skip_assets':skip_assets,'native_export':want_native},'generation':0,'blocks':[],'assets':{},'asset_failures':{},'image_skips':{},'phase':'inventory','failures':[],'end_blocks':[],'native_export':None};checkpoint(out,state)
 try:
  ensure_revision(state);inv,invraw=get_inventory(out,cfg['base']+'doc-view.aspx','inventory/start.html',cfg);ensure_revision(state)
  if state.get('inventory_sha256'):assert state['inventory_sha256']==inv['sha256'],'Inventory checkpoint mismatch'
  else:state['inventory_sha256']=inv['sha256'];state['inventory_raw']=invraw;checkpoint(out,state)
  atomic_json(out/'inventory.json',inv);known={n['id']:n for n in inv['nodes']}
  if state.pop('rebuild_block_ids',False):
   for block in state['blocks']:
    raw=validate_file(out,block['path'],block['sha256']);meta=read_json(raw.with_name(raw.name+'.receipt.json'));assert meta['url']==block['url'] and meta['http_status']==200
    parsed=parse_document(decode(raw.read_bytes(),meta['headers']),block['requested'],cfg,known,state.get('image_skips',{}));block['record_ids']=[r['id'] for r in parsed]
   checkpoint(out,state)
  records,dups=assemble(out,state,inv);state['phase']='collecting';checkpoint(out,state)
  for node in inv['nodes']:
   ensure_revision(state)
   if node['id'] in records:continue
   if max_items is not None and len(state['blocks'])>=max_items:break
   path='raw/node-'+node['id']+'.html';url=cfg['base']+'doc-view.aspx?'+urllib.parse.urlencode({'secid':node['id'],'ajax':0});data,meta=cached(out,url,path);ensure_revision(state);parsed=parse_document(decode(data,meta['headers']),node['id'],cfg,known,state.get('image_skips',{}));assert parsed
   block=entry(path,meta)|{'requested':node['id'],'record_ids':[r['id'] for r in parsed]};state['blocks'].append(block);checkpoint(out,state);merge_parsed(records,dups,parsed,block)
   if interrupt_after and len(state['blocks'])>=interrupt_after:raise InterruptedError('Intentional durable checkpoint interruption')
  state['phase']='assets';checkpoint(out,state)
  required={a['url'] for r in records.values() for a in r['assets'] if a['required']}
  for url in sorted(required):
   ensure_revision(state)
   key=digest(url.encode());path='assets/'+key+'.bin'
   if skip_assets:continue
   try:
    if url.startswith('data:'):
     head,payload=url.split(',',1);data=base64.b64decode(payload) if ';base64' in head else urllib.parse.unquote_to_bytes(payload);p=out/path
     if p.exists():assert digest(p.read_bytes())==digest(data),'Corrupt dataasset'
     else:atomic_bytes(p,data)
     asset={'path':path,'sha256':digest(data),'url':url,'kind':'inline-data'}
    else:
     data,meta=cached(out,url,path);low={k.lower():v for k,v in meta['headers'].items()};ctype=low.get('content-type','')
     if meta.get('image_body_intentionally_skipped'):
      state.setdefault('image_skips',{})[url]=entry(path,meta)|{'placeholder':'[IMAGE]','disposition':'Image Content-Type; body not read/downloaded'};checkpoint(out,state);continue
     # A document-library landing page is a required unresolved document, never an acquired PDF.
     if 'html' in ctype or data.lstrip().lower().startswith((b'<!doctype html',b'<html')):raise ValueError('Required asset is HTML landing page; follow advertised file separately: '+url)
     asset=entry(path,meta)|{'content_type':ctype,'kind':'linked-binary'}
    asset['document_integrity']=qualify_document(data,url,asset.get('content_type',''))
    if url in state['assets']:assert state['assets'][url]==asset,'Changed cached asset'
    state['assets'][url]=asset;checkpoint(out,state)
    state['asset_failures'].pop(url,None);checkpoint(out,state)
   except Exception as exc:
    state['asset_failures'][url]={'reason':str(exc),'raw_path':getattr(exc,'evidence_path',path if (out/path).exists() else None)};checkpoint(out,state)
  ensure_revision(state);records,dups=assemble(out,state,inv)
  if want_native:
   try:
    candidates=full_export_candidates(state['blocks'],records,known)
    if not candidates:state['native_export']={'status':'unavailable','reason':'No observed body-key root spans the complete source inventory; TOC000export is not full legal text'}
    else:
     b=candidates[0];data=(out/b['path']).read_bytes();meta=read_json(out/(b['path']+'.receipt.json'));state['native_export']=native_export(out,state,decode(data,meta['headers']));state['native_export']['source_container']=b['requested'];state['native_export']['covers_all_toc_ids']=True
     from pypdf import PdfReader
     reader=PdfReader(out/state['native_export']['path']);pdftext=' '.join(' '.join(p.extract_text() for p in reader.pages).split());norm=lambda x:''.join(c.casefold() for c in x if c.isalnum())
     needle=norm(pdftext);missing_h=[r['id'] for r in records.values() if r['heading_source']=='body_heading' and norm(r['heading']) not in needle];missing_a=[r['id'] for r in records.values() if r['text'].replace('[IMAGE]','').strip() and norm(' '.join(r['text'].replace('[IMAGE]','').split()[:12])) not in needle]
     state['native_export'].update(pages=len(reader.pages),metadata={str(k):str(v) for k,v in reader.metadata.items()},missing_headings=missing_h,missing_body_anchors=missing_a,text_anchor_qualification=not missing_h and not missing_a,image_semantic_equivalence=False)
     state['native_export']['scope']='Entire canonical body-key subtree rooted at '+b['requested']+' covering every TOC ID; not TOC000'

   except Exception as exc:state['native_export']={'status':'failed','reason':str(exc)}
   checkpoint(out,state)
  ensure_revision(state);state['phase']='end-check';checkpoint(out,state)
  endinv,endraw=get_inventory(out,cfg['base']+'doc-view.aspx','inventory/end-'+str(state.get('generation',0))+'.html',cfg);state['end_inventory']=endraw;state['end_inventory_sha256']=endinv['sha256'];assert inv['sha256']==endinv['sha256'],'End TOC changed'
  for block in state['blocks']:
   ensure_revision(state)
   path='end-'+str(state.get('generation',0))+'/'+pathlib.Path(block['path']).name;data,meta=cached(out,block['url'],path);ensure_revision(state);parsed=parse_document(decode(data,meta['headers']),block['requested'],cfg,known,state.get('image_skips',{}));old=parse_document(decode((out/block['path']).read_bytes(),read_json(out/(block['path']+'.receipt.json'))['headers']),block['requested'],cfg,known,state.get('image_skips',{}))
   assert hash_json(parsed)==hash_json(old),'End body snapshot drift '+block['requested'];end=entry(path,meta)|{'requested':block['requested']}
   if not any(x['requested']==block['requested'] for x in state['end_blocks']):state['end_blocks'].append(end)
   checkpoint(out,state)
  ensure_revision(state);state['phase']='finished';checkpoint(out,state)
 except Exception as exc:
  failed_phase=state.get('phase');state['phase']='interrupted' if isinstance(exc,InterruptedError) else 'failed';state['failures'].append({'type':type(exc).__name__,'reason':str(exc),'phase_at_failure':failed_phase,'evidence_path':getattr(exc,'evidence_path',None)});checkpoint(out,state)
  # Interrupted runs remain resumable; previous intentional interruptions do not count as permanent collection failures.
 records,dups=assemble(out,state,inv) if state.get('inventory_sha256') else ({},[])
 for name,data in outputs(list(records.values())).items():atomic_bytes(out/name,data)
 from .verify import verify
 report=verify(out)
 try:ensure_revision(state)
 except Exception as exc:
  state['phase']='failed';state['failures'].append({'type':type(exc).__name__,'reason':str(exc),'phase_at_failure':'final-verification'});checkpoint(out,state);report=verify(out)
 atomic_json(out/'coverage.json',report);return report
if __name__=='__main__':
 sys.modules['collectors.encodeplus.collect']=sys.modules[__name__]
 p=argparse.ArgumentParser();p.add_argument('target',help='Named target key, or custom name with --config');p.add_argument('--config',type=pathlib.Path,help='Explicit pinned publication config JSON; must contain base,identity,jurisdiction,scope');p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--resume',action='store_true');p.add_argument('--upgrade-code',action='store_true',help='Explicitly revalidate unchanged retained bytes under a new collector, retaining old checkpoint and script lineage');p.add_argument('--max-items',type=int);p.add_argument('--skip-assets',action='store_true');p.add_argument('--native-export',action='store_true');p.add_argument('--retry-native-export',action='store_true',help='Explicit retry preserving prior native attempts; requires --resume --native-export and refreshes closing checks');p.add_argument('--interrupt-after',type=int,help='Explicit fault-test interruption; not a collection limit');a=p.parse_args();r=collect(a.target,a.out,a.resume,a.max_items,a.skip_assets,a.native_export,a.interrupt_after,read_json(a.config) if a.config else None,a.upgrade_code,a.retry_native_export);print(json.dumps(r,indent=2));raise SystemExit(0 if r['publication_text_complete'] and r['attachments_complete'] else 2)
