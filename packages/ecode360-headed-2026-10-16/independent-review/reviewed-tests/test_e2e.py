import contextlib,io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import ecode360 as e
from ingest_cua import ingest
ROOT=Path(__file__).parent
class CurrentE2ETests(unittest.TestCase):
 def test_all_fourteen_current_source_exports(self):
  rows=e.load(ROOT/'current-routes.json');self.assertEqual(len(rows),14);total=0
  for city in rows:
   with self.subTest(slug=city['slug']):
    folder=ROOT/'live/verified'/city['slug'];r=e.load(folder/'e2e-result.json')
    self.assertTrue(r['supported_browser_e2e_verified']);self.assertFalse(r['full_collection_verified']);self.assertFalse(r['inventory_verified'])
    self.assertEqual(e.digest((folder/'retained-source.html').read_bytes()),r['source_sha256'])
    self.assertTrue(all(x['normalized_source_text_matches_export'] for x in r['record_source_text_comparisons']))
    for path,sha in r['export_hashes'].items():self.assertEqual(e.digest((folder/path).read_bytes()),sha)
    total+=r['parsed_records']
  self.assertEqual(total,134)
 def test_current_foster_wrapped_list_markers_and_real_table(self):
  folder=ROOT/'live/verified/foster-city-ca';inv=e.load(folder/'inventory.json');manifest=e.load(folder/'imported/artifacts.json');raw=e.safe_path(folder/'imported',manifest['artifacts'][0]['path']).read_text()
  _,items=e.parse_page(raw,'https://ecode360.com/51404426',inv['identity']);one=next(x for x in items if x['node_id']=='51404427')
  self.assertIn('A. Code entitled',one['full_text']);self.assertIn('J. Code entitled',one['full_text']);self.assertIn('<table>',one['full_text']);self.assertEqual(one['full_text'].count('A. Code entitled'),1)
 def test_tampered_current_source_cannot_import(self):
  source=ROOT/'live/verified/foster-city-ca';r=e.load(source/'capture-receipt.json')
  with tempfile.TemporaryDirectory() as tmp:
   base=Path(tmp);r['raw_artifact_path']='source.html';e.dump(base/'receipt.json',r);(base/'source.html').write_text('tampered')
   with self.assertRaises(e.ValidationError):ingest(base/'receipt.json','Foster City',base/'out')
   self.assertFalse((base/'out/exports/aggregate-fulltext.json').exists())
 def test_blocked_cli_returns_failure_code(self):
  with patch.object(e,'acquire',return_value={'route_verified':False,'http_status':403}),contextlib.redirect_stdout(io.StringIO()):
   self.assertEqual(e.main(['fetch','https://ecode360.com/123','--out','unused']),2)
if __name__=='__main__':unittest.main()
