"""Exact three-region native integration and source-profile refusal tests, no pixels."""
import collections,contextlib,copy,csv,hashlib,io,json,socket,unittest
from pathlib import Path
from unittest.mock import patch
import pdfplumber,pypdfium2
from pdfminer.pdftypes import PDFStream
from PIL import Image
from . import sto_physical_schedule as scoped
HERE=Path(__file__).resolve().parent;FIX=HERE/'fixtures/sto-four-column'
class StoPhysicalSchedule(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.config=json.loads((FIX/'source.json').read_text());cls.item=cls.config['item'];cls.raw=(FIX/'source.pdf').read_bytes();cls.digest=hashlib.sha256(cls.raw).hexdigest();cls.base=[json.loads(l) for l in (FIX/'baseline-three-pages.jsonl').read_text().splitlines()];cls.pdf=pdfplumber.open(io.BytesIO(cls.raw));cls.native=pypdfium2.PdfDocument(cls.raw);cls.calls=[];cls.stack=contextlib.ExitStack();original=PDFStream.get_data
  def noimage(stream):
   if getattr(stream.attrs.get('Subtype'),'name',None)=='Image' or ('W' in stream.attrs and 'H' in stream.attrs):cls.calls.append('image_stream.get_data');raise AssertionError('Image stream forbidden')
   return original(stream)
  def forbidden(*args,**kwargs):cls.calls.append('image_or_network');raise AssertionError('Image/native render/network forbidden')
  cls.stack.enter_context(patch.object(PDFStream,'get_data',noimage))
  for obj,names in [(socket,['socket']),(pypdfium2.PdfPage,['render','get_objects']),(pypdfium2.PdfImage,['extract','get_bitmap','get_data']),(pdfplumber.page.Page,['to_image']),(Image,['open'])]:
   for name in names:
    if hasattr(obj,name):cls.stack.enter_context(patch.object(obj,name,forbidden))
  cls.rows=[]
  for baseline in cls.base:
   n=baseline['physical_page'];native=cls.native[n-1];tp=native.get_textpage()
   try:
    row=copy.deepcopy(baseline);assert scoped.attach_record(row,cls.pdf.pages[n-1],tp,cls.item,cls.digest);cls.rows.append(row)
   finally:tp.close();native.close()
 @classmethod
 def tearDownClass(cls):cls.pdf.close();cls.native.close();cls.stack.close();assert not cls.calls
 def first(self,callback):
  row=copy.deepcopy(self.base[0]);native=self.native[4];tp=native.get_textpage()
  try:return callback(row,self.pdf.pages[4],tp)
  finally:tp.close();native.close()
 def test_actual_regions_cells_rows_original_diagnostics_and_image_identity(self):
  dimensions=scoped.summary(self.rows);self.assertEqual((dimensions['complete_physical_cells'],dimensions['physical_data_rows'],dimensions['header_rows']),(308,74,3));self.assertTrue(dimensions['physical_cell_fidelity_complete']);self.assertFalse(dimensions['logical_continuation_semantics_complete']);self.assertFalse(dimensions['reference_role_intent_complete']);self.assertFalse(dimensions['whole_pdf_table_semantics_complete']);self.assertEqual(dimensions['original_failed_detector_cells_retained'],60)
  source=json.loads((FIX/'reconstructed.json').read_text())
  for baseline,row,expected in zip(self.base,self.rows,source['tables']):
   table=json.loads(json.dumps(row['source_physical_schedules'][0]));self.assertEqual(table['cells'],expected['cells']);self.assertEqual(table['rows'],expected['rows']);self.assertEqual(table['baseline_tables'],baseline['tables']);self.assertFalse(table['publication_or_whole_PDF_table_semantics_complete'])
   original=row['superseded_detector_diagnostics']['original_record_fields'];self.assertEqual(original,{k:baseline[k] for k in row['canonical_structure_selection']['authoritative_fields']})
   unchanged=copy.deepcopy(row)
   for key,value in original.items():unchanged[key]=value
   for key in ['source_physical_schedules','superseded_detector_diagnostics','canonical_structure_selection']:unchanged.pop(key)
   self.assertEqual(unchanged,baseline)
 def test_nonmatching_source_url_or_page_is_unchanged(self):
  for change in ('sha','url','page'):
   row=copy.deepcopy(self.base[0]);item=copy.deepcopy(self.item);digest=self.digest
   if change=='sha':digest='0'*64
   elif change=='url':item['url']='https://example.test/unobserved-alias.pdf'
   else:row['physical_page']=6
   before=copy.deepcopy(row);self.assertFalse(scoped.attach_record(row,None,None,item,digest));self.assertEqual(row,before)
 def test_observed_native_alias_and_id_neutral_ownership(self):
  def check(row,page,tp):
   old=row['id'];new='82-04514ddf4ea3::page:5'
   def rebase(v):
    if isinstance(v,str):return v.replace(old,new)
    if isinstance(v,list):return [rebase(x) for x in v]
    if isinstance(v,dict):return {k:rebase(x) for k,x in v.items()}
    return v
   row=rebase(row);row['document_id']='82-04514ddf4ea3';item=dict(self.item,id=row['document_id'],url=scoped.SOURCE_URLS[1]);row['source_url']=item['url']+'#page=5';self.assertTrue(scoped.attach_record(row,page,tp,item,self.digest));self.assertTrue(all(w['id'].startswith(new) for w in row['source_physical_schedules'][0]['source_words']))
  self.first(check)
 def test_changed_detector_flags_bounds_missing_diagnostics_refused(self):
  for kind in ('flag','bounds','missing'):
   def check(row,page,tp):
    cells=row['tables'][0]['cells']
    if kind=='flag':cells[0]['independent_character_agreement']=not cells[0]['independent_character_agreement']
    elif kind=='bounds':cells[0]['extraction_bbox'][0]+=.01
    else:cells.pop()
    with self.assertRaises(AssertionError):scoped.attach_record(row,page,tp,self.item,self.digest)
    self.assertNotIn('source_physical_schedules',row)
   self.first(check)
 def test_style_or_pinned_bounds_drift_refused(self):
  def check(row,page,tp):
   original=page.dedupe_chars
   class Changed:
    def __init__(self,page):self.page=page
    def __getattr__(self,key):return getattr(self.page,key)
    def extract_words(self,**kwargs):
     words=self.page.extract_words(**kwargs);words[0]['fontname']='ALTERED-SOURCE-FONT';return words
   with patch.object(page,'dedupe_chars',side_effect=lambda **kw:Changed(original(**kw))):
    with self.assertRaises(AssertionError):scoped.attach_record(row,page,tp,self.item,self.digest)
   self.assertNotIn('source_physical_schedules',row);wrong=dict(scoped.PINS[5]);wrong['row_boundaries']=wrong['row_boundaries'][:-1]+[wrong['row_boundaries'][-1]+.01]
   with patch.dict(scoped.PINS,{5:wrong}):
    with self.assertRaises(AssertionError):scoped.attach_record(row,page,tp,self.item,self.digest)
  self.first(check)
 def test_ordinary_native_parser_records_and_coverage_unchanged(self):
  from . import native_document,pdf_structure
  cfg=json.loads((HERE/'configs/native-82-4b983dc51ab6.json').read_text());data=(HERE/'fixtures/overland-solid-waste-native.pdf').read_bytes();expected=[json.loads(l) for l in (FIX/'ordinary-solid-waste-baseline.jsonl').read_text().splitlines()];
  # This remains the generic historical six-page diagnostic control; selected
  # source-native logical behavior is separately exercised by full6 evidence.
  with patch('collectors.encodeplus.solid_waste_logical.matches',return_value=False),patch.object(pdf_structure,'pages',return_value=(expected,[])):
   records,details=native_document.page_records(data,cfg)
  self.assertEqual(records,expected);self.assertNotIn('source_physical_schedule_dimensions',details);self.assertFalse(details['pdf_table_semantics_complete'])
 def test_native_coverage_exposes_physical_not_logical_semantics(self):
  from . import native_document,pdf_structure
  cfg=json.loads((HERE/'configs/native-82-04514ddf4ea3.json').read_text())
  with patch.object(pdf_structure,'pages',return_value=(copy.deepcopy(self.rows),[])):
   records,details=native_document.page_records(self.raw,cfg)
  dimensions=details['source_physical_schedule_dimensions'];self.assertTrue(dimensions['physical_cell_fidelity_complete']);self.assertEqual(dimensions['complete_physical_cells'],308);self.assertEqual(dimensions['unresolved_statute_only_lines'],7);self.assertFalse(dimensions['logical_continuation_semantics_complete']);self.assertFalse(details['pdf_table_semantics_complete']);self.assertTrue(details['reading_order_manual_review_required'])
 def test_partial_summary_cannot_claim_complete_or_whole_pdf(self):
  partial=scoped.summary(self.rows[:-1]);self.assertFalse(partial['physical_cell_fidelity_complete']);self.assertFalse(partial['whole_pdf_table_semantics_complete'])
  with self.assertRaises(AssertionError):scoped.summary(self.rows+[self.rows[0]])
 def test_canonical_consumer_tables_ordered_blocks_text_and_CSV_agree(self):
  from . import native_document,pdf_structure
  for row in self.rows:
   source=row['source_physical_schedules'][0];table=row['tables'][0];block=row['ordered_blocks'][0]
   self.assertEqual(row['canonical_structure_selection']['canonical_table_ids'],[table['id']]);self.assertEqual(block['id'],table['id']);self.assertEqual(block['word_ids'],[w for c in source['cells'] for w in c['source_word_ids']]);self.assertEqual(len(block['word_ids']),len(set(block['word_ids'])))
   self.assertEqual([c['text'] for c in table['cells']],[c['text'] for c in source['cells']]);self.assertTrue(all(c['rowspan']==c['colspan']==1 for c in table['cells']));self.assertEqual(table['header_rows'],[0]);self.assertEqual(row['text'],block['text']);self.assertEqual(row['pdf_qualification']['detected_table_cells'],len(table['cells']));self.assertEqual(row['pdf_qualification']['independent_table_cells_agree'],len(table['cells']))
   expected='\n'.join('\t'.join(c['text'] for c in source['cells'] if c['row']==ri) for ri in range(len(source['rows'])));self.assertEqual(row['text'],expected)
   exported=native_document.outputs([row]);jsonrow=json.loads(exported['records.jsonl']);csvrow=next(csv.DictReader(io.StringIO(exported['records.csv'].decode())));self.assertEqual(jsonrow['text'],expected);self.assertEqual(csvrow['text'],expected);self.assertEqual(jsonrow['tables'],json.loads(json.dumps(row['tables'])))
 def test_exact_superseded_diagnostics_restores_original_and_old_false_cells(self):
  count=0
  for before,after in zip(self.base,self.rows):
   old=after['superseded_detector_diagnostics']['original_record_fields'];self.assertEqual(old,{k:before[k] for k in ['tables','ordered_blocks','text','ordering','pdf_qualification']});count+=sum(not c['independent_character_agreement'] for t in old['tables'] for c in t['cells']);self.assertEqual(after['raw_ref'],before['raw_ref']);self.assertEqual(after['raw_sha256'],before['raw_sha256']);self.assertEqual(after['image_placeholder_count'],before['image_placeholder_count']);self.assertEqual(len(after['tables']),1)
  self.assertEqual(count,60)
 def test_canonical_projection_refuses_changed_header_word_glyph_or_blank(self):
  baseline=self.base[0];original=self.rows[0]['source_physical_schedules'][0]
  for kind in ('header','word','glyph','blank'):
   with self.subTest(kind=kind):
    source=copy.deepcopy(original);nonempty=next(c for c in source['cells'] if c['source_word_ids']);blank=next(c for c in source['cells'] if not c['source_word_ids'])
    if kind=='header':nonempty['role']='Invented header role'
    elif kind=='word':nonempty['source_word_ids'].append(nonempty['source_word_ids'][0])
    elif kind=='glyph':nonempty['source_glyph_ids'].pop()
    else:blank['text']='Invented continuation value'
    before=copy.deepcopy(baseline)
    with self.assertRaises(AssertionError):scoped._canonical_projection(baseline,source)
    self.assertEqual(baseline,before)
 def test_canonical_source_anomaly_and_unmerged_blank_rows_remain_explicit(self):
  sources=[s for r in self.rows for s in r['source_physical_schedules']];anomalies=[row for s in sources for row in s['rows'] if row.get('source_alignment_anomaly')];self.assertEqual(len(anomalies),1);self.assertEqual(anomalies[0]['printed_values'],['8-1743','12.04.178.2','','Safety Glazing Material Required']);continuations=[row for s in sources for row in s['rows'] if row.get('statute_only_line')];self.assertEqual(len(continuations),7);self.assertTrue(all(not r['logical_merge_performed'] and not r['statute_only_line']['logical_continuation_association_qualified'] for r in continuations))
  before=copy.deepcopy(self.rows[0])
  with self.assertRaisesRegex(AssertionError,'already selected'):scoped._canonical_projection(self.rows[0],sources[0])
  self.assertEqual(self.rows[0],before)
if __name__=='__main__':unittest.main(verbosity=2)
