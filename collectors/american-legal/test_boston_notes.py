"""Source-bound Boston printed-label/source-anchor tests; no network or images."""
import copy,hashlib,importlib.util,json,pathlib,socket,sys,unittest
from unittest.mock import patch
from PIL import Image
import model,audit_native
HERE=pathlib.Path(__file__).resolve().parent;FIXTURE=HERE/'fixtures/boston-footnote-source-v1.json';F=json.loads(FIXTURE.read_text());HTML=F['source_group_html'];assert hashlib.sha256(HTML.encode()).hexdigest()==F['source_group_sha256'];INV={'nodes':[F['owner']]};checks=[]
def parse(fragment=HTML):
 raw=('<html><body>'+fragment+'</body></html>').encode();return raw,model.native_records(raw,INV,F['identity'],F['source_receipt']['requested_url'],hashlib.sha256(raw).hexdigest())
def mutate(old,new):
 assert old in HTML and old!=new;return HTML.replace(old,new)
class Boston(unittest.TestCase):
 def test01_actual_three_printed_labels_bind_exact_different_source_keys(self):
  raw,records=parse();r=records[0];self.assertEqual(len(r['native_auxiliary_fragments']),2);self.assertEqual(len(r['tables'][-1]),3);self.assertEqual(sum(len(x) for x in r['tables'][-1]),6)
  for x in r['native_auxiliary_fragments']:
   self.assertEqual(x['marker_labels'],['6','7','8']);self.assertEqual([(v['printed_label'],v['source_anchor_key']) for v in x['marker_anchor_bindings']],[('6','1'),('7','2'),('8','3')])
  for plan in ['A','D','E']:self.assertEqual(r['text'].count('Plan '+plan+', as noted in the ballot question'),1)
  self.assertTrue(audit_native.audit(raw,records)['passed'])
 def test02_equal_printed_labels_keep_prior_profile_no_new_metadata(self):
  html=HTML
  for key,label in [('1','6'),('2','7'),('3','8')]:html=html.replace('href="#foot--'+key+'">'+label+'</a>','href="#foot--'+key+'">'+key+'</a>').replace('<span class="cs-folk-footnote">'+label+'</span>','<span class="cs-folk-footnote">'+key+'</span>')
  _,records=parse(html)
  for x in records[0]['native_auxiliary_fragments']:self.assertNotIn('marker_anchor_bindings',x)
 def test03_missing_reciprocal_note_backlink_rejected(self):
  with self.assertRaises(AssertionError):parse(mutate('href="#text--1"','href="#text--wrong"'))
 def test04_missing_unique_inline_named_source_target_rejected(self):
  with self.assertRaises(AssertionError):parse(mutate('name="text--1"','name="text--wrong"'))
 def test05_inline_printed_label_mismatch_rejected(self):
  with self.assertRaises(AssertionError):parse(mutate('href="#foot--1">6</a>','href="#foot--1">9</a>'))
 def test06_ambiguous_note_source_anchor_rejected(self):
  with self.assertRaises(AssertionError):parse(mutate('<a name="foot--1"></a>','<a name="foot--1"></a><a name="foot--99"></a>'))
 def test07_note_outside_immediate_source_owner_rejected(self):
  start=HTML.index('<p>Notes</p>');end=HTML.index('</table>',start)+len('</table>');notes=HTML[start:end];fragment=HTML[:start]+HTML[end:]+notes
  with self.assertRaises(AssertionError):parse(fragment)
 def test08_unowned_operative_footer_not_suppressed(self):
  with self.assertRaises(AssertionError):parse(HTML+'<p>Additional operative legal text must not vanish.</p>')
 def test09_omitted_note_ownership_or_cells_fail_independent_raw_audit(self):
  raw,records=parse();bad=copy.deepcopy(records);bad[0]['native_auxiliary_fragments']=[];self.assertFalse(audit_native.audit(raw,bad)['passed']);bad=copy.deepcopy(records);bad[0]['tables'][-1][0][1]['text']='';self.assertFalse(audit_native.audit(raw,bad)['passed'])
 def test10_image_in_note_becomes_literal_placeholder_and_keeps_IDs(self):
  raw,base=parse();_,records=parse(mutate('as amended.</span></div></td>','as amended.<img src="https://example.invalid/note.png" alt="available source label"></span></div></td>'));r=records[0];self.assertEqual(r['body_block_ids'],base[0]['body_block_ids']);self.assertEqual(r['text'].count('[IMAGE]'),3);self.assertNotIn('<img',r['html']);self.assertTrue(all(a.get('disposition')=='image-placeholder' for a in r['assets']));self.assertEqual(len(r['native_auxiliary_fragments']),2)
if __name__=='__main__':
 class Result(unittest.TextTestResult):
  def addSuccess(self,test):super().addSuccess(test);checks.append({'name':test.id(),'passed':True})
 with patch.object(socket,'socket',side_effect=AssertionError('Network forbidden')) as net,patch.object(Image,'open',side_effect=AssertionError('Image decode forbidden')) as dec:
  result=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(unittest.defaultTestLoader.loadTestsFromTestCase(Boston))
 report={'passed':result.wasSuccessful(),'count':result.testsRun,'tests':checks,'failures':[(str(t),s) for t,s in result.errors+result.failures],'network_calls':net.call_count,'image_decode_calls':dec.call_count,'model_sha256':hashlib.sha256((HERE/'model.py').read_bytes()).hexdigest(),'fixture_sha256':hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),'test_script_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()};print(json.dumps(report,indent=2));sys.exit(0 if result.wasSuccessful() else 1)
