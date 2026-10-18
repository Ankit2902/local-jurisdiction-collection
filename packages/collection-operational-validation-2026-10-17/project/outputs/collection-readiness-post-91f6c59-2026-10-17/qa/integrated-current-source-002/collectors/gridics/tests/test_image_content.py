import unittest
from collectors.gridics.image_content import is_image_content


class ImageResponseTests(unittest.TestCase):
    def test_mislabeled_separate_image_formats_are_rejected(self):
        sources = (b'\x89PNG\r\n\x1a\n', b'\xff\xd8\xff\xe0', b'GIF89a', b'II*\x00', b'MM\x00*', b'BM\x00\x00', b'\x00\x00\x01\x00', b'RIFF\x00\x00\x00\x00WEBP', b'\x00\x00\x00\x18ftypavif', b'\x00\x00\x00\x18ftypheic', b'\xef\xbb\xbf<?xml version="1.0"?>\n<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        for source in sources:
            with self.subTest(source=source):
                self.assertTrue(is_image_content('application/octet-stream', source))

    def test_native_documents_with_embedded_image_markup_remain_source_evidence(self):
        for source in (b'%PDF-1.7\n/Subtype /Image', b'<html><body><svg></svg><img src="map.png"></body></html>', b'{"text":"<img src=map.png>"}', b'const x = "<svg></svg>";', b'PK\x03\x04word/media/image1.png'):
            with self.subTest(source=source):
                self.assertFalse(is_image_content('application/octet-stream', source))

    def test_mime_rejection_does_not_need_body_bytes(self):
        for mime in ('image/png', 'IMAGE/SVG+XML; charset=UTF-8', ' image/avif '):
            self.assertTrue(is_image_content(mime))


if __name__ == '__main__':
    unittest.main()
