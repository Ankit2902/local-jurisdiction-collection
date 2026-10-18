"""Original-source routing, current-code binding and acceptance boundaries."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from collectors.registry import dispatch
from collectors.ops import launcher


class OriginalDispatch(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config_path = self.root / 'collectors/originals/configs/flagstaff.json'
        self.config_path.parent.mkdir(parents=True)
        self.config = dict(target_id='original-flagstaff-az', jurisdiction='Flagstaff',
                           state='AZ', source_url='https://www.codepublishing.com/AZ/Flagstaff/',
                           profile='flagstaff_html', required_formats=['html'])
        self.config_path.write_text(json.dumps(self.config))
        self.pub = dict(id='original-flagstaff-az-primary', publisher='official',
                        adapter_family='originals', runnable=True, role='primary',
                        source_url=self.config['source_url'], title='City Code including Charter',
                        adapter_config_path='collectors/originals/configs/flagstaff.json',
                        scope_kind='publication', required_for_jurisdiction=True)
        self.target = dict(id=self.config['target_id'], jurisdiction='Flagstaff', state='AZ',
                           expected_identity={'client_names': ['Flagstaff'], 'state': 'AZ'})
        self.patch = patch.object(dispatch, 'ROOT', self.root)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.addCleanup(self.temp.cleanup)

    def test_exact_collect_verify_and_resume_routes(self):
        for verify, resume in [(False, False), (False, True), (True, False)]:
            plan = dispatch.command(self.pub, self.target, '/fresh-output', 'python',
                                    verify=verify, resume=resume)
            self.assertEqual(plan['argv'][:3], ['python', 'collectors/originals/cli.py',
                                               'verify' if verify else 'collect'])
            self.assertEqual('--resume' in plan['argv'], resume)
            self.assertFalse(plan['jurisdiction_complete'])
            self.assertIsNone(plan['staged_config'])

    def test_foreign_source_identity_profile_and_path_refused(self):
        for key, value in [('target_id', 'another-target'), ('jurisdiction', 'King County'),
                           ('state', 'WA'), ('source_url', 'https://example.com/'),
                           ('profile', 'generic-unqualified'), ('profile', 'king_html_word'),
                           ('required_formats', [])]:
            changed = dict(self.config, **{key: value})
            self.config_path.write_text(json.dumps(changed))
            with self.assertRaises(dispatch.Unsupported, msg=key):
                dispatch.command(self.pub, self.target, '/fresh-output')
        self.config_path.write_text(json.dumps(self.config))
        with self.assertRaises(dispatch.Unsupported):
            dispatch.command(dict(self.pub, adapter_config_path='elsewhere.json'), self.target, '/out')

    def test_bounded_and_export_modes_cannot_silently_change_scope(self):
        for options in [dict(max_items=1), dict(native_export=True),
                        dict(upgrade_code=True, resume=True)]:
            with self.assertRaises(dispatch.Unsupported):
                dispatch.command(self.pub, self.target, '/out', **options)

    def test_verification_requires_exact_retained_config(self):
        out = self.root / 'run'
        out.mkdir()
        checkpoint = out / 'checkpoint.json'
        checkpoint.write_text(json.dumps({'config': self.config}))
        self.assertTrue(dispatch.bind_run(self.pub, self.target, out))
        checkpoint.write_text(json.dumps({'config': dict(self.config, state='WA')}))
        with self.assertRaises(dispatch.Unsupported):
            dispatch.bind_run(self.pub, self.target, out)

    def test_material_profile_and_wrapper_bytes_bound(self):
        family = self.root / 'collectors/originals'
        for name in ['cli.py', 'source_character_dispositions.json', 'source_dispositions.json']:
            (family / name).write_text('{}')
        ops = self.root / 'collectors/ops'
        ops.mkdir()
        for name in ['launcher.py', 'browser_check.cjs', 'requirements.txt']:
            (ops / name).write_text('')
        with patch.object(launcher, 'ROOT', self.root), patch.object(launcher, 'HERE', ops):
            before = launcher.code_binding('originals')
            (family / 'source_character_dispositions.json').write_text('{"changed":true}')
            after = launcher.code_binding('originals')
        self.assertNotEqual(before, after)
        self.assertIn('collectors/originals/cli.py', before)
        self.assertEqual(launcher.implementation_family(self.pub), 'originals')
        with self.assertRaises(launcher.OperationError):
            launcher.implementation_family(dict(self.pub, publisher='ecode'))

    def test_each_aggregate_gate_is_required_for_acceptance(self):
        out = self.root / 'coverage'
        out.mkdir()
        keys = ['publication_text_complete', 'attachments_complete',
                'legal_structure_qualified', 'source_consistency_complete']
        good = {key: True for key in keys}
        for failed in [None] + keys:
            report = dict(good)
            if failed:
                report[failed] = False
            (out / 'coverage.json').write_text(json.dumps(report))
            result = launcher.publication_acceptance(self.pub, out)
            self.assertEqual(result['publication_coverage_accepted'], failed is None, failed)
            self.assertFalse(result['jurisdiction_complete'])
        (out / 'coverage.json').write_text(json.dumps({'complete': True}))
        self.assertFalse(launcher.publication_acceptance(self.pub, out)['publication_coverage_accepted'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
