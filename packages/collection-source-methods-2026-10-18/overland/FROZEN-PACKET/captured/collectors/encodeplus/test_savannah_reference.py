import copy,json,unittest
from pathlib import Path
from unittest.mock import patch,PropertyMock
from pypdf import PageObject
import pypdfium2 as pdfium
from .publication_references import reconcile,qualify_bound_document
from .savannah_reference import ALTERNATIVE as Q
HERE=Path(__file__).resolve().parent/'fixtures/savannah-adopted-reference'
class SavannahReference(unittest.TestCase):
 def rows(self):return {'6459':json.loads((HERE/'owner.json').read_text())}
 def cfg(self):return json.loads((HERE/'config.json').read_text())
 def test_actual_adopted_native_and_exact_owner_qualify_without_image_or_network(self):
  def forbidden(*a,**k):raise AssertionError('No image/network/render/object APIs')
  with patch('socket.socket',side_effect=forbidden),patch.object(PageObject,'images',new_callable=PropertyMock,side_effect=forbidden),patch.object(pdfium.PdfPage,'render',side_effect=forbidden),patch.object(pdfium.PdfPage,'get_objects',side_effect=forbidden),patch.object(pdfium.PdfImage,'extract',side_effect=forbidden):
   before=self.rows();rows=reconcile(copy.deepcopy(before),self.cfg());a=rows['6459']['assets'][0];self.assertEqual(a['url'],Q['url']);self.assertEqual(a['original_source_url'],Q['original_url']);self.assertEqual(rows['6459']['links'],before['6459']['links']);self.assertEqual(qualify_bound_document(rows,Q['url'],(HERE/'adopted-2018-04-12-3.pdf').read_bytes()),Q)
 def test_wrong_scope_owner_body_raw_identity_and_label_fail_closed(self):
  for key in Q['owner']:
   rows=self.rows();rows['6459'][key]='wrong';self.assertEqual(reconcile(copy.deepcopy(rows),self.cfg()),rows,key)
  for field in ['base','identity','jurisdiction','scope']:
   cfg=self.cfg();cfg[field]='changed';rows=self.rows();self.assertEqual(reconcile(copy.deepcopy(rows),cfg),rows,field)
  for field in ['text','attributes']:
   rows=self.rows();rows['6459']['links'][0][field]='changed' if field=='text' else {'href':'doclibrary.aspx?id=other'};self.assertEqual(reconcile(copy.deepcopy(rows),self.cfg()),rows,field)
 def test_wrong_native_hash_and_changed_binding_refuse(self):
  rows=reconcile(self.rows(),self.cfg());data=(HERE/'adopted-2018-04-12-3.pdf').read_bytes()
  with self.assertRaises(ValueError):qualify_bound_document(rows,Q['url'],data+b'changed')
  rows['6459']['assets'][0]['source_qualified_alternative']['identity']='different edition'
  with self.assertRaises(ValueError):qualify_bound_document(rows,Q['url'],data)
if __name__=='__main__':unittest.main()
