"""Current-launcher acceptance of actual required-PDF coverage, no publisher access."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get('COLLECTION_TEST_REPO', HERE.parents[1])).resolve()
FIXTURE = HERE / 'fixtures/overland-required-pdf-coverage.json'
FIXTURE_SHA = 'dd938b413c9753de5767c5af62d1f636c1ee46ae2489a1079799df4b6dd707dd'


class RequiredPdfAcceptance(unittest.TestCase):
    def setUp(self):
        tripwire = patch.object(socket, 'socket', side_effect=AssertionError('Network forbidden in acceptance regression'))
        tripwire.start()
        self.addCleanup(tripwire.stop)
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.output = Path(self.temporary.name)
        spec = importlib.util.spec_from_file_location('required_pdf_current_ops', REPO / 'collectors/ops/launcher.py')
        self.ops = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.ops)
        raw = FIXTURE.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), FIXTURE_SHA)
        self.coverage = json.loads(raw)
        self.pub = {'publisher': 'encodeplus', 'source_url': 'https://codes.opkansas.org/municipal-code/'}

    def acceptance(self, coverage):
        (self.output / 'coverage.json').write_text(json.dumps(coverage))
        return self.ops.publication_acceptance(self.pub, self.output)

    def test_actual_five_required_pdfs_preserve_html_binary_but_refuse_semantics(self):
        self.assertEqual(len(self.coverage['asset_document_integrity']), 5)
        self.assertEqual(sum(d['pages'] for d in self.coverage['asset_document_integrity'].values()), 636)
        result = self.acceptance(self.coverage)
        self.assertTrue(result['publication_text_complete'])
        self.assertTrue(result['required_nonimage_documents_complete'])
        self.assertFalse(result['legal_structure_qualified'])
        self.assertFalse(result['publication_coverage_accepted'])
        self.assertEqual(len(result['pdf_structure_dimensions']), 10)
        self.assertTrue(all(value is None for value in result['pdf_structure_dimensions'].values()))

    def test_parent_aggregate_qualification_cannot_override_required_documents(self):
        coverage = copy.deepcopy(self.coverage)
        coverage.update(pdf_semantic_text_completeness_qualified=True, pdf_table_completeness_qualified=True)
        result = self.acceptance(coverage)
        self.assertFalse(result['legal_structure_qualified'])
        self.assertFalse(result['publication_coverage_accepted'])
        self.assertTrue(result['required_nonimage_documents_complete'])

    def test_character_conservation_is_not_pdf_semantic_qualification(self):
        coverage = copy.deepcopy(self.coverage)
        for detail in coverage['asset_document_integrity'].values():
            detail['extractable_text_character_conservation_qualified'] = True
        result = self.acceptance(coverage)
        self.assertFalse(result['legal_structure_qualified'])
        self.assertTrue(result['publication_text_complete'])
        self.assertTrue(result['required_nonimage_documents_complete'])

    def test_html_without_required_pdf_assets_keeps_its_independent_pass(self):
        coverage = {'publication_text_complete': True, 'attachments_complete': True, 'asset_document_integrity': {}}
        result = self.acceptance(coverage)
        self.assertTrue(result['publication_coverage_accepted'])
        self.assertTrue(result['legal_structure_qualified'])
        self.assertEqual(result['pdf_structure_dimensions'], {})

    def test_non_pdf_integrity_is_not_mislabeled_as_pdf_qualification(self):
        # This checks classification only, not legal semantics of the non-PDF.
        coverage = {'publication_text_complete': True, 'attachments_complete': True,
                    'asset_document_integrity': {'https://example.test/appendix.zip':
                        {'format': 'non-PDF binary', 'bytes': 10,
                         'qualification': 'nonempty bytes only; document semantics unqualified'}}}
        result = self.acceptance(coverage)
        self.assertTrue(result['required_nonimage_documents_complete'])
        self.assertEqual(result['pdf_structure_dimensions'], {})


if __name__ == '__main__':
    unittest.main(verbosity=2)
