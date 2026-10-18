"""Finite actual-source recomputation, profile drift and scope controls; no pixels."""
import contextlib,copy,hashlib,io,json,socket,unittest
from pathlib import Path
from unittest.mock import patch
import pdfplumber,pypdfium2
from pdfminer.pdftypes import PDFStream
from PIL import Image
from . import upoc_printed_index as scoped
H=Path(__file__).resolve().parent;F=H/'fixtures/upoc-index';canon=lambda v:json.loads(json.dumps(v))
class UpocPrintedIndex(unittest.TestCase):
 @classmethod
 def setUpClass(c):
  c.cfg=json.loads((F/'source.json').read_text());c.base=[json.loads(l) for l in (F/'baseline-four-regions.jsonl').read_text().splitlines()];c.expected=json.loads((F/'reconstructed.json').read_text());c.sources={};c.stack=contextlib.ExitStack();c.calls=[];original=PDFStream.get_data
  def noimage(s):
   if getattr(s.attrs.get('Subtype'),'name',None)=='Image' or ('W' in s.attrs and 'H' in s.attrs):c.calls.append('image_stream');raise AssertionError('No images')
   return original(s)
  def forbidden(*a,**kw):c.calls.append('image_or_network');raise AssertionError('No image/render/OCR/network')
  c.stack.enter_context(patch.object(PDFStream,'get_data',noimage))
  for obj,names in [(socket,['socket']),(pypdfium2.PdfPage,['render','get_objects']),(pypdfium2.PdfImage,['extract','get_bitmap','get_data']),(pdfplumber.page.Page,['to_image']),(Image,['open'])]:
   for n in names:
    if hasattr(obj,n):c.stack.enter_context(patch.object(obj,n,forbidden))
  for conf in c.cfg['items']:
   it=conf['item'];data=(F/(it['expected_sha256']+'.pdf')).read_bytes();assert hashlib.sha256(data).hexdigest()==it['expected_sha256'];c.sources[it['id']]=(it,data,pdfplumber.open(io.BytesIO(data)),pypdfium2.PdfDocument(data))
  c.rows=[]
  for b in c.base:
   it,data,pdf,nat=c.sources[b['document_id']];n=b['physical_page'];p=nat[n-1];tp=p.get_textpage()
   try:
    r=copy.deepcopy(b);assert scoped.attach_record(r,pdf.pages[n-1],tp,it,it['expected_sha256']);c.rows.append(r)
   finally:tp.close();p.close()
 @classmethod
 def tearDownClass(c):
  for it,data,pdf,nat in c.sources.values():pdf.close();nat.close()
  c.stack.close();assert not c.calls
 def first(self,fn):
  r=copy.deepcopy(self.base[0]);it,data,pdf,nat=self.sources[r['document_id']];p=nat[0];tp=p.get_textpage()
  try:return fn(r,pdf.pages[0],tp,it)
  finally:tp.close();p.close()
 def test_actual_four_regions_exact_reviewed_output_and_legacy_fields(self):
  for b,r,e in zip(self.base,self.rows,self.expected['regions']):
   x=copy.deepcopy(r['source_printed_indexes'][0]);x.pop('source_binding');x.pop('detector_evidence_disposition');self.assertEqual(canon(x),e)
   z=copy.deepcopy(r);z.pop('source_printed_indexes')
   for k in ['source_index_glyph_capture_complete','source_index_unicode_complete','source_index_rectangle_boundaries_complete']:z['pdf_qualification'].pop(k)
   self.assertEqual(z,b);self.assertFalse(x['whole_publication_table_semantics_complete']);self.assertFalse(x['legacy_40th_vs_primary_42nd_adoption_conflict_resolved'])
 def test_known_content_and_CID_overlap_edition_limits_separate(self):
  d=scoped.summary(self.rows);self.assertFalse(d['whole_book_semantic_or_table_completeness_qualified']);self.assertFalse(d['legacy_40th_vs_primary_42nd_adoption_conflict_resolved']);gs=d['sources']
  for key,n in [('source_words',859),('source_glyphs',7112),('fields',444),('index_entries',112),('original_failed_detector_cells_retained',417),('unqualified_CID_headings',2),('known_unicode_rectangle_overlap_diagnostics',2)]:self.assertEqual(sum(g[key] for g in gs),n)
  for g in gs:self.assertTrue(g['source_index_glyph_capture_complete']);self.assertFalse(g['rectangle_boundaries_complete']);self.assertFalse(g['whole_book_semantic_or_edition_complete'])
  self.assertFalse(next(g for g in gs if g['edition'].startswith('40th'))['all_region_unicode_qualified'])
 def test_unknown_profile_noop_selected_ownership_refusals(self):
  for change in ['sha','url','page']:
   r=copy.deepcopy(self.base[0]);it=copy.deepcopy(self.sources[r['document_id']][0]);h=it['expected_sha256']
   if change=='sha':h='0'*64
   elif change=='url':it['url']='https://wrong.invalid/unobserved'
   else:r['physical_page']=168
   before=copy.deepcopy(r);self.assertFalse(scoped.attach_record(r,None,None,it,h));self.assertEqual(r,before)
  for change in ['raw','owner','url']:
   def check(r,p,tp,it):
    r[{'raw':'raw_sha256','owner':'document_id','url':'source_url'}[change]]='wrong';before=copy.deepcopy(r)
    with self.assertRaises(AssertionError):scoped.attach_record(r,p,tp,it,it['expected_sha256'])
    self.assertEqual(r,before)
   self.first(check)
 def test_observed_current_alias_id_neutral_namespace(self):
  b=next(r for r in self.base if r['raw_sha256'].startswith('bb91') and r['physical_page']==1);it,data,pdf,nat=self.sources[b['document_id']];p=nat[0];tp=p.get_textpage()
  try:
   old=b['id'];new='native-upoc::page:1'
   def rebase(v):
    if isinstance(v,str):return v.replace(old,new)
    if isinstance(v,list):return [rebase(x) for x in v]
    if isinstance(v,dict):return {k:rebase(x) for k,x in v.items()}
    return v
   r=rebase(b);it=dict(it,id='native-upoc',url=scoped.PROFILES[b['raw_sha256']]['urls'][1]);r['document_id']=it['id'];r['source_url']=it['url']+'#page=1';self.assertTrue(scoped.attach_record(r,pdf.pages[0],tp,it,b['raw_sha256']));self.assertTrue(r['source_printed_indexes'][0]['source_words'][0]['id'].startswith(new))
  finally:tp.close();p.close()
 def test_changed_detector_flags_bounds_missing_cells_refused(self):
  for change in ['flag','bounds','missing']:
   def check(r,p,tp,it):
    cs=r['tables'][0]['cells']
    if change=='flag':cs[0]['independent_character_agreement']=not cs[0]['independent_character_agreement']
    elif change=='bounds':cs[0]['extraction_bbox'][0]+=.0001
    else:cs.pop()
    before=copy.deepcopy(r)
    with self.assertRaises(AssertionError):scoped.attach_record(r,p,tp,it,it['expected_sha256'])
    self.assertEqual(r,before)
   self.first(check)
 def test_style_native_stream_and_source_fingerprint_drift_refused(self):
  def check(r,p,tp,it):
   original=p.dedupe_chars
   class Changed:
    def __init__(self,p):self.p=p
    def __getattr__(self,k):return getattr(self.p,k)
    def extract_words(self,**kw):
     ws=self.p.extract_words(**kw);ws[0]['fontname']='ALTERED';return ws
   with patch.object(p,'dedupe_chars',side_effect=lambda **kw:Changed(original(**kw))):
    with self.assertRaises(AssertionError):scoped.attach_record(r,p,tp,it,it['expected_sha256'])
   with patch.object(tp,'get_text_range',return_value=tp.get_text_range()+'MUTATED'):
    with self.assertRaises(AssertionError):scoped.attach_record(r,p,tp,it,it['expected_sha256'])
   profile=copy.deepcopy(scoped.PROFILES[it['expected_sha256']]);profile['pins'][1]['region_sha256']='0'*64
   with patch.dict(scoped.PROFILES,{it['expected_sha256']:profile}):
    with self.assertRaises(AssertionError):scoped.attach_record(r,p,tp,it,it['expected_sha256'])
   self.assertNotIn('source_printed_indexes',r)
  self.first(check)
 def test_partial_duplicate_and_native_coverage_separation(self):
  self.assertFalse(scoped.summary(self.rows[:1])['sources'][0]['source_index_glyph_capture_complete'])
  with self.assertRaises(AssertionError):scoped.summary(self.rows+[self.rows[0]])
  from . import native_document,pdf_structure
  it=self.cfg['items'][0]['item'];cfg={'id':'native-upoc','title':'UPOC','url':it['url'],'jurisdiction':'Overland Park','state':'KS','expected_sha256':it['expected_sha256'],'expected_pages':172}
  with patch.object(pdf_structure,'pages',return_value=(copy.deepcopy(self.rows[:2]),[])):rs,ds=native_document.page_records(self.sources[it['id']][1],cfg)
  self.assertIn('source_printed_index_dimensions',ds);self.assertNotIn('source_physical_schedule_dimensions',ds);self.assertFalse(ds['pdf_table_semantics_complete']);self.assertTrue(ds['reading_order_manual_review_required'])
 def test_ordinary_sixpage_full_parser_noop(self):
  from . import native_document
  cfg=json.loads((H/'configs/native-82-4b983dc51ab6.json').read_text());data=(H/'fixtures/overland-solid-waste-native.pdf').read_bytes();expected=[json.loads(l) for l in (H/'fixtures/sto-four-column/ordinary-solid-waste-baseline.jsonl').read_text().splitlines()];rs,ds=native_document.page_records(data,cfg);self.assertEqual(rs,expected);self.assertNotIn('source_printed_index_dimensions',ds);self.assertNotIn('source_physical_schedule_dimensions',ds);self.assertFalse(ds['pdf_table_semantics_complete'])
if __name__=='__main__':unittest.main(verbosity=2)
