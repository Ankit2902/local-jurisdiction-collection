"""Actual native source fixture; no PDF/image parser is imported or invoked."""
import sys
sys.dont_write_bytecode=True
import copy,json,tempfile,shutil,unittest
from pathlib import Path
from unittest.mock import patch
from html.parser import HTMLParser
from common import load
import american_legal_attachment as attachment

class ActualAttachment(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);shutil.copytree(Path(__file__).with_name('fixtures')/'cleveland-frontage-printable-source',self.root,dirs_exist_ok=True)
  self.a=load(self.root/'asset.json');self.p=load(self.root/'page.json');self.owner=load(self.root/'owner.json');self.family=load(self.root/'family.json');self.req=load(self.root/'requests.json')
 def tearDown(self):self.temp.cleanup()
 def run_profile(self):return attachment.qualify(self.root,self.a,self.p,self.owner,self.family,self.req)
 def refused(self):
  with self.assertRaises((ValueError,KeyError,IndexError)):self.run_profile()
 def test_actual_complete_native_attachment_all_text_grid_note_images(self):
  with patch('socket.socket.connect',side_effect=AssertionError('network')) as n,patch('base64.b64decode',side_effect=AssertionError('image_decode')) as d:
   body,receipt,witness=self.run_profile();n.assert_not_called();d.assert_not_called()
  self.assertEqual(body.count('[IMAGE]'),9);self.assertEqual(body.count('<td '),18);self.assertEqual(body.count('<tr>'),9);self.assertEqual(witness['owned_nonwhitespace_glyph_count'],2201);self.assertEqual(witness['source_glyph_count'],2589);self.assertEqual(witness['source_row_labels'],['a.','b.','c.','d.','e.','f.','g.','h.']);self.assertEqual(body.count('Required Frontage Features'),1);self.assertEqual(body.count('(Ord. No.'),1);self.assertNotIn('<img',body);self.assertNotIn('src=',body)
 def test_not_any_single_pdf_page(self):self.a['sha256']='0'*64;self.refused()
 def test_wrong_source_owner_refuses(self):self.owner['document_id']='other';self.refused()
 def test_wrong_referring_provision_heading_refuses(self):self.owner['heading']='§ 348.03 Different';self.refused()
 def test_missing_owned_source_link_refuses(self):self.owner['assets']=[];self.refused()
 def test_wrong_edition_publication_refuses(self):self.family['publication_identity']['code_uuid']='other';self.refused()
 def test_native_bytes_corrupt_refuses(self):(self.root/self.a['file']).write_bytes(b'corrupt');self.refused()
 def test_missing_declared_page_refuses(self):self.a['normalized_pdf_page_ids']=[];self.refused()
 def test_wrong_declared_native_page_count_refuses(self):self.a['validation']['pages']=2;self.refused()
 def test_missing_native_binary_receipt_refuses(self):self.req={};self.refused()
 def test_wrong_native_binary_receipt_timestamp_not_synthesized(self):
  body,r,w=self.run_profile();self.assertEqual(r['retrieved_at'],'2026-10-17T21:35:23.972934+00:00')
 def test_false_whole_source_qualification_refuses(self):self.family['pdf_semantic_text_completeness_qualified']=False;self.refused()
 def test_unqualified_cell_border_refuses(self):self.p['source_qualification']['cells'][7]['closed_original_border']=False;self.refused()
 def test_missing_middle_table_row_refuses(self):self.p['layout']['table_candidates'][0]['cells'].pop(4);self.refused()
 def test_swapped_table_rows_refuse(self):self.p['layout']['table_candidates'][0]['cells'][3:5]=reversed(self.p['layout']['table_candidates'][0]['cells'][3:5]);self.refused()
 def test_cell_text_loss_refuses(self):self.p['layout']['table_candidates'][0]['cells'][2][0]['text']=self.p['layout']['table_candidates'][0]['cells'][2][0]['text'][:-4];self.refused()
 def test_cell_span_mutation_refuses(self):self.p['layout']['table_candidates'][0]['cells'][2][0]['rowspan']=2;self.refused()
 def test_native_glyph_mutation_refuses(self):self.p['native_source_evidence']['glyphs'][18]['text']='x';self.refused()
 def test_native_glyph_geometry_unowned_refuses(self):self.p['native_source_evidence']['glyphs'][18]['x']=999;self.refused()
 def test_missing_image_placeholder_refuses(self):self.p['layout']['table_candidates'][0]['cells'][2][1]['text']='';self.refused()
 def test_wrong_image_cell_owner_refuses(self):self.p['source_qualification']['image_cell_owners'][2]['cell_indices']=[4];self.refused()
 def test_missing_ordinance_note_refuses(self):self.p['layout']['text_blocks'].pop();self.refused()
 def test_source_typo_or_truncation_not_silently_corrected(self):
  body,_,_=self.run_profile();self.assertIn('set bach from',body);self.assertIn('of-way tine',body);self.assertIn('The deep front yard setback</td>',body)
 def test_no_third_party_parser_dependency(self):
  import ast
  tree=ast.parse(Path(attachment.__file__).read_text());imports=[n.module.split('.')[0] for n in ast.walk(tree) if isinstance(n,ast.ImportFrom) and n.module]+[a.name.split('.')[0] for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names];self.assertFalse(set(imports)&{'bs4','fitz','pymupdf','pypdf','pdfminer','PIL','playwright'})
if __name__=='__main__':unittest.main()
