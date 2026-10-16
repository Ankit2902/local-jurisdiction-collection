"""Offline validation of Oct15 browser DOM; replayable with no browser/network."""
from pathlib import Path
from bs4 import BeautifulSoup
import csv,json,unittest,tempfile
import municipal_codes_cli as m
ROOT=Path(__file__).resolve().parent
EXPECTED={'berkeley-ca':(5238,10),'petaluma-ca':(2860,9),'sonoma-ca':(2177,10),'bellingham-wa':(2846,13),'everett-wa':(3742,12)}
class LiveSnapshotTests(unittest.TestCase):
 def test_full_tree_lengths_and_links(self):
  for slug,(count,_) in EXPECTED.items():
   with self.subTest(slug=slug):
    p=ROOT/'evidence'/slug/'live-contents-full.html';html=p.read_text();receipt=m.read_json(p.with_suffix('.json'));self.assertEqual(len(html.encode('utf-16-le'))//2,receipt['length']);s=BeautifulSoup(html,'html.parser');self.assertEqual(len(s.select('main ul.contents-toc a[href]')),count);self.assertEqual(len(m.read_json(p.parent/'inventory.json')['nodes']),count)
 def test_current_five_chapter_profiles(self):
  for slug,(_,count) in EXPECTED.items():
   with self.subTest(slug=slug):
    obj=m.read_json(ROOT/'evidence'/slug/'live-parsed.json');sections=[r for r in obj['records'] if r['node_kind']=='section'];self.assertEqual(len(sections),count)
    for r in sections:self.assertNotIn('Search Within This',r['full_text']);self.assertNotIn('included in your selections',r['full_text']);self.assertTrue(r['full_text']);self.assertTrue(r['node_id']);self.assertTrue(m.allowed(r['source_url'],m.ROUTES[slug][2]))
 def test_reject_truncated_dom(self):
  h=(ROOT/'evidence/berkeley-ca/live-contents-full.html').read_text()[:200000]
  with self.assertRaisesRegex(m.QualificationError,'Truncated'):m.inventory(h,m.ROUTES['berkeley-ca'][1],m.ROUTES['berkeley-ca'][2],'main > ul.contents-toc')
 def test_current_exports_csv_dispositions_lineage(self):
  for slug,(_,count) in EXPECTED.items():
   p=ROOT/'examples'/slug;obj=m.read_json(p/'aggregate-fulltext.json');expected=count+(1 if slug in ('petaluma-ca','everett-wa') else 0);self.assertEqual(len(obj['provisions']),expected)
   with (p/'aggregate-fulltext.csv').open(encoding='utf-8-sig',newline='') as f:self.assertEqual(list(csv.DictReader(f)),obj['provisions'])
   dispositions=[json.loads(l) for l in (p/'node-dispositions.jsonl').read_text().splitlines()];self.assertEqual(len(dispositions),EXPECTED[slug][0]);self.assertGreater(sum(d['disposition']=='unresolved' for d in dispositions),0)
   for line in (p/'record-provenance.jsonl').read_text().splitlines():
    for source in json.loads(line)['sources']:self.assertEqual(m.sha((p/source['raw_artifact_path']).read_bytes()),source['raw_sha256'])
if __name__=='__main__':unittest.main(verbosity=2)
