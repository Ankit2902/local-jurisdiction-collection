import copy,json,unittest,tempfile,shutil
from pathlib import Path
from unittest.mock import patch,PropertyMock
from pypdf import PageObject
import pypdfium2 as pdfium
from . import savannah_empty_qualification as subject
FIXTURE=Path(__file__).resolve().parent/'fixtures/savannah-source-empty6451'
class SavannahEmpty(unittest.TestCase):
 def rows(self):return {'6451':json.loads((FIXTURE/'full-source-record.json').read_text())}
 def cfg(self):return json.loads((FIXTURE/'config.json').read_text())
 def test_actual_full_owned_node_and_selected_native_qualify_without_images_or_network(self):
  def forbidden(*a,**k):raise AssertionError('No network/image/render/object APIs')
  before=self.rows()
  with patch('socket.socket',side_effect=forbidden),patch.object(PageObject,'images',new_callable=PropertyMock,side_effect=forbidden),patch.object(pdfium.PdfPage,'render',side_effect=forbidden),patch.object(pdfium.PdfPage,'get_objects',side_effect=forbidden),patch.object(pdfium.PdfImage,'get_bitmap',side_effect=forbidden),patch.object(pdfium.PdfImage,'extract',side_effect=forbidden):after=subject.qualify(copy.deepcopy(before),self.cfg())
  r=after['6451'];self.assertEqual(r['kind'],'confirmed_source_empty');self.assertEqual(r['text'],'');self.assertEqual({k for k in before['6451'] if before['6451'][k]!=r[k]},{'kind','disposition'});self.assertEqual(r['path'],before['6451']['path']);self.assertEqual(r['assets'],[]);self.assertEqual(r['image_refs'],[])
 def test_wrong_scope_body_raw_hierarchy_native_or_missing_fixture_keep_unresolved(self):
  for field in subject.QUALIFICATION['record']:
   rows=self.rows();rows['6451'][field]='changed';self.assertEqual(subject.qualify(copy.deepcopy(rows),self.cfg()),rows,field)
  cfg=self.cfg();cfg['identity']='different edition';rows=self.rows();self.assertEqual(subject.qualify(copy.deepcopy(rows),cfg),rows)
  with tempfile.TemporaryDirectory() as td:
   td=Path(td);dest=td/'fixtures/savannah-source-empty6451';shutil.copytree(FIXTURE,dest)
   with patch.object(subject,'HERE',td):
    p=dest/'native/attempt-0/publication.pdf';p.write_bytes(p.read_bytes()+b'changed');self.assertEqual(subject.qualify(copy.deepcopy(rows),self.cfg()),rows)
   shutil.rmtree(dest);shutil.copytree(FIXTURE,dest);(dest/'source-before.html').unlink()
   with patch.object(subject,'HERE',td):self.assertEqual(subject.qualify(copy.deepcopy(rows),self.cfg()),rows)
if __name__=='__main__':unittest.main()
