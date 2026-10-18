"""Independent retained transport identity/chronology/route ledger checks; no network."""
from datetime import datetime
from pathlib import Path
from source_common import load,sha,key
FLAG='https://www.codepublishing.com/AZ/Flagstaff/'

def instant(s):
 if not isinstance(s,str):raise ValueError('Acquisition timestamps required')
 d=datetime.fromisoformat(s.replace('Z','+00:00'))
 if d.tzinfo is None:raise ValueError('Timezone-aware acquisition timestamp required')
 return d

def validate(family,source):
 src=Path(source);state=load(src/'checkpoint.json');art=state['artifacts']
 if state.get('errors') or state.get('blocked'):raise ValueError('Retained source error/access stop is incomplete, never an acquisition pass')
 for a in art:
  if a['status']!=200 or sha((src/a['path']).read_bytes())!=a['sha256']:raise ValueError('Unavailable/corrupt source receipt')
  if a.get('final_url')!=a['source_url']:raise ValueError('Unqualified response redirect identity')
  if instant(a['finished_at'])<instant(a['started_at']):raise ValueError('Invalid source receipt chronology')
 if family.startswith('king'):
  from king_acquire import URL as KING,inventory
  starts=[a for a in art if a['role']=='index-start'];ends=[a for a in art if a['role']=='index-end']
  if len(starts)!=1 or len(ends)!=1:raise ValueError('Exactly one native opening/closing index required')
  if any(a['source_url']!=KING for a in starts+ends):raise ValueError('Wrong source index URL')
  docs=inventory((src/starts[0]['path']).read_bytes());closing=inventory((src/ends[0]['path']).read_bytes())
  if docs!=closing:raise ValueError('Source opening/closing inventory or update-label drift')
  role='native-word' if family=='king-word' else 'content';bodies=[a for a in art if a['role']==role]
  expected={d['id']:(next((x['url'] for x in d['native_alternatives'] if x['url'].lower().endswith('.docx')),None) if role=='native-word' else d['url']) for d in docs}
  actual={}
  for a in bodies:
   identity=a.get('document_id') if role=='native-word' else a['source_url']
   if identity in actual or identity not in expected or a['source_url']!=expected[identity]:raise ValueError('Missing/duplicate/foreign native source binding')
   actual[identity]=a
  if set(actual)!=set(expected):raise ValueError('Source route coverage differs from whole index')
  opening=starts[0];closing=ends[0]
 else:
  if state.get('source_url')!=FLAG:raise ValueError('Wrong Flagstaff primary publication')
  expected={key(e['source_url']) for e in state['inventory']};bodies=[a for a in art if a['role']=='content']
  if len(bodies)!=len({a['source_url'] for a in bodies}) or {a['source_url'] for a in bodies}!=expected:raise ValueError('Missing/duplicate/extra publication body route')
  roots=[a for a in art if a['role']=='root-toc-start'];ends=[a for a in art if a['role']=='root-toc-end']
  if len(roots)!=1 or len(ends)!=1:raise ValueError('Whole-publication root opening/closing required')
  opening=roots[0];closing=ends[0]
  for a in [x for x in art if x['role']=='toc-start']:
   if instant(a['finished_at'])>min(instant(b['started_at']) for b in bodies):raise ValueError('Reader opening acquired after substantive body')
 if any(instant(a['started_at'])<instant(opening['finished_at']) or instant(a['finished_at'])>instant(closing['started_at']) for a in bodies):raise ValueError('Source opening/body/closing chronology mismatch')
 return {'source_route_ledger_verified':True,'opening_body_closing_chronology_verified':True,'source_documents':len(bodies),'source_checkpoint_sha256':sha((src/'checkpoint.json').read_bytes())}
