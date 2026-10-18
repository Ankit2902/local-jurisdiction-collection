"""Exact source-image opaque inline URI context, including scheme casing."""
import json,unittest
from unittest.mock import patch
from bs4 import BeautifulSoup
from collectors.encodeplus.model import replace_images

class KnownImageDataContext(unittest.TestCase):
 def test_typed_image_opaque_data_payload_never_survives_in_metadata(self):
  for scheme in ('data:','DATA:','DaTa:'):
   with self.subTest(scheme=scheme),patch('socket.socket.connect',side_effect=AssertionError('NO_NETWORK')):
    body=BeautifulSoup('<p>Legal before<img alt="Available caption" src="'+scheme+'application/octet-stream;base64,CONTEXT_PIXEL_SENTINEL">Legal after</p>','html.parser');refs=replace_images(body,'https://example.invalid/')
    self.assertEqual(body.get_text(),'Legal before[IMAGE]Legal after');self.assertEqual(len(refs),1)
    self.assertIsNone(refs[0]['url']);self.assertTrue(refs[0]['inline_data_sha256']);self.assertEqual(refs[0]['alt'],'Available caption');self.assertNotIn('CONTEXT_PIXEL_SENTINEL',json.dumps(refs))
if __name__=='__main__':unittest.main()
