import json,unittest,hashlib
from unittest.mock import patch
from bs4 import BeautifulSoup
from .model import replace_images
class ImageContextScheme(unittest.TestCase):
 def test_known_image_data_addresses_hash_payload_for_either_scheme_case(self):
  for scheme in ['data:','DATA:']:
   value=scheme+'application/octet-stream;base64,CONTEXT_PIXEL_SENTINEL';body=BeautifulSoup('<div>Before<img src="'+value+'"/>after caption.</div>','html.parser')
   with patch('socket.socket',side_effect=AssertionError('No requests')),patch('base64.b64decode',side_effect=AssertionError('No image decoding')):metadata=replace_images(body,'https://example.invalid/')
   self.assertEqual(body.get_text(),'Before[IMAGE]after caption.');self.assertEqual(len(metadata),1);self.assertIsNone(metadata[0]['url']);self.assertEqual(metadata[0]['inline_data_sha256'],hashlib.sha256(value.encode()).hexdigest());self.assertNotIn('CONTEXT_PIXEL_SENTINEL',json.dumps(metadata));self.assertNotIn('application/octet-stream',str(body))
if __name__=='__main__':unittest.main()
