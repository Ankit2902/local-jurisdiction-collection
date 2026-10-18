"""Operational method qualification: synthetic whole inventories, not live-source claims."""
import contextlib,copy,io,json,sys,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from profile import load_config,parse_config
from source_common import load,save,sha
import shared_transport as transport
import cli,workflow,king_acquire
ROOT=Path(__file__).resolve().parents[1]

def sources(parent):
 html=parent/'synthetic-html';native=parent/'synthetic-word';html.mkdir();native.mkdir();rows=[]
 for i in range(1,11):
  u=king_acquire.PREFIX+f'{i}_Title_{i}.htm';rows.append(f'<h3><a href="{u}">Title {i}: Test</a></h3><p>(Updated: 10/17/2026) <a href="{u[:-4]}.docx">Word</a></p>')
 index=('<html><title>King County Code</title><body><main>'+''.join(rows)+'</main></body></html>').encode();docs=king_acquire.inventory(index)
 for target,role in [(html,'content'),(native,'native-word')]:
  artifacts=[]
  def add(role,url,data,doc=None):
   n=len(artifacts);rel=f'raw/{n:03d}.bin';(target/rel).parent.mkdir(exist_ok=True);(target/rel).write_bytes(data);a={'role':role,'source_url':url,'final_url':url,'path':rel,'status':200,'sha256':sha(data),'bytes':len(data),'started_at':f'2026-10-17T12:00:{n*2:02d}+00:00','finished_at':f'2026-10-17T12:00:{n*2+1:02d}+00:00'}
   if doc:a['document_id']=doc['id']
   artifacts.append(a)
  add('index-start',king_acquire.URL,index)
  for i,d in enumerate(docs,1):
   if role=='content':raw=f'<html><body><p>Title {i}</p><p>UPDATED: October 17, 2026</p><p><b>{i}.01.010 Test.</b> Operative body.</p></body></html>'.encode();url=d['url']
   else:
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w') as z:
     z.writestr('[Content_Types].xml','<Types/>');z.writestr('word/_rels/document.xml.rels','<Relationships/>');z.writestr('word/document.xml',f'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Title {i}</w:t></w:r></w:p><w:p><w:r><w:t>UPDATED: October 17, 2026</w:t></w:r></w:p><w:p><w:r><w:t>{i}.01.010 Test. Operative body.</w:t></w:r></w:p></w:body></w:document>')
    raw=buf.getvalue();url=d['native_alternatives'][0]['url']
   add(role,url,raw,d if role=='native-word' else None)
  add('index-end',king_acquire.URL,index);save(target/'checkpoint.json',{'source_url':king_acquire.URL,'inventory':docs,'artifacts':artifacts,'errors':[],'opening_closing_inventory_equal':True,'synthetic_fixture':True})
 return html,native

