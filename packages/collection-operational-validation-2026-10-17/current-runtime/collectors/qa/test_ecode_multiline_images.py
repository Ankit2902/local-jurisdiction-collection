"""Synthetic regression for bounded image data in nonvisual source attributes."""
import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from collectors.ecode.adapters import normalized_images


class EcodeMultilineImages(unittest.TestCase):
    def test_complete_attribute_payload_omitted_without_losing_visible_text(self):
        payload = 'prefix DATA:IMAGE/PNG;base64,QUJD\nQ09OVElOVUFUSU9OX1BJWEVMUw=='
        source = '<p id="rule-12" data-image-metadata="' + payload + '">Required caption and legal text.</p>'
        result = normalized_images(source)
        self.assertEqual(result.p['id'], 'rule-12')
        self.assertEqual(result.p.get_text(), 'Required caption and legal text.')
        self.assertEqual(result.p['data-image-metadata'], '[IMAGE] image-data-sha256:' + hashlib.sha256(payload.encode()).hexdigest())
        self.assertNotIn('Q09OVElOVUFUSU9OX1BJWEVMUw==', str(result))
        self.assertNotIn('data:image/', str(result).lower())

    def test_multivalue_attribute_omits_every_payload_fragment(self):
        result = normalized_images('<p class="ordinary data:image/png;base64,QUJD Q09OVElOVUFUSU9O">Legal rule.</p>')
        self.assertNotIn('Q09OVElOVUFUSU9O', str(result))
        self.assertEqual(result.p.get_text(), 'Legal rule.')


if __name__ == '__main__':
    unittest.main(verbosity=2)
