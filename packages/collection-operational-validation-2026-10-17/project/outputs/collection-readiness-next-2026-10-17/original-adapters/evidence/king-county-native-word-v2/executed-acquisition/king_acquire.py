"""Fresh/resumable complete source-listed King County HTML publication acquisition, no retries."""
import argparse,re,sys,shutil
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from bs4 import BeautifulSoup,Tag
from source_common import *
URL='https://kingcounty.gov/en/dept/council/governance-leadership/county-legislation-codes/king-county-code'
PREFIX='https://aqua.kingcounty.gov/council/clerk/code/'
FILES=['king_acquire.py','source_common.py','shared_transport.py']

def inventory(raw):
 text,encoding=decode(raw);s=BeautifulSoup(text,'html.parser')
 if not s.title or 'King County Code' not in s.title.get_text():raise ValueError('Official King County index identity mismatch')
 docs=[]
 for h in s.select('main h3'):
  a=h.find('a',href=True)
  if not a:continue
  u=urljoin(URL,a['href'])
  if not u.startswith(PREFIX):continue
  label=clean(a.get_text(' ',strip=True));context=[];alternatives=[]
  for sib in h.next_siblings:
   if getattr(sib,'name',None) in ['h2','h3']:break
   if isinstance(sib,Tag):
    context.append(clean(sib.get_text(' ',strip=True)))
    for x in sib.select('a[href]'):
     target=urljoin(URL,x['href'])
     if target.startswith(PREFIX):alternatives.append({'url':target,'label':clean(x.get_text(' ',strip=True))})
  match=re.search(r'\(Updated\s*:?\s*([^)]*)\)', ' '.join(context),re.I)
  if not match:raise ValueError('Per-document updated edition marker absent: '+label)
  if not u.lower().endswith('.htm'):raise ValueError('Unprofiled official source document '+u)
  docs.append({'id':key(u),'url':u,'heading':label,'kind':'title' if re.match('Title ',label,re.I) else 'charter' if label=='Charter' else 'editorial','updated':clean(match.group(1)),'source_listing_context':' '.join(context),'native_alternatives':alternatives})
 if len(docs)<10 or len({d['id'] for d in docs})!=len(docs):raise ValueError('Empty/duplicate/truncated official title inventory')
 return docs

def collect(out,resume=False,max_items=None):
 out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
 if resume:
  state=load(out/'checkpoint.json')
  if state['errors']:raise ValueError('Retained source failure; no automatic resume/retry')
  for n,h in state['code_fingerprint'].items():
   if sha((Path(__file__).parent/n).read_bytes())!=h or sha((out/'executed-acquisition'/n).read_bytes())!=h:raise ValueError('Acquisition version changed; exact source required')
  for a in state['artifacts']:
   if sha((out/a['path']).read_bytes())!=a['sha256']:raise ValueError('Corrupt cached acquisition')
 else:
  if any(out.iterdir()):raise ValueError('Use fresh output or explicit resume')
  state={'schema':'original-official-acquisition-1','source_url':URL,'started_at':stamp(),'code_fingerprint':source_snapshot(out,FILES),'artifacts':[],'errors':[],'limits_applied':max_items is not None,'complete':False};save(out/'checkpoint.json',state)
 try:
  if not state.get('inventory'):
   raw,a=acquire(out,state,'index-start',URL);state['inventory']=inventory(raw);state['inventory_sha256']=sha(canon(state['inventory']));save(out/'checkpoint.json',state)
  acquired={a['source_url'] for a in state['artifacts'] if a['role']=='content' and a['status']==200}
  remaining=[d for d in state['inventory'] if d['url'] not in acquired]
  for i,d in enumerate(remaining):
   if max_items is not None and i>=max_items:break
   acquire(out,state,'content',d['url']);print(json.dumps({'acquired':len(acquired)+i+1,'inventory':len(state['inventory']),'url':d['url']}),flush=True)
  if max_items is None:
   raw,a=acquire(out,state,'index-end',URL);end=inventory(raw)
   if end!=state['inventory']:raise ValueError('Opening/closing official title/currency inventory drift')
   state['opening_closing_inventory_equal']=True;state['limits_applied']=False
 except Exception as e:state['errors'].append({'type':type(e).__name__,'message':str(e),'at':stamp()})
 state['finished_at']=stamp();state['content_routes_acquired']=len({a['source_url'] for a in state['artifacts'] if a['role']=='content' and a['status']==200});state['complete']=False;state['scope']='Acquisition only: normalization/own-body/dependency/source-edition verification still required; all source-listed routes are intended, no sample promoted';save(out/'checkpoint.json',state);return state
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--resume',action='store_true');p.add_argument('--max-items',type=int);a=p.parse_args()
 try:r=collect(a.out,a.resume,a.max_items);print(json.dumps({'acquired':r['content_routes_acquired'],'inventory':len(r.get('inventory',[])),'errors':r['errors'],'acquisition_only':True},indent=2));raise SystemExit(3 if r['errors'] else 2 if r['limits_applied'] else 0)
 except Exception as e:print(json.dumps({'complete':False,'error':type(e).__name__,'message':str(e)}));raise SystemExit(1)
