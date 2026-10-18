"""Independent actual reader consumer/source audit. No collector/normalizer imports."""
import collections,csv,hashlib,io,json,re,socket,sys
from pathlib import Path
from unittest.mock import patch
from bs4 import BeautifulSoup
B=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00');S=B/'outputs/collection-readiness-poste026685-2026-10-17/ecode-corpus-reader-v1';H=Path(__file__).resolve().parent
FIELDS='jurisdiction code_name division title subtitle chapter subchapter article part subpart section_number section_name citation full_text source_url scrape_date'.split()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def lines(p):return [json.loads(x)for x in p.read_text().split('\n')if x]
def tree(p):return {str(x.relative_to(p)):sha(x)for x in p.rglob('*')if x.is_file()}
def norm(s):return re.sub(r'\s+',' ',s).strip()
def cells(t):
 return [(c.name,c.get('rowspan','1'),c.get('colspan','1'),norm(c.get_text()))for c in t.select('th,td')]
def main():
 before=tree(S);m=load(S/'MANIFEST.json');assert sha(S/'MANIFEST.json')=='8b8343f6bb5fe84478ebb302fab7f6810aab73896b9240d662df09e5633b1635';assert {x['path']:x['sha256']for x in m['files']}=={k:v for k,v in before.items()if k!='MANIFEST.json'}
 P=S/'package';R=P/'evidence/input';cp=load(R/'checkpoint.json');inv=load(R/'inventory.json');ds=load(R/'dispositions.json');ir=lines(R/'records.jsonl');by={r['id']:r for r in ir};nodes=lines(P/'source-nodes.jsonl');disps=lines(P/'node-dispositions.jsonl');pr=lines(P/'record-provenance.jsonl');rows=load(P/'aggregate-fulltext.json')['provisions'];cov=load(R/'coverage.json');assert load(P/'inherited-coverage.json')==cov
 assert len(ir)==len(rows)==len(pr)==3006 and len(inv)==len(ds)==len(nodes)==len(disps)==3253
 assert collections.Counter(d['disposition']for d in disps)=={'included':3006,'structural':194,'reserved_or_repealed':53}
 assert {d['node_id'].split(':',1)[1]:d['evidence']for d in disps}=={d['id']:d for d in ds}
 proof=load(P/'evidence/proofs/read-only-proof.json');f=load(P/'evidence/proofs/family-verification.json');assert proof['evidence_sha256_before']==proof['evidence_sha256_after']==tree(R);assert dict(f,verified=None)!=cov and {k:v for k,v in f.items()if k!='verified'}==cov and f['verified']is True
 positions={};raws={};allraw401=[];rawbodies={};notes_source_checked=0;tables_source_checked=0;source_differences=[]
 for a in cp['artifacts']:
  p=R/a['path'];assert sha(p)==a['sha256']and p.stat().st_size==a['bytes'];sp=BeautifulSoup(p.read_bytes().decode('utf-8','strict'),'html.parser');found=[(t['data-guid'],t['data-position'])for t in sp.select('#toc .contentTitle[data-guid][data-position]')];allraw401.append((a['path'],len(found)))
  if a['role']not in ['root-start','content']or a['status']!=200:continue
  local=[]
  for ident,value in found:
   v=int(value);local.append(v);assert ident not in positions or positions[ident]==v;positions[ident]=v
  assert local==sorted(local)and len(local)==len(set(local))
  raws[a['path']]=a
  # Parse source own bodies for direct source-table/note checks. Nested content
  # owners are removed; no image byte/member or serializer API is invoked.
  for r in ir:
   if r['raw_witnesses'][0]!=a['path']:continue
   owner=sp.find(id=r['id']+'_content');assert owner is not None;owned=BeautifulSoup(str(owner),'html.parser')
   for child in owned.select('.content .content,article article'):child.decompose()
   for ui in owned.select('script,button,input,.actions,.selection-control'):ui.decompose()
   for tag in list(owned.select('picture,svg,img')):
    if tag.parent:tag.replace_with('[IMAGE]')
   expected_tables=owned.select('table');retained_tables=[BeautifulSoup(t,'html.parser').find('table')for t in r['tables_html']]
   assert len(expected_tables)==len(retained_tables)
   for x,y in zip(expected_tables,retained_tables):
    assert cells(x)==cells(y),(r['id'],'source table cells');tables_source_checked+=1
   expected_notes=owned.select('.history,.footnote,.footnotes,.note');retained_notes=[BeautifulSoup(t,'html.parser').find()for t in r['notes_html']];assert len(expected_notes)==len(retained_notes)
   for x,y in zip(expected_notes,retained_notes):
    assert norm(x.get_text())==norm(y.get_text()),(r['id'],'source note text');notes_source_checked+=1
 rootid=cp['identity']['customer_id'];assert len(positions)==3252 and set(positions)=={n['id']for n in inv}-{rootid} and len(set(positions.values()))==3252
 assert [n['node_id'].split(':',1)[1]for n in nodes]==[rootid]+sorted(positions,key=positions.get)
 ordinals={r['id']:i for i,r in enumerate(ir)};printed=0;counts=collections.Counter()
 for i,(row,p)in enumerate(zip(rows,pr)):
  ident=p['record_id'].split(':',1)[1];r=by[ident];assert list(row)==FIELDS and all(isinstance(v,str)for v in row.values());assert row['full_text']==r['semantic_html'];assert p['notes_html']==r['notes_html']and p['tables_html']==r['tables_html'];assert p['rich_ir']['line_ordinal']==ordinals[ident];assert p['source_order_witness']['literal_data_position']==str(positions[ident]);assert p['image_placeholder_count']==r['image_placeholder_count']==row['full_text'].count('[IMAGE]');assert row['source_url']==r['source_url']and row['scrape_date']==raws[r['raw_witnesses'][0]]['retrieved_at'];assert row['citation']==r['heading'];assert row['jurisdiction']==cp['config']['jurisdiction']and row['code_name']==cp['identity']['name'];assert p['parent_source_id']==r['parent_id'];assert p['hierarchy_chain'][-1]['id']==ident
  # Independently derive exact16field mapping from the literal retained chain.
  expected={x:''for x in FIELDS};expected.update(jurisdiction=row['jurisdiction'],code_name=row['code_name'],section_name=r['heading'],citation=r['heading'],full_text=r['semantic_html'],source_url=r['source_url'],scrape_date=row['scrape_date']);groups=collections.defaultdict(list)
  for n in p['hierarchy_chain']:
   label=n['heading'].strip();part,sep,rest=label.partition(' ');role=part.lower().rstrip('.')
   if role in ['division','title','subtitle','chapter','subchapter','article','part','subpart']and sep and rest:groups[role].append(label)
  for role,values in groups.items():
   unique=list(dict.fromkeys(values))
   if len(unique)==1:expected[role]=unique[0]
  if r['kind']=='section':
   match=re.fullmatch(r'(?:§|SECTION)\s*(\S+)\s*(.*)',r['heading'],re.S);assert match;expected['section_number']=match[1].rstrip(':');expected['section_name']=match[2];printed+=1
  assert row==expected,(ident,'16field independent projection')
  counts['IMAGE']+=r['image_placeholder_count'];counts['tables']+=len(r['tables_html']);counts['notes']+=len(r['notes_html'])
 assert counts['IMAGE']==28 and counts['tables']==24
 for folder,stem in [('', 'aggregate-fulltext'),('', 'aggregate-toc'),('publications/'+proof['publication_id']+'/', 'fulltext'),('publications/'+proof['publication_id']+'/', 'toc')]:
  data=(P/(folder+stem+'.csv')).read_bytes();assert data.startswith(b'\xef\xbb\xbf');csv.field_size_limit(64*1024*1024);reader=csv.DictReader(io.StringIO(data.decode('utf-8-sig'),newline=''));assert reader.fieldnames==FIELDS;assert list(reader)==load(P/(folder+stem+'.json'))['provisions']
 assert load(P/'aggregate-toc.json')['provisions']==[dict(r,full_text='')for r in rows]
 assert cov['complete']is False and cov['publication_text_complete']is False and cov['attachments_complete']is False and cov['start_end_inventory_consistent']is False and len(cov['missing_assets'])==6 and cov['acquired_assets']==0 and cov['resumable']is False;assert any(e.get('access_stop')and '403'in e['message']for e in cov['errors']);assert cp['network_prohibited']is True
 report=load(P/'validation-report.json');assert report['complete']is False and report['downstream_ready']is False and report['serialization_complete']is True
 assert tree(S)==before
 result={'passed':True,'input_packet_manifest_sha256':sha(S/'MANIFEST.json'),'files_checked':len(before)-1,'input_files':len(tree(R)),'records_exact16fields':3006,'source_nodes_and_dispositions':3253,'disposition_counts':dict(collections.Counter(d['disposition']for d in disps)),'raw_artifacts_checked':len(allraw401),'literal_source_positions':3252,'all_source_order_and_owner_provenance_equal':True,'printed_section_numbers':printed,'source_table_count':tables_source_checked,'source_note_element_occurrences':notes_source_checked,'canonical_notes_array_occurrences':counts['notes'],'IMAGE_count':28,'all_4_CSV_JSON_BOM_projections_equal':True,'closing_sweep_missing':True,'required_documents_missing':6,'retained_403_stop':True,'publication_ready':False,'strict_complete':False,'source_unchanged':True,'source_normalizer_native_image_network_apis_called':False,'reader_code_sha256':sha(S/'source/ecode_html.py'),'scope':'Full retained acquired HTML only; no publication, native, edition, required-document or jurisdiction completeness promotion.'};(H/'consumer-review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':
 with patch.object(socket,'socket',side_effect=AssertionError('Offline')):main()
