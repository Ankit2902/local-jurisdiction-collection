"""Exact-version native inventory initialization recovery; retain every interrupted generation."""
from pathlib import Path
from source_common import load,save,sha,stamp
import shared_transport as transport
import re
from bs4 import BeautifulSoup
URL='https://www.codepublishing.com/AZ/Flagstaff/'
NAME='inventory-initialization.json'
def fingerprint(files):
 root=Path(__file__).resolve().parent
 return {name:sha((root/name).read_bytes()) for name in files}
def digest_tree(folder):
 return {str(p.relative_to(folder)):sha(p.read_bytes()) for p in sorted(folder.rglob('*')) if p.is_file()}
def ensure_snapshot(out,state,marker,files):
 expected=state['code_fingerprint'];selected=out/'executed-acquisition'
 for attempt in state.setdefault('snapshot_attempts',[]):
  if attempt.get('status')=='interrupted_preserved':
   folder=out/attempt['path']
   if folder.exists()!=attempt['directory_exists'] or digest_tree(folder)!=attempt['manifest']:raise ValueError('Interrupted code snapshot generation changed')
 if selected.exists():
  if digest_tree(selected)!=expected:raise ValueError('Executed initialization snapshot corrupt or revision mismatched')
  for attempt in state['snapshot_attempts']:
   if attempt.get('status')=='running':attempt.update(status='selected',path='executed-acquisition',finished_at=stamp())
  save(marker,state);return
 for attempt in state['snapshot_attempts']:
  if attempt.get('status')=='running':
   folder=out/attempt['path'];attempt.update(status='interrupted_preserved',directory_exists=folder.exists(),manifest=digest_tree(folder),observed_at=stamp());save(marker,state)
 attempt={'path':'.code-snapshot-attempt-'+str(len(state['snapshot_attempts'])+1).zfill(4),'status':'running','started_at':stamp()};state['snapshot_attempts'].append(attempt);save(marker,state);folder=out/attempt['path'];folder.mkdir()
 for name in files:transport.atomic(folder/name,(Path(__file__).resolve().parent/name).read_bytes())
 if digest_tree(folder)!=expected:raise ValueError('Code snapshot changed during initialization')
 folder.rename(selected);attempt.update(status='selected',path='executed-acquisition',finished_at=stamp());save(marker,state)

def checked_receipt(path):
 receipt=path/'receipt.json'
 # Inspect durable response ledgers even if interruption prevented the final receipt.
 # No image body is opened, no live gate is changed, and no requests are made here.
 for name in ['network-events.json','network-bodies.json']:
  if (path/name).exists():
   for event in load(path/name):
    headers={str(k).lower():str(v).lower() for k,v in event.get('headers',{}).items()}
    if event.get('status') in [403,429] or headers.get('cf-mitigated')=='challenge' or headers.get('retry-after'):raise ValueError('Native inventory refusal retained; no automatic retry')
    if name=='network-bodies.json' and event.get('path'):
     mime=headers.get('content-type','')
     if mime.startswith('image/'):raise ValueError('Unexpected separate image body in native inventory ledger; operator review required')
     if 'html' in mime or mime.startswith('text/'):
      raw=(path/event['path']).read_bytes()
      if sha(raw)!=event.get('sha256'):raise ValueError('Corrupt retained native response; no automatic retry')
      match=re.search(br'<title\b[^>]*>(.*?)</title\s*>',raw[:100000],re.I|re.S);title=BeautifulSoup(match.group(1),'html.parser').get_text(' ',strip=True) if match else ''
      if re.search(r'^(?:just a moment|attention required|access denied|verify (?:you are|that you)|checking your browser|security verification|human verification|captcha)',' '.join(title.split()),re.I) or b'/cdn-cgi/challenge-platform/' in raw[:100000].lower():raise ValueError('Retained native challenge body; no automatic retry')
 if not receipt.exists():return None
 meta=load(receipt)
 if meta.get('source_url')!=URL or meta.get('error') or meta.get('blocked'):raise ValueError('Native inventory generation failed or stopped; retain evidence for operator review, no automatic retry')
 return meta

