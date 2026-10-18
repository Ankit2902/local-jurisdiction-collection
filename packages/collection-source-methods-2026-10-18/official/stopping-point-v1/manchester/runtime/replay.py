#!/usr/bin/env python3
"""Reparse a complete retained acquisition into a fresh current-runtime bundle.

No source acquisition is permitted. Original evidence is read-only; all source
and closing receipts are copied and rebound to current parsed output. This is a
retained-source replay, never a fresh current-edition network observation.
"""
import argparse,contextlib,csv,json,pathlib,shutil,sys
import collect,model,transport
PARSER_KEYS={'pdf_normalization','inventory_label_exclusions','resolve_internal_router_references','native_label_attachment_rules'}

@contextlib.contextmanager
def offline():
 original=collect.fetch_raw
 def cached(run,name,url,config,**kwargs):
  ref=pathlib.Path(run)/'raw'/(model.sha(name.encode())[:20]+'.bin')
  if not ref.exists() or not ref.with_suffix('.receipt.json').exists():raise ValueError('Retained replay missing observed source; network is forbidden: '+name)
  return original(run,name,url,config,fresh=False)
 collect.fetch_raw=cached
 try:yield
 finally:collect.fetch_raw=original

def initialize(config,out,source):
 source=pathlib.Path(source).resolve();c=collect.load(config);prior=collect.load(source/'config.json');old=collect.load(source/'checkpoint.json')
 if model.sha(model.encoded(prior))!=old['config_sha256']:raise ValueError('Retained source config binding corrupt')
 acquisition=lambda value:{k:v for k,v in value.items() if k not in PARSER_KEYS}
 if model.encoded(acquisition(c))!=model.encoded(acquisition(prior)):raise ValueError('Retained replay source/publication/selection/edition config differs; only declared normalization policies may change')
 if not old.get('completed') or set(old['done'])!={i['id']for i in old['items']} or len(old['done'])!=len(set(old['done'])):raise ValueError('Retained replay requires a terminal full acquired inventory; partial input cannot be promoted')
 if model.sha(model.encoded(collect.load(source/'inventory.json')))!=old['inventory_sha256'] or collect.load(source/'inventory.json')!=old['items']:raise ValueError('Retained source inventory hash/content mismatch')
 for name,digest in old['scripts'].items():
  if model.sha((source/'executed'/name).read_bytes())!=digest:raise ValueError('Retained executed-source snapshot corrupt')
 for item in old['items']:
  expected='raw/'+model.sha(('item:'+item['id']).encode())[:20]+'.bin'
  if item.get('raw_ref')!=expected:raise ValueError('Retained item/source identity crosswire')
  receipt=collect.load((source/expected).with_suffix('.receipt.json'))
  if receipt.get('url')!=item['url'] or receipt.get('request_name')!='item:'+item['id'] or not receipt.get('success',receipt.get('status')==200) or receipt.get('access_stop'):raise ValueError('Retained item acquisition failed or mismatched requested URL')
  if receipt.get('download_url') and model.key(receipt['download_url'])!=item['id']:raise ValueError('Retained native download source differs from selected item')
  doc=collect.load(source/'items'/(model.sha(item['id'].encode())[:24]+'.json'))
  if doc['item']!=item or doc['raw_sha256']!=receipt['sha256']:raise ValueError('Retained item metadata/source binding mismatch')
 out.mkdir(parents=True);(out/'raw').mkdir();(out/'items').mkdir();(out/'executed').mkdir()
 witnesses=[]
 for receipt in sorted((source/'raw').glob('*.receipt.json')):
  meta=collect.load(receipt);raw=receipt.with_name(receipt.name.replace('.receipt.json','.bin'))
  if not raw.exists() or model.sha(raw.read_bytes())!=meta.get('sha256'):raise ValueError('Retained raw/receipt bytes corrupt')
  extra=raw.with_name(raw.name+'.legal.html');files=[raw,receipt]
  if meta.get('legal_response'):
   if not extra.exists() or model.sha(extra.read_bytes())!=meta['legal_response']['sha256']:raise ValueError('Retained native body response corrupt')
   files.append(extra)
  for file in files:shutil.copyfile(file,out/'raw'/file.name)
  witnesses.append({'raw_ref':'raw/'+raw.name,'sha256':meta['sha256'],'receipt_sha256':model.sha(receipt.read_bytes()),'request_name':meta.get('request_name'),'url':meta.get('url')})
 with offline():items,identity=collect.discover(out,c)
 old_items={i['id']:i for i in old['items']};seen=set();cursor=0
 while cursor<len(items):
  item=items[cursor];cursor+=1
  if item['id']in seen:raise ValueError('Duplicate retained replay inventory identity')
  seen.add(item['id']);previous=old_items.get(item['id'])
  if not previous:raise ValueError('Current discovery requires a source document absent from retained inventory')
  item['raw_ref']=previous['raw_ref'];data=(out/item['raw_ref']).read_bytes()
  if item['kind']!=previous['kind'] or item['url']!=previous['url']:raise ValueError('Current discovery selected a different source document')
  if c['mode']in ['legacy_codepublishing','html_graph']:
   known={i['id']for i in items}
   for extra in collect.discover_graph(data,item['url'],c):
    if extra['id']not in known:items.append(extra);known.add(extra['id'])
 if seen!=set(old_items):raise ValueError('Current source-derived inventory does not close over the complete retained document set')
 scripts=collect.runtime_scripts()
 for name in scripts:shutil.copyfile(collect.BASE/name,out/'executed'/name)
 collect.save(out/'config.json',c);collect.save(out/'inventory.json',items)
 provenance={'schema':1,'kind':'retained_source_replay','network_requests':0,'original_source_path_provenance':str(source),'source_checkpoint_sha256':model.sha((source/'checkpoint.json').read_bytes()),'source_config_sha256':model.sha((source/'config.json').read_bytes()),'source_record_bytes_sha256':model.sha((source/'records.jsonl').read_bytes()),'original_reported_consistency':old.get('consistency'),'original_runtime':old['scripts'],'normalization_policy_delta':{k:[prior.get(k),c.get(k)]for k in sorted(PARSER_KEYS)if prior.get(k)!=c.get(k)},'source_witnesses':witnesses,'claim':'Complete retained acquisition reparsed under current executed source; no fresh acquisition, currentness observation or universal PDF semantics claimed.'}
 collect.save(out/'retained-replay.json',provenance)
 state={'schema':1,'config_sha256':model.sha(model.encoded(c)),'code_binding':model.sha(model.encoded(scripts)),'scripts':scripts,'started_at':transport.now(),'items':items,'done':[],'completed':False,'identity':identity,'consistency':old.get('consistency'),'item_consistency':old.get('item_consistency',[]),'inventory_sha256':model.sha(model.encoded(items)),'limits_history':[],'command':sys.argv,'runtime':{'python':sys.version,'network':'forbidden retained-source replay'},'invocations':[],'retained_replay_sha256':model.sha((out/'retained-replay.json').read_bytes()),'retained_asset_downloads':{i['id']:collect.load(source/'items'/(model.sha(i['id'].encode())[:24]+'.json')).get('asset_downloads',[])for i in old['items']}}
 collect.save(out/'checkpoint.json',state);return c,state

