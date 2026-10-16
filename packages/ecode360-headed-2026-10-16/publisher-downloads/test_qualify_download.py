import json,tempfile,unittest
from pathlib import Path
from qualify_download import digest,qualify
from export_intake import Rejected
class ReceiptQualificationTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.raw=self.root/'actual.html';self.raw.write_text('<html><title>Example Municipal Code</title><body><h1>Example Municipal Code</h1><h2>1.01.010 Adoption.</h2><p>This synthetic offline test provision describes adoption and retains all substantive language in the test fixture.</p><footer>Code current through2026-01-01</footer></body></html>');self.upstream=self.root/'upstream.json';self.upstream.write_text('{"fixture":true,"not_live":true}');self.script=self.root/'executed.py';self.script.write_text('# synthetic executed-script fixture, no network\n');self.receipt=self.root/'canonical.json'
  self.claim={'source_url':'https://example.gov/code','jurisdiction':'Example','publication':'Municipal Code','selection_scope':'section1.01.010','retrieved_at':'2026-10-16T03:00:00Z','artifact_kind':'publisher-export','acquisition_mode':'unattended-standalone','edition_evidence':'synthetic fixture only','artifact_sha256':digest(self.raw),'artifact_bytes':self.raw.stat().st_size,'upstream_receipt_path':'upstream.json','upstream_receipt_sha256':digest(self.upstream),'acquisition_script_path':'executed.py','acquisition_script_sha256':digest(self.script),'download_status':'acquired','selected_citations':['1.01.010'],'format':'html','currentness_check':{'expected_export_text':'Code current through2026-01-01'}}
 def tearDown(self):self.tmp.cleanup()
 def run_claim(self,**updates):
  self.claim.update(updates);self.receipt.write_text(json.dumps(self.claim));return qualify(self.raw,self.receipt,self.root/'output')
 def test_actual_file_receipt_links_and_text(self):
  r=self.run_claim();self.assertEqual(r['classification'],'PASS_BOUNDED_DOWNLOADED_FILE_CHECKS');self.assertFalse(r['whole_publication_complete']);self.assertEqual(r['legal_semantic_status'],'MANUAL_REVIEW_REQUIRED')
 def test_button_and_login_are_not_download(self):
  for status in ['button_visible','login_required','not_tested']:
   with self.subTest(status=status),self.assertRaisesRegex(Rejected,'actual acquired'):self.run_claim(download_status=status)
 def test_browser_print_never_publisher_download(self):
  with self.assertRaisesRegex(Rejected,'publisher-generated'):self.run_claim(artifact_kind='browser-print')
 def test_citation_city_and_edition_text_required(self):
  for update in [{'selected_citations':[]},{'selected_citations':['9.99.999']},{'jurisdiction':'Other City'},{'currentness_check':{'expected_export_text':'Wrong edition'}}]:
   with self.subTest(update=update),self.assertRaises(Rejected):self.run_claim(**update)
   self.claim.update(selected_citations=['1.01.010'],jurisdiction='Example',currentness_check={'expected_export_text':'Code current through2026-01-01'})
 def test_raw_hash_and_length_match_receipt(self):
  with self.assertRaisesRegex(Rejected,'byte length'):self.run_claim(artifact_bytes=1)
  self.claim['artifact_bytes']=self.raw.stat().st_size
  with self.assertRaisesRegex(Rejected,'download SHA256'):self.run_claim(artifact_sha256='0'*64)
 def test_upstream_receipt_hash_verified(self):
  with self.assertRaisesRegex(Rejected,'upstream acquisition receipt'):self.run_claim(upstream_receipt_sha256='0'*64)
 def test_executed_script_hash_verified(self):
  with self.assertRaisesRegex(Rejected,'executed acquisition script'):self.run_claim(acquisition_script_sha256='0'*64)
if __name__=='__main__':unittest.main()
