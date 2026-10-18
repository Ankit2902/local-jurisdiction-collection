"""Source-provider nonimage document acceptance controls; no acquired nonPDF claim."""
import copy,importlib.util,json,socket,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent

def load(name,file):
 spec=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

class RequiredNonPdfAcceptance(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.out=Path(self.temp.name)
  tripwire=patch.object(socket,'socket',side_effect=AssertionError('No network'));tripwire.start();self.addCleanup(tripwire.stop)
  self.ops=load('candidate_nonpdf_ops','launcher-candidate.py');self.old=load('baseline_nonpdf_ops','launcher-baseline.py');self.provider=load('actual_ep_documents','encodeplus-documents.py')
  self.pub={'publisher':'encodeplus'}
 def coverage(self,entries):return {'publication_text_complete':True,'attachments_complete':True,'asset_document_integrity':entries}
 def accept(self,coverage,ops=None,pub=None):
  (self.out/'coverage.json').write_text(json.dumps(coverage));return (ops or self.ops).publication_acceptance(pub or self.pub,self.out)
 def test_actual_provider_integrity_only_response_does_not_establish_semantics(self):
  entries={}
  for ext,mime in [('docx','application/vnd.openxmlformats-officedocument.wordprocessingml.document'),('zip','application/zip')]:
   # Exact current provider is exercised with nonempty test bytes; it performs
   # no DOCX/archive parse. This is not an acquired publisher-document witness.
   url='https://example.test/required.'+ext;detail=self.provider.qualify_document(b'nonempty test bytes',url,mime)
   self.assertEqual(detail['format'],'non-PDF binary');self.assertIn('semantics unqualified',detail['qualification']);entries[url]=detail
  coverage=self.coverage(entries);before=self.accept(coverage,self.old);after=self.accept(coverage)
  self.assertTrue(before['publication_coverage_accepted']);self.assertFalse(after['publication_coverage_accepted']);self.assertFalse(after['legal_structure_qualified']);self.assertTrue(after['required_nonimage_documents_complete']);self.assertTrue(after['publication_text_complete']);self.assertEqual(after['pdf_structure_dimensions'],{});self.assertEqual(len(after['nonpdf_document_structure_dimensions']),4);self.assertTrue(all(v is None for v in after['nonpdf_document_structure_dimensions'].values()))
 def test_parent_flags_and_character_conservation_do_not_override_documents(self):
  c=self.coverage({'https://example.test/book.docx':{'format':'non-PDF binary','extractable_text_character_conservation_qualified':True}});c.update(document_text_completeness_qualified=True,document_structure_completeness_qualified=True)
  self.assertFalse(self.accept(c)['publication_coverage_accepted'])
 def test_each_generic_document_dimension_must_be_explicitly_true(self):
  keys=('document_text_completeness_qualified','document_structure_completeness_qualified');entries={url:{'format':'non-PDF binary',**{k:True for k in keys}} for url in ('https://example.test/a.docx','https://example.test/b.zip')};c=self.coverage(entries)
  self.assertTrue(self.accept(c)['publication_coverage_accepted']) # Schema control only.
  for url in entries:
   for key in keys:
    for value in (None,False,'true'):
     with self.subTest(url=url,key=key,value=value):
      bad=copy.deepcopy(c);bad['asset_document_integrity'][url][key]=value;result=self.accept(bad);self.assertFalse(result['publication_coverage_accepted']);self.assertTrue(result['required_nonimage_documents_complete'])
 def test_empty_asset_map_preserves_independent_html_acceptance(self):
  c=self.coverage({});result=self.accept(c);self.assertTrue(result['publication_coverage_accepted']);self.assertEqual(result['nonpdf_document_structure_dimensions'],{})
  old=self.accept(c,self.old);result.pop('nonpdf_document_structure_dimensions');self.assertEqual(old,result)
 def test_pdf_only_dimensions_remain_separate_and_conservative(self):
  c=self.coverage({'https://example.test/a.pdf':{'format':'PDF','pages':1}});result=self.accept(c);old=self.accept(c,self.old);self.assertEqual(result['nonpdf_document_structure_dimensions'],{});result.pop('nonpdf_document_structure_dimensions');self.assertEqual(old,result);self.assertFalse(result['publication_coverage_accepted'])
 def test_mixed_documents_cannot_hide_nonpdf_with_qualified_pdf(self):
  c=self.coverage({'https://example.test/a.pdf':{'format':'PDF','pdf_semantic_text_completeness_qualified':True,'pdf_table_completeness_qualified':True},'https://example.test/a.docx':{'format':'non-PDF binary'}})
  result=self.accept(c);self.assertTrue(all(v is True for v in result['pdf_structure_dimensions'].values()));self.assertFalse(result['legal_structure_qualified'])
 def test_family_aggregate_cannot_override_required_nonpdf(self):
  c=self.coverage({'https://example.test/a.docx':{'format':'non-PDF binary'}});c.update(publication_html_text_coverage_complete=True,publication_file_coverage_complete=True,legal_semantic_coverage_complete=True)
  self.assertFalse(self.accept(c,pub={'publisher':'official'})['publication_coverage_accepted'])

if __name__=='__main__':unittest.main(verbosity=2)
