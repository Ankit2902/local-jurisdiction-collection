#!/usr/bin/env python3
"""Network-free tests of fresh-directory operator reuse and fail-closed state."""
import hashlib,json,socket,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
from resume_copy import prepare
from verify import verify

class ResumeCopyTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name);self.source=self.base/'source'
  with zipfile.ZipFile(Path(__file__).with_name('fixtures')/'live-index.zip') as z:z.extractall(self.source)
  self.before=self.hashes(self.source)
 def tearDown(self):self.tmp.cleanup()
 def hashes(self,p):return {str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in p.rglob('*') if f.is_file()}
 def change(self,name,fn):
  p=self.source/name;j=json.loads(p.read_text());fn(j);p.write_text(json.dumps(j))
 def test_fresh_copy_preserves_original_raw_and_history_and_requires_execution(self):
  with patch.object(socket.socket,'connect',side_effect=AssertionError('No network')),patch('PIL.Image.open',side_effect=AssertionError('No image decoding')):command=prepare(self.source,self.base/'copy')
  out=self.base/'copy';self.assertEqual(self.hashes(self.source),self.before)
  original=json.loads((out/'operator-origin/run.json').read_text());current=json.loads((out/'run.json').read_text())
  self.assertEqual(original,json.loads((self.source/'run.json').read_text()));self.assertEqual(current['executions'],original['executions']);self.assertEqual(current['status'],'operator-prepared');self.assertIn('--resume',command)
  for item in json.loads((out/'requests.json').read_text()).values():self.assertEqual((out/item['file']).read_bytes(),(self.source/item['file']).read_bytes())
  with self.assertRaisesRegex(AssertionError,'not a complete terminal'):verify(out)
 def test_corrupt_original_raw_rejected_before_clone(self):
  e=next(iter(json.loads((self.source/'requests.json').read_text()).values()));(self.source/e['file']).write_bytes(b'corrupt')
  with self.assertRaisesRegex(AssertionError,'Corrupt source raw'):prepare(self.source,self.base/'copy')
  self.assertFalse((self.base/'copy').exists())
 def test_unsafe_original_raw_path_rejected_before_clone(self):
  self.change('requests.json',lambda j:next(iter(j.values())).update(file='../outside'))
  with self.assertRaisesRegex(AssertionError,'Unsafe retained source path'):prepare(self.source,self.base/'copy')
 def test_superseded_image_policy_rejected_without_decode(self):
  self.change('run.json',lambda j:j.update(image_policy='old-image-download-policy'))
  with patch('PIL.Image.open',side_effect=AssertionError('Decoder must not run')):
   with self.assertRaisesRegex(AssertionError,'Image policy differs'):prepare(self.source,self.base/'copy')
 def test_nonimage_asset_upgrade_only_strengthens_in_fresh_copy(self):
  prepare(self.source,self.base/'copy',upgrade_assets=True);m=json.loads((self.base/'copy/run.json').read_text());self.assertEqual(m['assets_policy'],'download');self.assertEqual(self.hashes(self.source),self.before);self.assertEqual(m['image_policy'],'literal-[IMAGE]-no-image-fetch-v1')
 def test_existing_output_and_source_descendant_rejected(self):
  out=self.base/'copy';out.mkdir()
  with self.assertRaisesRegex(AssertionError,'fresh --out'):prepare(self.source,out)
  with self.assertRaisesRegex(AssertionError,'outside original source'):prepare(self.source,self.source/'child')

if __name__=='__main__':unittest.main(verbosity=2)
