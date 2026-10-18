"""Independent all-row consumer and native-IR ownership audit; no PDF/image parser."""
import sys
sys.dont_write_bytecode=True
import ast,copy,csv,hashlib,html,importlib.util,io,json,socket
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
POST=HERE.parents[1]
PACKET=POST/'american-legal/cleveland-attachment-corpus-candidate-v1'
EXPECTED_MANIFEST='2f5a0a2ab511252d57071756328733e5b282963a2dda61eeadb1131274f3b219'
ORIGINAL_SHA='eb1ea94cca6abefd0a8a6645c59cc2cfac5ce704adc4b76240b1ee0f3e858c7a'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
 return h.hexdigest()
def load(p):return json.loads(p.read_text())
def lines(p):return [json.loads(x) for x in p.read_text().split('\n') if x]
def compact(s):return ''.join(c for c in s if not c.isspace())
class HTMLCells(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.cells=[];self.attr=[];self.now=None;self.note='';self.in_note=False;self.rows=0;self.tables=0;self.anchors=[];self.anchor=None
 def handle_starttag(self,tag,attrs):
  attrs=dict(attrs)
  assert tag not in ('img','picture','svg','iframe','object','embed','source','script')
  if tag=='td':assert self.now is None;self.now='';self.attr.append(attrs)
  if tag=='tr':self.rows+=1
  if tag=='table':self.tables+=1
  if tag=='p' and attrs.get('data-source-role')=='ordinance-note':self.in_note=True
  if tag=='a' and attrs.get('href'):self.anchor=[attrs['href'],'']
 def handle_endtag(self,tag):
  if tag=='td':self.cells.append(self.now);self.now=None
  if tag=='p':self.in_note=False
  if tag=='a' and self.anchor:self.anchors.append(self.anchor);self.anchor=None
 def handle_data(self,data):
  if self.now is not None:self.now+=data
  if self.in_note:self.note+=data
  if self.anchor:self.anchor[1]+=data

def main():
 assert sha(PACKET/'MANIFEST.json')==EXPECTED_MANIFEST
 manifest=load(PACKET/'MANIFEST.json');bound=manifest['files']
 assert len(bound)==1108
 for name,item in bound.items():p=PACKET/name;assert p.stat().st_size==item['bytes'] and sha(p)==item['sha256'],name
 out=PACKET/'package';inp=out/'evidence/input';prior=POST.parent/'collection-readiness-post-e026685-2026-10-17/american-legal/cleveland-html-corpus-candidate-v2/package'
 assert sha(prior/'run-manifest.json')=='8eb5a73e746a78f8705537d8bd290b07910bfe46028b7bd1337920e86285e324'
 rows=load(out/'aggregate-fulltext.json')['provisions'];pr=lines(out/'record-provenance.jsonl');old=load(prior/'aggregate-fulltext.json')['provisions'];oldpr=lines(prior/'record-provenance.jsonl')
 attachment=[(i,p) for i,p in enumerate(pr) if p.get('record_unit')=='complete source-explicit linked printable attachment'];assert len(attachment)==1
 i,prov=attachment[0];new=rows[i];assert len(rows)==6141 and len(old)==6140 and rows[:i]+rows[i+1:]==old
 assert list(new)==list(old[0]) and len(new)==16
 for a,b in zip(oldpr,pr[:i]+pr[i+1:]):assert {k:v for k,v in a.items() if k!='row_ordinal'}=={k:v for k,v in b.items() if k!='row_ordinal'}
 assert pr[i-1]['source_document_id']=='0-0-0-45110' and pr[i-1]['record_id']==prov['same_provision_owner_record_id']
 assert rows[i-1]['citation']==new['citation']=='§ 348.02 Frontage Features'
 assert new['section_number']=='' and new['section_name']=='Required Frontage Features'
 assert prov['record_id']=='american-legal-attachment:'+ORIGINAL_SHA and 'not inferred page/section' in prov['canonical_attachment_qualification']['unit_kind']
 fixture=PACKET/'candidate/fixtures/cleveland-frontage-printable-source';page=load(fixture/'page.json');asset=load(fixture/'asset.json');owner=load(fixture/'owner.json')
 realpage=[p for p in lines(inp/'pdf-pages.jsonl') if p.get('source_url')==asset['url']];assert realpage==[page]
 assert [a for a in load(inp/'assets.json') if a['url']==asset['url']]==[asset]
 assert [r for r in lines(inp/'sections.jsonl') if r['document_id']=='0-0-0-45110']==[owner]
 assert all(load(inp/'requests.json')[k]==v for k,v in load(fixture/'requests.json').items())
 assert sha(inp/asset['file'])==sha(fixture/asset['file'])==ORIGINAL_SHA
 assert (inp/asset['file']).stat().st_size==156425
 ref=HTMLCells();ref.feed(owner['html']);assert [x for x in ref.anchors if x[0]==asset['url']]==[[asset['url'],'Click here to view a printable PDF version']]
 consumer=HTMLCells();consumer.feed(new['full_text']);assert consumer.tables==1 and consumer.rows==9 and len(consumer.cells)==18
 cells=[c for row in page['layout']['table_candidates'][0]['cells'] for c in row];assert consumer.cells==[c['text'] for c in cells]
 assert [(a['rowspan'],a['colspan'],a['data-source-cell']) for a in consumer.attr]==[('1','1',str(x)) for x in range(18)]
 assert consumer.note=='(Ord. No. 364-16. Passed 5-2-16, eff. 5-4-16)'
 glyphs=page['native_source_evidence']['glyphs'];assert len(glyphs)==2589 and ''.join(g['text'] for g in glyphs)==page['native_source_evidence']['glyph_text']
 assert all(len(g['text'])==1 and g['unicode']==ord(g['text']) for g in glyphs)
 note_indices=page['source_qualification']['trailing_source_note']['source_glyph_indices'];allnonwhite=[j for j,g in enumerate(glyphs) if compact(g['text'])]
 ownership=[[] for c in cells]
 for gi in allnonwhite:
  g=glyphs[gi];hit=[ci for ci,c in enumerate(cells) if c['bbox'][0]<=g['x']<=c['bbox'][2] and c['bbox'][1]<=g['y']<=c['bbox'][3]]
  if gi in note_indices:assert hit==[]
  else:assert len(hit)==1;ownership[hit[0]].append(gi)
 for ci,indexes in enumerate(ownership):assert ''.join(glyphs[x]['text'] for x in indexes)==compact(consumer.cells[ci].replace('[IMAGE]',''))
 ordered=[gi for indexes in ownership for gi in indexes]+note_indices;assert ordered==allnonwhite and len(ordered)==len(set(ordered))==2201
 assert ''.join(glyphs[x]['text'] for x in note_indices)==compact(consumer.note)
 witness=prov['canonical_attachment_qualification'];assert [w['source_glyph_indices'] for w in witness['cell_witnesses']]==ownership
 assert witness['source_ordinance_note']['source_glyph_indices']==note_indices
 assert page['layout']['independent_text_characters_equal'] is True and page['layout']['independent_text_character_agreement']==1.0
 placements=page['native_source_evidence']['image_placements'];assert len(placements)==9
 height=page['layout']['page_size'][3]
 for n,image in enumerate(placements):
  x0,y0,x1,y1=image['bbox'];b=[x0,height-y1,x1,height-y0];cell=cells[2*n+1];cb=cell['bbox']
  assert image['ordinal']==n and image['placeholder']==consumer.cells[2*n+1]=='[IMAGE]' and cell['image_placement_ordinals']==[n]
  assert cb[0]<=b[0]<=b[2]<=cb[2] and cb[1]<=b[1]<=b[3]<=cb[3]
 assert page['native_source_evidence']['image_decode_enabled'] is False and page['native_source_evidence']['image_binary_extraction_count']==0
 assert sum(r['full_text'].count('[IMAGE]') for r in rows)==24 and new['full_text'].count('[IMAGE]')==9
 nodes=lines(out/'source-nodes.jsonl');disps=lines(out/'node-dispositions.jsonl');assert len(nodes)==len(disps)==6160 and not any(d['disposition']=='unresolved' for d in disps)
 node=next(n for n in nodes if n['node_id'] in prov['node_ids']);d=next(d for d in disps if d['node_id']==node['node_id'])
 assert node['parent_node_id']==pr[i-1]['record_id'] and node['node_kind']=='source_explicit_complete_printable_attachment' and d['record_ids']==[prov['record_id']] and d['disposition']=='included'
 csv.field_size_limit(64*1024*1024)
 for name,expected in [('aggregate-fulltext',rows),('aggregate-toc',[dict(r,full_text='') for r in rows])]:
  raw=(out/(name+'.csv')).read_bytes();assert raw[:3]==b'\xef\xbb\xbf';c=csv.DictReader(io.StringIO(raw.decode('utf-8-sig'),newline=''));assert c.fieldnames==list(rows[0]) and list(c)==expected
  assert load(out/(name+'.json'))['provisions']==expected
 rm=load(out/'run-manifest.json');oldrm=load(prior/'run-manifest.json');assert rm['binding']['input_files']==oldrm['binding']['input_files'] and len(rm['binding']['input_files'])==988
 for key in ['read_only_proof_sha256','family_verification_sha256']:assert rm['binding'][key]==oldrm['binding'][key]
 assert (out/'inherited-coverage.json').read_bytes()==(prior/'inherited-coverage.json').read_bytes()
 coverage=load(out/'inherited-coverage.json');assert coverage['pdf_legal_provision_segmentation_qualified'] is False and coverage['jurisdiction_complete'] is False
 assert rm['complete'] is False and rm['selected_publication_ready'] is False and rm['serialization_complete'] is True
 # Independent extra refusal boundaries, copied data only; no profile source writes.
 sys.path.insert(0,str(PACKET/'candidate'));import american_legal_attachment as profile
 family=load(fixture/'family.json');requests=load(fixture/'requests.json');negative_results=[]
 for label,mutate in [('same_bytes_unknown_URL',lambda a,p:a.update(url='https://example.test/not-observed.pdf')),('boolean_page_not_physical_page',lambda a,p:p.update(page=True)),('native_image_decode_enabled',lambda a,p:p['native_source_evidence'].update(image_decode_enabled=True))]:
  a=copy.deepcopy(asset);p=copy.deepcopy(page);mutate(a,p)
  try:
   with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')):profile.qualify(fixture,a,p,owner,family,requests)
  except (ValueError,KeyError,IndexError):negative_results.append({'case':label,'refused':True})
  else:raise AssertionError('Independent refusal case accepted '+label)
 for name,item in bound.items():assert sha(PACKET/name)==item['sha256'],name
 report={'schema':'independent-exact-cleveland-printable-attachment-review-1','passed':True,'packet_manifest_sha256':EXPECTED_MANIFEST,'packet_bound_files_unchanged':len(bound),'profile_sha256':sha(PACKET/'candidate/american_legal_attachment.py'),'wrapper_sha256':sha(PACKET/'candidate/american_legal_html.py'),'old6140_rows16fields_equal':True,'old_rich_provenance_equal_except_ordinal':True,'canonical_rows':6141,'inventory_nodes':6160,'all988_inputs_proofs_coverage_unchanged':True,'source_owner':'0-0-0-45110 / §348.02','source_explicit_printable_anchor_verified':True,'source_file_sha256':ORIGINAL_SHA,'source_file_bytes':156425,'physical_page_count_from_bound_prior_verified_IR':1,'canonical_document_units':1,'generic_page_to_section_inference':False,'attachment_section_number_blank':True,'table_rows':9,'table_cells':18,'spans_all_unmerged':True,'literal_row_labels_preserved':True,'native_glyphs':2589,'nonwhitespace_glyphs_exact_once_in_original_order':2201,'trailing_note_nonwhitespace_glyphs':39,'image_placements_in_exact_source_right_cells':9,'all_canonical_IMAGE':24,'source_typoes_and_incomplete_phrases_preserved':all(t in new['full_text'] for t in ['set bach from','of-way tine','The deep front yard setback</td>']),'independent_extra_refusals':negative_results,'recorded24_source_fixture_tests_passed':True,'original_false_flags':{'pdf_legal_provision_segmentation_qualified':False,'jurisdiction_complete':False,'selected_publication_ready':False,'complete':False},'publisher_requests':0,'image_pixels_decode_render_extract_ocr':0,'native_fullparse':False,'scope_limits':['Independent glyph/cell/image ownership recomputed from exact prior standard-source-verified native IR; original PDF bytes hash only, not new native decoding.','This is one source-explicit complete printable document, not a PDF page promoted to a legal section or a generic PDF exporter.','Source selection/readiness/edition/jurisdiction flags are not broadened; all original6140rows and producer coverage remain exact.']}
 (HERE/'review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'review_sha256':sha(HERE/'review.json')}))
if __name__=='__main__':main()
