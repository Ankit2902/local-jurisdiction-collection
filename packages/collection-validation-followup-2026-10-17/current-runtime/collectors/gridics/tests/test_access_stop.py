"""The observed live refusal must survive relocation and a fresh empty gate."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from collectors.gridics.collect import acquire, enforce_access_advisory, Invalid


class AccessStopTests(unittest.TestCase):
    def test_direct_collect_refuses_before_output_or_browser(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'new-output'
            with patch('playwright.sync_api.sync_playwright',side_effect=AssertionError('Browser must not start')):
                with self.assertRaisesRegex(Invalid,'Published Gridics workflow access stop'):
                    acquire(output,{},False)
            self.assertFalse(output.exists())

    def test_missing_catalog_does_not_release_known_stop(self):
        with patch('collectors.gridics.collect.read',side_effect=FileNotFoundError):
            with self.assertRaisesRegex(Invalid,'known Gridics PDF HEAD 403 stop remains'):
                enforce_access_advisory()

    def test_altered_or_absent_stop_does_not_release_known_stop(self):
        for value in ({'schema_version':999,'advisories':[]},{'schema_version':1,'advisories':[]},{'schema_version':1,'advisories':[{'family':'gridics','operator_review_required':False}]}):
            with self.subTest(value=value),patch('collectors.gridics.collect.read',return_value=value):
                with self.assertRaises(Invalid):
                    enforce_access_advisory()


if __name__ == '__main__':
    unittest.main()
