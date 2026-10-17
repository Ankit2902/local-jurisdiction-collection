"""Synthetic production collection must never request its known image asset."""
import contextlib,io,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'collectors/american-legal'));import collect,test_faults
from verify import verify
class Tests(unittest.TestCase):
 def test_known_image_not_requested_and_placeholder_preserved(self):
  with tempfile.TemporaryDirectory() as td:
   out=Path(td)/'run';test_faults.FakeBrowser.interrupt_after=None
   with patch.object(collect,'Browser',test_faults.FakeBrowser),contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):self.assertEqual(collect.run(test_faults.args(out)),0)
   self.assertFalse(any('.png' in (url or '') for op,url in test_faults.FakeBrowser.calls));self.assertTrue(verify(out)['publication_complete']);data=(out/'sections.jsonl').read_text();self.assertIn('[IMAGE]',data);self.assertNotIn('<img',data)
if __name__=='__main__':unittest.main(verbosity=2)
