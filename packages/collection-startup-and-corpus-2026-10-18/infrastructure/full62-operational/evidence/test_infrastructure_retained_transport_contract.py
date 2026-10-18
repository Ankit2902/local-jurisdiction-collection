import importlib.util,json,pathlib,sys,tempfile,unittest
BASE=pathlib.Path(__file__).resolve().parent
RUNTIME=BASE/'infrastructure-full62-final-runtime-v3'
sys.path.insert(0,str(RUNTIME))
spec=importlib.util.spec_from_file_location('driver',RUNTIME/'retained_native.py');driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
from collectors.encodeplus.collect import entry
from collectors.encodeplus.util import validate_file
class ExactCachedContract(unittest.TestCase):
 def test_actual_source_relative_entry_and_validator(self):
  source=BASE.parent.parent/'collection-readiness-2026-10-17/encodeplus/native-82-0c6b3dc40877-final-live';cfg=json.loads((RUNTIME/'collectors/encodeplus/configs/native-82-0c6b3dc40877.json').read_text());adapter=driver.RetainedTransport(source,cfg)
  with tempfile.TemporaryDirectory()as d:
   out=pathlib.Path(d)
   for name in ['start','end']:
    rel='raw/'+name+'.pdf';data,meta=adapter(out,cfg['url'],rel);e=entry(rel,meta);self.assertEqual(e['path'],rel);self.assertEqual(e['url'],cfg['url']);self.assertEqual(validate_file(out,e['path'],e['sha256']).read_bytes(),data);self.assertEqual((out/(rel+'.receipt.json')).read_bytes(),(source/(rel+'.receipt.json')).read_bytes())
if __name__=='__main__':unittest.main()
