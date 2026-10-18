import sys
sys.dont_write_bytecode=True
import pathlib,tempfile,shutil,os,json,hashlib,unittest
H=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(H/'captured'))
from collectors.encodeplus import retained_native as n
from collectors.encodeplus.util import hash_json
class Artifacts(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.out=pathlib.Path(self.tmp.name)/'copy';shutil.copytree(H/'full-native/82-cfe47a936088',self.out,copy_function=os.link)
 def tearDown(self):self.tmp.cleanup()
 def write(self,name,value):
  p=self.out/name;p.unlink();p.write_text(json.dumps(value,sort_keys=True)+'\n')
 def test_original_all224_readonly(self):self.assertTrue(n.verify(self.out)['artifact_replay_verified'])
 def test_normalized_corruption(self):
  p=self.out/'records.csv';raw=p.read_bytes();p.unlink();p.write_bytes(raw+b'changed')
  with self.assertRaises(AssertionError):n.verify(self.out)
 def test_rehashed_missing_page(self):
  p=self.out/'records.jsonl';lines=p.read_text().split('\n');p.unlink();p.write_text('\n'.join(lines[1:]));cp=json.loads((self.out/'checkpoint.json').read_text());cp['normalized_outputs']['records.jsonl']=hashlib.sha256(p.read_bytes()).hexdigest();self.write('checkpoint.json',cp)
  with self.assertRaises(AssertionError):n.verify(self.out)
 def test_rehashed_claimed_semantic_pass(self):
  r=json.loads((self.out/'coverage.json').read_text());r['publication_complete']=True;cp=json.loads((self.out/'checkpoint.json').read_text());cp['report_sha256']=hash_json(r);self.write('coverage.json',r);self.write('checkpoint.json',cp)
  with self.assertRaises(AssertionError):n.verify(self.out)
 def test_rehashed_wrong_source_url(self):
  cfg=json.loads((self.out/'config.json').read_text());cfg['url']='https://example.invalid/wrong.pdf';cp=json.loads((self.out/'checkpoint.json').read_text());cp['config']=cfg;cp['config_sha256']=hash_json(cfg);self.write('config.json',cfg);self.write('checkpoint.json',cp)
  with self.assertRaises(AssertionError):n.verify(self.out)
 def test_existing_output_not_reextracted(self):
  cfg=json.loads((self.out/'config.json').read_text())
  with self.assertRaisesRegex(AssertionError,'Fresh output'):n.extract(cfg,self.out/'raw/source.pdf',self.out/'raw/source.pdf.receipt.json',self.out)
if __name__=='__main__':unittest.main()
