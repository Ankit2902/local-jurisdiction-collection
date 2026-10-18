"""Independent all-row consumer: no reader/model imports or native decoding."""
import sys
sys.dont_write_bytecode=True
import csv,io,json,hashlib,re,html,time
from pathlib import Path
from html.parser import HTMLParser
B=Path(__file__).resolve().parent;O=B/'package';R=O/'evidence/input'
def load(p):return json.loads(p.read_text())
def lines(p):return [json.loads(x) for x in p.read_text().split('\n') if x]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
start=time.time();m=load(O/'run-manifest.json');source=lines(R/'sections.jsonl');irord={r['document_id']:i for i,r in enumerate(source)};irs={r['document_id']:r for r in source};inv=load(R/'inventory.json');nodes={n['document_id']:n for n in inv['nodes']};req=load(R/'requests.json');run=load(R/'run.json');rows=load(O/'aggregate-fulltext.json')['provisions'];toc=load(O/'aggregate-toc.json')['provisions'];pr=lines(O/'record-provenance.jsonl');sn=lines(O/'source-nodes.jsonl');dis=lines(O/'node-dispositions.jsonl')
assert len(rows)==len(toc)==len(pr)==len(source)==6140
# Walk original raw publisher branches, not the flat stored inventory or reader.
data=(R/req['overview-start']['file']).read_text();literal=re.search(r'window\._redux_state\s*=\s*JSON\.parse\(("(?:[^"\\]|\\.)*")',data)[1];state=json.loads(json.loads(literal))['codes'];book=next(x for x in state['selectedVersion']['toc'] if x['uuid']==run['identity']['code_uuid']);order=[];branches=[]
def visit(n,parent,path):
 did=n['doc_id'];assert did not in order;order.append(did);stored=nodes[did];assert stored['parent_id']==parent and stored['path']==path+[n['title']] and stored['heading']==n['title']
 if n.get('has_children'):
  e=req['start:toc:'+did];assert sha(R/e['file'])==e['sha256'];body=load(R/e['file']);assert body['doc_id']==did and body['code_uuid']==run['identity']['code_uuid'];branches.append(did)
  for child in body['children']:visit(child,did,stored['path'])
for n in book['sections']:visit(n,None,[])
assert len(branches)==459 and len(order)==6140
class Blocks(HTMLParser):
 def __init__(self):super().__init__();self.ids=[]
 def handle_starttag(self,t,a):
  for k,v in a:
   if k=='id' and v.startswith('rid-'):self.ids.append(v[4:])
parser=Blocks();native=req['native-export'];parser.feed((R/native['file']).read_text())
assert [x for x in parser.ids if x in irs]==[d for d in order if irs[d]['kind']=='publisher-native-html-owned-range']
assert [x for d in order for x in irs[d]['body_block_ids']]==parser.ids
assert len(parser.ids)==43676 and len(set(parser.ids))==43676
fieldnames=['jurisdiction','code_name','division','title','subtitle','chapter','subchapter','article','part','subpart','section_number','section_name','citation','full_text','source_url','scrape_date'];roles=fieldnames[2:10];conflict_counts={k:0 for k in roles};counts={'native':0,'passthrough':0,'tables':0,'cells':0,'HTML_IMAGE':0,'literal_section_numbers':0}
for i,(d,row,p) in enumerate(zip(order,rows,pr)):
 r=irs[d];assert p['source_document_id']==d and p['rich_ir']['line_ordinal']==irord[d] and p['body_block_ids']==r['body_block_ids'];assert list(row)==fieldnames
 chain=[];current=d
 while current:chain.append(nodes[current]);current=nodes[current]['parent_id']
 chain.reverse();assert p['source_chain']==[{'id':n['document_id'],'heading':n['heading']} for n in chain]
 assert row['jurisdiction']==run['identity']['jurisdiction']+', '+run['identity']['state'] and row['code_name']==run['identity']['code_title']
 for role in roles:
  labels=list(dict.fromkeys(n['heading'] for n in chain if re.match('^'+role+r'[.]?\s+\S',n['heading'],re.I)))
  expected=labels[0] if len(labels)==1 else '';assert row[role]==expected
  if len(labels)>1:conflict_counts[role]+=1;assert any(x['field']==role for x in p['source_hierarchy_conflicts'])
 assert row['citation']==r['heading'] and row['source_url']==r['source_url'];e=native if r['kind']=='publisher-native-html-owned-range' else req['start:toc:'+d];assert row['scrape_date']==e['retrieved_at']
 if r['html'] is None:assert row['full_text']==html.escape(r['heading'],quote=False);counts['passthrough']+=1
 else:assert row['full_text']==r['html'];counts['native']+=1
 assert p['source_tables']==r['tables'] and p['source_links']==r['links'] and p['source_notes']==r['notes'] and p['source_image_placeholders']==r['image_placeholders']
 assert row['full_text'].count('[IMAGE]')==len(r['image_placeholders']);counts['HTML_IMAGE']+=row['full_text'].count('[IMAGE]');counts['tables']+=len(r['tables']);counts['cells']+=sum(len(row) for t in r['tables'] for row in t)
 if row['section_number']:assert row['section_number'] in r['heading'];counts['literal_section_numbers']+=1
 expected_toc=dict(row,full_text='');assert toc[i]==expected_toc
# Independent CSV parser, every value/quote/newline/BOM checked.
for stem,expected in [('aggregate-fulltext',rows),('aggregate-toc',toc)]:
 raw=(O/(stem+'.csv')).read_bytes();assert raw.startswith(b'\xef\xbb\xbf');csv.field_size_limit(64*1024*1024);reader=csv.DictReader(io.StringIO(raw.decode('utf-8-sig'),newline=''));assert reader.fieldnames==fieldnames and list(reader)==expected
assert load(O/'inherited-coverage.json')==load(R/'coverage.json')
assets=load(R/'assets.json');assert len(sn)==len(dis)==6140+len(assets)
for a,n,d in zip(assets,sn[6140:],dis[6140:]):
 assert n['asset_evidence']==a and not d['record_ids']
 if a['status']=='image-placeholder':assert a['required'] is False and 'file' not in a and d['disposition']=='excluded_by_scope'
 else:assert sha(R/a['file'])==a['sha256'] and d['disposition'] in ['unresolved','excluded_by_scope']
assert len([d for d in dis if d['disposition']=='unresolved'])==1
summary={'passed':True,'scope':'Full retained Cleveland HTML corpus projection and original source/order/metadata consumer; not new acquisition, native PDF segmentation or jurisdiction closure','records':len(rows),'source_nodes':len(sn),'raw_branches':len(branches),'native_blocks':len(parser.ids),'counts':counts,'same_type_hierarchy_conflicts':conflict_counts,'inherited_publication_complete':load(R/'coverage.json')['publication_complete'],'strict_complete':m['complete'],'unresolved_required_nonimage_assets':1,'native_sha256':sha(R/native['file']),'sections_sha256':sha(R/'sections.jsonl'),'run_manifest_sha256':sha(O/'run-manifest.json'),'audit_source_sha256':sha(Path(__file__)),'seconds':time.time()-start,'source_normalizations':0,'image_or_network_operations':0};assert m['complete'] is False
(B/'actual-consumer.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
