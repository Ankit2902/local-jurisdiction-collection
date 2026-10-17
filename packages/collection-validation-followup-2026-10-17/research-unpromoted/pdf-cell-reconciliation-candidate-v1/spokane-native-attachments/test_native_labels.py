import copy,json,socket,unittest
from pathlib import Path
from unittest.mock import patch
import pypdfium2
from native_labels import project_record
BASE=Path(__file__).resolve().parent;PROJECT=BASE.parents[3]
def deny(*a,**kw):raise AssertionError('Forbidden network/image pixel operation')
class NativeLabelTests(unittest.TestCase):
 def row(self,n):return json.loads((BASE/f'attachment-{n}/records.jsonl').read_text().splitlines()[0])
 def project_actual(self,n):
  r=self.row(n);data=(PROJECT/r['raw_ref']).read_bytes()
  import hashlib
  self.assertEqual(hashlib.sha256(data).hexdigest(),r['raw_sha256'])
  with patch.object(socket.socket,'connect',deny),patch.object(pypdfium2.PdfPage,'render',deny),patch.object(pypdfium2.PdfPage,'get_objects',deny),patch.object(pypdfium2.PdfImage,'extract',deny),patch.object(pypdfium2.PdfImage,'get_bitmap',deny):
   d=pypdfium2.PdfDocument(data);p=d[0];t=p.get_textpage()
   try:result=project_record(r,t)
   finally:t.close();p.close();d.close()
  return result
 def test_actual_parcel_labels_full_and_geometry_owned(self):
  r=self.project_actual(1);self.assertIn('35202.2115',r['text']);self.assertTrue(r['requested_scope_qualification']['attachment_text_normalization_qualified']);self.assertEqual(2090,len(r['native_label_glyph_geometry']));self.assertFalse(r['text_serialization']['inferred_map_reading_order'])
 def test_actual_overprinted_map_preserved_but_not_waived(self):
  r=self.project_actual(2);self.assertIn('Havana St',r['text']);self.assertIn('Broadway Ave',r['text']);self.assertEqual(5529,len(r['native_label_glyph_geometry']));self.assertTrue(r['requested_scope_qualification']['native_label_projection_complete']);self.assertFalse(r['requested_scope_qualification']['attachment_text_normalization_qualified']);self.assertIsNotNone(r['requested_scope_qualification']['remaining_native_text_qualification_gap'])
 def test_source_proven_no_glyph_is_image_policy_na(self):
  for n in (3,4):
   r=project_record(self.row(n));self.assertEqual('[IMAGE]',r['text']);self.assertTrue(r['requested_scope_qualification']['source_proven_no_glyph_text_NA']);self.assertTrue(r['requested_scope_qualification']['attachment_text_normalization_qualified'])
 def test_false_no_glyph_exemption_rejected(self):
  r=self.row(3);r['pdfium_stream_text']='Legal caption'
  with self.assertRaises(ValueError):project_record(r)
 def test_no_ordinary_border_promoted_to_vector_map(self):
  r=self.row(3);r['source_url']='https://example.invalid/schedule.pdf';r['required_by']=[];r['pdf_qualification']['vector_curve_count']=4
  out=project_record(r);self.assertFalse(out['requested_scope_qualification']['source_graphic_map_qualification']['whole_map_graphic_placeholder_qualified'])
 def test_source_page_required_for_available_labels(self):
  with self.assertRaises(ValueError):project_record(self.row(1))
if __name__=='__main__':unittest.main()
