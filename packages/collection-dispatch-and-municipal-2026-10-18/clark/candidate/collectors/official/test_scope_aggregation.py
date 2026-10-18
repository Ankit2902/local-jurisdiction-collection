"""Actual synthetic PDF overprint versus no-glyph image policy controls."""
import contextlib,io,pathlib,tempfile,unittest
from unittest.mock import patch
import collect,model,transport,verify
from test_pdf_structure import native,text
ROOT='https://scope-fixture.invalid/index';BODY='https://scope-fixture.invalid/code/1/all';PDF='https://scope-fixture.invalid/required.pdf'
class Scope(unittest.TestCase):
 def bundle(self,commands):
  root=pathlib.Path(self.temp.name);data=native(commands);config={'schema':1,'id':'scope-fixture','jurisdiction':'Fixture','state':'ZZ','publication':'Complete synthetic source publication','source_url':ROOT,'mode':'portland_titles','transport':'http','inventory_selector':'main a[href]','content_selector':'main','coverage_level':'publication_text','pdf_normalization':'coordinate-v1','native_label_attachment_rules':[{'url':PDF,'source_kind':'map','sha256':model.sha(data)}]};cf=root/'config.json';collect.save(cf,config)
  sources={ROOT:b'<main><a href="/code/1">Title 1 Complete publication</a></main>',BODY:b'<main><div class="node--embedded"><h3><a href="/code/1/01/010">1.01.010 Operative rule.</a></h3><div class="field--name-field-section-body">Every applicant shall comply with this operative legal requirement. Appendix map incorporated by reference <a href="/required.pdf">Required native source attachment</a>.</div></div></main>',PDF:data}
  def fake(url,max_bytes=0):
   raw=sources[url];return raw,{'url':url,'status':200,'headers':{},'sha256':model.sha(raw),'transport':'Controlled source/PDF fixture; no network'}
  out=root/'run'
  with patch.object(transport,'fetch',fake),contextlib.redirect_stdout(io.StringIO()):code=collect.collect(cf,out)
  return verify.verify(out),code,out
 def setUp(self):self.temp=tempfile.TemporaryDirectory()
 def tearDown(self):self.temp.cleanup()
 def test_actual_native_overprint_gap_requires_scope_review(self):
  phrase='Available native label';report,code,out=self.bundle(text(40,700,phrase)+text(40,700,phrase));q=report['native_attachment_outputs'][0]['qualification'];self.assertTrue(q['native_label_projection_complete']);self.assertFalse(q['attachment_text_normalization_qualified']);self.assertFalse(report['requested_coverage_complete']);self.assertFalse(report['legal_semantic_coverage_complete']);self.assertTrue(report['manual_review_required'])
 def test_source_proven_no_glyph_image_policy_is_not_failure(self):
  report,code,out=self.bundle('20 20 m 200 200 l 200 20 l h S\n');q=report['native_attachment_outputs'][0]['qualification'];self.assertEqual(q['source_proven_no_glyph_pages'],1);self.assertTrue(q['attachment_text_normalization_qualified']);self.assertTrue(report['requested_coverage_complete']);self.assertTrue(report['legal_semantic_coverage_complete']);self.assertFalse(report['manual_review_required']);self.assertEqual(code,0)
if __name__=='__main__':unittest.main(verbosity=2)
