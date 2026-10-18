import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from inert_browser_source import attach_inert_html
from playwright.sync_api import sync_playwright
class InertSource(unittest.TestCase):
 def test_image_forms_removed_before_attachment_without_resource_request(self):
  with sync_playwright() as pw:
   b=pw.chromium.launch(channel='chrome',headless=True);ctx=b.new_context(java_script_enabled=False);requests=[];ctx.route('**/*',lambda r:(requests.append(r.request.url),r.abort()));p=ctx.new_page()
   raw='''<html><head><title>NONLEGAL_HEAD_METADATA</title><style>.x{background:url(https://invalid.test/a)}</style></head><body><h1 id="legal">Heading</h1><table><tr><td background="DATA:IMAGE/PNG;base64,PIXELS">A<img src="data:image/png;base64,PIXELS"><table><tr><td><svg><image href="https://invalid.test/x"/></svg>B</td></tr></table>C</td></tr></table><picture><source srcset="https://invalid.test/a"><img src="https://invalid.test/b"></picture><object type="IMAGE/PNG" data="data:image/png;base64,PIXELS"></object><video poster="https://invalid.test/c">fallback</video><script>throw Error('executed')</script></body></html>'''
   result=attach_inert_html(p,raw);html=p.content();self.assertFalse(requests);self.assertNotIn('PIXELS',html);self.assertNotIn('NONLEGAL_HEAD_METADATA',p.locator('body').inner_text());self.assertNotIn('data:image',html.lower());self.assertEqual(p.locator('#legal').inner_text(),'Heading');self.assertEqual(p.locator('td').last.inner_text(),'[IMAGE]B');self.assertIn('[IMAGE]fallback',p.locator('body').inner_text());self.assertGreaterEqual(result['image_placeholders_inserted'],6);self.assertFalse(result['image_decoding_or_rendering']);b.close()
 def test_body_offsets_count_only_lf_with_publisher_control_characters(self):
  from inert_browser_source import body_markup
  for control in ('\x1c','\x1d','\x1e','\x1f','\x85','\u2028','\u2029'):
   with self.subTest(control=hex(ord(control))):
    body='<section><p>Earlier'+control+'legal text.</p>\n<p>ATTEST: mandatory final legal caption.</p></section>\n'
    raw='<html>\n<head><title>nonlegal metadata</title></head>\n<body>'+body+'</body>\n</html>'
    self.assertEqual(body_markup(raw),body)
if __name__=='__main__':unittest.main(verbosity=2)
