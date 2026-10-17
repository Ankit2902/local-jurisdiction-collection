"""Actual full-root source fixture for a defect found by independent Chrome QA."""
import hashlib
import json
from pathlib import Path
import unittest
import zipfile
from collectors.gridics.model import native_records, normalize


class BlockBoundaryTests(unittest.TestCase):
    def test_actual_miami_nested_list_keeps_source_word_boundary(self):
        base=Path(__file__).resolve().parents[1]/'fixtures'
        meta=json.loads((base/'miami-list-boundaries-provenance.json').read_text())
        with zipfile.ZipFile(base/'miami-list-boundaries.zip') as archive:
            files={name:archive.read(name) for name in meta['files']}
        for name,raw in files.items():
            self.assertEqual(hashlib.sha256(raw).hexdigest(),meta['files'][name]['sha256'])
        records,_=native_records(json.loads(files['native.json']),meta['config'],meta['source_root']['root']['path'])
        record=next(r for r in records if r['source_id']==meta['source_id'])
        cell=record['tables'][0][30][1]['text']
        self.assertIn('Transit Corridors:\nNW 7th Avenue\nBiscayne Boulevard',cell)
        self.assertNotIn('Corridors:NW',cell)
        self.assertIn('3 Stories Abutting D1, except when Abutting T3',cell)

    def test_block_boundaries_preserve_inline_word_and_list_number(self):
        value=normalize('co<em>de</em><p>Paragraph</p>Tail<ul><li>First<ol start="2"><li>Second</li></ol>After</li></ul>End','https://example.org/code')
        self.assertEqual(value['text'],'code\nParagraph\nTail\nFirst\n2. Second\nAfter\nEnd')


if __name__ == '__main__':
    unittest.main()
