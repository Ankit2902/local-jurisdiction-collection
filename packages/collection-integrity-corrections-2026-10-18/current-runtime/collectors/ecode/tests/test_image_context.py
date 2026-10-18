"""Known image context excludes opaque data even when its MIME label is wrong."""
import base64
import json
import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup
from collectors.ecode import adapters


class ImageContext(unittest.TestCase):
    def test_real_record_omits_opaque_image_payloads_without_decoding(self):
        payload = 'SU1BR0VfQllURVM='
        uri = 'data:application/octet-stream;base64,' + payload
        body = BeautifulSoup(
            '<div id="rule"><h3>Map rule</h3><p>Before and after.</p>'
            f'<img id="map" alt="Available caption" src="{uri}">'
            f'<picture><source src="{uri}"></picture>'
            f'<object type="image/png" data="{uri}"></object>'
            f'<video poster="{uri}">Video caption</video>'
            f'<table><tr><td style="background:url({uri})">Cell text</td></tr></table>'
            f'<a type="image/png" href="{uri}">Map reference</a></div>',
            'html.parser',
        ).div
        with patch.object(base64, 'b64decode', side_effect=AssertionError('Image decoded')) as decoder:
            record = adapters._record('501', 'Map rule', 'section', body, 'https://ecode360.com/501')
        decoder.assert_not_called()
        encoded = json.dumps(record)
        self.assertNotIn(payload, encoded)
        self.assertNotIn('data:application/octet-stream', encoded)
        self.assertIn('image-data-sha256:', encoded)
        self.assertEqual(record['id'], '501')
        self.assertIn('[IMAGE]', record['text'])
        self.assertIn('Cell text', record['text'])
        self.assertIn('Available caption', encoded)
        self.assertIn('Map reference', record['text'])
        self.assertTrue(record['assets'])
        self.assertTrue(all(a['image'] and not a['required'] for a in record['assets']))
        self.assertFalse(BeautifulSoup(record['content_html'], 'html.parser').select('img,picture,object'))

    def test_image_download_anchor_becomes_inert_but_keeps_caption_and_provenance(self):
        uri = 'https://ecode360.com/attachment/336787/example.png'
        body = BeautifulSoup(f'<div><a id="source-map" href="{uri}">Map caption</a></div>', 'html.parser').div
        record = adapters._record('33432619', 'Maps', 'section', body, 'https://ecode360.com/33432619')
        anchor = BeautifulSoup(record['content_html'], 'html.parser').a
        self.assertEqual(anchor['href'], '#image-omitted')
        self.assertEqual(anchor['id'], 'source-map')
        self.assertIn('Map caption', record['text'])
        self.assertIn('[IMAGE]', record['text'])
        self.assertEqual(record['image_references'][0]['source_attributes']['href'], uri)
        self.assertTrue(all(a['image'] and not a['required'] for a in record['assets']))

    def test_nonimage_reference_and_available_prose_remain_unchanged(self):
        uri = 'data:application/pdf;base64,QUJD'
        html = f'<p>Legal caption data: application detail.</p><a href="{uri}">Attachment</a>'
        refs = adapters.asset_refs(html, 'https://ecode360.com/501', '501')
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0]['url'], uri)
        self.assertTrue(refs[0]['required'])
        self.assertFalse(refs[0]['image'])
        self.assertEqual(adapters.image_occurrences(html, '501'), [])
        self.assertEqual(adapters.image_attribute('alt', 'Legal data: application detail'), 'Legal data: application detail')


if __name__ == '__main__':
    unittest.main(verbosity=2)
