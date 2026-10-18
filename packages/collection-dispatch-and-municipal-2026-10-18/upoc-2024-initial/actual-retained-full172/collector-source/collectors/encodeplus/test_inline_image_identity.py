"""Source-reference metadata only: no source-name heuristic or image access."""
import copy,unittest
from types import SimpleNamespace
from .pdf_structure import image_source_name
class InlineImageIdentity(unittest.TestCase):
 def test_process_allocated_inline_names_are_not_source_identifiers(self):
  for allocated in ['4409951824','9999999999','Im0']:
   image={'name':allocated,'stream':SimpleNamespace(objid=None),'x0':2,'top':3,'x1':4,'bottom':5};before={k:v for k,v in image.items()if k!='stream'};self.assertIsNone(image_source_name(image));self.assertEqual(before,{k:v for k,v in image.items()if k!='stream'})
 def test_named_indirect_resource_preserved_even_numeric_name(self):
  for name in ['Im0','NamedMap','4409951824']:
   class MetadataOnly:
    objid=152
    def get_data(self):raise AssertionError('Image bytes forbidden')
   self.assertEqual(image_source_name({'name':name,'stream':MetadataOnly()}),name)
if __name__=='__main__':unittest.main(verbosity=2)
