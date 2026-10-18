"""Point-and-shoot collect/normalize/verify. Works as a script or Python module."""
import argparse,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
# Direct script invocation and python -m use the same self-contained sibling modules.
if str(HERE) not in sys.path:sys.path.insert(0,str(HERE))
from profile import load_config
from source_common import load,save

def normalize(cfg,format,source,out):
 from publication_source_verify import validate
 family=cfg.family(format);validate(family,Path(source).resolve())
 if family=='flagstaff-html':from flagstaff_html_normalize import run
 elif family=='king-word':from king_word_import import run
 else:from king_normalize import run
 result=run(Path(source).resolve(),Path(out).resolve());save(Path(out)/'originals-config.json',{'config':cfg.binding(),'config_sha256':cfg.digest,'format':format,'provenance':'Explicit retained-source normalization; no fresh acquisition implied'})
 return result

def verify(cfg,out=None,source=None,normalized=None,format='html'):
 from verify import verify as replay
 if out:
  if source or normalized:raise ValueError('Use --out OR explicit --source and --normalized')
  root=Path(out).resolve();marker=load(root/'collection-start.json')
  from workflow import runtime_binding,coverage
  state=load(root/'checkpoint.json')
  mode=state.get('acquisition_mode')
  if mode not in ['live','retained_source_replay'] or marker.get('acquisition_mode','live')!=mode or (mode=='retained_source_replay')!=bool(state.get('origin')):raise ValueError('Acquisition provenance mode differs from executed start marker; retained-source replay cannot be relabelled freshlive')
  if state.get('config')!=cfg.binding() or state.get('source_identity')!={k:cfg.binding()[k] for k in ['target_id','jurisdiction','state','source_url','profile','publication','required_formats']} or state.get('code_fingerprint')!=runtime_binding():raise ValueError('Collection checkpoint source/configuration/revision binding differs')
  if marker.get('target')!=cfg.id or marker.get('publication_config')!=cfg.binding():raise ValueError('Collection target/config binding differs; foreign or unbound output cannot be promoted')
  if cfg.profile.value=='flagstaff_html':
   html=replay('flagstaff-html',root/'source',root/'normalized');word=None
  else:
   html=replay('king',root/'html-source',root/'normalized');word=replay('king-word',root/'native-source',root/'native-normalized')
  result=coverage(cfg.binding(),root,html,word,write=False);stored=load(root/'coverage.json')
  for field in ['config','required_formats','publication_text_complete','publication_bodies_acquired_and_owned','attachments_complete','legal_structure_qualified','source_consistency_complete','publication_accepted','complete','whole_jurisdiction_complete','external_adopted_legal_dependency_closure_complete','errors']:
   if stored.get(field)!=result.get(field):raise ValueError('Stored coverage differs from independently recomputed source: '+field)
  result.update(full_raw_replay_equal=True,input_files_modified=False,source_route_ledger_verified=html['source_route_ledger_verified'],opening_body_closing_chronology_verified=html['opening_body_closing_chronology_verified'],native_full_raw_replay_equal=word['full_raw_replay_equal'] if word else None,acquisition_mode=state['acquisition_mode'])
  return result
 if not source or not normalized:raise ValueError('Explicit verification requires both --source and --normalized')
 result=replay(cfg.family(format),source,normalized)
 marker=Path(normalized)/'originals-config.json'
 if marker.exists():
  binding=load(marker)
  if binding.get('config')!=cfg.binding() or binding.get('format')!=format or binding.get('config_sha256')!=cfg.digest:raise ValueError('Normalized publication config/format binding mismatch')
 return result

def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
 for action in ['collect','normalize','verify','doctor','replay']:
  p=sub.add_parser(action);p.add_argument('--config',required=True)
  if action=='collect':p.add_argument('--out',required=True);p.add_argument('--resume',action='store_true')
  elif action=='replay':p.add_argument('--source',required=True);p.add_argument('--native-source');p.add_argument('--out',required=True);p.add_argument('--resume',action='store_true')
  elif action=='normalize':p.add_argument('--source',required=True);p.add_argument('--out',required=True);p.add_argument('--format',choices=['html','word'],default='html')
  elif action=='verify':p.add_argument('--out');p.add_argument('--source');p.add_argument('--normalized');p.add_argument('--format',choices=['html','word'],default='html')
  else:p.add_argument('--source')
 args=parser.parse_args(argv)
 try:
  cfg=load_config(args.config)
  if args.command=='collect':
   from collect import main as collect
   result=collect(cfg.id,args.out,args.resume,publication_config=cfg.binding())
   if not result.get('stage'):
    from workflow import coverage
    result=coverage(cfg.binding(),args.out);save(Path(args.out)/'collection-result.json',result)
   else:
    from workflow import incomplete_coverage
    result=incomplete_coverage(cfg.binding(),args.out,result.get('errors',[]))
  elif args.command=='replay':
   from workflow import replay
   result=replay(cfg,args.source,args.out,args.native_source,args.resume)
  elif args.command=='normalize':result=normalize(cfg,args.format,args.source,args.out)
  elif args.command=='verify':result=verify(cfg,args.out,args.source,args.normalized,args.format)
  else:
   from doctor import run
   result=run(cfg.id,args.source)
  result=dict(result,family='originals',publication_config=cfg.binding(),publication_config_sha256=cfg.digest)
  print(json.dumps(result,indent=2,ensure_ascii=False));return 0 if result.get('ready_to_attempt_collection') is True and args.command=='doctor' else 0 if result.get('complete') else 2
 except Exception as e:
  print(json.dumps({'complete':False,'error':type(e).__name__,'message':str(e),'operator_action':'Keep evidence and access gates. Use the exact executed code/config for resume, or a new output for explicit retained-source normalization. Do not clear stops or change routes to force access.'},ensure_ascii=False));return 1
if __name__=='__main__':sys.exit(main())
