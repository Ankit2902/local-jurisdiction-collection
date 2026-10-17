"""Hash-retained actual bounded publisher files; no live acquisition or corpus claim."""
import tempfile,unittest
from pathlib import Path
from collectors.ecode.operator import inspect_download
from collectors.ecode.common import QualificationError

FIXTURES=Path(__file__).resolve().parents[1]/'fixtures/readiness-native'
class NativeFixtureTests(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
 def tearDown(self):self.temp.cleanup()
 def test_actual_albany_pdf_matches_city_and_section(self):
  p=FIXTURES/'albany';r=inspect_download(p/'publisher-export-0.pdf',p/'source.html','https://ecode360.com/7678220',self.root/'pdf',terms=['When effective'])
  self.assertTrue(r['native_file_qualified']);self.assertFalse(r['complete']);self.assertEqual(r['qualification']['pages'],1);self.assertEqual(r['qualification']['identity_terms'],['City of Albany, NY','When effective'])
 def test_actual_eugene_html_all_eight_bodies_match_source(self):
  p=FIXTURES/'eugene';r=inspect_download(p/'publisher-export-0.html',p/'source.html','https://eugene.municipal.codes/EC/1',self.root/'html',publication='EC')
  self.assertFalse(r['complete']);self.assertEqual(r['qualification']['owned_content_nodes'],8);self.assertEqual(len(r['qualification']['source_body_matches']),8);self.assertEqual(r['qualification']['source_bodies_not_independently_witnessed'],[])
 def test_native_scope_and_operative_text_mismatch_fail(self):
  p=FIXTURES/'albany'
  with self.assertRaises(QualificationError):inspect_download(p/'publisher-export-0.pdf',p/'source.html','https://ecode360.com/7678220',self.root/'wrong-scope',terms=['Definitions and Rules'])
  with self.assertRaises(QualificationError):inspect_download(p/'publisher-export-0.pdf',p/'source.html','https://ecode360.com/7678221',self.root/'wrong-node',terms=['When effective'])
  p=FIXTURES/'eugene';raw=(p/'publisher-export-0.html').read_bytes();self.assertIn(b'Eugene, Oregon.',raw);bad=self.root/'modified.html';bad.write_bytes(raw.replace(b'Eugene, Oregon.',b'Another City, Oregon.'))
  with self.assertRaisesRegex(QualificationError,'legal body disagrees'):inspect_download(bad,p/'source.html','https://eugene.municipal.codes/EC/1',self.root/'wrong-body',publication='EC')

if __name__=='__main__':unittest.main()
