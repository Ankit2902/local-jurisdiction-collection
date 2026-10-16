from pathlib import Path
import sys, unittest
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from adapters.ecode360 import parse_rendered_sections
class ECode360Tests(unittest.TestCase):
    def test_section_boundaries_and_text(self):
        html = (Path(__file__).parent / 'fixtures' / 'ecode360' / 'section.html').read_text()
        rows = parse_rendered_sections(html)
        self.assertEqual(len(rows), 2)
        self.assertIn('1.01.010 Findings.', rows[0]['label'])
        self.assertIn('adopts this Code', rows[0]['full_text'])
    def test_current_rendered_section_layout(self):
        html = '''<header><div class="contentTitle sectionTitle" data-code-content-type="section" data-full-title="§ 1.04.010: Definitions."><h2>§ 1.04.010 Definitions.</h2></div></header><div class="section_content content"><p>City means the City of Burlingame.</p></div>'''
        rows = parse_rendered_sections(html)
        self.assertEqual(rows, [{"label": "§ 1.04.010: Definitions.", "full_text": "City means the City of Burlingame."}])
if __name__ == '__main__': unittest.main()
