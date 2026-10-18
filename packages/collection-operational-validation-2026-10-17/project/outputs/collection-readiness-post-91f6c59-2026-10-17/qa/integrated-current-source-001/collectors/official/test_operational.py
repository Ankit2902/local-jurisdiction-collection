"""Exact label/anchor reconciliation and operational retained-source fault tests."""
import contextlib,copy,io,json,pathlib,shutil,tempfile,unittest
from unittest.mock import patch
from bs4 import BeautifulSoup
import collect,model,publication_refs,replay,transport,verify
LABEL_RULE={'selector':'span.ae-compliance-indent','exact_text':' PDF','exact_attributes':{'class':['ae-compliance-indent'],'style':'display:none;'}}
ROOT='https://fixture.invalid/code/'
class Operational(unittest.TestCase):
 def test_exact_accessibility_label_only_not_legal_or_other_hidden_text(self):
  c={'inventory_label_exclusions':[LABEL_RULE]};a=BeautifulSoup('<a>Chapter 01 - General Provisions<span class="ae-compliance-indent" style="display:none;"> PDF</span></a>','html.parser').a
  self.assertEqual(collect.inventory_label(a,c),'Chapter 01 - General Provisions');self.assertIn(' PDF',str(a))
  for source in ['<a>Chapter PDF</a>','<a>Chapter<span class="ae-compliance-indent"> PDF</span></a>','<a>Chapter<span class="ae-compliance-indent" style="display:none;"> Mandatory legal caption</span></a>']:
   self.assertEqual(collect.inventory_label(BeautifulSoup(source,'html.parser').a,c),' '.join(BeautifulSoup(source,'html.parser').a.get_text(' ',strip=True).split()))
 def test_label_projection_preserves_changed_links_and_legal_labels(self):
  c={'source_url':ROOT,'inventory_selector':'a[href]','mode':'pdf_set','inventory_label_exclusions':[LABEL_RULE]};a=b'<a href="one.pdf">Chapter1<span class="ae-compliance-indent" style="display:none;"> PDF</span></a>';b=b'<a href="one.pdf">Chapter1</a>'
  self.assertEqual(collect.inventory_projection(a,c),collect.inventory_projection(b,c));self.assertNotEqual(collect.inventory_projection(a,c),collect.inventory_projection(b.replace(b'one.pdf',b'two.pdf'),c));self.assertNotEqual(collect.inventory_projection(a,c),collect.inventory_projection(b.replace(b'Chapter1',b'Chapter2'),c))
 def router(self):return {'source_url':ROOT,'mode':'legacy_codepublishing','resolve_internal_router_references':True,'content_selector':'#mainContent'}
 def document(self,body):
  data=('<main id="mainContent">'+body+'</main>').encode();url=ROOT+'#!/Title/Chapter.html';return {url:{'id':url,'url':url,'data':data,'raw_ref':'raw/a.bin','raw_sha256':model.sha(data),'record_ids':['source-section']}}
 def test_internal_router_exact_scope_and_no_shell_acquisition(self):
  c=self.router();url=ROOT+'#!/Title/Chapter.html#1';self.assertEqual(publication_refs.router_target(url,c)['source_anchor'],'1');a=model.classify_asset({'url':url,'context':'Appendix incorporated by reference'},c);self.assertTrue(a['required']);self.assertEqual(a['status'],'pending_internal_reference')
  for bad in ['https://other.invalid/code/#!/Title/Chapter.html#1',ROOT+'#!/../Chapter.html#1',ROOT+'#!/Title/Chapter.pdf#1',ROOT+'#!/Title/Chapter.html']:self.assertIsNone(publication_refs.router_target(bad,c))
 def test_anchor_alias_ancestry_missing_duplicate_and_hash_faults(self):
  c=self.router();asset={'url':ROOT+'#!/Title/Chapter.html#1','required':True};docs=self.document('<h3 id="1"><a name="1">1</a> Legal heading.</h3><p>Operative body.</p>');result=publication_refs.resolve([asset],docs,c)[0];self.assertEqual(result['status'],'retained_internal_reference');self.assertEqual(result['internal_reference']['exclusive_source_target_count'],1);self.assertFalse(result['requires_manual_review'])
  for body in ['<h3 id="2">Different anchor</h3>','<h3 id="1">First</h3><h3 id="1">Second</h3>']:self.assertEqual(publication_refs.resolve([asset],self.document(body),c)[0]['status'],'unresolved')
  self.assertEqual(publication_refs.resolve([asset],{},c)[0]['status'],'unresolved');next(iter(docs.values()))['raw_sha256']='0'*64
  with self.assertRaisesRegex(ValueError,'hash mismatch'):publication_refs.resolve([asset],docs,c)
 def source(self,root):
  config={'schema':1,'id':'retained-fixture','mode':'html_graph','source_url':ROOT,'jurisdiction':'Fixture','state':'ZZ','publication':'Whole fixture publication','inventory_selector':'main a[href]','include_url_regex':r'/[ab]\.html$','content_selector':'main','traverse_selector':'main a[href]','legal_marker_regex':'Operative rule','coverage_level':'publication_text'};cf=root/'config.json';collect.save(cf,config)
  sources={ROOT:b'<main><a href="a.html">A</a><a href="b.html">B</a></main>'}
  for name in ['a','b']:sources[ROOT+name+'.html']=('<main><h1>Operative rule '+name+'</h1><p>Every applicant shall comply with this complete legal body and retain the mandatory source caption.</p></main>').encode()
  def fetch(url,max_bytes=0):
   data=sources[url];return data,{'url':url,'status':200,'headers':{},'sha256':model.sha(data),'transport':'Synthetic network fixture, no actual network'}
  old=root/'old'
  with patch.object(transport,'fetch',fetch),contextlib.redirect_stdout(io.StringIO()):self.assertEqual(collect.collect(cf,old),0)
  return cf,old
 def test_operational_replay_resume_no_network_and_current_verifier(self):
  with tempfile.TemporaryDirectory()as td:
   root=pathlib.Path(td);cf,old=self.source(root)
   with patch.object(transport,'fetch',side_effect=AssertionError('NO NETWORK')),contextlib.redirect_stdout(io.StringIO()):
    full=root/'full';self.assertEqual(replay.run(cf,full,old),0);self.assertTrue(verify.verify(full)['requested_coverage_complete'])
    part=root/'part';self.assertEqual(replay.run(cf,part,old,interrupt_after=1),3);self.assertEqual(replay.run(cf,part,resume=True),0);self.assertEqual((full/'records.jsonl').read_bytes(),(part/'records.jsonl').read_bytes());verify.verify(part)
   self.assertEqual((old/'records.jsonl').read_bytes(),(full/'records.jsonl').read_bytes())
 def test_operational_replay_rejects_wrong_identity_corruption_and_partial_source(self):
  with tempfile.TemporaryDirectory()as td:
   root=pathlib.Path(td);cf,old=self.source(root);wrong=collect.load(cf);wrong['publication']='Another publication';wf=root/'wrong.json';collect.save(wf,wrong)
   with self.assertRaisesRegex(ValueError,'config differs'):replay.run(wf,root/'bad',old)
   state=collect.load(old/'checkpoint.json');raw=old/state['items'][0]['raw_ref'];raw.write_bytes(raw.read_bytes()+b'corruption')
   with self.assertRaisesRegex(ValueError,'corrupt'):replay.run(cf,root/'corrupt',old)
   state['completed']=False;collect.save(old/'checkpoint.json',state)
   with self.assertRaisesRegex(ValueError,'terminal full acquired'):replay.run(cf,root/'partial',old)
if __name__=='__main__':unittest.main(verbosity=2)
