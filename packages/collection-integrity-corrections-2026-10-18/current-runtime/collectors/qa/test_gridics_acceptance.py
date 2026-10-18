"""Independent production-entrypoint Gridics source-binding/closing faults; synthetic law only."""
import copy,json,tempfile,unittest
from pathlib import Path
from collectors.gridics import model,collect
CFG={'source_url':'https://codehub.gridics.com/us/zz/synthetic','document_id':'75','identity_term':'Synthetic'}
class GridicsAcceptance(unittest.TestCase):
 def setUp(self):self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name);self.make(self.root)
 def tearDown(self):self.t.cleanup()
 def save(self,p,x):p.write_text(json.dumps(x))
 def make(self,out):
  body='<p>Every applicant must satisfy this operative legal requirement.</p><table><tr><td rowspan="2">A</td><th>B</th></tr><tr><td><img src="map.png"></td></tr></table>'
  heading={'id':'A','path':'/A','docId':'75','text':'Section A','ref':{},'li_attr':{'tag':'h2','dataTag':'section'},'children':[{'id':'body-A','path':'/A/body-A','docId':'75','ref':{'parent':'A'},'li_attr':{'dataTag':'BodyM'},'text':body}]};inventory=[{k:v for k,v in heading.items() if k!='children'}];ledger=[]
  def receipt(phase,kind,value,stamp):
   data=json.dumps(value).encode();name=phase+'-'+kind+'.bin';(out/name).write_bytes(data);q='topLevel=1' if kind=='inventory' else 'tree=1&pathes%5B%5D=A';r={'url':'https://codehub.gridics.com/api/v1/codehub/75?'+q+'&revision=9258','path':name,'sha256':model.digest(data),'bytes':len(data),'status':200,'content_type':'application/json','phase':phase,'epoch':'synthetic-epoch','at':stamp,'method':'GET'};ledger.append(r);return r
  for phase,minute in [('start','00'),('end','10')]:
   inv=receipt(phase,'inventory',inventory,'2026-10-17T00:'+minute+':00+00:00');tree=receipt(phase,'tree',[heading],'2026-10-17T00:'+minute+':01+00:00');dom='<div class="section" data-path="/A"><div id="anchor-A"><h2>Section A</h2></div>'+body+'</div>';name=phase+'-dom.html';(out/name).write_text(dom);self.save(out/(phase+'-checkpoint.json'),{'phase':phase,'phase_complete':True,'roots_response':inv,'roots':[{'root':inventory[0],'tree_response':tree,'dom_path':name,'dom_sha256':model.digest(dom.encode())}]})
  self.save(out/'responses.json',ledger);(out/'executed-source').mkdir();(out/'executed-source/model.py').write_text('synthetic executed revision');self.save(out/'acquisition.json',{'config':CFG,'collector_sources':{'model.py':model.digest((out/'executed-source/model.py').read_bytes())}})
 def mutate_receipt(self,phase,kind,change):
  path=self.root/(phase+'-checkpoint.json');cp=model.read(path);r=cp['roots_response'] if kind=='inventory' else cp['roots'][0]['tree_response'];old=r['path'];change(r);self.save(path,cp);ledger=model.read(self.root/'responses.json');ledger=[r if x['path']==old else x for x in ledger];self.save(self.root/'responses.json',ledger)
 def reject(self):
  try:result=model.analyze(self.root,CFG)[2]
  except (ValueError,KeyError,AssertionError):return
  self.assertFalse(result['publication_text_complete'],result)
 def test_complete_synthetic_baseline_and_no_image_payload(self):
  records,refs,cov=model.analyze(self.root,CFG);self.assertTrue(cov['complete']);self.assertEqual(cov['records'],1);self.assertEqual(cov['image_placeholders'],1);self.assertNotIn('<img',records[0]['html'])
 def test_wrong_endpoint_with_rehashed_registered_receipt_rejected(self):
  self.mutate_receipt('start','tree',lambda r:r.update(url=r['url'].replace('/75?','/76?')));self.reject()
 def test_wrong_body_document_id_with_rehashed_receipt_rejected(self):
  def edit(r):
   p=self.root/r['path'];tree=model.read(p);tree[0]['docId']='76';data=json.dumps(tree).encode();p.write_bytes(data);r.update(sha256=model.digest(data),bytes=len(data))
  self.mutate_receipt('start','tree',edit);self.reject()
 def test_unregistered_receipt_or_incomplete_phase_rejected(self):
  cp=model.read(self.root/'end-checkpoint.json');cp['roots'][0]['tree_response']['epoch']='not-registered';self.save(self.root/'end-checkpoint.json',cp);self.reject()
 def test_copied_opening_receipt_cannot_close_publication(self):
  start=model.read(self.root/'start-checkpoint.json')['roots'][0]['tree_response'];self.mutate_receipt('end','tree',lambda r:r.update(at=start['at']));self.reject()
 def test_epoch_crosswire_even_if_registered_is_rejected(self):
  self.mutate_receipt('end','tree',lambda r:r.update(epoch='another-acquisition-epoch'));self.reject()
 def test_real_closing_time_must_follow_opening_not_string_sort(self):
  # 00:10+01:00 is actually before 00:00+00:00, despite lexical ordering.
  self.mutate_receipt('end','inventory',lambda r:r.update(at='2026-10-17T00:10:00+01:00'));self.mutate_receipt('end','tree',lambda r:r.update(at='2026-10-17T00:10:01+01:00'));self.reject()
 def test_executed_source_corruption_fails_real_verify(self):
  collect.write_outputs(self.root,CFG);(self.root/'executed-source/model.py').write_text('corrupt');
  with self.assertRaisesRegex(model.Invalid,'Executed acquisition source'):collect.verify(self.root,CFG)
 def test_corrupt_original_raw_body_rejected(self):
  (self.root/'start-tree.bin').write_text('corrupt');self.reject()
if __name__=='__main__':unittest.main(verbosity=2)
