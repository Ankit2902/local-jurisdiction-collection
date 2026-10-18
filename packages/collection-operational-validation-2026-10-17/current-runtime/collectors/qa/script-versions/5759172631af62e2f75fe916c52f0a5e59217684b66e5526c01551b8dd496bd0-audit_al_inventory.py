"""Independent overview/recursive API graph, full native block and closing binding."""
import argparse,collections,datetime,hashlib,json,re
from pathlib import Path
from html.parser import HTMLParser
class IDs(HTMLParser):
 def __init__(self):super().__init__();self.ids=[]
 def handle_starttag(self,tag,attrs):
  value=dict(attrs).get('id','')
  if value.startswith('rid-'):self.ids.append(value[4:])
def sha(b):return hashlib.sha256(b).hexdigest()
def audit(run):
 requests=json.loads((run/'requests.json').read_text());manifest=json.loads((run/'run.json').read_text());records_bytes=(run/'sections.jsonl').read_bytes();records=[json.loads(s) for s in records_bytes.splitlines()];errors=[];sources=[]
 def read_request(key):
  e=requests[key];raw=(run/e['file']).read_bytes()
  if sha(raw)!=e['sha256'] or len(raw)!=e['bytes'] or e['response']['status']!=200:raise ValueError('Source receipt binding failed '+key)
  sources.append({'request_key':key,'path':e['file'],'sha256':sha(raw),'requested_url':e['requested_url'],'retrieved_at':e['retrieved_at']});return raw,e
 def overview(key):
  raw,e=read_request(key);m=re.search(r'window\._redux_state\s*=\s*JSON\.parse\(("(?:[^"\\]|\\.)*")',raw.decode());state=json.loads(json.loads(m[1]));v=state['codes']['selectedVersion'];books=[b for b in v['toc'] if b['slug']==manifest['publication_selector']];assert len(books)==1
  book=books[0];assert v['uuid']==manifest['identity']['version_uuid'] and book['uuid']==manifest['identity']['code_uuid'] and book['client_slug']==manifest['identity']['client_slug'];return book,v
 def graph(book,prefix):
  queue=[(n,None,[]) for n in book['sections']];nodes={};expanded=[]
  while queue:
   n,parent,path=queue.pop(0);ident=str(n.get('doc_id') or n['id']);title=n['title'];row={'id':ident,'internal_id':n['id'],'parent_id':parent,'heading':title,'has_children':n.get('has_children',False),'passthru_doc_id':n.get('passthru_doc_id'),'path':path+[title]}
   if ident in nodes:raise ValueError('Duplicate original source graph ID '+ident)
   nodes[ident]=row
   if row['has_children']:
    raw,e=read_request(prefix+ident);body=json.loads(raw)
    if e['requested_url']!=f"https://codelibrary.amlegal.com/api/section-toc/{n['id']}/" or str(body.get('doc_id') or body['id'])!=ident or body['id']!=n['id'] or body.get('code_uuid',book['uuid'])!=book['uuid']:raise ValueError('Wrong source branch response '+ident)
    expanded.append(ident);queue.extend((c,ident,row['path']) for c in body['children'])
  return nodes,expanded
 startbook,version=overview('overview-start');endkey='overview-end:'+str(manifest['resume_count']);endbook,endversion=overview(endkey);start,branches=graph(startbook,'start:toc:');end,endbranches=graph(endbook,'end:'+str(manifest['resume_count'])+':toc:')
 if start!=end:errors.append('Start/end raw source graphs differ')
 if version!=endversion:errors.append('Start/end independently published family/version metadata differs')
 ids={r['document_id'] for r in records}
 if ids!=set(start) or len(ids)!=len(records):errors.append('Normalized record ID set differs from raw recursive source graph')
 for r in records:
  n=start.get(r['document_id'])
  if not n or r['parent_id']!=n['parent_id'] or r['path']!=n['path'] or r['heading']!=n['heading']:errors.append('Record source hierarchy/heading mismatch '+r['document_id'])
 native,e=read_request('native-export');job=e['response']['job'];payload=e['response']['payload']
 if job['version']!=version['uuid'] or payload['version']!=version['uuid'] or json.loads(payload['scope'])!=[{'code_slug':startbook['slug']}] or e['response']['download_final_url']!=f"https://export.amlegal.com/api/export-requests/{job['uuid']}/download/":errors.append('Native job scope/version/download UUID differs')
 p=IDs();p.feed(native.decode());counter=collections.Counter(p.ids);owned=[block for r in records for block in r['body_block_ids']];ownedcounter=collections.Counter(owned)
 if counter!=ownedcounter or any(v!=1 for v in ownedcounter.values()):errors.append('Native rich-block IDs not exhaustively owned exactly once')
 for r in records:
  if r['body_block_ids']:
   if r['source_sha256']!=sha(native):errors.append('Record native original hash mismatch '+r['document_id'])
  else:
   source=requests['start:toc:'+r['document_id']];node=start[r['document_id']];target=r.get('passthru_target_id');current=target;ancestors=set()
   while current in start and start[current]['parent_id']:
    current=start[current]['parent_id'];ancestors.add(current)
   if r['kind']!='publisher-toc-passthrough-container' or not node['has_children'] or node['passthru_doc_id']!=target or r['document_id'] not in ancestors or r['source_sha256']!=source['sha256'] or r['source_url']!=source['requested_url']:errors.append('Virtual grouping lacks exact source-backed descendant/branch hash '+r['document_id'])
 exported=datetime.datetime.fromisoformat(e['retrieved_at']);closing=[s for s in sources if s['request_key'].startswith('end:') or s['request_key']==endkey]
 if any(datetime.datetime.fromisoformat(s['retrieved_at'])<=exported for s in closing):errors.append('Closing acquisition not later than native original')
 return {'schema_version':1,'kind':'independent-AL-recursive-inventory-native-block-and-closing-reconciliation','script_sha256':sha(Path(__file__).read_bytes()),'records_sha256':sha(records_bytes),'native_sha256':sha(native),'identity':manifest['identity'],'start_source_nodes':len(start),'closing_source_nodes':len(end),'start_branches':len(branches),'closing_branches':len(endbranches),'original_native_rich_blocks':len(p.ids),'owned_native_rich_blocks':len(owned),'source_only_virtual_groupings':[r['document_id'] for r in records if not r['body_block_ids']],'source_responses':sources,'record_source_hierarchy_and_heading_checked':True,'network_requests':0,'passed':not errors,'errors':errors,'limits':['Raw source graph and block ownership closure is not proof of serialized cell/body fidelity or required-PDF legal semantics. Known independent table differences remain separate blockers.']}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 if a.out.exists() or a.run.resolve() in a.out.resolve().parents:raise SystemExit('Fresh report outside original evidence required')
 r=audit(a.run);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='source_responses'},indent=2));raise SystemExit(0 if r['passed'] else 2)
