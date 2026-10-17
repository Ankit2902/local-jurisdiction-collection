"""Independent Notes source-field/image/attachment probes through full reconciliation."""
import copy,json,tempfile,unittest
from pathlib import Path
from test_municode_edges import fixture,m
PIXELS='Tk9URV9JTkxJTkVfSU1BR0VfUEFZTE9BRF9GT1JCSURERU4='
class MunicodeNotes(unittest.TestCase):
 def parse(self,notes):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);cp=fixture(root);entry=cp['units']['content'];receipt=json.loads((root/entry['receipt']).read_text());raw=json.loads((root/receipt['body_file']).read_text());raw['Docs'][1]['Notes']=copy.deepcopy(notes);data=json.dumps(raw).encode();(root/receipt['body_file']).write_bytes(data);receipt['sha256']=m.sha(data);entry['sha256']=receipt['sha256'];(root/entry['receipt']).write_text(json.dumps(receipt));records,report=m.reconcile_publication(root,cp,1);return next(r for r in records if r['node_id']=='S1'),report
 def test_nested_notes_images_have_placeholders_no_active_html_or_payload(self):
  notes=[{'NoteContent':'<p>Operative note<img src="data:image/png;base64,'+PIXELS+'"></p>','nested':[{'Html':'<img src="a.png" alt="data:image/png;base64,'+PIXELS+'">'}]}];r,c=self.parse(notes);encoded=json.dumps(r);self.assertNotIn(PIXELS,encoded);self.assertNotIn('data:image/',encoded.lower());self.assertNotIn('<img',encoded.lower());self.assertIn('[IMAGE]',encoded);self.assertTrue(r['notes_source_sha256']);self.assertTrue(c['publication_text_complete'])
 def test_notes_table_background_and_nonimage_incorporation(self):
  notes={'NoteContent':'<table><tr><td background="map.png">Map note</td></tr></table><p>Adopted <a href="https://example.invalid/required.pdf">Required Appendix</a></p>'};r,c=self.parse(notes);self.assertIn('[IMAGE]',json.dumps(r['notes']));self.assertNotIn('background=',json.dumps(r['notes']));self.assertFalse(c['publication_attachments_complete']);self.assertFalse(c['publication_complete'])
 def test_plain_typed_notes_preserved_without_reinterpreting_metadata(self):
  notes={'Page':1,'Flag':False,'Absent':None,'Text':'Legitimate legal note. The map is available as map.png'};r,c=self.parse(notes);self.assertEqual(r['notes'],notes);self.assertTrue(c['publication_complete'])
if __name__=='__main__':unittest.main(verbosity=2)
