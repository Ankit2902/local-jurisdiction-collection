"""No-network named enCodePlus scope binding regression for current repository code.

Install at collectors/qa/test_named_encodeplus_binding.py. For isolated review,
COLLECTION_TEST_REPO may identify the repository whose current modules are tested.
All mutations are restricted to temporary repositories.
"""
import copy
import importlib.util
import json
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(os.environ.get('COLLECTION_TEST_REPO', Path(__file__).resolve().parents[2])).resolve()


def module(name, relative):
    spec = importlib.util.spec_from_file_location(name, REPO / relative)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


class NamedEncodePlusBinding(unittest.TestCase):
    def setUp(self):
        self.no_network = patch.object(socket, 'socket', side_effect=AssertionError('Network forbidden in binding regression'))
        self.no_network.start()
        self.addCleanup(self.no_network.stop)
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.ops = module('named_config_ops', 'collectors/ops/launcher.py')
        self.qa = module('named_config_qa', 'collectors/qa/readiness_binding.py')
        self.dispatch = module('named_config_dispatch', 'collectors/registry/dispatch.py')
        for loaded in (self.ops, self.dispatch):
            loaded.ROOT = self.root
        self.ops.HERE = self.root / 'collectors/ops'
        # Real current configuration and selected registry identities; no frozen
        # candidate/baseline snapshot or copied historical test fixture required.
        self.configs = json.loads((REPO / 'collectors/encodeplus/targets.json').read_text())
        self.pub = next(p for p in json.loads((REPO / 'collectors/registry/publications.json').read_text())['publications'] if p['id'] == '82-primary')
        self.target = next(t for t in json.loads((REPO / 'collectors/registry/targets.json').read_text())['targets'] if t['id'] == self.pub['target_id'])
        for name in ('ops/launcher.py', 'ops/browser_check.cjs', 'ops/requirements.txt',
                     'registry/collect.py', 'registry/dispatch.py', 'registry/catalog.py',
                     'encodeplus/model.py', 'municode/model.py'):
            path = self.root / 'collectors' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('constant no-network fingerprint fixture')
        self.write_configs()

    def write_configs(self):
        self.path = self.root / 'collectors/encodeplus/targets.json'
        self.path.write_text(json.dumps(self.configs, indent=2) + '\n')

    def plan(self):
        return self.dispatch.command(self.pub, self.target, 'OUTPUT')

    def selection(self, plan):
        return self.qa.selected_configuration(self.root, self.pub, self.target, plan)

    def test_named_dispatch_binds_exact_current_entry_and_file(self):
        plan = self.plan()
        self.assertEqual(plan['named_config_path'], 'collectors/encodeplus/targets.json')
        self.assertEqual(plan['named_config_key'], 'overland')
        self.assertEqual(plan['argv'], ['python3', '-m', 'collectors.encodeplus.collect', 'overland', '--out', 'OUTPUT'])
        self.assertEqual(self.ops.selected_runtime_config(plan), self.configs['overland'])
        descriptor = self.selection(plan)['descriptor']
        self.assertEqual(descriptor['qualified_config'], self.configs['overland'])
        self.assertEqual(descriptor['qualified_config_file_sha256'], self.qa.sha(self.path))

    def test_actual_overland_scope_mutation_changes_all_bindings_with_stale_plan(self):
        plan = self.plan()
        selected = self.selection(plan)
        components = self.ops.code_binding('encodeplus')
        qa_components = self.qa.current_components(self.root, 'encodeplus')
        self.configs['overland']['scope'] += ' [MUTATED SCOPE]'
        self.write_configs()
        self.assertEqual(plan, self.plan())
        self.assertNotEqual(selected['sha256'], self.selection(plan)['sha256'])
        self.assertNotEqual(components, self.ops.code_binding('encodeplus'))
        self.assertNotEqual(qa_components, self.qa.current_components(self.root, 'encodeplus'))
        self.assertEqual(self.ops.selected_runtime_config(plan), self.configs['overland'])

    def test_whole_file_change_is_bound_even_when_selected_entry_unchanged(self):
        plan = self.plan()
        before = self.selection(plan)
        key = next(k for k in self.configs if k != 'overland')
        self.configs[key]['scope'] += ' [OTHER ENTRY MUTATION]'
        self.write_configs()
        after = self.selection(plan)
        self.assertEqual(before['descriptor']['qualified_config'], after['descriptor']['qualified_config'])
        self.assertNotEqual(before['sha256'], after['sha256'])

    def test_missing_named_file_fails_before_any_collection(self):
        plan = self.plan()
        self.path.unlink()
        for call in (lambda: self.ops.code_binding('encodeplus'),
                     lambda: self.qa.current_components(self.root, 'encodeplus'),
                     lambda: self.ops.selected_runtime_config(plan),
                     lambda: self.selection(plan)):
            with self.subTest(call=call):
                with self.assertRaises((ValueError, OSError)):
                    call()

    def test_missing_wrong_or_nonobject_key_refused(self):
        original = self.plan()
        for key in (None, 'absent-key', 'overland'):
            plan = dict(original, named_config_key=key)
            if key == 'overland':
                self.configs[key] = 'not a configuration object'
                self.write_configs()
            with self.subTest(key=key):
                with self.assertRaises(self.ops.OperationError):
                    self.ops.selected_runtime_config(plan)
                with self.assertRaises(ValueError):
                    self.selection(plan)

    def test_ambiguous_or_unexpected_named_source_refused(self):
        original = self.plan()
        for change in ({'named_config_path': '../targets.json'},
                       {'qualified_config_path': 'collectors/encodeplus/targets.json'}):
            plan = dict(original, **change)
            with self.subTest(change=change):
                with self.assertRaises(self.ops.OperationError):
                    self.ops.selected_runtime_config(plan)
                with self.assertRaises(ValueError):
                    self.selection(plan)

    def test_other_family_component_scope_does_not_include_ep_named_configs(self):
        before = self.ops.code_binding('municode')
        qa_before = self.qa.current_components(self.root, 'municode')
        self.assertNotIn('collectors/encodeplus/targets.json', before)
        self.configs['overland']['scope'] += ' [MUTATED SCOPE]'
        self.write_configs()
        self.assertEqual(before, self.ops.code_binding('municode'))
        self.assertEqual(qa_before, self.qa.current_components(self.root, 'municode'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
