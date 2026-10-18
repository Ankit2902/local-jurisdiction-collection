"""Actual finite canonical source projection and corruption tests."""
from pathlib import Path
from collections import Counter
import copy,gzip,hashlib,json,unittest
from unittest.mock import patch,PropertyMock
import pdfplumber,pypdfium2 as p
from pdfminer.pdftypes import PDFStream
from pypdf._page import PageObject
try:from . import sto_appendix_b as m
except ImportError:import sto_appendix_b as m
FIX=Path(__file__).resolve().parent/'fixtures/sto-appendix-b'
def load():
 cfg=json.loads((FIX/'source.json').read_text());rs=[json.loads(l) for l in (FIX/'baseline-seven-pages.jsonl').read_text().splitlines()];old=json.loads(gzip.decompress((FIX/'reconstructed.json.gz').read_bytes()));return cfg,rs,old
class Canonical(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.cfg,cls.base,cls.expected=load();cls.source=FIX/'source.pdf';assert hashlib.sha256(cls.source.read_bytes()).hexdigest()==m.PDF_SHA;cls.calls=[];getdata=PDFStream.get_data
  def no(*a,**kw):cls.calls.append('forbidden');raise AssertionError('Noimage/network/render/OCR')
  def stream(s):
   if getattr(s.attrs.get('Subtype'),'name',None)=='Image':return no()
   return getdata(s)
  cls.guards=[patch('socket.socket',side_effect=no),patch.object(PageObject,'images',new_callable=PropertyMock,side_effect=no),patch.object(p.PdfPage,'render',side_effect=no),patch.object(p.PdfPage,'get_objects',side_effect=no),patch.object(p.PdfImage,'get_bitmap',side_effect=no),patch.object(p.PdfImage,'extract',side_effect=no),patch.object(PDFStream,'get_data',stream)]
  for guard in cls.guards:guard.start()
  cls.pdf=pdfplumber.open(cls.source);cls.native=p.PdfDocument(cls.source.read_bytes());cls.rows=[]
  for n in m.PINS:
   r=copy.deepcopy(next(b for b in cls.base if b['physical_page']==n));pg=cls.native[n-1];tp=pg.get_textpage()
   try:assert m.attach_record(r,cls.pdf.pages[n-1],tp,cls.cfg['item'],m.PDF_SHA);cls.rows.append(r)
   finally:tp.close();pg.close()
 @classmethod
 def tearDownClass(cls):
  cls.native.close();cls.pdf.close()
  for guard in reversed(cls.guards):guard.stop()
  assert not cls.calls
 def test_all_physical_source_cells_become_canonical_and_old_fields_exact_diagnostic(self):
  total=0
  for record in self.rows:
   old=next(b for b in self.base if b['physical_page']==record['physical_page']);src=next(r for r in self.expected['regions'] if r['physical_page']==record['physical_page']);reg=record['source_appendix_b_schedules'][0]
   for k,v in src.items():self.assertEqual(json.loads(json.dumps(reg[k])),v)
   self.assertEqual(record['superseded_detector_diagnostics']['original_record_fields'],{k:old[k] for k in ['tables','ordered_blocks','text','ordering','pdf_qualification']});self.assertEqual(record['canonical_structure_selection']['profile'],'sto_appendix_b');self.assertEqual(len(record['tables']),1)
   wids=[w for b in record['ordered_blocks'] for w in b['word_ids']];gids=[g for b in record['ordered_blocks'] for g in b['source_glyph_ids']];self.assertEqual(Counter(wids),Counter(w['id'] for w in src['source_words']));self.assertEqual(Counter(gids),Counter(g['id'] for g in src['source_glyphs']));self.assertEqual(Counter(m.compact(record['text'])),Counter(m.compact(''.join(w['text'] for w in src['source_words']))));total+=len(record['tables'][0]['cells'])
   self.assertTrue(all(c['independent_character_agreement'] for c in record['tables'][0]['cells']));self.assertFalse(record['pdf_qualification']['source_physical_logical_semantics_complete'])
  self.assertEqual(total,723);self.assertTrue(m.summary(self.rows)['physical_cell_fidelity_complete']);self.assertEqual(m.summary(self.rows)['original_failed_detector_cells_retained'],274)
 def test_preheader_order_context_folios_reference_only_and_boundary_metadata(self):
  r199=next(r for r in self.rows if r['physical_page']==199);t=r199['tables'][0];self.assertEqual([c['text'] for c in t['cells'][:3]],['','','clearance']);self.assertEqual(t['header_rows'],[1,2]);self.assertTrue(r199['text'].startswith('\t\tclearance\nSTO'))
  r198=self.rows[0];self.assertTrue(r198['text'].startswith('APPENDIX B\nOrdinance Traffic Infractions'));self.assertIn('is for reference only and is not a legal description.',r198['text']);self.assertEqual(r198['ordered_blocks'][-1]['text'],'187');self.assertFalse(r198['source_appendix_b_schedules'][0]['cross_page_continuation_witness']['canonical_text_filled_or_merged'])
  self.assertEqual([r['ordered_blocks'][-1]['text'] for r in self.rows],['187','188','189','190','191','192']);self.assertFalse(m.summary(self.rows)['whole_pdf_table_semantics_complete'])
 def test_wrong_scope_noop_and_record_url_owner_table_corruption_fail_before_mutation(self):
  base=next(b for b in self.base if b['physical_page']==199);page=self.pdf.pages[198];pg=self.native[198];tp=pg.get_textpage()
  try:
   for kind in ['otherhash','otherurl','otherpage']:
    r=copy.deepcopy(base);item=copy.deepcopy(self.cfg['item']);sha=m.PDF_SHA
    if kind=='otherhash':sha='0'*64
    elif kind=='otherurl':item['url']='https://wrong.invalid/native'
    else:r['physical_page']=197
    before=copy.deepcopy(r);self.assertFalse(m.attach_record(r,page,tp,item,sha));self.assertEqual(r,before)
   for kind in ['url','owner','table','duplicate_selection','wrongphysical']:
    r=copy.deepcopy(base)
    if kind=='url':r['source_url']='https://wrong.invalid/native#page=199'
    elif kind=='owner':r['document_id']='wrong-owner'
    elif kind=='table':r['tables'][0]['cells'].pop()
    elif kind=='duplicate_selection':r['canonical_structure_selection']={'already':True}
    else:r['physical_page']=200;r['source_url']=self.cfg['item']['url']+'#page=200'
    before=copy.deepcopy(r)
    with self.subTest(fault=kind):
     with self.assertRaises(AssertionError):m.attach_record(r,page,tp,self.cfg['item'],m.PDF_SHA)
     self.assertEqual(r,before)
  finally:tp.close();pg.close()
 def test_header_sorting_word_glyph_loss_and_guessed_cells_refused(self):
  src=next(r for r in self.expected['regions'] if r['physical_page']==199);base=next(b for b in self.base if b['physical_page']==199)
  for kind in ['headerfirst','celltext','wordloss','glyphloss','falseimage']:
   r=copy.deepcopy(src)
   if kind=='headerfirst':r['physical_lines'][0:3]=r['physical_lines'][1:3]+r['physical_lines'][0:1]
   elif kind=='celltext':r['cells'][2]['text']='invented clearance correction'
   elif kind=='wordloss':r['cells'][2]['source_word_ids']=[]
   elif kind=='glyphloss':r['cells'][2]['source_glyph_ids']=[]
   else:r['image_placeholders']=[{'text':'data:image/png;base64,SENTINEL'}]
   with self.subTest(fault=kind):
    with self.assertRaises(AssertionError):m._projection(copy.deepcopy(base),r)
 def test_alias_and_namespace_do_not_weaken_hash_or_body_binding(self):
  n=199;r=copy.deepcopy(next(b for b in self.base if b['physical_page']==n));oldid=r['id'];newid='standalone-native-STO::page:199';r=json.loads(json.dumps(r).replace(oldid,newid));r['id']=newid;r['document_id']='standalone-native-STO';item=copy.deepcopy(self.cfg['item']);item['id']=r['document_id'];item['url']=m.SOURCE_URLS[1];r['source_url']=item['url']+'#page=199';pg=self.native[n-1];tp=pg.get_textpage()
  try:self.assertTrue(m.attach_record(r,self.pdf.pages[n-1],tp,item,m.PDF_SHA));self.assertEqual(r['canonical_structure_selection']['source_url'],item['url']+'#page=199');self.assertTrue(all(w.startswith(newid) for b in r['ordered_blocks'] for w in b['word_ids']))
  finally:tp.close();pg.close()
if __name__=='__main__':unittest.main()
