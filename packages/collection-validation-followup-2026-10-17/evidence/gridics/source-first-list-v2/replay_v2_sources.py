"""Read-only full-book derivative plus exact raw-list/ownership audit; no network."""
import sys
sys.dont_write_bytecode=True
import json,socket,warnings,re
from pathlib import Path
from collections import Counter
from bs4 import BeautifulSoup,MarkupResemblesLocatorWarning
base=Path(__file__).resolve().parent;sys.path.insert(0,str(base))
from collectors.gridics import model
warnings.filterwarnings('ignore',category=MarkupResemblesLocatorWarning)
def deny(*a,**k):raise AssertionError('Offline replay forbids network')
socket.socket.connect=deny;socket.socket.connect_ex=deny;socket.create_connection=deny
project=base.parents[3]
implementation={p.name:model.digest(p.read_bytes()) for p in sorted((base/'collectors/gridics').glob('*.py'))}
results=[]
def without_v2_attributes(markup):
 soup=BeautifulSoup(markup,'html.parser')
 for node in soup.find_all(['ol','ul','li']):
  node.attrs.pop('class',None);node.attrs.pop('data-list-marker-unqualified',None)
  if node.name=='ul':
   for k in ['start','type','value','reversed','style']:node.attrs.pop(k,None)
 return str(soup)
for relative in ['outputs/collection-readiness-next-2026-10-17/gridics/miami-client-qualified-v1','outputs/collection-readiness-2026-10-17/gridics/cupertino-portable-v4-replay']:
 print('Read-only V2 replay: '+relative,flush=True)
 source=project/relative
 manifest={str(p.relative_to(source)):model.digest(p.read_bytes()) for p in source.rglob('*') if p.is_file()}
 config=model.read(source/'acquisition.json')['config']
 dest=base/'full-source-derivatives'/source.name
 lineage={'source':relative,'source_manifest':manifest,'candidate_runtime_hashes':implementation,'kind':'offline_retained_source_derivative','network_requests':0}
 if (dest/'lineage.json').exists():
  assert model.read(dest/'lineage.json')==lineage
  records=[json.loads(x) for x in (dest/'records.jsonl').read_text().split('\n') if x]
  coverage=model.read(dest/'coverage.json')
 else:
  records,refs,coverage=model.analyze(source,config)
  assert implementation=={p.name:model.digest(p.read_bytes()) for p in sorted((base/'collectors/gridics').glob('*.py'))}
  assert manifest=={str(p.relative_to(source)):model.digest(p.read_bytes()) for p in source.rglob('*') if p.is_file()}
  dest.mkdir(parents=True,exist_ok=False)
  (dest/'records.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records))
  (dest/'references.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in refs))
  model.save(dest/'coverage.json',coverage);model.save(dest/'lineage.json',lineage)
 previous=base.parent/'isolated-source-first-candidate-v1/positive-source-derivatives'/source.name/'records.jsonl'
 old=[json.loads(x) for x in previous.read_text().split('\n') if x]
 assert len(old)==len(records)
 changed=[]
 for a,b in zip(old,records):
  for key in ['source_id','source_path','source_url','document_id','parent_id','heading','heading_html','heading_images','heading_tag','body_block_ids','source_body_sha256','child_ids','source_sequence','source_original_text_sha256','source_own_fields_sha256','images']:
   assert a[key]==b[key],(relative,b['source_id'],key)
  assert without_v2_attributes(a['html'])==without_v2_attributes(b['html']),(relative,b['source_id'],'HTML changed beyond exact list attrs')
  if a['text']!=b['text']:changed.append({'source_id':b['source_id'],'old_text_sha256':model.digest(a['text'].encode()),'new_text_sha256':model.digest(b['text'].encode()),'reason':'List marker projection amended; canonical legal HTML unchanged apart from retained source list attributes'})
  assert not re.search(r'data\s*:\s*image/',json.dumps(b),re.I),'Normalized image payload retained'
  soup=BeautifulSoup(b['html'],'html.parser')
  assert not soup.find(['img','svg','picture','canvas'])
  assert not any(node.has_attr('src') or node.has_attr('background') for node in soup.find_all())
 # Independent actual raw source list enumeration, not normalized HTML.
 rows=model.read(source/'start-checkpoint.json')['roots'];node_map={}
 def walk(n):
  assert n['id'] not in node_map;node_map[n['id']]=n
  for child in n.get('children',[]):walk(child)
 for row in rows:
  for root in json.loads(model.checked(source,row['tree_response'])):walk(root)
 counts=Counter();list_count=0;classed=0
 for record in records:
  raw=''.join(node_map[b]['text'] for b in record['body_block_ids'])
  lists=BeautifulSoup(raw,'html.parser').find_all(['ol','ul'])
  assert len(lists)==len(record['lists']),(record['source_id'],'raw list count')
  rendered=BeautifulSoup(record['html'],'html.parser').find_all(['ol','ul'])
  assert len(rendered)==len(lists)
  for source_list,normalized_list,metadata in zip(lists,rendered,record['lists']):
   list_count+=1
   assert metadata['source_list_sha256']==model.digest(str(source_list).encode())
   assert metadata['tag']==source_list.name
   assert metadata['source_attributes'].get('class',[])==source_list.get('class',[])
   assert normalized_list.get('class',[])==source_list.get('class',[])
   assert len(metadata['items'])==len(source_list.find_all('li',recursive=False))
   if source_list.get('class'):
    classed+=1;assert not metadata['marker_format_qualified']
    counts.update(source_list['class'])
 assert all(model.digest((source/n).read_bytes())==sha for n,sha in manifest.items())
 summary={'source':relative,'records':len(records),'source_files':len(manifest),'source_files_unchanged':True,'canonical_legal_html_preserved':True,'source_id_ownership_order_and_hashes_preserved':True,'raw_source_lists':list_count,'classed_lists':classed,'source_list_classes':dict(counts),'raw_source_list_metadata_checks_passed':True,'text_projection_changes':changed,'raw_native_start_end_consistent':coverage['raw_native_start_end_consistent'],'list_marker_qualification_gaps':len(coverage['list_marker_qualification_gaps']),'unqualified_source_ids':coverage['unqualified_source_ids'],'observed_stylesheet_sources':coverage['observed_stylesheet_sources'],'publication_text_complete':coverage['publication_text_complete'],'required_assets_complete':coverage['required_assets_complete'],'complete':coverage['complete'],'new_network_requests':0,'separate_image_downloads':0,'normalized_image_payload_audit_passed':True}
 results.append(summary);model.save(base/'full-source-replay-progress.json',{'implementation':implementation,'results':results})
 print('Checked '+str(len(records))+' records, '+str(list_count)+' raw source lists, '+str(classed)+' classed; complete='+str(coverage['complete']),flush=True)
assert implementation=={p.name:model.digest(p.read_bytes()) for p in sorted((base/'collectors/gridics').glob('*.py'))}
model.save(base/'full-source-replay-summary.json',{'kind':'offline retained-source derivative; not live acquisition','network_requests':0,'implementation':implementation,'results':results})
print('Both full retained source derivatives and raw-list/image audits passed',flush=True)
