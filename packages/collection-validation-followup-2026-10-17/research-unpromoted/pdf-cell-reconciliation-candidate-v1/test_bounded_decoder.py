"""Actual native hyphen fixture and source-proof fault tests; no image API."""
import sys
sys.dont_write_bytecode=True
import io,json,hashlib,unittest
from pathlib import Path
from unittest.mock import patch
import pdfplumber,pypdfium2
from bounded_decoder import bounded_decoder_aliases
import pdf_structure
BASE=Path(__file__).resolve().parent
URL='https://export.amlegal.com/media/32eb4da1492d2ce5e4435e569daed30a1af89a42/DATAOBJECTS/0-0-0-13294.pdf'
BBOX=[57.72,435.18,369.84,484.62]
class BoundedAliases(unittest.TestCase):
 def fixture(self):
  raw=(BASE/'fixtures/cleveland-native.pdf').read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),'eb1ea94cca6abefd0a8a6645c59cc2cfac5ce704adc4b76240b1ee0f3e858c7a')
  miner=pdfplumber.open(io.BytesIO(raw));doc=pypdfium2.PdfDocument(raw);page=miner.pages[0].dedupe_chars(tolerance=.5);native=doc[0];tp=native.get_textpage();text=tp.get_text_range();_,res=pdf_structure.invalid_decoder_resolutions(text,tp,page)
  bounded=tp.get_text_bounded(BBOX[0],page.height-BBOX[3],BBOX[2],page.height-BBOX[1])
  return raw,miner,doc,page,native,tp,text,res,bounded
 def test_actual_native_cell_retains_original_and_qualifies_exact_alias(self):
  raw=(BASE/'fixtures/cleveland-native.pdf').read_bytes()
  # Pixel/bitmap/object extraction APIs are forbidden even though the original
  # PDF legitimately contains nine images retained only as source/metadata.
  with patch.object(pypdfium2.PdfPage,'render',side_effect=AssertionError('RENDER')),patch.object(pypdfium2.PdfPage,'get_objects',side_effect=AssertionError('IMAGE OBJECT API')),patch.object(pypdfium2.PdfImage,'extract',side_effect=AssertionError('EXTRACT')),patch.object(pypdfium2.PdfImage,'get_bitmap',side_effect=AssertionError('PIXELS')):
   rows,_=pdf_structure.pages(raw,{'id':URL,'url':URL,'heading':'Native grid','raw_ref':'original-native.pdf'},{'publication':'Fixture native','jurisdiction':'Cleveland','state':'OH'})
  cells=rows[0]['tables'][0]['cells'];self.assertEqual(len(cells),18);self.assertTrue(all(c['independent_character_agreement'] for c in cells))
  cell=cells[16];self.assertIn('\x02',cell['independent_pdfium_text']);self.assertNotIn('\x02',cell['qualified_pdfium_text']);self.assertIn('right-\nof-way',cell['text']);self.assertIn('right-of-way',cell['qualified_pdfium_text'])
  proof=cell['bounded_decoder_alias_resolutions'];self.assertEqual(len(proof),1);self.assertTrue(proof[0]['native_is_hyphen']);self.assertEqual(proof[0]['pdfminer_unicode'],'-')
  self.assertEqual(rows[0]['image_placeholder_count'],9);self.assertEqual(sum(bool(c.get('image_placeholder_ids')) for c in cells),9)
  self.assertTrue(rows[0]['pdf_qualification']['source_word_ownership_complete']);self.assertTrue(rows[0]['pdf_qualification']['source_words_cover_deduplicated_glyph_characters']);self.assertTrue(rows[0]['semantic_review_required'])
 def test_no_alias_without_native_hyphen_flag(self):
  self.guard_failure('FPDFText_IsHyphen',0)
 def test_no_alias_for_other_native_control_or_unicode(self):
  self.guard_failure('FPDFText_GetUnicode',65)
 def test_no_alias_when_native_index_mapping_missing(self):
  self.guard_failure('FPDFText_GetCharIndexFromTextIndex',-1)
 def guard_failure(self,api,value):
  raw,miner,doc,page,native,tp,text,res,bounded=self.fixture()
  try:
   with patch.object(pypdfium2.raw,api,return_value=value):actual,proof=bounded_decoder_aliases(bounded,BBOX,res,tp,page,text)
   self.assertEqual(actual,bounded);self.assertEqual(proof,[])
  finally:tp.close();native.close();doc.close();miner.close()
 def test_no_alias_for_outside_cell_or_unaccounted_control(self):
  raw,miner,doc,page,native,tp,text,res,bounded=self.fixture()
  try:
   self.assertEqual(bounded_decoder_aliases(bounded,[57.72,435.18,350,484.62],res,tp,page,text),(bounded,[]))
   self.assertEqual(bounded_decoder_aliases(bounded+'\x02',BBOX,res,tp,page,text),(bounded+'\x02',[]))
  finally:tp.close();native.close();doc.close();miner.close()
if __name__=='__main__':unittest.main()
