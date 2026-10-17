#!/usr/bin/env python3
"""Independent coordinate fixtures and actual source-PDF table checks; no pixels/network."""
import io,pathlib,sys,unittest
sys.dont_write_bytecode=True
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject
import pdf_structure
BASE=pathlib.Path(__file__).resolve().parent
ITEM={'id':'fixture','url':'https://fixture.invalid/qualified.pdf','heading':'Controlled PDF','raw_ref':'fixture.pdf'}
CONFIG={'publication':'Controlled fixture','jurisdiction':'Fixture','state':'ZZ'}
def native(commands):
 writer=PdfWriter();page=writer.add_blank_page(width=600,height=800);font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')});page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})});stream=DecodedStreamObject();stream.set_data(commands.encode());page[NameObject('/Contents')]=writer._add_object(stream);out=io.BytesIO();writer.write(out);return out.getvalue()
def text(x,y,t):return 'BT /F1 12 Tf '+str(x)+' '+str(y)+' Td ('+t+') Tj ET\n'
class Structure(unittest.TestCase):
 def test_real_source_all_pages_and_independent_actual_table_cells(self):
  rows,_=pdf_structure.pages((BASE/'fixtures/portland-33-10.pdf').read_bytes(),ITEM,CONFIG);self.assertEqual(len(rows),4)
  self.assertTrue(all(r['pdf_qualification']['source_word_ownership_complete'] and r['pdf_qualification']['normalized_source_word_characters_agree'] and r['pdf_qualification']['independent_text_engine_characters_agree'] for r in rows));self.assertEqual(rows[2]['pdf_qualification']['detected_table_cells'],16);self.assertEqual(rows[2]['pdf_qualification']['independent_table_cells_agree'],16)
  fixes=rows[0]['pdf_qualification']['invalid_decoder_glyph_resolutions'];self.assertEqual([x['pdfminer_unicode']for x in fixes],['-','-']);self.assertFalse(rows[0]['pdf_qualification']['raw_independent_text_engine_characters_agree']);self.assertTrue(all(r['semantic_review_required'] for r in rows))
 def test_controlled_two_column_reading_order(self):
  body=''.join(text(40,750-i*18,'LEFT row'+chr(97+i)) + text(340,750-i*18,'RIGHT row'+chr(97+i)) for i in range(25));rows,_=pdf_structure.pages(native(body),ITEM,CONFIG);row=rows[0];self.assertIsNotNone(row['ordering']['gutter']);self.assertLess(row['text'].index('LEFT rowy'),row['text'].index('RIGHT rowa'));self.assertTrue(row['pdf_qualification']['source_word_ownership_complete']);self.assertTrue(row['pdf_qualification']['normalized_source_word_characters_agree'])
 def test_controlled_merged_table_geometry_and_cell_text(self):
  body='0.5 w\n'+''.join('40 '+str(y)+' m 340 '+str(y)+' l S\n' for y in [700,670,640,610])+''.join(str(x)+' 610 m '+str(x)+' 700 l S\n' for x in [40,240,340])+'140 610 m 140 670 l S\n'
  body+=text(55,680,'MERGED')+text(255,680,'C')+''.join(text(x,650-i*30,t)for i,row in enumerate([['A1','B1','C1'],['A2','B2','C2']])for x,t in zip([55,155,255],row));rows,_=pdf_structure.pages(native(body),ITEM,CONFIG);table=rows[0]['tables'][0];self.assertEqual(len(table['cells']),8);self.assertEqual(next(c for c in table['cells']if c['text']=='MERGED')['colspan'],2);self.assertTrue(all(c['independent_character_agreement'] for c in table['cells']));self.assertTrue(rows[0]['pdf_qualification']['source_word_ownership_complete'])
 def test_blank_vector_figure_placeholder_without_text_claim(self):
  rows,_=pdf_structure.pages(native('20 20 m 200 200 l 200 20 l h S\n'),ITEM,CONFIG);self.assertEqual(rows[0]['text'],'[IMAGE]');self.assertIn('image_only_or_no_extractable_legal_text',rows[0]['pdf_qualification']['review_conditions']);self.assertTrue(rows[0]['semantic_review_required'])
 def test_truncated_native_envelope_rejected(self):
  with self.assertRaises(ValueError):pdf_structure.pages(native(text(40,700,'Legal provision'))[:100],ITEM,CONFIG)
if __name__=='__main__':unittest.main(verbosity=2)
