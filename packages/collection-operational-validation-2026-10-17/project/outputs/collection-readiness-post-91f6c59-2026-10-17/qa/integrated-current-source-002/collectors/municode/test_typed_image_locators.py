"""Known typed image locator bytes are never normalized metadata; raw source stays intact."""
import sys;sys.dont_write_bytecode=True
import hashlib,json,tempfile,unittest
from pathlib import Path
from image_policy import sanitize,safe_metadata
from model import reconcile_publication,references
from verify import verify
from test_faults import run_fixture,replace_unit,save,FakeBrowser
BASE='https://library.municode.com/zz/fixture/codes/test_publication'
PAYLOAD='SU1BR0VfQllURVM='
URI='data:application/octet-stream;base64,'+PAYLOAD
class TypedImageLocators(unittest.TestCase):
 def test_actual_sanitizer_typed_locator_payloads_omitted_and_hashed(self):
  cases=[('<img src="'+URI+'" alt="Available caption" data-label="ordinary metadata">',URI),('<img srcset="'+URI+' 1x" alt="Caption">',URI+' 1x'),('<object type="image/png" data="'+URI+'"></object>',URI),('<a href="'+URI+'">Diagram label</a>',URI),('<image xlink:href="'+URI+'"/>',URI),('<div style="background:url('+URI+')">CSS legal caption</div>','url('+URI+')'),('<video poster="'+URI+'">Available fallback</video>',URI),('<table><tr><td background="'+URI+'">Cell caption</td></tr></table>',URI)]
  for markup,locator in cases:
   with self.subTest(markup=markup):
    clean,omissions=sanitize(markup,BASE,known=[URI]);encoded=json.dumps([clean,omissions]);self.assertIn('[IMAGE]',clean);self.assertNotIn(PAYLOAD,encoded);self.assertNotIn(URI,encoded);self.assertIn(hashlib.sha256(locator.encode()).hexdigest(),encoded)
  clean,meta=sanitize(cases[0][0],BASE);self.assertEqual(meta[0]['attributes']['alt'],'Available caption');self.assertEqual(meta[0]['attributes']['data-label'],'ordinary metadata')
 def test_ordinary_nonimage_metadata_and_reference_unchanged(self):
  doc='data:application/pdf;base64,UEZERg=='
  value={'label':'Legal prose data:application/json is a source notation.','document':doc,'nested':[{'text':'Available caption'}]};self.assertEqual(safe_metadata(value),value)
  r=references([{'node_id':'S1','html':'<a href="'+doc+'">Native document reference</a>'}],BASE);self.assertEqual(r[0]['source_value'],doc);self.assertNotEqual(r[0]['kind'],'image_omitted')
 def test_actual_reconcile_and_verify_payload_absent_raw_source_preserved(self):
  html='<p>Available legal caption.</p><img src="'+URI+'" alt="Alt caption"><img srcset="'+URI+' 1x"><div style="background:url('+URI+')">CSS caption</div><video poster="'+URI+'">Fallback caption</video><svg><image xlink:href="'+URI+'"/></svg>'
  with tempfile.TemporaryDirectory() as td:
   folder=Path(td)/'run';FakeBrowser.fail_after=None;cp=run_fixture(folder);replace_unit(folder,cp,'content-root:17',lambda a:[a[0],a[1],{**a[2],'Content':html}]);save(folder,cp);records,cov=reconcile_publication(folder,cp,17);encoded=json.dumps({'records':records,'coverage':cov});self.assertNotIn(PAYLOAD,encoded);self.assertIn('source_string_sha256',encoded);self.assertIn('Available legal caption.',records[-1]['text']);self.assertIn('CSS caption',records[-1]['text']);self.assertIn('Fallback caption',records[-1]['text']);self.assertTrue(verify(folder)['publication_complete'])
   entry=cp['units']['content-root:17'];receipt=json.loads((folder/entry['receipt']).read_text());self.assertIn(PAYLOAD,(folder/receipt['body_file']).read_text())
if __name__=='__main__':unittest.main()
