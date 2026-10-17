"""Faults for MIME/signature audit. Test bytes are synthetic, not source-law evidence."""
import json,tempfile,unittest
from pathlib import Path
from audit_images import audit
class Tests(unittest.TestCase):
 def test_image_signature_caught_under_opaque_name(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);(p/'body.bin').write_bytes(b'\x89PNG\r\n\x1a\nsynthetic');self.assertFalse(audit(p)['passed'])
 def test_image_mime_caught_without_known_signature(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);(p/'body.bin').write_bytes(b'unknown-format-image');(p/'checkpoint.json').write_text(json.dumps({'artifacts':[{'path':'body.bin','headers':{'content-type':'image/unknown'}}]}));self.assertFalse(audit(p)['passed'])
 def test_uuid_named_receipt_caught_without_known_signature(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);(p/'raw').mkdir();(p/'raw/payload.body').write_bytes(b'unknown-format-image');(p/'raw/7a340d92.json').write_text(json.dumps({'body_file':'raw/payload.body','headers':{'content-type':'image/unknown'}}));self.assertFalse(audit(p)['passed'])
 def test_zero_byte_image_header_only_and_embedded_native_original_allowed(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);(p/'head.bin').write_bytes(b'');(p/'head.receipt.json').write_text(json.dumps({'body_file':'head.bin','headers':{'content-type':'image/png'},'method':'HEAD'}));(p/'source.html').write_text('<html><img src="data:image/png;base64,AAAA"></html>');(p/'native.pdf').write_bytes(b'%PDF-synthetic embedded signature\x89PNG\r\n\x1a\n');self.assertTrue(audit(p)['passed'])
if __name__=='__main__':unittest.main(verbosity=2)