def initialize(out,files,validate,resume=False):
 out=Path(out);marker=out/NAME;expected=fingerprint(files)
 gate=transport.ROOT/sha(b'www.codepublishing.com')[:20]/'state.json'
 if gate.exists() and load(gate).get('stop'):raise ValueError('Persisted publisher host stop; native inventory browser not started')
 if resume:
  state=load(marker)
  if state.get('schema')!='flagstaff-native-initialization-1' or state.get('source_url')!=URL or state.get('code_fingerprint')!=expected:raise ValueError('Native initialization source/revision mismatch; exact executed revision required')
  if state.get('error'):raise ValueError('Native initialization failure retained; operator review required')
 else:
  if any(out.iterdir()):raise ValueError('Fresh native initialization output required')
  state={'schema':'flagstaff-native-initialization-1','source_url':URL,'started_at':stamp(),'code_fingerprint':expected,'stage':'code_snapshot','attempts':[],'error':None};save(marker,state)
 # Durable revision marker precedes every source-code snapshot write and native request.
 ensure_snapshot(out,state,marker,files)
 if state['stage']=='code_snapshot':state['stage']='native_inventory';save(marker,state)
 selected=out/'inventory-origin'
 for attempt in state['attempts']:
  if attempt.get('status')=='interrupted_preserved':
   folder=out/attempt['path']
   if folder.exists()!=attempt['directory_exists'] or (folder.exists() and not folder.is_dir()) or digest_tree(folder)!=attempt['manifest']:raise ValueError('Interrupted inventory generation changed; preserve evidence and review')
 if selected.exists():
  if state.get('selected_manifest') and digest_tree(selected)!=state['selected_manifest']:raise ValueError('Selected native inventory generation changed')
  meta=checked_receipt(selected)
  if meta is None:raise ValueError('Selected native inventory lacks completed receipt')
  validate(selected)
  running=[a for a in state['attempts'] if a.get('status')=='running']
  if len(running)>1:raise ValueError('Ambiguous native inventory publication generation')
  if running:running[0].update(status='selected',path='inventory-origin',finished_at=stamp())
  state.update(stage='inventory_ready',selected='inventory-origin',selected_manifest=digest_tree(selected));save(marker,state);return selected
 # A generation interrupted before a final receipt is preserved, never reused as a
 # completed inventory. Its exact tree is recorded before a fresh ordinary attempt.
 for attempt in state['attempts']:
  folder=out/attempt['path']
  if attempt.get('status')=='running':
   meta=checked_receipt(folder)
   if meta and meta.get('whole_publication_selected_values') and meta.get('checked_values')==meta.get('whole_publication_selected_values'):
    validate(folder);folder.rename(selected);attempt.update(status='selected',path='inventory-origin',finished_at=stamp());state.update(stage='inventory_ready',selected='inventory-origin',selected_manifest=digest_tree(selected));save(marker,state);return selected
   attempt.update(status='interrupted_preserved',directory_exists=folder.exists(),observed_at=stamp(),manifest=digest_tree(folder));save(marker,state)
  elif attempt.get('status')=='interrupted_preserved':
   if folder.exists()!=attempt['directory_exists'] or (folder.exists() and not folder.is_dir()) or digest_tree(folder)!=attempt['manifest']:raise ValueError('Interrupted inventory generation changed; preserve evidence and review')
 attempt={'path':'inventory-attempt-'+str(len(state['attempts'])+1).zfill(4),'status':'running','started_at':stamp()};state['attempts'].append(attempt);save(marker,state)
 from flagstaff_inventory import run
 try:
  run(out/attempt['path']);meta=checked_receipt(out/attempt['path'])
  if meta is None or not meta.get('whole_publication_selected_values') or meta.get('checked_values')!=meta.get('whole_publication_selected_values'):raise ValueError('Native inventory selection not complete')
  validate(out/attempt['path'])
  (out/attempt['path']).rename(selected);attempt.update(path='inventory-origin',status='selected',finished_at=stamp());state.update(stage='inventory_ready',selected='inventory-origin',selected_manifest=digest_tree(selected));save(marker,state);return selected
 except Exception as e:
  state['error']={'type':type(e).__name__,'message':str(e),'at':stamp()};save(marker,state);raise
