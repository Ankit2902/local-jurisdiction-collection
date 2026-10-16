#!/usr/bin/env python3
"""Offline real-source checks against retained Aug 28 snapshots; no current coverage claim."""
import json,re,unittest
from pathlib import Path
from bs4 import BeautifulSoup
import municipal_codes_cli as m
ROOT=Path(__file__).resolve().parent
class RetainedSourceTests(unittest.TestCase):
 def test_five_real_chapter_bundles(self):
  expected={'berkeley-ca':10,'petaluma-ca':9,'sonoma-ca':10,'bellingham-wa':13,'everett-wa':12}
  for slug,count in expected.items():
   with self.subTest(slug=slug):
    path=ROOT/'fixtures/retained-2026-08-28'/slug/'page-1.html';html=path.read_text();base=m.ROUTES[slug][2];url=base+'/1.01.010'
    rows,notes=m.parse_page(html,url,base);sections=[r for r in rows if r['node_kind']=='section'];self.assertEqual(len(sections),count)
    observed=BeautifulSoup(html,'html.parser').select('main article.type-Section');self.assertEqual(len(sections),len(observed))
    self.assertEqual([r['section_number'] for r in sections],[a['data-short-cite'] for a in observed])
    self.assertEqual(len({r['node_id'] for r in sections}),count)
    for row,card in zip(sections,observed):
     self.assertEqual(row['section_name'],card.select_one('header .name').get_text(' ',strip=True));self.assertIn(card.select_one('p').get_text(' ',strip=True)[:30],re.sub(r'\s+',' ',row['full_text']))
     self.assertNotIn('Search Within This',row['full_text']);self.assertNotIn('included in your selections',row['full_text'])
    replay,_=m.parse_page(html,base+'/1.01',base)
    self.assertEqual([(r['node_id'],r['body_sha256']) for r in rows],[(r['node_id'],r['body_sha256']) for r in replay])
 def test_bellingham_contents_no_records_and_full_retained_tree(self):
  path=ROOT/'fixtures/retained-2026-08-28/bellingham-wa/page-0.html';base=m.ROUTES['bellingham-wa'][2];html=path.read_text();rows,_=m.parse_page(html,base+'/contents',base);self.assertEqual(rows,[])
  inv=m.inventory(html,base+'/contents',base,'main > ul.contents-toc');self.assertGreater(len(inv['nodes']),1000);self.assertEqual(inv['pending_controls'],0);self.assertEqual(inv['completeness'],'unverified')
  m.write_json(ROOT/'evidence/bellingham-wa/retained-inventory.json',inv)
 def test_reject_overwritten_everett_contents_cache(self):
  path=ROOT/'fixtures/retained-2026-08-28/everett-wa/page-0.html'
  with self.assertRaises(m.QualificationError):m.parse_page(path.read_text(),m.ROUTES['everett-wa'][1],m.ROUTES['everett-wa'][2])
 def test_real_editorial_parent_notes_preserved(self):
  for slug in ['petaluma-ca','everett-wa']:
   html=(ROOT/'fixtures/retained-2026-08-28'/slug/'page-1.html').read_text();base=m.ROUTES[slug][2];rows,_=m.parse_page(html,base+'/1.01.010',base);parents=[r for r in rows if r['node_kind']!='section'];self.assertEqual(len(parents),1);self.assertIn('statutory provisions',parents[0]['full_text']);self.assertNotIn('Legal body',parents[0]['full_text'])
if __name__=='__main__':unittest.main(verbosity=2)
