"""Synthetic source-context tripwires: no inline payload decoding or silent qualification."""
import base64,io,json,unittest
from unittest.mock import patch
from bs4 import BeautifulSoup
from pypdf import PdfWriter
import model
class InlineContext(unittest.TestCase):
 def parse(self,markup):
  with patch.object(base64,'b64decode',side_effect=AssertionError('decoder forbidden')) as decoder:
   result=model.semantics(BeautifulSoup(markup,'html.parser').find(),'https://fixture.invalid/code')
  decoder.assert_not_called()
  return result
 def test_known_image_context_before_any_claimed_mime_or_decoder(self):
  uri='DATA:application/octet-stream;base64,QUJD\nUElYRUxT'
  cases=['<p><img src="'+uri+'"></p>','<picture><source src="'+uri+'"></picture>','<svg><image href="'+uri+'"></image><use xlink:href="'+uri+'"></use></svg>','<video poster="'+uri+'">Caption</video>','<p background="'+uri+'">Caption</p>','<p style="background:url('+uri+')">Caption</p>','<object type="IMAGE/PNG" data="'+uri+'"></object>','<a type="IMAGE/PNG" href="'+uri+'">Image label</a>']
  for markup in cases:
   with self.subTest(markup=markup):
    r=self.parse(markup);dumped=json.dumps(r);self.assertNotIn('QUJD',dumped);self.assertNotIn('UElYRUxT',dumped);self.assertIn('[IMAGE]',r['text']);self.assertTrue(r['assets']);self.assertTrue(all(not a['required'] and a['status']=='policy_omitted_image'for a in r['assets']))
 def test_image_attributes_hash_only_with_legal_caption(self):
  uri='data:application/octet-stream;base64,QUJD\nUElYRUxT';r=self.parse('<p>Mandatory legal caption<img src="'+uri+'" alt="'+uri+'" title="Published map label"></p>');self.assertEqual(r['text'],'Mandatory legal caption[IMAGE]');self.assertEqual(r['assets'][0]['source_descriptive_attributes']['title'],'Published map label');self.assertNotIn('UElYRUxT',json.dumps(r));self.assertIn(model.sha(uri.encode()),json.dumps(r))
 def test_ordinary_legal_link_with_image_style_hashes_metadata(self):
  uri='data:application/octet-stream;base64,UNIQUE_PIXEL_SENTINEL';r=self.parse('<p><a href="/law" style="background:url('+uri+')">Mandatory caption</a></p>');self.assertNotIn('UNIQUE_PIXEL_SENTINEL',json.dumps(r));self.assertEqual(r['links'][0]['url'],'https://fixture.invalid/law');self.assertEqual(r['links'][0]['attributes']['style'],'[IMAGE]');self.assertIn('Mandatory caption',r['text'])
 def test_nonimage_inline_is_inert_unqualified_even_valid_pdf(self):
  b=io.BytesIO();w=PdfWriter();w.add_blank_page(width=72,height=72);w.write(b)
  for payload in [b'',b'%PDF-1.7\ntruncated',b.getvalue()]:
   uri='data:application/pdf;base64,'+base64.b64encode(payload).decode();r=self.parse('<div><iframe src="'+uri+'"></iframe><object data="'+uri+'">Mandatory label</object><a href="'+uri+'">PDF</a></div>');self.assertEqual(len(r['assets']),3);self.assertTrue(all(a['required'] and not a['format_qualified']and a['status']=='unqualified_inline_nonimage_document' for a in r['assets']));self.assertNotIn(uri,json.dumps(r));self.assertIn('Mandatory label',r['text']);self.assertIn('unqualified-inline-document-ref:sha256:',r['html'])
if __name__=='__main__':unittest.main(verbosity=2)
