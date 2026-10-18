"""Known bounded PDF metadata must not retain unescaped SVG image payloads."""
import importlib.util,json,socket,unittest,sys,types
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
URI='data:image/svg+xml,<svg><text>VECTOR_SENTINEL</text></svg>'
def models():
 for family in ['official','encodeplus']:
  directory=ROOT/'collectors'/family;name='qa_svg_'+family;package=types.ModuleType(name);package.__path__=[str(directory)];sys.modules[name]=package
  path=directory/'pdf_structure.py';spec=importlib.util.spec_from_file_location(name+'.pdf_structure',path);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m
  prior=list(sys.path);old_helper=sys.modules.pop('bounded_decoder',None);sys.path.insert(0,str(directory))
  try:spec.loader.exec_module(m)
  finally:
   sys.path[:]=prior;sys.modules.pop('bounded_decoder',None)
   if old_helper is not None:sys.modules['bounded_decoder']=old_helper
  yield family,m
class PDFSVGMetadata(unittest.TestCase):
 def test_standalone_known_field_is_literal_placeholder(self):
  with patch.object(socket.socket,'connect',side_effect=AssertionError('NO_IMAGE_NETWORK')):
   for family,m in models():
    for value in [URI,'  '+URI.upper()]:
     with self.subTest(family=family,value=value):
      out=m.redact_metadata({'uri':value,'caption':'Separate legal caption stays.'});self.assertEqual(out['uri'],'[IMAGE]');self.assertEqual(out['caption'],'Separate legal caption stays.');self.assertNotIn('VECTOR_SENTINEL',json.dumps(out))
 def test_quoted_svg_preserves_prose_or_explicitly_refuses(self):
  for family,m in models():
   with self.subTest(family=family):
    try:out=m.redact_metadata('Before legal text "'+URI+'" after legal caption remains mandatory.')
    except ValueError:continue
    self.assertIn('Before legal text',out);self.assertIn('after legal caption remains mandatory.',out);self.assertNotIn('VECTOR_SENTINEL',out);self.assertNotIn('<svg',out);self.assertNotIn('data:image/',out.lower());self.assertIn('[IMAGE]',out)
 def test_separate_svg_roots_do_not_swallow_intervening_legal_text(self):
  for family,m in models():
   with self.subTest(family=family):
    for value in [URI+' mandatory legal caption.<svg></svg>','data:image/svg+xml,<svg/> mandatory legal caption.</svg>']:
     with self.assertRaises(ValueError):m.redact_metadata(value)
if __name__=='__main__':unittest.main(verbosity=2)
