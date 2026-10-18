import unittest,tempfile,sys,json,shutil,hashlib
from pathlib import Path
from unittest.mock import patch
import argparse,os,socket,urllib.request,datetime
sys.dont_write_bytecode=True
parser=argparse.ArgumentParser(description='18 durable native inventory initialization guards; no browser/network.')
parser.add_argument('--source',type=Path,default=Path(os.environ.get('ORIGINALS_QA_SOURCE',str(Path(__file__).resolve().parents[1]/'originals'))));parser.add_argument('--receipt',type=Path)
options=parser.parse_args();SOURCE=options.source.resolve()
if not (SOURCE/'flagstaff_initialization.py').is_file():raise SystemExit('Select reviewed early-inventory source with --source')
def snapshot():return {str(p.relative_to(SOURCE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(SOURCE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
BEFORE=snapshot()
def forbidden(*args,**kwargs):raise AssertionError('Initialization QA attempted actual network/browser operation')
socket.socket.connect=forbidden;socket.create_connection=forbidden;urllib.request.OpenerDirector.open=forbidden
import playwright.sync_api
playwright.sync_api.sync_playwright=forbidden
sys.path.insert(0,str(SOURCE));import flagstaff_initialization as m,flagstaff_inventory
class InitTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.base=Path(self.temp.name);self.out=self.base/'source';self.out.mkdir();self.gate=self.base/'gate';self.addCleanup(patch.stopall);patch.object(m.transport,'ROOT',self.gate).start();self.files=['flagstaff_initialization.py'];self.called=0
 def native(self,out):
  self.called+=1;out.mkdir();(out/'raw.bin').write_bytes(b'<p>Actual callback boundary proof</p>');m.save(out/'receipt.json',{'source_url':m.URL,'checked_values':['city-code'],'whole_publication_selected_values':['city-code'],'blocked':[]})
 def valid(self,out):
  assert (out/'raw.bin').read_bytes()==b'<p>Actual callback boundary proof</p>'
 def start(self,resume=False,run=None):
  with patch.object(flagstaff_inventory,'run',run or self.native):return m.initialize(self.out,self.files,self.valid,resume)
 def interrupt(self,out):
  self.called+=1;out.mkdir();(out/'partial.bin').write_bytes(b'durable interrupted native source');raise KeyboardInterrupt()
 def test_marker_precedes_native(self):
  def callback(out):
   self.assertTrue((self.out/m.NAME).exists());self.assertFalse((self.out/'checkpoint.json').exists());self.native(out)
  self.start(run=callback);self.assertEqual(m.load(self.out/m.NAME)['stage'],'inventory_ready')
 def test_interrupted_generation_preserved_samecommand(self):
  with self.assertRaises(KeyboardInterrupt):self.start(run=self.interrupt)
  first=m.digest_tree(self.out/'inventory-attempt-0001');self.start(True);state=m.load(self.out/m.NAME);self.assertEqual(first,state['attempts'][0]['manifest']);self.assertEqual(first,m.digest_tree(self.out/'inventory-attempt-0001'));self.assertEqual(state['attempts'][1]['path'],'inventory-origin')
 def test_wrong_source_refused(self):
  with self.assertRaises(KeyboardInterrupt):self.start(run=self.interrupt)
  p=self.out/m.NAME;s=m.load(p);s['source_url']='https://other.invalid/';m.save(p,s)
  with self.assertRaisesRegex(ValueError,'source/revision'):self.start(True)
  self.assertEqual(self.called,1)
 def test_wrong_version_refused(self):
  with self.assertRaises(KeyboardInterrupt):self.start(run=self.interrupt)
  p=self.out/m.NAME;s=m.load(p);s['code_fingerprint'][self.files[0]]='0'*64;m.save(p,s)
  with self.assertRaisesRegex(ValueError,'source/revision'):self.start(True)
 def test_prior_partial_mutation_refused(self):
  with self.assertRaises(KeyboardInterrupt):self.start(run=self.interrupt)
  with self.assertRaises(KeyboardInterrupt):self.start(True,run=self.interrupt)
  (self.out/'inventory-attempt-0001/partial.bin').write_bytes(b'changed')
  with self.assertRaisesRegex(ValueError,'generation changed'):self.start(True)
 def test_retained403_before_retry(self):
  with self.assertRaises(KeyboardInterrupt):self.start(run=self.interrupt)
  m.save(self.out/'inventory-attempt-0001/receipt.json',{'source_url':m.URL,'blocked':[{'status':403}]})
  with self.assertRaisesRegex(ValueError,'failed or stopped'):self.start(True)
  self.assertEqual(self.called,1)
 def test_retained429_header_before_retry(self):
  with self.assertRaises(KeyboardInterrupt):self.start(run=self.interrupt)
  m.save(self.out/'inventory-attempt-0001/receipt.json',{'source_url':m.URL,'blocked':[]});m.save(self.out/'inventory-attempt-0001/network-events.json',[{'status':429}])
  with self.assertRaisesRegex(ValueError,'refusal retained'):self.start(True)
  self.assertEqual(self.called,1)
 def test_retained_native_error_before_retry(self):
  with self.assertRaises(KeyboardInterrupt):self.start(run=self.interrupt)
  m.save(self.out/'inventory-attempt-0001/receipt.json',{'source_url':m.URL,'error':{'message':'unprofiled shape'}})
  with self.assertRaisesRegex(ValueError,'failed or stopped'):self.start(True)
 def test_host_stop_before_browser(self):
  key=hashlib.sha256(b'www.codepublishing.com').hexdigest()[:20];m.save(self.gate/key/'state.json',{'stop':{'status':429}})
  with self.assertRaisesRegex(ValueError,'host stop'):self.start()
  self.assertEqual(self.called,0)
 def test_completed_generation_not_reacquired(self):
  self.start();before=m.digest_tree(self.out/'inventory-origin');self.start(True);self.assertEqual(before,m.digest_tree(self.out/'inventory-origin'));self.assertEqual(self.called,1)
 def test_selected_mutation_refused(self):
  self.start();(self.out/'inventory-origin/raw.bin').write_bytes(b'changed')
  with self.assertRaisesRegex(ValueError,'Selected native inventory generation changed'):self.start(True)
 def test_preexisting_unmarked_source_refused(self):
  (self.out/'partial.bin').write_bytes(b'legacy')
  with self.assertRaisesRegex(ValueError,'Fresh native'):self.start()
  self.assertEqual(self.called,0)
 def interrupted_snapshot(self,path,raw):
  self.real_atomic(path,raw)
  if Path(path).parent.name.startswith('.code-snapshot-attempt-'):
   self.assertTrue((self.out/m.NAME).exists());raise KeyboardInterrupt()
 def test_snapshot_interruption_has_prior_marker_and_preserves_generation(self):
  self.real_atomic=m.transport.atomic
  with patch.object(m.transport,'atomic',self.interrupted_snapshot):
   with self.assertRaises(KeyboardInterrupt):self.start()
  generation=self.out/'.code-snapshot-attempt-0001';before=m.digest_tree(generation);self.assertEqual(self.called,0);self.start(True);state=m.load(self.out/m.NAME);self.assertEqual(state['snapshot_attempts'][0]['status'],'interrupted_preserved');self.assertEqual(before,m.digest_tree(generation));self.assertEqual(self.called,1)
 def test_completed_code_snapshot_corruption_refused(self):
  self.start();(self.out/'executed-acquisition'/self.files[0]).write_bytes(b'changed code')
  with self.assertRaisesRegex(ValueError,'snapshot corrupt'):self.start(True)
  self.assertEqual(self.called,1)
 def test_preserved_code_generation_mutation_refused(self):
  self.real_atomic=m.transport.atomic
  with patch.object(m.transport,'atomic',self.interrupted_snapshot):
   with self.assertRaises(KeyboardInterrupt):self.start()
   with self.assertRaises(KeyboardInterrupt):self.start(True)
  (self.out/'.code-snapshot-attempt-0001'/self.files[0]).write_bytes(b'changed interrupted generation')
  with self.assertRaisesRegex(ValueError,'snapshot generation changed'):self.start(True)
  self.assertEqual(self.called,0)
 def test_interrupt_before_native_directory_preserves_absence(self):
  def before_dir(out):self.called+=1;raise KeyboardInterrupt()
  with self.assertRaises(KeyboardInterrupt):self.start(run=before_dir)
  self.assertFalse((self.out/'inventory-attempt-0001').exists());self.start(True);self.start(True);s=m.load(self.out/m.NAME);self.assertFalse(s['attempts'][0]['directory_exists']);self.assertEqual(s['attempts'][0]['manifest'],{});self.assertEqual(self.called,2)
 def test_no_receipt_retained429_ledger_refuses_before_restart(self):
  with self.assertRaises(KeyboardInterrupt):self.start(run=self.interrupt)
  m.save(self.out/'inventory-attempt-0001/network-events.json',[{'status':429}])
  self.assertFalse((self.out/'inventory-attempt-0001/receipt.json').exists())
  with self.assertRaisesRegex(ValueError,'refusal retained'):self.start(True)
  self.assertEqual(self.called,1)
 def test_no_receipt_retained_headerless_challenge_refuses_before_restart(self):
  with self.assertRaises(KeyboardInterrupt):self.start(run=self.interrupt)
  folder=self.out/'inventory-attempt-0001';raw=b'<html><title>Just a moment...</title></html>';(folder/'challenge.bin').write_bytes(raw);m.save(folder/'network-bodies.json',[{'status':200,'headers':{'content-type':'text/html'},'path':'challenge.bin','sha256':hashlib.sha256(raw).hexdigest()}])
  with self.assertRaisesRegex(ValueError,'challenge body'):self.start(True)
  self.assertEqual(self.called,1)
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(InitTests))
 unchanged=snapshot()==BEFORE
 if not unchanged:raise AssertionError('Tested initialization source changed')
 if options.receipt:
  output=options.receipt.resolve()
  if output.exists() or output==SOURCE or SOURCE in output.parents:raise FileExistsError('Fresh external QA receipt required')
  output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'schema':'originals-initialization-regressions-1','source':str(SOURCE),'source_sha256':BEFORE,'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'tests':result.testsRun,'errors':len(result.errors),'failures':len(result.failures),'passed':result.wasSuccessful(),'source_unchanged':unchanged,'publisher_requests':0,'browser_network_startup_blocked':True,'scope':'Bounded native/code generation, exactrevision, missingreceipt accessstop/challenge and corruption controls. Actual SIGINT/source/body proof retained separately; no newlive claim.'},indent=2)+'\n')
 sys.exit(0 if result.wasSuccessful() else 1)
