import sys
sys.dont_write_bytecode=True
import pathlib,tempfile,shutil,os,json,unittest,hashlib
H=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(H))
import overland_historical_native_qualification as q
class Qualification(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.h=pathlib.Path(self.tmp.name)/'packet';shutil.copytree(H,self.h,copy_function=os.link,ignore=shutil.ignore_patterns('FROZEN-PACKET'));self.spec=json.loads((self.h/'native-method-qualification.json').read_text())
 def tearDown(self):self.tmp.cleanup()
 def write(self,rel,v):
  p=self.h/rel;p.unlink();p.write_text(json.dumps(v)+'\n')
 def verify(self):self.write('native-method-qualification.json',self.spec);return q.verify_packet(self.h,False)
 def test_original_whole1111(self):self.assertEqual(self.verify()['total_pages'],1111)
 def test_changed_alias(self):
  self.spec['entries'][1]['url']=self.spec['entries'][1]['url'].replace('codes.opkansas.org/municipal-code','online.encodeplus.com/regs/overlandpark-ks')
  with self.assertRaises(ValueError):self.verify()
 def test_wrong_native_original(self):
  p=self.h/self.spec['entries'][0]['native_path'];p.unlink();p.write_bytes(b'%PDF-truncated')
  with self.assertRaises(ValueError):self.verify()
 def test_missing_page_rehashed(self):
  e=self.spec['entries'][0];rel=e['run_path']+'/records.jsonl';p=self.h/rel;lines=p.read_text().split('\n');p.unlink();p.write_text('\n'.join(lines[1:]));e['records_sha256']=q.sha(p.read_bytes());cp=json.loads((self.h/e['run_path']/'checkpoint.json').read_text());cp['normalized_outputs']['records.jsonl']=e['records_sha256'];self.write(e['run_path']+'/checkpoint.json',cp);e['checkpoint_sha256']=q.sha((self.h/e['run_path']/'checkpoint.json').read_bytes())
  with self.assertRaises(ValueError):self.verify()
 def test_unearned_edition_pass_rehashed(self):
  e=self.spec['entries'][0];rel=e['run_path']+'/coverage.json';cov=json.loads((self.h/rel).read_text());cov['edition_complete']=True;self.write(rel,cov);e['coverage_sha256']=q.sha((self.h/rel).read_bytes());cp=json.loads((self.h/e['run_path']/'checkpoint.json').read_text());cp['report_sha256']=q.sha(q.canon(cov));self.write(e['run_path']+'/checkpoint.json',cp);e['checkpoint_sha256']=q.sha((self.h/e['run_path']/'checkpoint.json').read_bytes())
  with self.assertRaises(ValueError):self.verify()
 def test_changed_source_anchor_base(self):
  self.spec['entries'][1]['source_anchor_url']='https://online.encodeplus.com/regs/overlandpark-ks/page.aspx?name=documents'
  with self.assertRaises(ValueError):self.verify()
if __name__=='__main__':unittest.main()
