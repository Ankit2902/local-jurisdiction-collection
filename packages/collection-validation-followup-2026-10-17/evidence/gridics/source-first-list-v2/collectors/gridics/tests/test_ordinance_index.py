import copy
import hashlib
import json
from pathlib import Path
import unittest
import zipfile

from collectors.gridics.model import native_records, dom_records, index_reference_kind, normalize


class OrdinanceIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base = Path(__file__).resolve().parents[1] / 'fixtures'
        cls.provenance = json.loads((base / 'cupertino-ordinance-index-provenance.json').read_text())
        with zipfile.ZipFile(base / 'cupertino-ordinance-index.zip') as archive:
            cls.raw = {name: archive.read(name) for name in cls.provenance['files']}
        for name, raw in cls.raw.items():
            assert hashlib.sha256(raw).hexdigest() == cls.provenance['files'][name]['sha256']
        cls.records, _ = native_records(json.loads(cls.raw['native.json']), cls.provenance['config'], cls.provenance['root']['path'])

    def test_actual_index_every_row_and_locator_preserved(self):
        self.assertEqual(len(self.records), 1)
        record = self.records[0]
        dom = dom_records(self.raw['rendered.html'].decode(), self.provenance['config'])[record['source_path']]
        self.assertEqual(record['tables'], dom['tables'])
        self.assertEqual(len(record['tables'][0]), 2290)
        self.assertEqual(len(record['links']), 2291)
        kinds = [index_reference_kind(record, link) for link in record['links']]
        self.assertEqual(kinds.count('ordinance_index_reference'), 2289)
        self.assertEqual(kinds.count('editorial_search_reference'), 2)
        self.assertNotIn(None, kinds)
        for link in record['links']:
            self.assertTrue(link['url'])
            self.assertTrue(link['source_context_sha256'])
            if index_reference_kind(record, link) == 'ordinance_index_reference':
                self.assertEqual(len(link['source_context_cells']), 2)
                self.assertEqual(link['source_context_cells'][0], link['label'])

    def test_operative_and_contextless_links_do_not_get_index_exemption(self):
        record = copy.deepcopy(self.records[0])
        link = next(link for link in record['links'] if index_reference_kind(record, link) == 'ordinance_index_reference')
        for field, value in [('heading', 'APPENDIX: ADOPTED ORDINANCES'), ('parent_id', 'operative-provision'), ('tables', [])]:
            altered = dict(record, **{field: value})
            self.assertIsNone(index_reference_kind(altered, link))
        self.assertIsNone(index_reference_kind(record, {'url': link['url'], 'label': link['label']}))
        self.assertIsNone(index_reference_kind(record, dict(link, label='Required Appendix A')))

    def test_reference_context_uses_same_image_policy(self):
        value = normalize('<p><img src="DATA:IMAGE/PNG;base64,SECRETPIXELS"><a href="https://example.org/law.pdf">Law</a></p>', 'https://example.org')
        self.assertNotIn('SECRETPIXELS', json.dumps(value))
        self.assertEqual(value['links'][0]['source_context_text'], '[IMAGE]Law')


if __name__ == '__main__':
    unittest.main()