def asset_ledger(out,rows,dispositions,old,c):
 source=next((d['archive']['assets']for d in dispositions if 'archive'in d),None)
 if source is None:source=[a for r in rows for a in r.get('assets',[])+r.get('document_assets',[])]
 referenced={a['url']for a in source};result=[]
 for asset in old:
  if asset['url']not in referenced:continue
  if model.publication_refs.router_target(asset['url'],c):continue
  asset=dict(asset)
  if asset.get('status','').startswith('acquired'):
   if any(a['url']==asset['url']and (model.image_asset(a)or a.get('status')=='policy_omitted_image')for a in source):raise ValueError('Separate image acquisition cannot be imported into replay')
   ref='raw/'+model.sha(('asset:'+asset['url']).encode())[:20]+'.bin';receipt=collect.load((out/ref).with_suffix('.receipt.json'));data=(out/ref).read_bytes()
   if asset.get('raw_ref')!=ref or receipt['url']!=asset['url'] or model.sha(data)!=asset['sha256']or receipt['sha256']!=asset['sha256']:raise ValueError('Required asset raw/source identity mismatch')
   q=model.qualify_attachment(data,asset['url'],c)
   if q is not None:asset['qualification']=q
  result.append(asset)
 return result

def run(config,out,source=None,resume=False,interrupt_after=None):
 out=pathlib.Path(out).resolve()
 if resume:
  if not(out/'retained-replay.json').exists():raise ValueError('Resume requires a retained replay bundle')
  c=collect.load(out/'config.json');state=collect.load(out/'checkpoint.json')
  if model.encoded(c)!=model.encoded(collect.load(config))or state['scripts']!=collect.runtime_scripts():raise ValueError('Retained replay resume config/runtime mismatch')
  if state['retained_replay_sha256']!=model.sha((out/'retained-replay.json').read_bytes()):raise ValueError('Retained replay provenance corrupt')
  with offline():collect.validate_cached(out,state,c)
 else:
  if source is None:raise ValueError('--replay-from source is required for a fresh retained replay')
  if out.exists()and any(out.iterdir()):raise ValueError('Retained replay output must be fresh')
  if out.exists():out.rmdir()
  c,state=initialize(config,out,source)
 state['invocations'].append({'command':sys.argv,'resume':resume,'started_at':transport.now()});collect.save(out/'checkpoint.json',state);count=0
 try:
  for item in state['items']:
   if item['id']in state['done']:continue
   data=(out/item['raw_ref']).read_bytes();collect.check_edition(data,c);rows,dispositions=collect.parse_item(data,item,c);assets=asset_ledger(out,rows,dispositions,state['retained_asset_downloads'].get(item['id'],[]),c)
   collect.save(out/'items'/(model.sha(item['id'].encode())[:24]+'.json'),{'item':item,'raw_sha256':model.sha(data),'records':rows,'dispositions':dispositions,'asset_downloads':assets});state['done'].append(item['id']);collect.save(out/'checkpoint.json',state);count+=1
   if interrupt_after is not None and count>=interrupt_after:raise InterruptedError('Retained replay interrupted after durable item boundary')
  state['completed']=True
  with offline():same=collect.recompute_consistency(out,c,state)
  if state.get('consistency'):state['consistency']['consistent']=same;state['consistency']['recomputed_under_retained_replay']=True
  state['finished_at']=transport.now();state.pop('last_error',None);collect.save(out/'checkpoint.json',state)
 except Exception as error:
  state['completed']=False;state['last_error']=str(error);collect.save(out/'checkpoint.json',state)
 records=[]
 for item in state['items']:
  path=out/'items'/(model.sha(item['id'].encode())[:24]+'.json')
  if path.exists():records+=collect.load(path)['records']
 transport.atomic(out/'records.jsonl',collect.lines(records))
 with(out/'records.csv').open('w',newline='')as f:
  writer=csv.DictWriter(f,fieldnames=['id','document_id','unit','jurisdiction','state','publication','heading','source_url','text','raw_ref','raw_sha256'],extrasaction='ignore');writer.writeheader();writer.writerows(records)
 import attachment_outputs
 attachment_outputs.write(out,c,state)
 with offline():coverage=collect.reconcile(out)
 collect.save(out/'coverage.json',coverage);print(json.dumps({'retained_source_replay':True,'network_requests':0,'coverage':collect.brief(coverage)},indent=2));return 0 if coverage['requested_coverage_complete']else 3

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--config',required=True,type=pathlib.Path);p.add_argument('--out',required=True,type=pathlib.Path);p.add_argument('--replay-from',type=pathlib.Path);p.add_argument('--resume',action='store_true');p.add_argument('--interrupt-after',type=int);a=p.parse_args()
 try:raise SystemExit(run(a.config,a.out,a.replay_from,a.resume,a.interrupt_after))
 except Exception as error:print(str(error),file=sys.stderr);raise SystemExit(3)
