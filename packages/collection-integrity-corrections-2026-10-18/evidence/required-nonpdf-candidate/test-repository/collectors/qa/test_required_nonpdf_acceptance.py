"""Required non-PDF documents need semantic proof separate from byte integrity."""
import copy
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


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, REPO / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RequiredNonPdfAcceptance(unittest.TestCase):
    def setUp(self):
        tripwire = patch.object(socket, 'socket', side_effect=AssertionError('No network in document acceptance regression'))
        tripwire.start()
        self.addCleanup(tripwire.stop)
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.out = Path(self.temporary.name)
        self.ops = load('required_nonpdf_ops', 'collectors/ops/launcher.py')
        self.documents = load('required_nonpdf_provider', 'collectors/encodeplus/documents.py')

    def accept(self, entries, extra=None):
        coverage = {'publication_text_complete': True, 'attachments_complete': True, 'asset_document_integrity': entries}
        coverage.update(extra or {})
        (self.out / 'coverage.json').write_text(json.dumps(coverage))
        return self.ops.publication_acceptance({'publisher': 'encodeplus'}, self.out)

    def test_provider_nonempty_bytes_do_not_qualify_required_document_semantics(self):
        entries = {}
        for suffix, mime in (('docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'), ('zip', 'application/zip')):
            url = 'https://example.test/required.' + suffix
            # Provider-behavior fixture only; not an acquired publisher document.
            entries[url] = self.documents.qualify_document(b'nonempty unit fixture bytes', url, mime)
            self.assertEqual(entries[url]['format'], 'non-PDF binary')
            self.assertIn('semantics unqualified', entries[url]['qualification'])
        result = self.accept(entries)
        self.assertTrue(result['publication_text_complete'])
        self.assertTrue(result['required_nonimage_documents_complete'])
        self.assertFalse(result['legal_structure_qualified'])
        self.assertFalse(result['publication_coverage_accepted'])
        self.assertEqual(result['pdf_structure_dimensions'], {})
        self.assertEqual(len(result['nonpdf_document_structure_dimensions']), 4)
        self.assertTrue(all(v is None for v in result['nonpdf_document_structure_dimensions'].values()))

    def test_aggregate_and_character_conservation_cannot_override_missing_structure(self):
        result = self.accept({'https://example.test/a.docx': {'format': 'non-PDF binary', 'extractable_text_character_conservation_qualified': True}},
                             {'document_text_completeness_qualified': True, 'document_structure_completeness_qualified': True})
        self.assertFalse(result['publication_coverage_accepted'])
        self.assertTrue(result['required_nonimage_documents_complete'])

    def test_every_required_document_dimension_must_be_explicit_true(self):
        entries = {url: {'format': 'non-PDF binary', 'document_text_completeness_qualified': True, 'document_structure_completeness_qualified': True}
                   for url in ('https://example.test/a.docx', 'https://example.test/b.zip')}
        self.assertTrue(self.accept(entries)['publication_coverage_accepted'])  # Schema control, no actual-document claim.
        for url in entries:
            for key in ('document_text_completeness_qualified', 'document_structure_completeness_qualified'):
                changed = copy.deepcopy(entries)
                changed[url].pop(key)
                self.assertFalse(self.accept(changed)['publication_coverage_accepted'])

    def test_no_required_assets_preserves_independent_html_pass(self):
        result = self.accept({})
        self.assertTrue(result['publication_coverage_accepted'])
        self.assertEqual(result['nonpdf_document_structure_dimensions'], {})


if __name__ == '__main__':
    unittest.main(verbosity=2)
