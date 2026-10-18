import hashlib
import json
from pathlib import Path
import unittest
import zipfile

from collectors.gridics.model import native_records, dom_records, normalize
from collectors.gridics.publisher import (
    RENDERER_SHA256, ROUTER_SHA256, body_for_rendering, fragment_path, script_role,
)


class PublisherTests(unittest.TestCase):
    def test_actual_full_roots_project_to_independent_browser_without_changing_export(self):
        base = Path(__file__).resolve().parents[1] / 'fixtures'
        provenance = json.loads((base / 'miami-renderer-provenance.json').read_text())
        with zipfile.ZipFile(base / 'miami-renderer.zip') as archive:
            raw = {name: archive.read(name) for name in provenance['files']}
        for name, value in raw.items():
            self.assertEqual(hashlib.sha256(value).hexdigest(), provenance['files'][name]['sha256'])
            self.assertEqual(len(value), provenance['files'][name]['bytes'])
        self.assertEqual(hashlib.sha256(raw['publisher-renderer.js']).hexdigest(), RENDERER_SHA256)
        self.assertEqual(hashlib.sha256(raw['publisher-router.js']).hexdigest(), ROUTER_SHA256)
        differences = 0
        for row in provenance['roots']:
            tree = json.loads(raw[row['tree']])
            original, _ = native_records(tree, provenance['config'], row['root']['path'])
            projected, _ = native_records(tree, provenance['config'], row['root']['path'], project_renderer=True)
            rendered = dom_records(raw[row['dom']].decode(), provenance['config'])
            self.assertEqual(set(rendered), {r['source_path'] for r in projected})
            for source, projection in zip(original, projected):
                witness = rendered[source['source_path']]
                for field in ('heading', 'text'):
                    self.assertEqual(' '.join(projection[field].split()), ' '.join(witness[field].split()))
                self.assertEqual(projection['tables'], witness['tables'])
                self.assertEqual(len(projection['images']), len(witness['images']))
                differences += source['text'] != projection['text']
            self.assertEqual(original, native_records(tree, provenance['config'], row['root']['path'])[0])
        self.assertGreater(differences, 1)

    def test_projection_does_not_waive_arbitrary_spaces_or_changed_words(self):
        markup = '<p>land use <b>T1</b> <b>T3</b> intact</p>'
        projected = body_for_rendering(markup, 'section')
        self.assertEqual(projected, '<p>land use <b>T1</b><b>T3</b> intact</p>')
        self.assertIn('land use', projected)
        self.assertNotEqual(normalize(projected, 'https://example.org')['text'], 'landuse T1T3 intact')
        self.assertEqual(body_for_rendering(markup, 'other'), markup)
        self.assertEqual(body_for_rendering('<p>\x85</p>', 'section'), '<p>\x85</p>')
        self.assertEqual(body_for_rendering('<p></p>', 'section'), '<p><br /></p>')

    def test_publisher_fragment_separators_and_anchor_options(self):
        self.assertEqual(fragment_path(r'\root\child&anchor=123&elementIndex=4&elementTag=p'), '/root/child')
        self.assertEqual(fragment_path('%5Croot%5Cchild'), '/root/child')
        self.assertEqual(fragment_path('/root/child'), '/root/child')
        self.assertEqual(fragment_path('%255Croot'), '/%255Croot')

    def test_script_profile_requires_publisher_and_actual_bundle_route(self):
        self.assertEqual(script_role('https://codehub.gridics.com/build/static/js/Doc.fac920ca.chunk.js'), 'renderer')
        self.assertEqual(script_role('https://codehub.gridics.com/react/init/js?tmudor'), 'router')
        self.assertIsNone(script_role('https://other.example/react/init/js'))
        self.assertIsNone(script_role('https://codehub.gridics.com/unrelated.js'))


if __name__ == '__main__':
    unittest.main()
