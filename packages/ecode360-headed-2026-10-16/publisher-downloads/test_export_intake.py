import json,tempfile,unittest
from unittest.mock import MagicMock,patch
from pathlib import Path
from export_intake import Rejected,inspect,parse_sample,sniff,validate_provenance,write_result

HTML=b'''<!doctype html><html><head><title>Fremont Municipal Code</title></head><body><h1>Chapter1</h1><h3 id="1.01">Definitions</h3><p>Access denied means a denial of permission. Authentication is a legal definition preserved verbatim here.</p><table><tr><th colspan="2">Officer</th></tr><tr><td>A</td><td>Finance</td></tr></table></body></html>'''
def provenance(**updates):
 p={'source_url':'https://example.gov/export.html','jurisdiction':'Example','publication':'Municipal Code','selection_scope':'Chapter1','retrieved_at':'2026-10-15T12:00:00Z','artifact_kind':'publisher-export','acquisition_mode':'operator-browser-download','edition_evidence':'Publisher page notice captured separately'};p.update(updates);return p
class IntakeTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.file=self.root/'input.html';self.file.write_bytes(HTML)
 def tearDown(self):self.tmp.cleanup()
 def test_signature_beats_extension(self):
  self.file=self.root/'pretend.pdf';self.file.write_bytes(HTML)
  with self.assertRaisesRegex(Rejected,'format mismatch'):inspect(self.file,provenance(),expected_format='pdf')
 def test_reject_challenge_disguised_as_export(self):
  self.file.write_text('<html><title>Just a moment...</title><body>'+('security verification '*30)+'</body></html>')
  with self.assertRaisesRegex(Rejected,'challenge'):inspect(self.file,provenance())
 def test_reject_login_form(self):
  self.file.write_text('<html><title>Code</title><form><input type="password"></form><p>'+('x'*100)+'</p></html>')
  with self.assertRaisesRegex(Rejected,'authentication'):inspect(self.file,provenance())
 def test_legal_definitions_not_removed(self):
  r=inspect(self.file,provenance(),expect=['Access denied means','Authentication is a legal definition'])
  self.assertIn('Definitions',r['sample']['text']);self.assertEqual(r['legal_semantic_status'],'MANUAL_REVIEW_REQUIRED')
 def test_preserve_table_cells_and_spans(self):
  r=inspect(self.file,provenance());self.assertEqual(r['sample']['tables'][0]['rows'][0][0]['colspan'],'2');self.assertEqual(r['sample']['tables'][0]['rows'][1][1]['text'],'Finance');self.assertIn('<table>',r['sample']['tables'][0]['html'])
 def test_wrong_hash_and_missing_sample_fail(self):
  with self.assertRaisesRegex(Rejected,'SHA256 mismatch'):inspect(self.file,provenance(),expected_sha='0'*64)
  with self.assertRaisesRegex(Rejected,'sample absent'):inspect(self.file,provenance(),expect=['Different city'])
 def test_no_implicit_whole_code_or_standalone(self):
  r=inspect(self.file,provenance(artifact_kind='browser-print'))
  self.assertEqual(r['scope_completeness_status'],'NOT_PROVEN');self.assertFalse(r['browser_print_is_publisher_export']);self.assertEqual(r['provenance_claim']['acquisition_mode'],'operator-browser-download')
 def test_required_provenance_and_url_security(self):
  for bad in ({'source_url':'https://user:password@example.gov/x'},{'source_url':'http://example.gov/x'},{'retrieved_at':'2026-10-15'},{'edition_evidence':''},{'artifact_kind':'complete-auto-export'}):
   with self.subTest(bad=bad),self.assertRaises(Rejected):validate_provenance(provenance(**bad))
 def test_no_overwrite(self):
  out=self.root/'verified';write_result(self.file,provenance(),out)
  with self.assertRaisesRegex(Rejected,'never overwritten'):write_result(self.file,provenance(),out)
 def test_rtf_remains_explicit_manual_gate(self):
  r=parse_sample(b'{\\rtf1 ANSI Sample}', 'rtf');self.assertEqual(r['text'],'');self.assertIn('no semantic parser',r['review_gates'][0])
 def test_reject_empty_binary_and_tiny_error(self):
  for data in (b'',b'\xff\xfe',b'Not found'):
   self.file.write_bytes(data)
   with self.subTest(data=data),self.assertRaises(Rejected):inspect(self.file,provenance())
 def test_actual_pdf_doc_page_sample(self):
  p=Path(__file__).parent/'evidence/docs/user-level-chart-2020.pdf'
  self.assertTrue(p.exists(),'retained documentation PDF required')
  r=inspect(p,provenance(selection_scope='Publisher feature chart, not legal code'),expected_format='pdf',pages=[1],expect=['Download','PDF'])
  self.assertEqual(r['sample']['sampled_pages'],[1]);self.assertEqual(r['scope_completeness_status'],'NOT_PROVEN')
 def test_sparse_pdf_is_acquisition_only_review(self):
  self.file.write_bytes(b'%PDF-1.7 mocked scanned receipt')
  page=MagicMock();page.extract_text.return_value='';page.extract_words.return_value=[];page.images=[{'name':'scan'}];page.width=612;page.height=792
  with patch('pdfplumber.open') as opened:
   opened.return_value.__enter__.return_value.pages=[page]
   r=inspect(self.file,provenance())
  self.assertEqual(r['integrity_status'],'PASS');self.assertEqual(r['sample_status'],'REVIEW_REQUIRED');self.assertEqual(r['sample']['text_extraction_status'],'REVIEW_REQUIRED');self.assertIn('OCR',r['sample']['review_gates'][0])
 def test_no_marker_is_not_text_qualification(self):
  r=inspect(self.file,provenance())
  self.assertEqual(r['text_expectation_status'],'UNSPECIFIED');self.assertEqual(r['sample_status'],'REVIEW_REQUIRED');self.assertEqual(r['method_e2e_status'],'NOT_QUALIFIED_BY_FILE_INTAKE_ALONE')
 def test_corrupt_pdf_rejected(self):
  self.file.write_bytes(b'%PDF-1.7 corrupt')
  with self.assertRaisesRegex(Rejected,'pdf parsing failed'):inspect(self.file,provenance())
 def test_pdf_page_out_of_range(self):
  p=Path(__file__).parent/'evidence/docs/user-level-chart-2020.pdf'
  with self.assertRaisesRegex(Rejected,'outside document'):inspect(p,provenance(),pages=[999])
if __name__=='__main__':unittest.main()
