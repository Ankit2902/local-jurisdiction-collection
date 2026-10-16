import json
import unittest
from pathlib import Path
from handoff_tools import inspect_rows,audit_bundle

class HandoffTests(unittest.TestCase):
    def test_exact_scope(self):
        routes=json.loads((Path(__file__).parent/'routes.json').read_text())
        self.assertEqual(len(routes['jurisdictions']),30)
        self.assertEqual(len({j['slug'] for j in routes['jurisdictions']}),30)
        self.assertEqual(sum(routes['source_type_counts'].values()),30)
        self.assertEqual(len(routes['source_type_counts']),8)
    def test_diagnostic_flags_known_bad_shapes(self):
        rows=[{'section_number':'Contents','section_name':'Contents','full_text':'TOC'},
              {'section_number':'','section_name':'','full_text':'text'},
              {'section_number':'1-1','section_name':'Rev. 2026','full_text':'bad\x96decode'},
              {'section_number':'1-1','section_name':'Real heading','full_text':'body'}]
        codes={x['code'] for x in inspect_rows(rows)}
        self.assertTrue({'CONTENTS_RECORD','MISSING_LABEL','REVISION_HEADER','ENCODING_REVIEW','REPEATED_LOCATOR'}<=codes)
    def test_ordinary_record_has_no_diagnostic(self):
        self.assertEqual(inspect_rows([{'section_number':'1.01.010','section_name':'Adoption.','full_text':'The code is adopted.'}]),[])
    def test_retained_samples_reproduce_review(self):
        report=audit_bundle(Path(__file__).parent)
        self.assertEqual(report['summary']['sample_rows'],288)
        flagged={j['slug'] for j in report['jurisdictions'] if j['findings']}
        self.assertTrue({'berkeley-ca','everett-wa','sonoma-ca','daly-city-ca','portland-me','king-county-wa'}<=flagged)

if __name__=='__main__':unittest.main()
