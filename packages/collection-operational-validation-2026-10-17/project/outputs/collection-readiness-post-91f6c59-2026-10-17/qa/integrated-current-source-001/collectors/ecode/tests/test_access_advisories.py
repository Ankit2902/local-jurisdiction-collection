"""Acquisition-only shipped-advisory checks. No live publisher or browser requests."""
import contextlib,io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from collectors.ecode import cli
from collectors.ecode.common import read,digest,AccessStop,QualificationError
from collectors.ecode.engine import published_access_advisories,enforce_published_advisory,adopt,verify
from collectors.ecode.operator import doctor,import_bundle,inspect_download

class PublishedAdvisoryTests(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
 def tearDown(self):self.temp.cleanup()
 def test_raw_cli_fresh_home_absent_gate_never_starts_browser_or_network(self):
  catalog=Path(__file__).resolve().parents[2]/'registry/access-advisories.json';before=digest(catalog.read_bytes())
  for family,url in [('ecode360','https://ecode360.com/AL0934'),('municipal.codes','https://phoenix.municipal.codes/CC')]:
   with self.subTest(family=family):
    out=self.root/family;gate=self.root/('absent-'+family);stdout=io.StringIO()
    with patch('collectors.ecode.browser.Browser',side_effect=AssertionError('Browser startup forbidden')) as browser,patch('socket.socket',side_effect=AssertionError('Network forbidden')),patch('socket.create_connection',side_effect=AssertionError('Network forbidden')),patch('pathlib.Path.home',return_value=self.root/'fresh-home'),patch('sys.argv',['ecode','collect','--url',url,'--out',str(out),'--gate-dir',str(gate)]),contextlib.redirect_stdout(stdout):code=cli.main()
    result=json.loads(stdout.getvalue());self.assertEqual(code,1);self.assertEqual(result['error'],'AccessStop');self.assertIn('Shipped',result['message']);self.assertIn('operator review',result['message']);browser.assert_not_called();self.assertFalse(out.exists());self.assertFalse(gate.exists())
  self.assertEqual(digest(catalog.read_bytes()),before)
 def test_doctor_reports_shipped_stop_with_absent_home_gate(self):
  for family,url in [('ecode360','https://ecode360.com/AL0934'),('municipal.codes','https://phoenix.municipal.codes/CC')]:
   with patch('socket.socket',side_effect=AssertionError('No network')),patch('pathlib.Path.home',return_value=self.root/'fresh-home'):r=doctor(url,gate_dir=self.root/'absent')
   self.assertTrue(r['transport_gate_clear']);self.assertFalse(r['published_advisory_clear']);self.assertFalse(r['ready']);self.assertFalse(r['network_ready']);self.assertEqual(r['published_access_advisories'][0]['family'],family);self.assertFalse((self.root/'absent').exists())
 def test_missing_or_malformed_catalog_fails_closed(self):
  with patch('collectors.ecode.engine.read',side_effect=FileNotFoundError('SYNTHETIC absent package catalog')):
   with self.assertRaisesRegex(QualificationError,'catalog missing'):enforce_published_advisory('ecode360')
  with patch('collectors.ecode.engine.read',return_value={'schema_version':999,'advisories':[]}):
   with self.assertRaisesRegex(QualificationError,'Unsupported'):published_access_advisories('ecode360')
 def test_offline_replay_import_inspect_do_not_consult_advisory(self):
  pkg=Path(__file__).resolve().parents[1];fixtures=pkg/'fixtures'
  with patch('collectors.ecode.engine.published_access_advisories',side_effect=AssertionError('Offline tools must not consult acquisition advisory')),patch('collectors.ecode.browser.Browser',side_effect=AssertionError('No browser')):
   src=fixtures/'readiness-synthetic-ecode';adopt(src,self.root/'replay',read(src/'checkpoint.json')['config'],True);self.assertTrue(verify(self.root/'replay')['complete'])
   r=import_bundle(None,fixtures/'readiness-standalone-municipal/bundle.json',self.root/'standalone');self.assertTrue(r['complete'])
   r=inspect_download(fixtures/'readiness-native/albany/publisher-export-0.pdf',fixtures/'readiness-native/albany/source.html','https://ecode360.com/7678220',self.root/'native',None,['When effective']);self.assertTrue(r['native_file_qualified']);self.assertFalse(r['complete'])

if __name__=='__main__':unittest.main()
