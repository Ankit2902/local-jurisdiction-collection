"""Independent all-row consumer audit. Stdlib only; no reader/writer imports."""
from pathlib import Path
import sys,json,csv,io,hashlib
F='jurisdiction code_name division title subtitle chapter subchapter article part subpart section_number section_name citation full_text source_url scrape_date'.split()
H=F[2:10]
sha=lambda b:hashlib.sha256(b).hexdigest()
canon=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def jl(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').split('\n') if x]
def files(p):return {x.relative_to(p).as_posix():sha(x.read_bytes()) for x in sorted(p.rglob('*')) if x.is_file()}
def audit(root):
 before=files(root);m=load(root/'run-manifest.json');kind=m['reader'];source=root/'evidence/input';cp=load(source/'checkpoint.json');proof=load(root/'evidence/proofs/read-only-proof.json');family=load(root/'evidence/proofs/family-verification.json')
 assert files(source)==proof['evidence_sha256_before']==proof['evidence_sha256_after']
 assert proof['evidence_read_only'] and proof['publisher_requests']==0 and not proof['source_changed_during_run'] and not proof['runtime_changed_during_run']
 p=load(root/'aggregate-fulltext.json');rows=p['provisions'];toc=load(root/'aggregate-toc.json')['provisions'];pr=jl(root/'record-provenance.jsonl');nodes=jl(root/'source-nodes.jsonl');ds=jl(root/'node-dispositions.jsonl')
 assert len(pr)==len(rows)==m['record_count'];assert len(nodes)==len(ds);assert {x['node_id'] for x in nodes}=={x['node_id'] for x in ds};assert len({x['node_id'] for x in nodes})==len(nodes);assert len({x['node_id'] for x in ds})==len(ds)
 represented=[i for d in ds for i in d['record_ids']];assert len(represented)==len(set(represented))==len(rows);assert set(represented)=={x['record_id'] for x in pr}
 for folder,stem in [('', 'aggregate-fulltext'),('', 'aggregate-toc'),('publications/'+m['publication_id']+'/', 'fulltext'),('publications/'+m['publication_id']+'/', 'toc')]:
  b=(root/(folder+stem+'.csv')).read_bytes();assert b.startswith(b'\xef\xbb\xbf');csv.field_size_limit(64*1024*1024);r=csv.DictReader(io.StringIO(b.decode('utf-8-sig'),newline=''));assert r.fieldnames==F;assert list(r)==load(root/(folder+stem+'.json'))['provisions']
 assert toc==[dict(x,full_text='') for x in rows]
 if kind=='municode-html-publication-v1':
  pid=next(iter(cp['publications']));pub=cp['publications'][pid];ir=jl(source/('publications/'+pid+'/sections.jsonl'));lookup={str(x['node_id']):x for x in ir};field='html';raw_doc={}
  def unit(n):
   u=cp['units'][n];receipt=load(source/u['receipt']);assert receipt['sha256']==u['sha256'];b=(source/receipt['body_file']).read_bytes();assert sha(b)==u['sha256'];return json.loads(b)
  native=unit(pub['toc_unit']);flat=[]
  def walk(n,parent,anc):
   assert n['ParentId']==parent or n['ParentId'] is None and parent is None;flat.append((str(n['Id']),n['Heading'],None if parent is None else str(parent),anc));
   for c in n.get('Children',[]):walk(c,n['Id'],anc+[{'id':str(n['Id']),'heading':n['Heading']}])
  walk(native,None,[]);assert [n['locator']['id'] for n in nodes]==[i for i,_,_,_ in flat]
  assert [x['record_id'].split(':')[-1] for x in pr]==[i for i,_,_,_ in flat if i in lookup]
  for un in pub['content_units']:
   for d in unit(un):assert str(d['Id']) not in raw_doc;raw_doc[str(d['Id'])]=d
  for ident,r in lookup.items():assert sha((raw_doc[ident].get('Content') or '').encode())==r['body_sha256']
  source_parents={i:(pa,anc) for i,h,pa,anc in flat};expected_config=cp['binding']
 else:
  assert kind=='encodeplus-html-publication-v1';ir=jl(source/'records.jsonl');lookup={str(x['id']):x for x in ir};field='body_html';inventory=load(source/'inventory.json')['nodes']
  assert {x['locator']['id'] for x in nodes}=={str(x['id']) for x in inventory}|set(family['embedded_ids'])
  assert [x['record_id'].split(':')[-1] for x in pr]==[str(i) for b in cp['blocks'] for i in b['record_ids']]
  for r in ir:assert sha(r['html'].encode())==r['body_sha256']
  source_parents={str(r['id']):(r['parent_id'],r['path']) for r in ir};expected_config=cp['config']
 assert len(lookup)==len(ir)==len(rows);assert m['source_config']==expected_config==proof['selected_config'];coverage=load(source/'coverage.json');assert load(root/'inherited-coverage.json')==coverage
 counts={'rows':len(rows),'source_nodes':len(nodes),'dispositions':len(ds),'canonical_image_markers':0,'table_tags':0,'list_tags':0,'headings_with_populated_section_number':0,'hierarchy_fields_with_source_components':0}
 for ordinal,(row,prov) in enumerate(zip(rows,pr)):
  assert list(row)==F and all(isinstance(x,str) for x in row.values());assert prov['row_ordinal']==ordinal and sha(canon(row))==prov['corpus_row_sha256'];ident=prov['record_id'].split(':')[-1];r=lookup[ident]
  assert row['full_text']==r[field] and row['source_url']==r['source_url'] and row['citation']==r['heading'];assert sha(canon(r))==prov['rich_ir']['record_sha256'];assert sha(row['full_text'].encode())==prov['canonical_html_sha256']
  assert str(prov['parent_source_id'])==str(source_parents[ident][0]);assert ir[prov['rich_ir']['line_ordinal']]==r
  chain=prov['hierarchy_chain'];assert chain[-1]['id']==ident and chain[-1]['heading']==r['heading'];assert chain[:-1]==source_parents[ident][1]
  for key in H:
   if row[key]:
    assert any(x['heading']==row[key] and x['heading'].strip().split(' ',1)[0].lower().rstrip('.')==key for x in chain);counts['hierarchy_fields_with_source_components']+=1
  if row['section_number']:
   assert any(x.get('field')=='section_number' and x.get('value')==row['section_number'] and x['source_heading']==r['heading'] for x in prov['field_source_components']);assert row['section_number'] in r['heading'];counts['headings_with_populated_section_number']+=1
  raw=(root/prov['raw_artifact_path']).read_bytes();assert sha(raw)==prov['raw_sha256'];counts['canonical_image_markers']+=row['full_text'].count('[IMAGE]');counts['table_tags']+=row['full_text'].lower().count('<table');counts['list_tags']+=row['full_text'].lower().count('<ol')+row['full_text'].lower().count('<ul')
 assert files(root)==before;assert load(root/'validation-report.json')['downstream_ready'] is False;assert coverage['jurisdiction_complete'] is False
 return {'passed':True,'reader':kind,'counts':counts,'input_file_count':len(proof['evidence_sha256_before']),'package_files':len(before),'all_source_html_exact':True,'all_source_parent_chain_exact':True,'all_json_csv_toc_16fields_exact':True,'all_original_coverage_fields_equal':True,'source_version':m['source_version'],'read_only':True,'publisher_requests':0,'source_html_reparsed':False,'image_apis_used':[],'scope':'Lossless projection/consumer proof from standard historically verified rich IR; no new independent raw DOM normalization, legal currency, whole-jurisdiction or attachment transcription qualification.'}
if __name__=='__main__':
 result=audit(Path(sys.argv[1]));Path(sys.argv[2]).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'counts':result['counts']}))
