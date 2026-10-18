"""Native attachment labels preserve exact stream/geometry and qualification gaps."""
import copy,hashlib,socket,unittest
from unittest.mock import patch
import pypdfium2,pdf_structure,native_labels
from test_pdf_structure import native,text,ITEM,CONFIG
class NativeLabels(unittest.TestCase):
 def fixture(self,commands=None):
  data=native(commands if commands is not None else text(40,700,'35202.2115 Havana St'))
  config=dict(CONFIG,native_label_attachment_rules=[{'url':ITEM['url'],'sha256':hashlib.sha256(data).hexdigest(),'source_kind':'map'}]);owner=[{'owner_record_id':'section-1','owner_document_id':'source-item','owner_source_sha256':'a'*64,'reference_url':ITEM['url']}]
  rows,_=pdf_structure.pages(data,ITEM,config);return data,config,owner,rows
 def project(self,data,config,owner,rows):
  def deny(*a,**k):raise AssertionError('Forbidden image/network operation')
  with patch.object(socket.socket,'connect',deny),patch.object(pypdfium2.PdfPage,'render',deny),patch.object(pypdfium2.PdfPage,'get_objects',deny),patch.object(pypdfium2.PdfImage,'extract',deny),patch.object(pypdfium2.PdfImage,'get_bitmap',deny):return native_labels.project(data,ITEM,config,owner,rows)
 def test_full_label_stream_source_geometry_and_owners(self):
  data,c,o,r=self.fixture();before=copy.deepcopy(r);rows,q=self.project(data,c,o,r)
  self.assertEqual(r,before);self.assertIn('35202.2115 Havana St',rows[0]['text']);self.assertTrue(q['native_label_projection_complete']);self.assertTrue(q['attachment_text_normalization_qualified']);self.assertFalse(q['semantic_complete']);self.assertEqual(rows[0]['required_by'],o);self.assertEqual(''.join(g['qualified_text'] for g in rows[0]['native_label_glyph_geometry']),'35202.2115HavanaSt');self.assertFalse(rows[0]['native_label_qualification']['inferred_map_reading_order'])
 def test_engine_disagreement_not_waived(self):
  d,c,o,r=self.fixture();r[0]['pdf_qualification']['independent_text_engine_characters_agree']=False
  rows,q=self.project(d,c,o,r);self.assertFalse(q['attachment_text_normalization_qualified']);self.assertTrue(q['native_label_projection_complete']);self.assertTrue(rows[0]['native_label_qualification']['remaining_native_text_qualification_gap'])
 def test_actual_zero_glyph_vector_is_image_policy_na(self):
  d,c,o,r=self.fixture('20 20 m 200 200 l 200 20 l h S\n');rows,q=self.project(d,c,o,r);self.assertEqual(rows[0]['text'],'[IMAGE]');self.assertEqual(q['source_proven_no_glyph_pages'],1);self.assertTrue(q['attachment_text_normalization_qualified'])
 def test_source_counts_and_stream_cannot_be_faked(self):
  d,c,o,r=self.fixture();r[0]['pdfium_stream_text']='different'
  with self.assertRaises(ValueError):self.project(d,c,o,r)
  d,c,o,r=self.fixture();del r[0]['pdf_qualification']['source_original_glyph_count']
  with self.assertRaises(ValueError):self.project(d,c,o,r)
 def test_selection_owner_hash_page_binding_required(self):
  for mutation in ('rule','owner','hash','page','geometry'):
   d,c,o,r=self.fixture()
   if mutation=='rule':c['native_label_attachment_rules']=[]
   if mutation=='owner':o=[]
   if mutation=='hash':c['native_label_attachment_rules'][0]['sha256']='0'*64
   if mutation=='page':r[0]['physical_page']=2
   if mutation=='geometry':r[0]['height']+=2
   with self.assertRaises(ValueError):self.project(d,c,o,r)
 def test_ordinary_borders_do_not_become_map_graphics(self):
  d,c,o,r=self.fixture();r[0]['pdf_qualification']['vector_curve_count']=4;rows,q=self.project(d,c,o,r);self.assertFalse(rows[0]['native_label_qualification']['whole_vector_map_placeholder_qualified'])
if __name__=='__main__':unittest.main()
