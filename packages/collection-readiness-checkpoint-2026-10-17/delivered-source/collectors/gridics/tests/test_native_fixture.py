"""Offline comparison of an actual acquired native tree and rendered witness."""
import hashlib
import json
from pathlib import Path
import unittest
import zipfile

from collectors.gridics.model import native_records, dom_records


class NativeFixtureTests(unittest.TestCase):
    def test_actual_title11_inventory_tables_and_image_placeholders(self):
        base = Path(__file__).resolve().parents[1] / 'fixtures'
        provenance = json.loads((base / 'cupertino-title11-provenance.json').read_text())
        with zipfile.ZipFile(base / 'cupertino-title11.zip') as archive:
            source = {name: archive.read(name) for name in provenance['files']}
        for name, raw in source.items():
            self.assertEqual(hashlib.sha256(raw).hexdigest(), provenance['files'][name]['sha256'])
            self.assertEqual(len(raw), provenance['files'][name]['bytes'])
        native, _ = native_records(json.loads(source['native.json']), provenance['config'], provenance['root']['path'])
        rendered = dom_records(source['rendered.html'].decode(), provenance['config'])
        self.assertEqual({r['source_path'] for r in native}, set(rendered))
        self.assertEqual(len(native), provenance['expected']['records'])
        self.assertEqual(sum(len(r['tables']) for r in native), provenance['expected']['tables'])
        self.assertEqual(sum(len(r['images']) for r in native), provenance['expected']['body_images'])
        for record in native:
            witness = rendered[record['source_path']]
            with self.subTest(source_id=record['source_id']):
                for field in ('heading', 'text'):
                    self.assertEqual(' '.join(record[field].split()), ' '.join(witness[field].split()))
                self.assertEqual(record['tables'], witness['tables'])
                self.assertEqual(len(record['images']), len(witness['images']))
                self.assertEqual(record['html'].count('[IMAGE]'), len(record['images']))
                self.assertNotRegex(record['html'], r'(?i)<(?:img|svg|picture)\b|data:image/')


if __name__ == '__main__':
    unittest.main()
