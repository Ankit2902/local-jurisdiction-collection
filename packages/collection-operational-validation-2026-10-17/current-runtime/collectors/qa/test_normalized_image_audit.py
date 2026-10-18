"""Reject image payloads in normalized PDF records as well as HTML records."""
import json
import tempfile
import unittest
from pathlib import Path

from audit_normalized_images import audit, NORMALIZED_RECORD_NAMES, NORMALIZED_METADATA_NAMES


class NormalizedImageAuditTests(unittest.TestCase):
    def check_record(self, name, record):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / name
            raw = json.dumps(record, ensure_ascii=False) + '\n'
            path.write_text(raw, encoding='utf-8')
            result = audit(root)
            self.assertEqual(path.read_text(encoding='utf-8'), raw)
            self.assertEqual(result['normalized_records'], 1)
            return result

    def test_inline_payload_rejected_in_recursive_pdf_metadata(self):
        result = self.check_record('pdf-pages.jsonl', {
            'id': 'page-1', 'text': '[IMAGE]',
            'figures': [{'source_attributes': {'src': 'data:image/png;base64,AAAA'}}],
        })
        self.assertFalse(result['passed'])
        self.assertEqual(result['errors'][0]['kind'], 'inline-image-payload-or-URI')

    def test_active_markup_rejected_in_each_normalized_format(self):
        for name in NORMALIZED_RECORD_NAMES:
            for markup in ('<img src="figure.png">', '<svg><path d="M0 0"/></svg>',
                           '<span style="background:url(figure.png)">caption</span>'):
                with self.subTest(name=name, markup=markup):
                    self.assertFalse(self.check_record(name, {'id': '1', 'html': markup})['passed'])

    def test_placeholder_labels_and_unicode_separators_preserved(self):
        result = self.check_record('pdf-pages.jsonl', {
            'id': 'page-2', 'text': 'Figure 2\u2028[IMAGE]\u2029Available caption',
            'figures': [{'label': 'Road width', 'omitted': True}],
        })
        self.assertTrue(result['passed'])
        self.assertEqual(result['placeholder_occurrences_across_serializations'], 1)

    def test_missing_normalized_output_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertFalse(audit(Path(td))['passed'])

    def test_supplemental_metadata_payload_fails_even_when_records_are_safe(self):
        for name in NORMALIZED_METADATA_NAMES:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                (root / 'records.jsonl').write_text('{"id":"1","text":"[IMAGE] Caption"}\n')
                (root / name).write_text(json.dumps([{'nested': {'value': 'DATA:IMAGE/PNG;base64,AAAA\nBBBB'}}]))
                result = audit(root)
                self.assertFalse(result['passed'])
                self.assertEqual(len(result['metadata_files']), 1)
                self.assertEqual(result['normalized_records'], 1)


    def test_official_native_attachment_metadata_is_included(self):
        for metadata in [{'text': '[IMAGE] Caption'}, {'source': {'uri': 'data:image/svg+xml,<svg>PIXELS</svg>'}}, {'html': '<img src="x.png">'}]:
            with self.subTest(metadata=metadata), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                (root/'attachment-pages.jsonl').write_text('{"id":"a::page:1","text":"[IMAGE] Caption"}\n')
                (root/'native-attachments').mkdir()
                (root/'native-attachments/a.json').write_text(json.dumps(metadata))
                result = audit(root)
                self.assertEqual(len(result['metadata_files']), 1)
                self.assertEqual(result['normalized_records'], 1)
                self.assertEqual(result['passed'], metadata == {'text': '[IMAGE] Caption'})


if __name__ == '__main__':
    unittest.main(verbosity=2)
