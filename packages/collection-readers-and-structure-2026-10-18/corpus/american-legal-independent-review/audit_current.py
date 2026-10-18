"""Independent stdlib-only actual all-row/raw-order audit, no reader/normalizer imports."""
import sys
sys.dont_write_bytecode=True
import csv,io,json,hashlib,html,re,collections
from pathlib import Path
from html.parser import HTMLParser

def load(p):return json.loads(p.read_text(encoding='utf-8'))
def lines(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').split('\n') if x]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(d):return json.dumps(d,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
def guard(event,args):
 if event.startswith('socket.') or event=='subprocess.Popen':raise AssertionError('Peer audit forbids network/process')
sys.addaudithook(guard)
class IDs(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.ids=[]
 def handle_starttag(self,t,a):
  for k,v in a:
   if k=='id' and v and v.startswith('rid-'):self.ids.append(v[4:])
 handle_startendtag=handle_starttag
def main():
 b=Path(sys.argv[1]);out=Path(sys.argv[2]);manifest=load(b/'CANDIDATE-MANIFEST.json');before={}
 for n,e in manifest['files'].items():
  p=b/n;assert not p.is_symlink() and p.stat().st_size==e['bytes'] and sha(p)==e['sha256'],n;before[n]=e['sha256']
 o=b/'package';root=o/'evidence/input';requests=load(root/'requests.json');run=load(root/'run.json');ir=lines(root/'sections.jsonl');by={r['document_id']:r for r in ir};oldordinal={r['document_id']:i for i,r in enumerate(ir)};inv=load(root/'inventory.json');invmap={n['document_id']:n for n in inv['nodes']}
 proof=load(b/'portable-verification/read-only-proof.json');report=load(b/'portable-verification/family-verification.json')
 assert proof['evidence_sha256_before']==proof['evidence_sha256_after'] and proof['collector_sources_before']==proof['collector_sources_after'];assert proof['verification']['forbidden_calls']==[] and proof['publisher_requests']==0
 for n,h in proof['evidence_sha256_before'].items():assert sha(root/n)==h
 assert hashlib.sha256((b/'portable-verification/family-verification.json').read_bytes()).hexdigest()==proof['verification']['family_report_sha256']
 assert report==load(root/'coverage.json')==load(o/'inherited-coverage.json')
 trees=[];branch_counts=[]
 for phase,overview in [('start','overview-start'),('end:'+str(run['resume_count']),'overview-end:'+str(run['resume_count']))]:
  e=requests[overview];assert sha(root/e['file'])==e['sha256'];raw=(root/e['file']).read_text(encoding='utf-8');literal=re.search(r'window\._redux_state\s*=\s*JSON\.parse\(("(?:[^"\\]|\\.)*")',raw)[1];codes=json.loads(json.loads(literal))['codes'];book=next(x for x in codes['selectedVersion']['toc'] if x['uuid']==run['identity']['code_uuid']);order=[];branches=[];source={}
  def walk(n,parent,path):
   did=n['doc_id'];assert did not in source;order.append(did);source[did]={'parent':parent,'heading':n['title'],'path':path+[n['title']]};assert invmap[did]['parent_id']==parent and invmap[did]['path']==source[did]['path'] and invmap[did]['heading']==n['title']
   if n.get('has_children'):
    e=requests[phase+':toc:'+did];assert sha(root/e['file'])==e['sha256'] and e['response']['status']==200;children=load(root/e['file']);assert children['doc_id']==did and children['code_uuid']==run['identity']['code_uuid'];branches.append(did)
    for child in children['children']:walk(child,did,source[did]['path'])
  for n in book['sections']:walk(n,None,[])
  trees.append((order,source));branch_counts.append(len(branches))
 assert trees[0]==trees[1] and branch_counts==[459,459];order,source=trees[0];assert len(order)==len(by)==6140
 native=requests['native-export'];assert sha(root/native['file'])==native['sha256'];parser=IDs();parser.feed((root/native['file']).read_text(encoding='utf-8'));parser.close();assert len(parser.ids)==len(set(parser.ids))==43676
 assert [x for x in parser.ids if x in by]==[did for did in order if by[did]['kind']=='publisher-native-html-owned-range'];assert [block for did in order for block in by[did]['body_block_ids']]==parser.ids
 obj=load(o/'aggregate-fulltext.json');rows=obj['provisions'];toc=load(o/'aggregate-toc.json')['provisions'];provenance=lines(o/'record-provenance.jsonl');nodes=lines(o/'source-nodes.jsonl');disps=lines(o/'node-dispositions.jsonl');assert len(rows)==len(toc)==len(provenance)==6140
 fields='jurisdiction code_name division title subtitle chapter subchapter article part subpart section_number section_name citation full_text source_url scrape_date'.split();roles=fields[2:10];counts=collections.Counter();conflicts=collections.Counter()
 for i,(did,row,p) in enumerate(zip(order,rows,provenance)):
  r=by[did];assert list(row)==fields and p['source_document_id']==did and p['rich_ir']['line_ordinal']==oldordinal[did] and p['rich_ir']['record_sha256']==hashlib.sha256(canonical(r)).hexdigest()
  assert row['jurisdiction']==run['identity']['jurisdiction']+', '+run['identity']['state'] and row['code_name']==run['identity']['code_title'] and row['citation']==r['heading'] and row['source_url']==r['source_url']
  headings=source[did]['path'];assert [x['heading'] for x in p['source_chain']]==headings
  for role in roles:
   found=list(dict.fromkeys(h for h in headings if re.match('^'+role+r'[.]?\s+\S',h,re.I)));assert row[role]==(found[0] if len(found)==1 else '')
   if len(found)>1:conflicts[role]+=1;assert any(x['field']==role for x in p['source_hierarchy_conflicts'])
  heading=r['heading'].strip()
  if row['section_number']:
   prefix=heading[:heading.index(row['section_number'])];assert prefix in ['§ ','§§ '];assert heading[len(prefix)+len(row['section_number']):].strip()==row['section_name'];counts['section_numbers']+=1
  else:assert row['section_name']==heading
  if r['html'] is None:
   assert r['kind']=='publisher-toc-passthrough-container' and row['full_text']==html.escape(r['heading'],quote=False) and not r['body_block_ids'];counts['passthrough']+=1;e=requests['start:toc:'+did]
  else:assert row['full_text']==r['html'];counts['HTML']+=1;e=native
  assert row['scrape_date']==e['retrieved_at'] and p['raw_sha256']==e['sha256']
  assert p['source_notes']==r['notes'] and p['source_tables']==r['tables'] and p['source_links']==r['links'] and p['source_native_auxiliary_fragments']==r.get('native_auxiliary_fragments',[]) and p['source_image_placeholders']==r['image_placeholders']
  assert row['full_text'].count('[IMAGE]')==len(r['image_placeholders']);counts['IMAGE']+=len(r['image_placeholders']);counts['tables']+=len(r['tables']);counts['cells']+=sum(len(row) for t in r['tables'] for row in t)
  assert toc[i]==dict(row,full_text='')
 for folder in ['', 'publications/'+load(o/'run-manifest.json')['publication_id']+'/']:
  for stem,expected in [('aggregate-fulltext' if not folder else 'fulltext',rows),('aggregate-toc' if not folder else 'toc',toc)]:
   data=(o/(folder+stem+'.csv')).read_bytes();assert data.startswith(b'\xef\xbb\xbf');csv.field_size_limit(64*1024*1024);reader=csv.DictReader(io.StringIO(data.decode('utf-8-sig'),newline=''));assert reader.fieldnames==fields and list(reader)==expected;assert load(o/(folder+stem+'.json'))['provisions']==expected
 assets=load(root/'assets.json');pages=lines(root/'pdf-pages.jsonl');assert len(nodes)==len(disps)==6140+len(assets)==6160;asset_checks=[]
 for a,n,d in zip(assets,nodes[6140:],disps[6140:]):
  owners=[r['document_id'] for r in ir if any(x['url']==a['url'] for x in r['assets'])];assert owners and len(owners)==len(n['source_owner_node_ids']) and n['asset_evidence']==a and not d['record_ids']
  if a['required']:
   assert sha(root/a['file'])==a['sha256'];related=[p for p in pages if p['source_url']==a['url']];assert len(related)==a['validation']['pages']==a['normalized_pdf_document_pages']==1;assert [p['document_id'] for p in related]==a['normalized_pdf_page_ids'];assert all(p['owner_id']==a['normalized_pdf_owner_id']=='attachment:'+a['sha256'] for p in related);asset_checks.append({'url':a['url'],'pages':1,'owners':len(owners),'disposition':d['disposition']})
  else:assert a['status']=='image-placeholder' and 'file' not in a and d['disposition']=='excluded_by_scope'
 assert sum(d['disposition']=='unresolved' for d in disps)==1;assert load(o/'run-manifest.json')['complete'] is False and load(o/'validation-report.json')['complete'] is False
 for n,h in before.items():assert sha(b/n)==h
 result={'passed':True,'candidate_manifest_sha256':sha(b/'CANDIDATE-MANIFEST.json'),'bound_files_verified':len(before),'source_inputs_verified':len(proof['evidence_sha256_before']),'rows_all16fields_verified':len(rows),'source_nodes':len(nodes),'opening_closing_raw_branch_counts':branch_counts,'native_block_ID_ownership':len(parser.ids),'counts':dict(counts),'scalar_conflicts':dict(conflicts),'actual_asset_checks':asset_checks,'original_inherited_coverage_unchanged':True,'strict_complete':False,'publisher_requests':0,'source_normalizations':0,'PDF_parsing_or_image_operations':0,'candidate_files_unchanged':True,'scope':'Actual allrow/rawTOC/nativeID/canonicalIR projection. Consumer noGlyph/owner fault guards reviewed separately; no new source acquisition, legal PDF segmentation or jurisdiction qualification.'}
 out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
