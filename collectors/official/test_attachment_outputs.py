"""Actual native-PDF attachment output/owner/page fault checks, no network/pixels."""
import copy,json,pathlib,socket,tempfile,unittest
from unittest.mock import patch
import attachment_outputs,collect,model
from test_pdf_structure import native,text,CONFIG
class AttachmentOutputs(unittest.TestCase):
 def bundle(self,root):
  (root/'raw').mkdir();(root/'items').mkdir();url='https://fixture.invalid/actual.pdf';data=native(text(40,700,'Available actual native legal map label'));ref='raw/'+model.sha(('asset:'+url).encode())[:20]+'.bin';(root/ref).write_bytes(data);collect.save((root/ref).with_suffix('.receipt.json'),{'url':url,'request_name':'asset:'+url,'status':200,'sha256':model.sha(data)})
  source=b'<main>Appendix map is incorporated by reference.</main>';owner_ref='raw/owner.bin';(root/owner_ref).write_bytes(source);item={'id':'source','url':'https://fixture.invalid/code','kind':'html','raw_ref':owner_ref};record={'id':'source-section','document_id':'source','raw_sha256':model.sha(source),'assets':[{'url':url,'required':True,'kind':'a','source_attribute':'href'}]};collect.save(root/'items'/(model.sha(b'source')[:24]+'.json'),{'item':item,'raw_sha256':model.sha(source),'records':[record],'asset_downloads':[{'url':url,'status':'acquired','raw_ref':ref,'sha256':model.sha(data)}]})
  state={'items':[item],'completed':True};c=dict(CONFIG,native_label_attachment_rules=[{'url':url,'sha256':model.sha(data),'source_kind':'map'}]);return c,state
 def test_current_native_attachment_output_pages_owners_and_readonly_verification(self):
  with tempfile.TemporaryDirectory()as td:
   root=pathlib.Path(td);c,s=self.bundle(root)
   with patch.object(socket.socket,'connect',side_effect=AssertionError('NO IMAGE/NETWORK')):
    attachment_outputs.write(root,c,s);attachment_outputs.validate(root,c,s)
   summaries=attachment_outputs.summaries(root,c,s);q=summaries[0]['qualification'];self.assertTrue(q['native_label_projection_complete']);self.assertTrue(q['attachment_text_normalization_qualified']);self.assertFalse(q['semantic_complete']);self.assertEqual(q['required_by'][0]['owner_record_id'],'source-section');rows=[json.loads(line)for line in(root/'attachment-pages.jsonl').read_text().splitlines()];self.assertEqual(len(rows),1);self.assertIn('Available actual native legal map label',rows[0]['text']);before=(root/'attachment-pages.jsonl').read_bytes();attachment_outputs.validate(root,c,s);self.assertEqual((root/'attachment-pages.jsonl').read_bytes(),before)
 def test_native_attachment_source_owner_and_page_output_faults_fail(self):
  for fault in ['pagegap','owner','source','request']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory()as td:
    root=pathlib.Path(td);c,s=self.bundle(root);attachment_outputs.write(root,c,s)
    if fault=='pagegap':(root/'attachment-pages.jsonl').write_bytes(b'')
    elif fault=='owner':
     f=next((root/'items').glob('*.json'));d=collect.load(f);d['records'][0]['raw_sha256']='0'*64;collect.save(f,d)
    elif fault=='source':
     f=next(p for p in(root/'raw').glob('*.bin')if p.name!='owner.bin');f.write_bytes(f.read_bytes()+b'corrupt')
    else:
     f=next((root/'raw').glob('*.receipt.json'));d=collect.load(f);d['request_name']='asset:https://wrong.invalid/a.pdf';collect.save(f,d)
    with self.assertRaises((ValueError,FileNotFoundError)):attachment_outputs.validate(root,c,s)
if __name__=='__main__':unittest.main(verbosity=2)
