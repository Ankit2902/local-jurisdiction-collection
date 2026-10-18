"""Acquire source-listed native Word alternatives to resolve source edition/HTML discrepancies."""
import argparse,sys,zipfile,io,re,xml.etree.ElementTree as ET
from pathlib import Path
from source_common import *
from king_acquire import URL,inventory

FILES=['king_native.py','king_acquire.py','source_common.py','shared_transport.py','word_model.py','model.py','legacy_html.py']
def run(source,out,resume=False,max_items=None):
 src=Path(source).resolve();out=Path(out).resolve();base=load(src/'checkpoint.json')
 if base.get('source_url')!=URL or base['errors']:raise ValueError('Wrong/failed original HTML source')
 for a in base['artifacts']:
  if sha((src/a['path']).read_bytes())!=a['sha256']:raise ValueError('Corrupt original source')
 if not any(a['role']=='index-end' for a in base['artifacts']):raise ValueError('Original source closing inventory required')
 if resume:
  state=load(out/'checkpoint.json')
  if state.get('source_url')!=URL or state['errors']:raise ValueError('Wrong/failed retained native source; no automatic retry')
  if state['source_inventory_sha256']!=base['inventory_sha256']:raise ValueError('Native/source inventory identity differs')
  for n,h in state['code_fingerprint'].items():
   if sha((Path(__file__).parent/n).read_bytes())!=h or sha((out/'executed-acquisition'/n).read_bytes())!=h:raise ValueError('Native acquisition version drift; use exact executed source')
  for a in state['artifacts']:
   if sha((out/a['path']).read_bytes())!=a['sha256']:raise ValueError('Corrupt native cached source')
  native=[a for a in state['artifacts'] if a['role']=='native-word']
  if len(native)!=len({a['source_url'] for a in native}):raise ValueError('Duplicate retained native route')
  if any(a.get('document_id') not in {d['id'] for d in base['inventory']} for a in native):raise ValueError('Unbound retained native source')
  if state.get('opening_closing_equal') and {a['document_id'] for a in native}=={d['id'] for d in base['inventory']}:return state
 else:
  if out.exists() and any(out.iterdir()):raise ValueError('Fresh native output or explicit exact-version resume required')
  out.mkdir(parents=True,exist_ok=True);state={'schema':'king-native-alternatives-2','source_url':URL,'started_at':stamp(),'source_inventory_sha256':base['inventory_sha256'],'provenance_source':str(src),'artifacts':[],'errors':[],'code_fingerprint':source_snapshot(out,FILES)};save(out/'checkpoint.json',state)
 try:
  raw,a=acquire(out,state,'index-resume' if resume else 'index-start',URL)
  if inventory(raw)!=base['inventory']:raise ValueError('Original/native current inventory differs; no body fetched')
  count=0
  for d in base['inventory']:
   choices=[x for x in d['native_alternatives'] if x['url'].lower().endswith('.docx')]
   if len(choices)!=1:raise ValueError('Native Word alternative absent/nonunique '+d['url'])
   url=choices[0]['url'];old=[a for a in state['artifacts'] if a['role']=='native-word' and a['source_url']==url]
   if len(old)>1:raise ValueError('Duplicate retained native source')
   if old:
    if old[0].get('document_id')!=d['id'] or old[0]['status']!=200:raise ValueError('Unbound/incomplete native capture; operator review required')
    continue
   if max_items is not None and count>=max_items:break
   raw,a=acquire(out,state,'native-word',url);a['document_id']=d['id'];a['index_updated']=d['updated'];a['heading']=d['heading'];save(out/'checkpoint.json',state)
   from word_model import inspect
   word=inspect(raw);a['body_updated_markers']=word['updated_markers'];a['native_table_count']=word['tables'];a['image_placeholder_count']=word['image_placeholder_count'];a['structural_members_read']=word['members_read'];a['image_members_never_read']=True
   save(out/'checkpoint.json',state);count+=1;print(json.dumps({'heading':d['heading'],'bytes':len(raw),'updated':a['body_updated_markers']}),flush=True)
  if max_items is None:
   raw,a=acquire(out,state,'index-end',URL)
   state['opening_closing_equal']=inventory(raw)==base['inventory']
   if not state['opening_closing_equal']:raise ValueError('Native opening/closing inventory edition drift')
 except Exception as e:state['errors'].append({'type':type(e).__name__,'message':str(e),'at':stamp()})
 state.update(finished_at=stamp(),complete=False,limits_applied=max_items is not None,scope='Native publisher alternatives; structural import, edition/dependency reconciliation required');save(out/'checkpoint.json',state);return state
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);p.add_argument('--resume',action='store_true');p.add_argument('--max-items',type=int);a=p.parse_args();r=run(a.source,a.out,a.resume,a.max_items);print(json.dumps({'native_documents':sum(x['role']=='native-word' for x in r['artifacts']),'errors':r['errors']}));sys.exit(3 if r['errors'] else 0)
