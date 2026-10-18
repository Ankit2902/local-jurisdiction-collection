"""Offline operator recovery. Never opens a browser, clears a gate, or fetches a URL."""
from __future__ import annotations
import datetime, io, json, platform, re, shutil, sys
from pathlib import Path
from urllib.parse import unquote, urlsplit
from .common import *
from .adapters import edition, clean_url, family_of
from .media import qualify_asset

def _timestamp(value):
 try:
  dt=datetime.datetime.fromisoformat(value.replace('Z','+00:00'))
  if dt.tzinfo is None:raise ValueError('timezone required')
  return dt.timestamp()
 except Exception as e:raise QualificationError('ISO8601 acquisition timestamp with timezone required') from e

def doctor(url,source=None,gate_dir=None):
 import os
 family=family_of(url);state=read(Path(source)/'checkpoint.json') if source else None
 if state and state['config']['family']!=family:raise QualificationError('Doctor source/family mismatch')
 if state and clean_url(url) not in {clean_url(state['config']['url']),clean_url(state.get('publication_url') or state['config']['url'])}:raise QualificationError('Doctor URL does not match retained source configuration/publication')
 gate=Path(gate_dir or (state or {}).get('config',{}).get('gate_dir') or os.environ.get('ICC_GATE_DIR','/tmp/complisolv-icc-full-gate'))/family
 stop=read(gate/'STOP.json') if (gate/'STOP.json').exists() else None
 from .engine import published_access_advisories
 advisories=published_access_advisories(family)
 result={'network_performed':False,'family':family,'source_url':url,'shared_gate_path':str(gate),'access_stop':stop,'published_access_advisories':advisories,'network_ready':not bool(stop or advisories),'python':sys.version,'platform':platform.platform(),'chrome_required':'Installed Google Chrome for live collect only','dependencies':{}}
 from importlib.metadata import version,PackageNotFoundError
 for name in ['beautifulsoup4','playwright','requests','pypdf']:
  try:result['dependencies'][name]=version(name)
  except PackageNotFoundError:result['dependencies'][name]=None
 candidates=[Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')]
 for env in ['PROGRAMFILES','PROGRAMFILES(X86)','LOCALAPPDATA']:
  if os.environ.get(env):candidates.append(Path(os.environ[env])/'Google/Chrome/Application/chrome.exe')
 chrome=next((str(p) for p in candidates if p.is_file()),None) or shutil.which('google-chrome') or shutil.which('google-chrome-stable')
 result['chrome_executable']=chrome;result['python_supported']=sys.version_info>=(3,12)
 result['dependencies_ready']=all(result['dependencies'].values()) and result['python_supported']
 result['actions']=['Do not clear STOP.json, change the gate, retry a refused route, or switch publisher host to evade the stop.','An authorised operator may supply genuine publisher downloads and source/edition/closing witnesses through export-plan and import-bundle. These commands never fetch URLs.','After publisher support confirms restored authorised access, an operator must review the persistent stop outside this collector; there is no automatic reset command.'] if stop or advisories else ['Use a fresh output, or exact-version --resume. Older versions require explicit --adopt-from into a fresh output.']
 if source:
  from .engine import code_fingerprint,load_artifact
  source=Path(source)
  for a in state['artifacts']:load_artifact(source,a)
  for name,h in state['code_fingerprint'].items():
   if digest((source/'executed-source'/name).read_bytes())!=h:raise QualificationError('Executed source snapshot corruption')
  result.update({'source_identity':state.get('identity'),'cache_raw_hashes_valid':True,'exact_runtime_revision':state.get('code_fingerprint')==code_fingerprint(),'source_network_prohibited':state.get('network_prohibited',False),'source_errors':state.get('errors',[]),'can_resume':not stop and not advisories and not state.get('network_prohibited') and state.get('code_fingerprint')==code_fingerprint() and not any(e.get('access_stop') for e in state.get('errors',[]))})
 result['transport_gate_clear']=not bool(stop);result['published_advisory_clear']=not bool(advisories);result['readiness_scope']='source_resume' if source else 'fresh_collect'
 if source:
  prohibited=state.get('network_prohibited') or any(e.get('access_stop') for e in state.get('errors',[])+state.get('operator_import',{}).get('historical_errors',[]))
  result['network_ready']=not bool(stop or advisories) and not prohibited
 result['offline_tools_ready']=result['dependencies_ready'];result['ready']=result['network_ready'] and result['dependencies_ready'] and bool(chrome) and (result.get('can_resume',True));return result

def export_plan(source,out):
 from .engine import adopt,rebuild
 source=Path(source).resolve();out=Path(out).resolve()
 if out.exists() and any(out.iterdir()):raise QualificationError('Export plan requires a fresh directory')
 out.mkdir(parents=True,exist_ok=True)
 # Requalify through current source into a separate, network-prohibited derivative.
 state=read(source/'checkpoint.json');adopt(source,out/'retained-proof',state['config'],True)
 state=read(out/'retained-proof/checkpoint.json');data=rebuild(out/'retained-proof',state)
 missing=[n for nid,n in data['nodes'].items() if nid not in data['dispositions']]
 docs=[{'source_url':u,'owners':[{'id':r['id'],'heading':r['heading']} for r in data['records'].values() if any(a['url']==u for a in r['assets'])]} for u,a in data['assets'].items() if not a]
 manifest={'schema':'icc-operator-bundle-1','identity':state['identity'],'genuine_publisher_downloads':False,'acquisition_method':'REPLACE: authorised publisher UI download or independently delivered official publisher files','files':[],'file_example':{'path':'downloads/source.html','sha256':'REPLACE','role':'content | native | asset | root-end | contents-end','source_url':'Exact observed publication/node/required-asset URL','retrieved_at':'ISO8601 timestamp with timezone','media_type':'text/html or qualified nonimage media','identity_terms':['For nonimage documents: exact source-backed title/identity phrases occurring in document text']}}
 save(out/'bundle-template.json',manifest)
 report={'network_performed':False,'identity':state['identity'],'source_config':state['config'],'missing_nodes':missing,'required_missing_documents':docs,'closing_required':{'root-end':state.get('publication_url'),'contents-end':state.get('contents_url')},'historical_errors':state.get('errors',[]),'instructions':['Keep genuine original file bytes. Do not render, OCR, extract or separately download images.','Use only authorised visible publisher download controls or official files delivered independently; this plan grants no source access and performs no requests.','Save root and, for municipal.codes, complete contents closing HTML after every supplied content/document file. Identity/edition must equal the retained source.','Fill bundle-template.json files with relative local paths, SHA256, exact observed source URL, role, MIME and real acquisition timestamp. Confirm genuine_publisher_downloads only for actual publisher files.','Every nonimage imported document needs source-backed identity_terms found in its readable text. Image-only or unmatched files remain unqualified; no OCR is attempted.','Run import-bundle into a fresh output. Full coverage is recomputed; a chapter file, missing assets or missing closing witness cannot certify the full publication.'],'claim':'A plan is not a successful acquisition or proof of available credentials.'}
 save(out/'export-plan.json',report);return report

def document_identity(raw,meta,terms,source_text):
 """Strict format + source-backed readable identity; no rendering/image extraction."""
 q=qualify_asset(raw,meta)
 if q['format']!='pdf':raise QualificationError('Operator document identity currently supports PDF only; other formats retained only after explicit adapter support')
 from pypdf import PdfReader
 reader=PdfReader(io.BytesIO(raw),strict=True);text='\n'.join(p.extract_text() or '' for p in reader.pages)
 norm=lambda s:re.sub(r'\s+',' ',s).strip().casefold()
 if not isinstance(terms,list) or not terms:raise QualificationError('Document needs source-backed identity_terms')
 for term in terms:
  if not isinstance(term,str) or len(norm(term))<5 or norm(term) not in norm(source_text):raise QualificationError('Document identity term not present in source witness')
  if norm(term) not in norm(text):raise QualificationError('Document identity term missing from PDF text: '+term)
 if len(norm(text))<30:raise QualificationError('Document has no substantive readable text; scanned/image-only content is not transcribed')
 return {**q,'identity_terms':terms,'identity_terms_matched':True,'text_sha256':digest(text.encode()),'text_characters':len(text),'qualification_scope':'Format and source-backed phrase identity only; no proof of currentness beyond pinned source witnesses.'}

def inspect_download(file,witness,source_url,out,publication=None,terms=None):
 """Qualify original publisher bytes against retained source. Never a corpus claim."""
 from .adapters import identity,parse_ecode,parse_municipal
 file=Path(file);witness=Path(witness);out=Path(out)
 if out.exists() and any(out.iterdir()):raise QualificationError('Download inspection requires fresh output')
 family=family_of(source_url);source=witness.read_bytes();raw=file.read_bytes();base=(('https://'+urlsplit(source_url).netloc+'/'+(publication or urlsplit(source_url).path.strip('/').split('/')[0])) if not (publication or '').startswith('https://') else publication) if family=='municipal.codes' else source_url
 if family=='municipal.codes' and urlsplit(base).netloc!=urlsplit(source_url).netloc:raise QualificationError('Publication host differs from source witness')
 expected=identity(source,source_url,family,base);media='application/pdf' if raw.lstrip().startswith(b'%PDF-') else 'text/html'
 witness_url=source_url
 if family=='ecode360':
  from .adapters import soup
  guid=soup(source).body.get('data-guid') or expected['customer_id'];witness_url='https://ecode360.com/'+guid
 witnessed=parse_ecode(source,witness_url,expected) if family=='ecode360' else parse_municipal(source,source_url,base,expected,{})
 selected=next((n for n in witnessed['nodes'] if clean_url(n['url'])==clean_url(source_url)),None)
 if not selected:raise QualificationError('Requested download scope not present in retained source inventory')
 meta={'requested_url':source_url,'headers':{'content-type':media}}
 if media=='application/pdf':
  from .adapters import soup
  selected_body=next((r for r in witnessed['records'] if r['id']==selected['id']),None)
  source_text=expected['name']+' '+selected['heading']+' '+(selected_body['text'] if selected_body else '')
  if not terms:raise QualificationError('PDF inspection requires --identity-term for its source-backed section/document scope, in addition to automatic publication identity')
  qualification=document_identity(raw,meta,[expected['name']]+terms,source_text);rows=[]
 else:
  known={}
  if family=='municipal.codes':
   known={n['id']:n for n in witnessed['nodes']}
  parsed=parse_ecode(raw,source_url,expected) if family=='ecode360' else parse_municipal(raw,source_url,base,expected,known)
  from .engine import equivalent_body
  source_rows={r['id']:r for r in witnessed['records']};rows=parsed['records'];matched=[];unwitnessed=[];exact_matches=0
  if not rows:raise QualificationError('Native HTML has no substantive legal bodies; title/navigation alone cannot qualify a legal download')
  for r in rows:
   if r['id'] not in source_rows:unwitnessed.append(r['id'])
   elif equivalent_body(source_rows[r['id']],r):
    matched.append(r['id']);exact_matches+=source_rows[r['id']]['body_sha256']==r['body_sha256']
   else:raise QualificationError('Native file legal body disagrees with retained source: '+r['id'])
  qualification={'format':'publisher_html','identity':parsed['identity'],'owned_content_nodes':len(rows),'source_body_matches':matched,'exact_body_hash_matches':exact_matches,'equivalent_observed_ui_matches':len(matched)-exact_matches,'source_bodies_not_independently_witnessed':unwitnessed,'table_structures':sum(len(r['tables_html']) for r in rows),'images_replaced':sum(r['image_placeholder_count'] for r in rows),'qualification_scope':'Exact parser identity and own bodies; only listed matching bodies have independent retained-source comparison. Bounded witness is not whole-publication inventory.'}
 out.mkdir(parents=True,exist_ok=True);atomic(out/'publisher-original.bin',raw);atomic(out/'source-witness.html',source);atomic(out/'records.jsonl',b''.join(canon(r)+b'\n' for r in rows))
 report={'network_performed':False,'native_file_qualified':True,'complete':False,'publication_text_complete':False,'scope':'Only supplied native file and its retained source witness; no whole-publication coverage claimed','source_url':source_url,'source_witness_url':witness_url,'selected_source_id':selected['id'],'selected_heading':selected['heading'],'identity':expected,'original_sha256':digest(raw),'source_witness_sha256':digest(source),'qualification':qualification,'provenance_level':'Operator supplied originals; inspect acquisition receipt separately. No claim of fresh transport.','image_policy':'No separate images downloaded, extracted, rendered or OCRed. Original publisher file retained as supplied; HTML normalization uses [IMAGE]. PDF is format/identity inspection only, not extracted corpus records.'}
 save(out/'download-inspection.json',report);return report

def operator_config(config):
 if not isinstance(config,dict) or not config.get('url') or not config.get('jurisdiction') or not config.get('state'):raise QualificationError('Standalone bundle needs config.url/jurisdiction/state')
 cfg={'publication':None,'subtree':False,'max_items':None,'gate_dir':None,**config};actual=family_of(cfg['url'])
 if cfg.get('family') not in [None,'auto',actual] or urlsplit(cfg['url']).scheme!='https':raise QualificationError('Standalone URL/family/HTTPS mismatch')
 cfg['family']=actual
 selected=cfg.get('publication')
 if selected and ('://' in selected) and (urlsplit(selected).scheme!='https' or urlsplit(selected).netloc!=urlsplit(cfg['url']).netloc or family_of(selected)!=actual):raise QualificationError('Standalone publication selector must remain on the configured publisher host/family')
 if set(cfg)-{'url','family','jurisdiction','state','publication','subtree','max_items','gate_dir'}:raise QualificationError('Unknown standalone bundle config fields')
 return cfg

def bootstrap_bundle(manifest,supplied,out):
 from .engine import VERSION,artifact,code_fingerprint
 from .adapters import identity,jurisdiction_check
 cfg=operator_config(manifest.get('config'));url=clean_url(cfg['url']);family=cfg['family'];selected=cfg.get('publication')
 base=clean_url(selected if selected and selected.startswith('https://') else 'https://'+urlsplit(url).netloc+'/'+selected.strip('/')) if selected else url
 starts=[(f,b) for f,b in supplied if f['role']=='root-start'];tocs=[(f,b) for f,b in supplied if f['role']=='contents-start']
 if len(starts)!=1 or starts[0][0]['source_url']!=base:raise QualificationError('Standalone bundle requires one exact selected root-start source')
 if family=='ecode360' and not cfg['subtree'] and not re.fullmatch('/[A-Z]{2}[0-9]{4}',urlsplit(base).path):raise QualificationError('Whole eCode bundle needs the observed customer-alias root, not a chapter')
 if family=='municipal.codes' and (len(tocs)!=1 or tocs[0][0]['source_url']!=base+'/contents'):raise QualificationError('Standalone municipal bundle requires independent exact contents-start')
 if family=='ecode360' and tocs:raise QualificationError('eCode uses its source TOC, not municipal contents')
 got=identity(starts[0][1],base,family,base);jurisdiction_check(got,cfg['jurisdiction'],cfg['state'])
 if manifest.get('identity') is not None and manifest['identity']!=got:raise QualificationError('Standalone expected identity differs from original root source')
 if out.exists() and any(out.iterdir()):raise QualificationError('Standalone import requires fresh output')
 out.mkdir(parents=True,exist_ok=True);(out/'executed-source').mkdir()
 for p in Path(__file__).parent.glob('*.py'):shutil.copyfile(p,out/'executed-source'/p.name)
 state={'schema_version':VERSION,'created_at':now(),'config':cfg,'publication_url':base,'identity':got,'artifacts':[],'errors':[],'limited':cfg['max_items'] is not None,'network_prohibited':True,'code_fingerprint':code_fingerprint()}
 if family=='municipal.codes':state['contents_url']=base+'/contents'
 for f,raw in starts+tocs:artifact(out,state,f['role'],raw,{'url':f['source_url'],'requested_url':f['source_url'],'status':200,'headers':{'content-type':f['media_type']},'retrieved_at':f['retrieved_at'],'transport':'operator-supplied original opening source; no collector network','operator_file_sha256':f['sha256']})
 return state

def import_bundle(source,manifest_path,out):
 from .engine import adopt,rebuild,artifact,write_outputs,verify,code_fingerprint
 source=Path(source).resolve() if source else None;manifest_path=Path(manifest_path).resolve();out=Path(out).resolve();manifest=read(manifest_path)
 if manifest.get('schema')!='icc-operator-bundle-1' or manifest.get('genuine_publisher_downloads') is not True:raise QualificationError('Genuine publisher download provenance must be explicitly supplied; template is not an acquisition')
 prior=read(source/'checkpoint.json') if source else None
 if prior and manifest.get('identity')!=prior.get('identity'):raise QualificationError('Operator bundle pinned identity/edition mismatch')
 if not isinstance(manifest.get('acquisition_method'),str) or len(manifest['acquisition_method'])<12 or manifest['acquisition_method'].startswith('REPLACE'):raise QualificationError('Actual authorised acquisition method required')
 files=manifest.get('files')
 if not isinstance(files,list) or not files:raise QualificationError('No supplied publisher files')
 # Preflight all local paths before creating output. Files must be contained regular files.
 supplied=[];seen=set()
 for f in files:
  if f.get('role') not in ['content','native','asset','root-end','contents-end']+([] if source else ['root-start','contents-start']):raise QualificationError('Unsupported operator role')
  rel=Path(f.get('path',''));path=manifest_path.parent/rel
  if rel.is_absolute() or '..' in rel.parts or not path.resolve().is_relative_to(manifest_path.parent) or path.is_symlink() or not path.is_file():raise QualificationError('Unsafe/missing operator file path')
  raw=path.read_bytes()
  if digest(raw)!=f.get('sha256'):raise QualificationError('Operator file hash mismatch')
  key=(f['role'],f.get('source_url'))
  if key in seen:raise QualificationError('Duplicate operator role/source witness')
  seen.add(key);_timestamp(f.get('retrieved_at',''))
  if _timestamp(f['retrieved_at'])>datetime.datetime.now(datetime.timezone.utc).timestamp()+300:raise QualificationError('Operator acquisition timestamp is in the future')
  mime=f.get('media_type','').lower()
  if mime.startswith('image/') or raw.lstrip().startswith((b'\x89PNG',b'\xff\xd8\xff',b'GIF87a',b'GIF89a')) or re.search(r'\.(?:svg|png|jpe?g|gif|webp|avif|tiff?)(?:[?#]|$)',f.get('source_url',''),re.I):raise QualificationError('Separate image imports forbidden; use [IMAGE] placeholders')
  if f['role']!='asset' and 'html' not in mime:raise QualificationError('Source node/closing witnesses must be original publisher HTML, not a PDF substituted for inventory')
  if f['role']!='asset':
   from .adapters import soup
   soup(raw)
  supplied.append((f,raw))
 if source:adopt(source,out,prior['config'],True);state=read(out/'checkpoint.json')
 else:state=bootstrap_bundle(manifest,supplied,out);manifest['identity']=state['identity']
 atomic(out/'operator-input.json',manifest_path.read_bytes())
 save(out/'operator-bundle.json',manifest)
 history=state.get('errors',[])+state.get('operator_import',{}).get('historical_errors',[]);state['operator_import']={'manifest_sha256':digest((out/'operator-bundle.json').read_bytes()),'input_manifest_sha256':digest((out/'operator-input.json').read_bytes()),'origin':'checkpoint_recovery' if source else 'standalone_bundle','acquisition_method':manifest['acquisition_method'],'historical_errors':history,'network_performed':False,'source_access_stop_preserved':any(e.get('access_stop') for e in history),'policy':'Operator-supplied genuine files; original live acquisition is not relabelled as successful. Persistent shared gates untouched.'};state['errors']=[]
 # Old closing receipts cannot close a newly supplied acquisition.
 state['artifacts']=[a for a in state['artifacts'] if a['role'] not in ['root-end','contents-end']]
 try:
  for f,raw in supplied:
   if f['role'] in ['root-start','contents-start']:continue
   data=rebuild(out,state);role=f['role'];u=f['source_url'];base=state['publication_url'];known={clean_url(n['url']) for n in data['nodes'].values()}
   if role=='content' and clean_url(u) not in known:raise QualificationError('Operator node URL not in observed inventory')
   if role=='native' and (state['config']['family']!='municipal.codes' or clean_url(u)!=base):raise QualificationError('Native HTML import must match selected municipal.codes publication root; chapter files use content role')
   if role=='root-end' and clean_url(u)!=base:raise QualificationError('Closing root URL mismatch')
   if role=='contents-end' and u!=state.get('contents_url'):raise QualificationError('Closing contents URL mismatch')
   meta={'url':u,'requested_url':u,'status':200,'headers':{'content-type':f['media_type']},'retrieved_at':f['retrieved_at'],'transport':'operator-supplied genuine publisher file; no collector network','operator_file_sha256':f['sha256']}
   if role=='asset':
    if u not in data['assets']:raise QualificationError('Operator document URL is not a required source reference')
    owners=[r for r in data['records'].values() if any(a['url']==u for a in r['assets'])]
    witness=' '.join([state['identity'].get('name',''),unquote(u)]+[r['heading'] for r in owners]+[l['label'] for r in owners for l in r['links'] if l['url']==u])
    if not f.get('identity_terms'):raise QualificationError('Imported PDF needs source-backed document scope identity_terms')
    meta['operator_document_identity']=document_identity(raw,meta,[state['identity']['name']]+f['identity_terms'],witness)
   artifact(out,state,role,raw,meta)
  # Closing witnesses must follow every original/supplied substantive artifact.
  body_times=[_timestamp(a['retrieved_at']) for a in state['artifacts'] if a['role'] in ['content','native','asset'] and a.get('retrieved_at')]
  for a in state['artifacts']:
   if a['role'] in ['root-start','contents-start'] and body_times and _timestamp(a['retrieved_at'])>min(body_times):raise QualificationError('Opening source postdates substantive acquisition')
   if a['role'] in ['root-end','contents-end'] and body_times and _timestamp(a['retrieved_at'])<max(body_times):raise QualificationError('Closing witness predates supplied/original acquisition')
 except Exception as e:state['errors'].append({'type':type(e).__name__,'message':str(e),'access_stop':False,'at':now()})
 state['inventory_bound_artifacts']=len(state['artifacts']);data=rebuild(out,state);state['inventory_sha256']=digest(canon(sorted(data['nodes'].values(),key=lambda n:n['id'])));save(out/'checkpoint.json',state);write_outputs(out,state,data);return verify(out)
