"""Actual six-page fixture plus diagnostic mutations; no native semantic promotion."""
import copy,json,socket,unittest
from pathlib import Path
from unittest.mock import patch
from . import native_document,pdf_structure
HERE=Path(__file__).resolve().parent

class NativeDiagnosticAggregate(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=(HERE/'fixtures/overland-solid-waste-native.pdf').read_bytes();cls.cfg=json.loads((HERE/'configs/native-82-4b983dc51ab6.json').read_text());cls.rows,cls.initial_details=native_document.page_records(cls.data,cls.cfg)
 def setUp(self):
  guard=patch.object(socket,'socket',side_effect=AssertionError('No network'));guard.start();self.addCleanup(guard.stop)
 def details(self,rows):
  with patch.object(pdf_structure,'pages',return_value=(rows,[])):return native_document.page_records(self.data,self.cfg)[1]
 def test_actual_all_six_pages_keep_existing_positive_capture_dimensions(self):
  self.assertEqual(len(self.rows),6);self.assertTrue(self.details(self.rows)['pdf_extractable_text_reconciled']);self.assertFalse(self.details(self.rows)['pdf_table_semantics_complete']);self.assertTrue(all(r['pdf_qualification']['source_words_cover_deduplicated_glyph_characters'] and r['pdf_qualification']['undecoded_cid_literals']==[] for r in self.rows))
 def test_false_or_missing_glyph_conservation_cannot_hide_in_aggregate(self):
  for value in (False,None,'true'):
   rows=copy.deepcopy(self.rows);rows[0]['pdf_qualification']['source_words_cover_deduplicated_glyph_characters']=value;self.assertFalse(self.details(rows)['pdf_extractable_text_reconciled'])
  rows=copy.deepcopy(self.rows);rows[0]['pdf_qualification'].pop('source_words_cover_deduplicated_glyph_characters');self.assertFalse(self.details(rows)['pdf_extractable_text_reconciled'])
 def test_unresolved_or_missing_cid_diagnostic_cannot_hide_in_aggregate(self):
  for value in (['(cid:17)'],None,False):
   rows=copy.deepcopy(self.rows);rows[0]['pdf_qualification']['undecoded_cid_literals']=value;self.assertFalse(self.details(rows)['pdf_extractable_text_reconciled'])
  rows=copy.deepcopy(self.rows);rows[0]['pdf_qualification'].pop('undecoded_cid_literals');self.assertFalse(self.details(rows)['pdf_extractable_text_reconciled'])

if __name__=='__main__':unittest.main(verbosity=2)
