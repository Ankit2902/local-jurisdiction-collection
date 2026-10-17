"""Retained actual labels and synthetic edge cases; no network or publication completion claim."""
import sys
sys.dont_write_bytecode=True
import unittest
from edition import assess_edition
class EditionTests(unittest.TestCase):
 def test_actual_udc_mismatch(self):
  r=assess_edition({'Id':495185,'Name':'Supplement 25 Update 1'},'SUPPLEMENT NO. 24 VOLUMES I AND II March 2026 UNIFIED DEVELOPMENT CODE');self.assertEqual(r['status'],'mismatch');self.assertFalse(r['edition_label_matches'])
 def test_missing_update_stays_unqualified(self):self.assertEqual(assess_edition({'Name':'Supplement 25 Update 1'},'SUPPLEMENT NO. 25')['status'],'unqualified')
 def test_actual_charter_header_stays_unqualified(self):self.assertEqual(assess_edition({'Name':'Republication 9'},'THE CHARTER Published in 2023')['status'],'unqualified')
 def test_exact_label_is_only_header_corroboration(self):
  r=assess_edition({'Name':'Supplement 59'},'SUPPLEMENT NO. 59 City Code');self.assertEqual(r['status'],'header_label_corroborated');self.assertFalse(r['full_body_correspondence_verified'])
 def test_partial_number_does_not_match(self):self.assertEqual(assess_edition({'Name':'Supplement 5'},'SUPPLEMENT NO. 59')['status'],'mismatch')
 def test_partial_republication_label_does_not_match(self):self.assertEqual(assess_edition({'Name':'Republication 9'},'REPUBLICATION 90')['status'],'unqualified')
if __name__=='__main__':unittest.main(verbosity=2)