class Operational(unittest.TestCase):
 def setUp(self):self.king=load_config(ROOT/'configs/king-county.json');self.flag=load_config(ROOT/'configs/flagstaff.json')
 def test_typed_roundtrip(self):self.assertEqual(parse_config(self.king.binding()),self.king);self.assertEqual(self.king.binding()['required_formats'],['html','word'])
 def test_foreign_government_rejected(self):
  value=self.king.binding();value['jurisdiction']='Another County'
  with self.assertRaisesRegex(ValueError,'identity'):parse_config(value)
 def test_foreign_host_rejected(self):
  value=self.flag.binding();value['source_url']='https://example.invalid/Flagstaff/'
  with self.assertRaisesRegex(ValueError,'identity'):parse_config(value)
 def test_unqualified_profile_rejected(self):
  value=self.flag.binding();value['profile']='generic_html'
  with self.assertRaisesRegex(ValueError,'profile'):parse_config(value)
 def test_king_word_cannot_be_omitted(self):
  value=self.king.binding();value['required_formats']=['html']
  with self.assertRaisesRegex(ValueError,'formats'):parse_config(value)
 def test_untyped_extra_field_rejected(self):
  value=self.flag.binding();value['ignore_edition']=True
  with self.assertRaisesRegex(ValueError,'fields'):parse_config(value)
 def test_flagstaff_word_format_unsupported(self):
  with self.assertRaisesRegex(ValueError,'HTML only'):self.flag.family('word')
 def test_replay_actual_methods_zero_network_and_complete_resume(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(transport,'fetch',side_effect=AssertionError('network forbidden')):
   root=Path(tmp);html,word=sources(root);out=root/'job';r=workflow.replay(self.king,html,out,word);self.assertTrue(r['complete']);self.assertTrue(r['full_raw_replay_equal']);self.assertEqual(r['publisher_requests'],0);self.assertEqual(load(out/'checkpoint.json')['config'],self.king.binding());before=sha((out/'normalized/records.jsonl').read_bytes());r=workflow.replay(self.king,html,out,word,resume=True);self.assertTrue(r['complete']);self.assertEqual(before,sha((out/'normalized/records.jsonl').read_bytes()));self.assertTrue(cli.verify(self.king,out=out)['complete'])
 def test_replay_requires_all_native_sources_before_output(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);html,word=sources(root)
   with self.assertRaisesRegex(ValueError,'native-source'):workflow.replay(self.king,html,root/'job')
   self.assertFalse((root/'job').exists())
 def test_interruption_resume_reuses_terminal_html_and_preserves_partial_generation(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(transport,'fetch',side_effect=AssertionError('network forbidden')):
   root=Path(tmp);html,word=sources(root);out=root/'job';real=cli.normalize
   def interrupt(cfg,format,source,dest):
    if format=='word':dest.mkdir();(dest/'partial.txt').write_text('interrupted');raise KeyboardInterrupt('synthetic durable interruption')
    return real(cfg,format,source,dest)
   with patch.object(cli,'normalize',side_effect=interrupt):
    with self.assertRaises(KeyboardInterrupt):workflow.replay(self.king,html,out,word)
   before=sha((out/'normalized/records.jsonl').read_bytes());r=workflow.replay(self.king,html,out,word,resume=True);self.assertTrue(r['complete']);self.assertEqual(before,sha((out/'normalized/records.jsonl').read_bytes()));self.assertEqual((out/'.normalization-attempt-word-0001/partial.txt').read_text(),'interrupted')
 def test_resume_code_drift_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);html,word=sources(root);out=root/'job';workflow.replay(self.king,html,out,word)
   state=load(out/'checkpoint.json');state['code_fingerprint']['cli.py']='changed';save(out/'checkpoint.json',state)
   with self.assertRaisesRegex(ValueError,'drift'):workflow.replay(self.king,html,out,word,resume=True)
 def test_copied_source_corruption_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);html,word=sources(root);out=root/'job';workflow.replay(self.king,html,out,word);state=load(out/'html-source/checkpoint.json');a=next(a for a in state['artifacts'] if a['role']=='content');(out/'html-source'/a['path']).write_bytes(b'corrupt')
   with self.assertRaisesRegex(ValueError,'corrupt'):cli.verify(self.king,out=out)
 def test_coverage_is_recomputed_not_trusted(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);html,word=sources(root);out=root/'job';workflow.replay(self.king,html,out,word);state=load(out/'coverage.json');state['attachments_complete']=False;save(out/'coverage.json',state)
   with self.assertRaisesRegex(ValueError,'coverage differs'):cli.verify(self.king,out=out)
 def test_wrong_config_checkpoint_rejected_before_parser(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);html,word=sources(root);out=root/'job';workflow.replay(self.king,html,out,word)
   with patch('verify.verify',side_effect=AssertionError('parser should not start')):
    with self.assertRaisesRegex(ValueError,'binding'):cli.verify(self.flag,out=out)
 def test_cli_replay_and_verify_use_same_complete_root(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(transport,'fetch',side_effect=AssertionError('network forbidden')),contextlib.redirect_stdout(io.StringIO()):
   root=Path(tmp);html,word=sources(root);out=root/'job';cfg=str(ROOT/'configs/king-county.json');self.assertEqual(cli.main(['replay','--config',cfg,'--source',str(html),'--native-source',str(word),'--out',str(out)]),0);self.assertEqual(cli.main(['verify','--config',cfg,'--out',str(out)]),0)
 def test_live_wrapper_wiring_and_readonly_verify_with_explicit_mock_acquisition(self):
  import shutil
  with tempfile.TemporaryDirectory() as tmp,patch.object(transport,'fetch',side_effect=AssertionError('network forbidden')),contextlib.redirect_stdout(io.StringIO()):
   root=Path(tmp);html,word=sources(root);out=root/'job'
   def capture(source,destination=None,**kwargs):
    if destination is None:destination=source;source=html
    shutil.copytree(word if str(source).endswith('html-source') else source,destination);return load(Path(destination)/'checkpoint.json')
   with patch('king_acquire.collect',side_effect=lambda destination,**kw:capture(html,destination)),patch('king_native.run',side_effect=lambda source,destination,**kw:capture(word,destination)):
    self.assertEqual(cli.main(['collect','--config',str(ROOT/'configs/king-county.json'),'--out',str(out)]),0)
   self.assertEqual(load(out/'checkpoint.json')['acquisition_mode'],'live');self.assertEqual(cli.main(['verify','--config',str(ROOT/'configs/king-county.json'),'--out',str(out)]),0)
 def test_source_acquisition_failure_has_explicit_false_coverage(self):
  with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()),patch('king_acquire.collect',return_value={'errors':['retained403stop']}):
   out=Path(tmp)/'job';self.assertEqual(cli.main(['collect','--config',str(ROOT/'configs/king-county.json'),'--out',str(out)]),2);coverage=load(out/'coverage.json');self.assertFalse(coverage['publication_accepted']);self.assertFalse(coverage['publication_text_complete']);self.assertIn('retained403stop',coverage['errors'])
 def test_preflight_refusal_before_browser_or_transport(self):
  with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()),patch('doctor.run',return_value={'ready_to_attempt_collection':False}),patch.object(transport,'fetch',side_effect=AssertionError('network forbidden')):
   out=Path(tmp)/'job';self.assertEqual(cli.main(['collect','--config',str(ROOT/'configs/flagstaff.json'),'--out',str(out)]),1);self.assertFalse(out.exists())
if __name__=='__main__':unittest.main()
