"""Actual retained coverage and temporary-output acceptance tests; no network."""
import copy,importlib.util,json,socket,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent

def load(name,file):
 spec=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

class RequiredPdfAcceptance(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.out=Path(self.temp.name)
  tripwire=patch.object(socket,'socket',side_effect=AssertionError('No network'));tripwire.start();self.addCleanup(tripwire.stop)
  self.ops=load('candidate_ops','launcher-candidate.py');self.old=load('baseline_ops','launcher-baseline.py')
  self.actual=json.loads((HERE/'fixtures/overland-coverage.json').read_text());self.pub={'publisher':'encodeplus','source_url':'https://codes.opkansas.org/municipal-code/'}
 def accept(self,coverage,ops=None,pub=None):
  (self.out/'coverage.json').write_text(json.dumps(coverage));return (ops or self.ops).publication_acceptance(pub or self.pub,self.out)
 def test_actual_five_pdf_false_acceptance_reproduced_then_refused(self):
  self.assertEqual(len(self.actual['asset_document_integrity']),5);self.assertEqual(sum(d['pages'] for d in self.actual['asset_document_integrity'].values()),636)
  old=self.accept(self.actual,self.old);new=self.accept(self.actual)
  self.assertTrue(old['publication_coverage_accepted']);self.assertTrue(old['legal_structure_qualified']);self.assertEqual(old['pdf_structure_dimensions'],{})
  self.assertFalse(new['publication_coverage_accepted']);self.assertFalse(new['legal_structure_qualified']);self.assertTrue(new['required_nonimage_documents_complete']);self.assertTrue(new['publication_text_complete']);self.assertEqual(len(new['pdf_structure_dimensions']),10);self.assertTrue(all(v is None for v in new['pdf_structure_dimensions'].values()))
 def test_parent_aggregate_true_does_not_qualify_missing_document_dimensions(self):
  coverage=copy.deepcopy(self.actual);coverage.update(pdf_semantic_text_completeness_qualified=True,pdf_table_completeness_qualified=True)
  self.assertFalse(self.accept(coverage)['legal_structure_qualified'])
 def test_each_required_document_dimension_must_be_explicitly_true(self):
  coverage=copy.deepcopy(self.actual);keys=('pdf_semantic_text_completeness_qualified','pdf_table_completeness_qualified')
  for detail in coverage['asset_document_integrity'].values():detail.update({k:True for k in keys})
  # This is a schema/boolean control, not a claim those real PDFs are qualified.
  self.assertTrue(self.accept(coverage)['legal_structure_qualified'])
  for url in coverage['asset_document_integrity']:
   for key in keys:
    for value in (None,False,'true'):
     with self.subTest(url=url,key=key,value=value):
      bad=copy.deepcopy(coverage);bad['asset_document_integrity'][url][key]=value;report=self.accept(bad);self.assertFalse(report['publication_coverage_accepted']);self.assertTrue(report['required_nonimage_documents_complete'])
 def test_no_asset_html_control_stays_accepted(self):
  c={'publication_text_complete':True,'attachments_complete':True,'asset_document_integrity':{}}
  self.assertEqual(self.accept(c),self.accept(c,self.old));self.assertTrue(self.accept(c)['publication_coverage_accepted'])
 def test_non_pdf_integrity_control_does_not_become_pdf(self):
  c={'publication_text_complete':True,'attachments_complete':True,'asset_document_integrity':{'https://example.test/appendix.zip':{'format':'ZIP','bytes':10,'qualification':'archive CRC checked'}}}
  self.assertEqual(self.accept(c),self.accept(c,self.old));self.assertTrue(self.accept(c)['publication_coverage_accepted'])
 def test_previous_numeric_pdf_and_no_pdf_controls_preserved(self):
  c={'publication_text_complete':True,'attachment_complete':True,'pdf_text_layer_pages_parsed':2,'pdf_retained_asset_document_count':1,'pdf_semantic_text_completeness_qualified':False,'pdf_table_completeness_qualified':False};pub={'publisher':'american-legal'}
  self.assertEqual(self.accept(c,pub=pub),self.accept(c,self.old,pub));self.assertFalse(self.accept(c,pub=pub)['legal_structure_qualified'])
  c.update(pdf_text_layer_pages_parsed=0,pdf_retained_asset_document_count=0);self.assertEqual(self.accept(c,pub=pub),self.accept(c,self.old,pub));self.assertTrue(self.accept(c,pub=pub)['legal_structure_qualified'])
 def test_actual_source_coverage_not_modified(self):
  before=(HERE/'fixtures/overland-coverage.json').read_bytes();self.accept(self.actual);self.assertEqual(before,(HERE/'fixtures/overland-coverage.json').read_bytes())

if __name__=='__main__':unittest.main(verbosity=2)
