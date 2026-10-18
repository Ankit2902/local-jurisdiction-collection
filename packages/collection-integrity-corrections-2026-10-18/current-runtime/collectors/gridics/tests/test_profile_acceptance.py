"""Production reconciliation must require exact acquired client evidence."""
import json
from pathlib import Path
import unittest
import zipfile

from collectors.gridics import model
from collectors.qa import test_gridics_acceptance as acceptance
CFG = acceptance.CFG


class ProfileAcceptance(unittest.TestCase):
    def setUp(self):
        self.fixture = acceptance.GridicsAcceptance()
        self.fixture.setUp()
        self.root = self.fixture.root
        self.install_body('<p><b>land</b> <b>use</b></p>', '<p><b>land</b><b>use</b></p>')
        ledger = model.read(self.root / 'responses.json')
        base = Path(__file__).resolve().parents[1] / 'fixtures'
        with zipfile.ZipFile(base / 'miami-renderer.zip') as archive:
            for phase, minute in [('start', '00'), ('end', '10')]:
                for kind, url in [('renderer', 'https://codehub.gridics.com/build/static/js/Doc.fac920ca.chunk.js'), ('router', 'https://codehub.gridics.com/react/init/js?tmudor')]:
                    raw = archive.read('publisher-' + kind + '.js')
                    name = phase + '-' + kind + '.js'
                    (self.root / name).write_bytes(raw)
                    ledger.append({'url': url, 'path': name, 'sha256': model.digest(raw), 'bytes': len(raw), 'status': 200, 'content_type': 'application/javascript', 'phase': phase, 'epoch': 'synthetic-epoch', 'at': '2026-10-17T00:' + minute + ':00+00:00'})
        model.save(self.root / 'responses.json', ledger)

    def tearDown(self):
        self.fixture.tearDown()

    def install_body(self, native, rendered):
        for phase in ('start', 'end'):
            def edit(receipt):
                path = self.root / receipt['path']
                tree = model.read(path)
                tree[0]['children'][0]['text'] = native
                raw = json.dumps(tree).encode()
                path.write_bytes(raw)
                receipt.update(sha256=model.digest(raw), bytes=len(raw))
            self.fixture.mutate_receipt(phase, 'tree', edit)
            cp = model.read(self.root / (phase + '-checkpoint.json'))
            row = cp['roots'][0]
            raw = ('<div class="section" data-path="/A"><div id="anchor-A"><h2>Section A</h2></div>' + rendered + '</div>').encode()
            (self.root / row['dom_path']).write_bytes(raw)
            row['dom_sha256'] = model.digest(raw)
            model.save(self.root / (phase + '-checkpoint.json'), cp)

    def test_only_exact_bound_client_qualifies_projection_and_native_text_stays(self):
        records, _, coverage = model.analyze(self.root, CFG)
        self.assertTrue(coverage['complete'])
        self.assertEqual(records[0]['text'], 'land use')
        self.assertEqual(len(coverage['publisher_rendering_reconciliations']), 2)
        ledger = model.read(self.root / 'responses.json')
        model.save(self.root / 'responses.json', [r for r in ledger if not r['path'].endswith('.js')])
        self.assertFalse(model.analyze(self.root, CFG)[2]['publication_text_complete'])

    def test_rehashed_changed_client_does_not_qualify(self):
        ledger = model.read(self.root / 'responses.json')
        for receipt in ledger:
            if receipt['path'].endswith('renderer.js'):
                raw = (self.root / receipt['path']).read_bytes() + b' /* different client */'
                (self.root / receipt['path']).write_bytes(raw)
                receipt.update(sha256=model.digest(raw), bytes=len(raw))
        model.save(self.root / 'responses.json', ledger)
        self.assertFalse(model.analyze(self.root, CFG)[2]['publication_text_complete'])

    def test_known_profile_never_waives_changed_operative_text(self):
        self.install_body('<p>land use</p>', '<p>landuse</p>')
        self.assertFalse(model.analyze(self.root, CFG)[2]['publication_text_complete'])

    def test_reference_must_belong_to_exact_book_and_observed_target(self):
        body = '<p><a href="' + CFG['source_url'] + r'#\A">in</a><a href="https://codehub.gridics.com/us/zz/other#\A">other</a><a href="' + CFG['source_url'] + r'#\missing">missing</a></p>'
        self.install_body(body, body)
        _, refs, coverage = model.analyze(self.root, CFG)
        self.assertEqual([r['disposition'] for r in refs], ['included_internal_provision', 'unresolved_scope_or_required_document', 'unresolved_scope_or_required_document'])
        self.assertFalse(coverage['required_assets_complete'])


if __name__ == '__main__':
    unittest.main()
