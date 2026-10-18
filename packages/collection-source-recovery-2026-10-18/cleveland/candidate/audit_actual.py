"""All original corpus rows unchanged + independent attachment consumer, no parser."""
import sys
sys.dont_write_bytecode=True
import json,hashlib,csv,io,time
from html.parser import HTMLParser
from pathlib import Path
B=Path(__file__).resolve().parent;O=B/'package';R=O/'evidence/input';OLD=B.parents[2]/'collection-readiness-post-e026685-2026-10-17/american-legal/cleveland-html-corpus-candidate-v2/package'
def load(p):return json.loads(p.read_text())
def lines(p):return [json.loads(x) for x in p.read_text().split('\n') if x]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
start=time.time();rows=load(O/'aggregate-fulltext.json')['provisions'];prs=lines(O/'record-provenance.jsonl');oldrows=load(OLD/'aggregate-fulltext.json')['provisions'];oldprs=lines(OLD/'record-provenance.jsonl');attachments=[(i,p) for i,p in enumerate(prs) if p.get('record_unit')=='complete source-explicit linked printable attachment'];assert len(attachments)==1;idx,pr=attachments[0];row=rows[idx];assert len(rows)==6141;assert rows[:idx]+rows[idx+1:]==oldrows
# Every original source body, note, rich field and raw witness remains unchanged.
for old,new in zip(oldprs,prs[:idx]+prs[idx+1:]):assert {k:v for k,v in old.items() if k!='row_ordinal'}=={k:v for k,v in new.items() if k!='row_ordinal'}
assert prs[idx-1]['record_id']==pr['same_provision_owner_record_id'] and rows[idx-1]['citation']=='§ 348.02 Frontage Features'
assert row['section_number']=='' and row['section_name']=='Required Frontage Features' and row['citation']==rows[idx-1]['citation'];assert row['source_url'].endswith('/DATAOBJECTS/0-0-0-13294.pdf') and row['scrape_date']=='2026-10-17T21:35:23.972934+00:00'
for key in ['jurisdiction','code_name','division','title','subtitle','chapter','subchapter','article','part','subpart']:assert row[key]==rows[idx-1][key]
pages=lines(R/'pdf-pages.jsonl');page=next(p for p in pages if p['source_url']==row['source_url']);asset=next(a for a in load(R/'assets.json') if a['url']==row['source_url']);assert sha(R/asset['file'])==pr['raw_sha256']==asset['sha256'];native_cells=[c for r in page['layout']['table_candidates'][0]['cells'] for c in r]
class Consumer(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.cells=[];self.spans=[];self.current=None;self.note='';self.in_note=False;self.tables=0;self.rows=0
 def handle_starttag(self,t,a):
  a=dict(a)
  if t=='table':self.tables+=1
  if t=='tr':self.rows+=1
  if t=='td':assert self.current is None;self.current='';self.spans.append((a['rowspan'],a['colspan'],a['data-source-cell']))
  if t=='p':assert a['data-source-role']=='ordinance-note';self.in_note=True
  assert t not in ['img','picture','svg','object','iframe','embed','source','script']
 def handle_endtag(self,t):
  if t=='td':self.cells.append(self.current);self.current=None
  if t=='p':self.in_note=False
 def handle_data(self,s):
  if self.current is not None:self.current+=s
  elif self.in_note:self.note+=s
c=Consumer();c.feed(row['full_text']);assert c.tables==1 and c.rows==9 and c.cells==[x['text'] for x in native_cells];assert c.spans==[('1','1',str(i)) for i in range(18)];assert c.note==page['layout']['text_blocks'][-1]['lines'][0]['text'];assert row['full_text'].count('[IMAGE]')==9
w=pr['canonical_attachment_qualification'];indices=[i for cell in w['cell_witnesses'] for i in cell['source_glyph_indices']]+w['source_ordinance_note']['source_glyph_indices'];glyphs=page['native_source_evidence']['glyphs'];expected=[i for i,g in enumerate(glyphs) if g['text'].strip()];assert indices==expected and len(indices)==len(set(indices))==2201;assert ''.join(glyphs[i]['text'] for i in indices)==''.join(ch for ch in ''.join(c.cells).replace('[IMAGE]','')+c.note if not ch.isspace())
assert sum(x['full_text'].count('[IMAGE]') for x in rows)==24
# Original proof/input and coverage bytes remain exact, including old false flags.
manifest=load(O/'run-manifest.json');oldmanifest=load(OLD/'run-manifest.json');assert manifest['binding']['input_files']==oldmanifest['binding']['input_files'];assert manifest['binding']['read_only_proof_sha256']==oldmanifest['binding']['read_only_proof_sha256'] and manifest['binding']['family_verification_sha256']==oldmanifest['binding']['family_verification_sha256'];assert (O/'inherited-coverage.json').read_bytes()==(OLD/'inherited-coverage.json').read_bytes();assert load(O/'inherited-coverage.json')['pdf_legal_provision_segmentation_qualified'] is False
nodes=lines(O/'source-nodes.jsonl');ds=lines(O/'node-dispositions.jsonl');assert len(nodes)==len(ds)==6160;dis=next(x for x in ds if x['record_ids']==[pr['record_id']]);assert dis['disposition']=='included';assert not any(x['disposition']=='unresolved' for x in ds);assert len(lines(O/'exceptions.jsonl'))==1439
fieldnames=list(rows[0]);assert len(fieldnames)==16
for prefix,expected_rows in [('aggregate-fulltext',rows),('aggregate-toc',[dict(r,full_text='') for r in rows])]:
 raw=(O/(prefix+'.csv')).read_bytes();assert raw.startswith(b'\xef\xbb\xbf');csv.field_size_limit(64*1024*1024);r=csv.DictReader(io.StringIO(raw.decode('utf-8-sig'),newline=''));assert r.fieldnames==fieldnames and list(r)==expected_rows;assert load(O/(prefix+'.json'))['provisions']==expected_rows
summary={'passed':True,'canonical_rows':6141,'all_original_6140_rows_16fields_unchanged':True,'all_original_rich_provenance_unchanged_except_row_ordinal':True,'attachment_canonical_units':1,'attachment_grid_rows':9,'attachment_cells':18,'attachment_native_glyphs':2589,'attachment_nonwhitespace_glyphs_exact_once':2201,'attachment_source_ordinance_notes':1,'attachment_IMAGE_markers':9,'all_canonical_IMAGE_markers':24,'source_nodes_dispositions':6160,'unresolved_dispositions':0,'all988_source_input_hashes_and_both_proofs_unchanged':True,'original_false_PDF_segmentation_flag_preserved':True,'strict_complete':manifest['complete'],'package_manifest_sha256':sha(O/'run-manifest.json'),'prior_package_manifest_sha256':sha(OLD/'run-manifest.json'),'scope':'One exact complete printable attachment; no generic PDF sections, new source capture, new edition, broader adopted-law or jurisdiction closure','seconds':time.time()-start,'consumer_sha256':sha(Path(__file__))};assert manifest['complete'] is False;(B/'actual-consumer.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
