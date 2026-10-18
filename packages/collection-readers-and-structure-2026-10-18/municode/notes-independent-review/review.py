"""Read-only independent census/ownership peer review. No collector imports."""
import collections,hashlib,json,socket
from pathlib import Path
from unittest.mock import patch
from bs4 import BeautifulSoup
B=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00');HERE=Path(__file__).resolve().parent
S=B/'outputs/collection-readiness-postf561-2026-10-17/qa/municode-source-notes-discovery-v1'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def manifest(p):return {str(f.relative_to(p)):h(f) for f in p.rglob('*') if f.is_file()}
def walk(v):
 if isinstance(v,dict):
  if 'DocType'in v and 'Id'in v:yield v
  for x in v.values():yield from walk(x)
 elif isinstance(v,list):
  for x in v:yield from walk(x)
def census(docs):
 c=collections.Counter()
 for d in docs:
  c['doc_occurrences']+=1
  for k,v in d.items():
   if k.lower()in ['notes','footnotes']:
    c[k+'_schema_'+type(v).__name__]+=1
    assert not v,(d.get('Id'),k,'Unexpected populated field')
 return dict(c)
def main():
 before=manifest(S);m=load(S/'MANIFEST.json');assert {k:v for k,v in before.items() if k!='MANIFEST.json'}==m['files'];report=load(S/'report.json');comm=load(S/'census.json');raw=load(S/'raw-response-census.json');inline=load(S/'inline-note-ownership.json')
 witness={**comm['source_manifest'],**raw['source_manifest'],**inline['source_manifest']}
 for p,v in witness.items():assert h(B/p)==v,(p,'source changed')
 cache={};counts=collections.Counter();refs=0
 for run in comm['runs']:
  root=B/run['root'];cp=load(root/'checkpoint.json')
  for pub in cp['publications'].values():
   units=list(pub.get('content_units',[]));landing=pub.get('root_landing_unit')
   if landing and landing not in units:units.append(landing)
   for unit in units:
    u=cp['units'][unit];r=load(root/u['receipt']);p=root/r['body_file'];assert h(p)==r['sha256']==u['sha256'];cache.setdefault(h(p),load(p));data=cache[h(p)];docs=data if isinstance(data,list)else data.get('Docs',[]);counts.update(census(docs));refs+=1
 assert counts.pop('doc_occurrences')==54150
 assert dict(counts)=={k:v for k,v in comm['totals'].items() if k!='doc_occurrences'}
 unique={}
 for r in raw['response_references']:
  receipt=load(B/r['receipt']);assert 'json'in {k.lower():v for k,v in receipt['headers'].items()}['content-type'].lower();p=B/r['body'];assert h(p)==receipt['sha256']==r['sha256'];unique.setdefault(h(p),load(p))
 rawcounts=census(d for v in unique.values() for d in walk(v));assert len(unique)==52 and len(raw['response_references'])==170 and rawcounts['doc_occurrences']==28978
 assert rawcounts['Notes_schema_list']==28978 and rawcounts['Footnotes_schema_NoneType']==28978
 # Independently reconstruct each published inline-note fragment from retained
 # body owner, canonical IR and final corpus row, using original occurrence order.
 P=B/'outputs/collection-readiness-post1997ee1-2026-10-17/qa/corpus-readers-municode-encodeplus-v1/FINAL-PACKET/fixtures/packages/henderson';R=P/'evidence/input';cp=load(R/'checkpoint.json');ir={x['node_id']:x for x in [json.loads(l)for l in (R/'publications/14896/sections.jsonl').read_text().split('\n')if l]};rows=load(P/'aggregate-fulltext.json')['provisions'];prov=[json.loads(l)for l in(P/'record-provenance.jsonl').read_text().split('\n')if l];out={p['record_id'].split(':',1)[1]:r for p,r in zip(prov,rows)};owners={};occurrences=[];docs=0
 def fragments(html):
  return [t for t in BeautifulSoup(html,'html.parser').find_all(True) if any(c=='footnote-content'or c.startswith('refeditor')or c.startswith('refnote')for c in t.get('class',[]))]
 for name in cp['publications']['14896']['content_units']:
  u=cp['units'][name];r=load(R/u['receipt']);p=R/r['body_file'];assert h(p)==r['sha256']==u['sha256']
  for d in load(p):
   docs+=1;i=str(d['Id']);source=d.get('Content')or'';record=ir[i];assert hashlib.sha256(source.encode()).hexdigest()==record['body_sha256'];assert record['html']==out[i]['full_text']
   if not any(c in source for c in ['footnote-content','refeditor','refnote']):continue
   a,b,c=fragments(source),fragments(record['html']),fragments(out[i]['full_text']);assert len(a)==len(b)==len(c)
   for x,y,z in zip(a,b,c):
    assert str(x)==str(y)==str(z)and x.get_text()==y.get_text()==z.get_text();occurrences.append((i,hashlib.sha256(str(x).encode()).hexdigest()));owners[i]=record['is_container']
 assert docs==2122 and len(occurrences)==240 and len(owners)==172 and sum(bool(v)for v in owners.values())==65
 assert occurrences==[(v['doc_id'],v['source_fragment_sha256'])for v in inline['matches']]
 for p,v in witness.items():assert h(B/p)==v
 assert manifest(S)==before
 result={'passed':True,'frozen_packet_manifest_sha256':h(S/'MANIFEST.json'),'reviewed_report_sha256':h(S/'report.json'),'checked_packet_files':len(before)-1,'source_witness_files':len(witness),'committed_run_roots':len(comm['runs']),'committed_unique_bodies':len(cache),'committed_doc_occurrences':54150,'broader_response_receipts':170,'broader_unique_json_bodies':52,'broader_doc_occurrences':28978,'populated_separate_fields':0,'full_henderson_doc_owners_checked':docs,'in_content_note_element_occurrences':240,'distinct_note_owner_docs':172,'container_note_owners':65,'all_source_canonical_export_fragments_equal':True,'input_packet_and_source_unchanged':True,'socket_calls':0,'native_image_pdf_apis_imported_or_called':False,'scope':'Only enumerated retained source. No nonempty separate-field schema qualification; existing Content note elements already owned and must not be appended again. Nested element occurrence counts are not distinct note counts.'}
 (HERE/'review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':
 with patch.object(socket,'socket',side_effect=AssertionError('Network forbidden')):main()
