#!/usr/bin/env python3
"""Independent coordinate fixtures and actual source-PDF table checks; no pixels/network."""
import io,pathlib,sys,unittest,types
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
 def test_malformed_selfclosed_svg_cannot_consume_legal_pdf_prose(self):
  self.assertEqual(pdf_structure.redact_metadata('data:image/svg+xml,<svg/>'),'[IMAGE]')
  uri='data:image/svg+xml,<svg/> mandatory legal caption.</svg>'
  with self.assertRaisesRegex(ValueError,'Unqualified literal image-markup boundary'):pdf_structure.redact_metadata(uri)
  with self.assertRaisesRegex(ValueError,'Unqualified literal image-markup boundary'):pdf_structure.pages(native(text(40,700,uri)),ITEM,CONFIG)
  self.assertEqual(pdf_structure.redact_metadata({'uri':uri,'title':'Separate legal caption'}),{'uri':'[IMAGE]','title':'Separate legal caption'})
 def test_literal_svg_native_pdf_annotation_field_and_prose_guard(self):
  from pypdf import PdfReader
  from pypdf.generic import ArrayObject,FloatObject,TextStringObject
  uri='data:image/svg+xml,<svg><text>VECTOR_SENTINEL</text></svg>'
  for value in [uri,'  '+uri.upper()]:
   self.assertEqual(pdf_structure.redact_metadata({'uri':value,'caption':'Separate legal caption stays.'}),{'uri':'[IMAGE]','caption':'Separate legal caption stays.'});self.assertEqual(pdf_structure.redact_metadata(value),'[IMAGE]')
  with self.assertRaisesRegex(ValueError,'Unqualified literal image-markup boundary'):pdf_structure.redact_metadata('Before legal text "'+uri+'" after legal caption remains mandatory.')
  with self.assertRaisesRegex(ValueError,'Unqualified literal image-markup boundary'):pdf_structure.redact_metadata(uri+' mandatory legal caption.<svg></svg>')
  with self.assertRaisesRegex(ValueError,'Ambiguous unquoted image data URI'):pdf_structure.redact_metadata('data:image/png;base64,AAA Mandatory legal caption')
  writer=PdfWriter();writer.append(PdfReader(io.BytesIO(native(text(40,700,'Mandatory legal page caption remains.')))))
  annotation=DictionaryObject({NameObject('/Type'):NameObject('/Annot'),NameObject('/Subtype'):NameObject('/Link'),NameObject('/Rect'):ArrayObject([FloatObject(v)for v in [40,690,300,715]]),NameObject('/A'):DictionaryObject({NameObject('/S'):NameObject('/URI'),NameObject('/URI'):TextStringObject(uri)}),NameObject('/T'):TextStringObject('Separate annotation legal caption'),NameObject('/Contents'):TextStringObject(uri)})
  writer.pages[0][NameObject('/Annots')]=ArrayObject([writer._add_object(annotation)]);out=io.BytesIO();writer.write(out);rows,_=pdf_structure.pages(out.getvalue(),ITEM,CONFIG);encoded=__import__('json').dumps(rows)
  self.assertIn('Mandatory legal page caption remains.',rows[0]['text']);self.assertIn('Separate annotation legal caption',encoded);self.assertIn('[IMAGE]',encoded);self.assertNotIn('VECTOR_SENTINEL',encoded);self.assertNotIn('<svg',encoded.lower())
 def test_typed_pdf_annotation_uri_boundary_keeps_separate_legal_labels(self):
  result=pdf_structure.redact_metadata({'uri':'DATA:IMAGE/PNG;base64,AAA\nPIXEL_CONTINUATION','title':'Available legal caption','contents':'Available source label'});self.assertEqual(result,{'uri':'[IMAGE]','title':'Available legal caption','contents':'Available source label'})
 def test_wrapped_image_payload_in_pdf_annotation_metadata_is_fully_redacted(self):
  payload='DATA:IMAGE/png;base64,AAA\nCONTINUATION\r\nSECONDLINE\tTAIL999';value={'contents':'Label "'+payload+'" Suffix','nested':[{'uri':'"'+payload+'"'}],'title':'Available legal caption'};result=pdf_structure.redact_metadata(value);self.assertEqual(result['contents'],'Label "[IMAGE]" Suffix');self.assertEqual(result['nested'][0]['uri'],'"[IMAGE]"');self.assertEqual(result['title'],'Available legal caption');self.assertNotIn('CONTINUATION',__import__('json').dumps(result))
  with self.assertRaisesRegex(ValueError,'Ambiguous unquoted image data URI'):pdf_structure.redact_metadata({'contents':'Label '+payload+' Mandatory legal caption'})
 def test_actual_pdf_page_text_rejects_ambiguous_uri_caption_boundary(self):
  data=native(text(40,700,'Operative legal rule data:image/png;base64,AAA Mandatory legal caption'))
  with self.assertRaisesRegex(ValueError,'Ambiguous unquoted image data URI'):pdf_structure.pages(data,ITEM,CONFIG)
 def test_actual_native_image_cells_preserve_adjacent_legal_captions(self):
  rows,_=pdf_structure.pages((BASE/'fixtures/cleveland-native-grid.pdf').read_bytes(),ITEM,CONFIG);self.assertEqual(len(rows),1);cells=[c for t in rows[0]['tables'] for c in t['cells']];self.assertEqual(len(cells),18)
  imagecells=[c for c in cells if c.get('image_placeholder_ids')];self.assertEqual(len(imagecells),9);self.assertTrue(all(c['text']=='[IMAGE]' and c['content_ordering']['qualified'] and c['source_extractable_text']=='' for c in imagecells));self.assertEqual(next(c for c in cells if c['row']==0 and c['column']==0)['text'],'Required Frontage Features')
  self.assertTrue(next(c for c in cells if c['row']==1 and c['column']==0)['text'].startswith('a. Common Yard:'))
  self.assertEqual(sum(c['independent_character_agreement'] for c in cells),17);self.assertTrue(any('independent_cell_text_disagreement' in f for f in rows[0]['pdf_qualification']['review_conditions']))
 def test_missing_native_text_words_cannot_be_waived_as_image_policy(self):
  from unittest.mock import patch
  with patch('pdfplumber.page.Page.extract_words',return_value=[]):rows,_=pdf_structure.pages(native(text(40,700,'Actual legal words')),ITEM,CONFIG)
  q=rows[0]['pdf_qualification'];from verify import extractable_text_reconciled
  self.assertFalse(extractable_text_reconciled([q]));self.assertFalse(q['source_words_cover_deduplicated_glyph_characters']);self.assertEqual(q['text_glyph_comparison_applicability'],'applicable');self.assertIn('source_text_glyphs_present_but_word_extraction_empty',q['review_conditions'])
 def test_image_bbox_markers_owned_by_enclosing_cell_without_pixels(self):
  table={'cells':[{'bbox':[10,10,100,100],'text':'Caption','independent_character_agreement':True},{'bbox':[100,10,200,100],'text':''}]}
  images=[{'id':'native-image-1','bbox':[20,20,80,80],'text':'[IMAGE]','pixel_extraction':False},{'id':'page-background','bbox':[0,0,600,800],'text':'[IMAGE]','pixel_extraction':False}]
  pdf_structure.cell_image_markers([table],images);cell=table['cells'][0];self.assertEqual(cell['text'],'Caption\n[IMAGE]');self.assertEqual(cell['source_extractable_text'],'Caption');self.assertEqual(cell['image_placeholder_ids'],['native-image-1']);self.assertEqual(table['cells'][1]['text'],'');self.assertTrue(cell['independent_character_agreement']);self.assertFalse(cell['content_ordering']['qualified'])
 def test_cell_images_follow_disjoint_source_geometry_above_between_below(self):
  words=[{'id':'a','text':'Top caption','x0':10,'x1':90,'top':40,'bottom':50},{'id':'b','text':'Bottom caption','x0':10,'x1':90,'top':90,'bottom':100}]
  cell={'bbox':[0,0,110,150],'text':'Top caption\nBottom caption','independent_character_agreement':True}
  images=[{'id':'below','bbox':[10,120,90,140]},{'id':'above','bbox':[10,5,90,25]},{'id':'between','bbox':[10,60,90,80]}]
  pdf_structure.cell_image_markers([{'cells':[cell]}],images,words)
  self.assertTrue(cell['content_ordering']['qualified']);self.assertEqual(cell['text'],'[IMAGE]\nTop caption\n[IMAGE]\nBottom caption\n[IMAGE]');self.assertEqual([u.get('id') for u in cell['content_units'] if u['kind']=='image_placeholder'],['above','between','below']);self.assertEqual(cell['source_extractable_text'],'Top caption\nBottom caption');self.assertTrue(cell['independent_character_agreement'])
 def test_cell_image_overlapping_caption_remains_unordered(self):
  words=[{'id':'a','text':'Caption','x0':10,'x1':90,'top':40,'bottom':50}];cell={'bbox':[0,0,110,100],'text':'Caption'}
  pdf_structure.cell_image_markers([{'cells':[cell]}],[{'id':'overlap','bbox':[10,35,90,55]}],words)
  self.assertFalse(cell['content_ordering']['qualified']);self.assertIn('overlap',cell['content_ordering']['reason']);self.assertEqual(cell['source_extractable_text'],'Caption');self.assertIn('[IMAGE]',cell['text'])
 def test_cell_clipped_word_geometry_cannot_qualify_image_position(self):
  words=[{'id':'a','text':'Caption','x0':10,'x1':90,'top':40,'bottom':50}];cell={'bbox':[0,0,110,100],'text':'Cap'}
  pdf_structure.cell_image_markers([{'cells':[cell]}],[{'id':'above','bbox':[10,5,90,25]}],words)
  self.assertFalse(cell['content_ordering']['qualified']);self.assertIn('do not match',cell['content_ordering']['reason']);self.assertEqual(cell['source_extractable_text'],'Cap')
 def test_real_nested_region_does_not_duplicate_page_text(self):
  rows,_=pdf_structure.pages((BASE/'fixtures/arlington-fire-page8.pdf').read_bytes(),ITEM,CONFIG);row=rows[0];q=row['pdf_qualification']
  self.assertEqual(q['detected_table_cells'],22);self.assertEqual(q['independent_table_cells_agree'],22)
  self.assertTrue(q['source_word_ownership_complete']);self.assertTrue(q['normalized_source_word_characters_agree']);self.assertTrue(q['independent_text_engine_characters_agree'])
  self.assertEqual(sum(bool(t.get('page_text_disposition')) for t in row['tables']),1)
  self.assertEqual(len([b for b in row['ordered_blocks'] if b['kind']=='table']),1)
 def test_pdfdocencoded_odd_length_annotation_not_utf16_text_failure(self):
  class Page:
   page_obj=types.SimpleNamespace(annots=[{'Rect':[1,2,3,4],'A':{'URI':b'https://example.gov/fa\xe7ade'},'Contents':b'fa\xe7ade!','P':None}])
   @property
   def annots(self):raise UnicodeDecodeError('utf-16-le',b'x',0,1,'truncated data')
  links,proof=pdf_structure.annotation_links(Page());self.assertEqual(links[0]['contents'],'façade!');self.assertEqual(links[0]['uri'],'https://example.gov/façade');self.assertEqual(proof[0]['fields']['contents']['encoding'],'PDFDocEncoding (PDF string without BOM)')
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
  rows,_=pdf_structure.pages(native('20 20 m 200 200 l 200 20 l h S\n'),ITEM,CONFIG);self.assertEqual(rows[0]['text'],'[IMAGE]');self.assertEqual(rows[0]['pdf_qualification']['text_glyph_comparison_applicability'],'not_applicable_source_has_no_text_glyph_characters');self.assertNotIn('image_only_or_no_extractable_legal_text',rows[0]['pdf_qualification']['review_conditions']);self.assertTrue(rows[0]['semantic_review_required'])
 def test_truncated_native_envelope_rejected(self):
  with self.assertRaises(ValueError):pdf_structure.pages(native(text(40,700,'Legal provision'))[:100],ITEM,CONFIG)
if __name__=='__main__':unittest.main(verbosity=2)
