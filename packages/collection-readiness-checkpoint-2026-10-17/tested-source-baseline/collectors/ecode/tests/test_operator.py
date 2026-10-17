"""Offline operator recovery tests. All complete examples are synthetic, never live law."""
import io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from collectors.ecode.common import *
from collectors.ecode.engine import collect,rebuild,write_outputs,verify,adopt
from collectors.ecode.operator import doctor,export_plan,import_bundle,document_identity
from .test_faults import CFG,FakeBrowser,ROOT,TWO,ONE,SOURCES,MCBASE,MCROOT,MCTOC,MCONE,FakeMC

def pdf_text(text):
 from pypdf import PdfWriter
 from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject
 writer=PdfWriter();page=writer.add_blank_page(width=600,height=800)
 font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
 page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
 stream=DecodedStreamObject();stream.set_data(('BT /F1 12 Tf 10 700 Td ('+text+') Tj ET').encode());page[NameObject('/Contents')]=writer._add_object(stream)
 out=io.BytesIO();writer.write(out);return out.getvalue()

class OperatorTests(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
 def tearDown(self):self.temp.cleanup()
 def stopped(self):
  out=self.root/'source'
  with patch('collectors.ecode.browser.Browser',FakeBrowser):collect(CFG,out)
  state=read(out/'checkpoint.json');state['artifacts']=[a for a in state['artifacts'] if a['role']!='root-end' and a['requested_url']!='https://ecode360.com/102']
  for a in state['artifacts']:a['retrieved_at']='2026-01-01T00:00:00+00:00'
  state['errors']=[{'type':'AccessStop','message':'SYNTHETIC403','access_stop':True}];data=rebuild(out,state);state['inventory_bound_artifacts']=len(state['artifacts']);state['inventory_sha256']=digest(canon(sorted(data['nodes'].values(),key=lambda n:n['id'])));save(out/'checkpoint.json',state);write_outputs(out,state,data);return out
 def bundle(self,source):
  folder=self.root/'bundle';folder.mkdir();files=[]
  for name,raw,role,url,stamp in [('chapter.html',TWO,'content','https://ecode360.com/102','2026-01-02T00:00:00+00:00'),('closing.html',ROOT,'root-end',CFG['url'],'2026-01-03T00:00:00+00:00')]:
   atomic(folder/name,raw);files.append({'path':name,'sha256':digest(raw),'role':role,'source_url':url,'retrieved_at':stamp,'media_type':'text/html'})
  save(folder/'bundle.json',{'schema':'icc-operator-bundle-1','identity':read(source/'checkpoint.json')['identity'],'genuine_publisher_downloads':True,'acquisition_method':'SYNTHETIC authorised fixture delivery; not real law','files':files});return folder/'bundle.json'
 def test_complete_offline_import_and_historical_stop(self):
  source=self.stopped();before=digest((source/'checkpoint.json').read_bytes());manifest=self.bundle(source)
  with patch('collectors.ecode.browser.Browser',side_effect=AssertionError('No browser allowed')):r=import_bundle(source,manifest,self.root/'imported')
  self.assertTrue(r['complete'],r);self.assertEqual(r['acquisition_mode'],'operator_supplied_download_bundle');self.assertFalse(r['resumable']);self.assertTrue(r['operator_import']['source_access_stop_preserved']);self.assertEqual(digest((source/'checkpoint.json').read_bytes()),before);self.assertTrue(verify(self.root/'imported')['complete'])
 def test_missing_closing_never_completes(self):
  source=self.stopped();m=self.bundle(source);s=read(m);s['files']=s['files'][:1];save(m,s);r=import_bundle(source,m,self.root/'imported');self.assertFalse(r['complete']);self.assertFalse(r['start_end_inventory_consistent'])
 def test_closing_before_acquisition_never_completes(self):
  source=self.stopped();m=self.bundle(source);s=read(m);s['files'][1]['retrieved_at']='2025-01-01T00:00:00+00:00';save(m,s)
  with self.assertRaisesRegex(QualificationError,'predates'):import_bundle(source,m,self.root/'imported')
 def test_wrong_edition_corrupt_duplicate_and_image_rejected(self):
  for mode in ['edition','hash','duplicate','image']:
   with self.subTest(mode=mode):
    source=self.stopped();m=self.bundle(source);s=read(m)
    if mode=='edition':s['identity']['code_id']='wrong'
    if mode=='hash':s['files'][0]['sha256']='wrong'
    if mode=='duplicate':s['files'].append(s['files'][0])
    if mode=='image':s['files'][0]['media_type']='image/svg+xml'
    save(m,s)
    with self.assertRaises(QualificationError):import_bundle(source,m,self.root/'imported')
    self.assertFalse((self.root/'imported').exists())
    import shutil;shutil.rmtree(source);shutil.rmtree(m.parent)
 def test_manifest_and_raw_tamper_fail_independent_verify(self):
  source=self.stopped();m=self.bundle(source);out=self.root/'imported';import_bundle(source,m,out);atomic(out/'operator-bundle.json',b'{}')
  with self.assertRaisesRegex(QualificationError,'manifest corruption'):verify(out)
 def test_imported_proof_replay_keeps_manifest_and_stop_history(self):
  source=self.stopped();m=self.bundle(source);out=self.root/'imported';import_bundle(source,m,out)
  with patch('collectors.ecode.browser.Browser',side_effect=AssertionError('No network')):adopt(out,self.root/'replayed',CFG,True)
  r=verify(self.root/'replayed');self.assertTrue(r['complete']);self.assertTrue(r['operator_import']['source_access_stop_preserved']);self.assertTrue((self.root/'replayed/provenance/operator-bundle.json').exists())
  with self.assertRaisesRegex(AccessStop,'read-only'):collect(CFG,out,True)
 def test_operator_history_tamper_is_not_silent_stop_clear(self):
  source=self.stopped();m=self.bundle(source);out=self.root/'imported';import_bundle(source,m,out);s=read(out/'checkpoint.json');s['operator_import']['historical_errors']=[];save(out/'checkpoint.json',s)
  with self.assertRaisesRegex(QualificationError,'historical failure'):verify(out)
 def test_export_plan_has_exact_missing_inventory_and_no_network(self):
  source=self.stopped()
  with patch('collectors.ecode.browser.Browser',side_effect=AssertionError('No browser allowed')):r=export_plan(source,self.root/'plan')
  self.assertEqual([x['id'] for x in r['missing_nodes']],['102']);self.assertFalse(r['network_performed']);self.assertFalse(read(self.root/'plan/bundle-template.json')['genuine_publisher_downloads'])
 def test_document_phrase_identity_requires_source_and_document(self):
  meta={'requested_url':'https://ecode360.com/attachment/fixture/Appendix.pdf','headers':{'content-type':'application/pdf'}};raw=pdf_text('Synthetic Municipality Appendix A operative law applies to all applicants.')
  r=document_identity(raw,meta,['Synthetic Municipality','Appendix A'],'Synthetic Municipality Appendix A');self.assertTrue(r['identity_terms_matched']);self.assertFalse(r['image_objects_extracted'])
  for terms,source in [(['Wrong municipality'],'Wrong municipality'),(['operative law'],'Synthetic Municipality Appendix A')]:
   with self.assertRaises(QualificationError):document_identity(raw,meta,terms,source)
 def test_municipal_import_requires_independent_contents_closing(self):
  cfg={**CFG,'family':'municipal.codes','url':MCBASE,'publication':'Code','jurisdiction':'Synthetic','state':'ZZ'};source=self.root/'source'
  with patch('collectors.ecode.browser.Browser',FakeMC):collect(cfg,source)
  s=read(source/'checkpoint.json');s['artifacts']=[a for a in s['artifacts'] if a['role'] not in ['content','root-end','contents-end']]
  for a in s['artifacts']:a['retrieved_at']='2026-01-01T00:00:00+00:00'
  s['errors']=[{'type':'AccessStop','message':'SYNTHETIC429','access_stop':True}];d=rebuild(source,s);s['inventory_bound_artifacts']=len(s['artifacts']);s['inventory_sha256']=digest(canon(sorted(d['nodes'].values(),key=lambda n:n['id'])));save(source/'checkpoint.json',s);write_outputs(source,s,d)
  folder=self.root/'bundle';folder.mkdir();files=[]
  for name,raw,role,url in [('chapter.html',MCONE,'content',MCBASE+'/1'),('root.html',MCROOT,'root-end',MCBASE),('contents.html',MCTOC,'contents-end',MCBASE+'/contents')]:
   atomic(folder/name,raw);files.append({'path':name,'sha256':digest(raw),'role':role,'source_url':url,'retrieved_at':'2026-01-02T00:00:00+00:00','media_type':'text/html'})
  manifest={'schema':'icc-operator-bundle-1','identity':s['identity'],'genuine_publisher_downloads':True,'acquisition_method':'SYNTHETIC authorised local HTML fixture delivery','files':files};save(folder/'bundle.json',manifest)
  r=import_bundle(source,folder/'bundle.json',self.root/'full');self.assertTrue(r['complete'],r);self.assertEqual(r['inventory_nodes'],3)
  manifest['files']=files[:2];save(folder/'bundle.json',manifest);r=import_bundle(source,folder/'bundle.json',self.root/'incomplete');self.assertFalse(r['complete']);self.assertFalse(r['start_end_inventory_consistent'])
 def test_required_pdf_import_is_source_and_scope_bound(self):
  original=SOURCES['https://ecode360.com/101'];u='https://documents.invalid/legal.pdf'
  try:
   SOURCES['https://ecode360.com/101']=ONE.replace(b'Alpha legal text.',b'Alpha legal text. <a href="https://documents.invalid/legal.pdf">Appendix A</a>')
   source=self.root/'source'
   with patch('collectors.ecode.browser.Browser',FakeBrowser):collect(CFG,source)
   s=read(source/'checkpoint.json')
   for a in s['artifacts']:a['retrieved_at']='2026-01-01T00:00:00+00:00'
   s['errors']=[{'type':'AccessStop','message':'SYNTHETIC403','access_stop':True}];save(source/'checkpoint.json',s)
   folder=self.root/'bundle';folder.mkdir();raw=pdf_text('Synthetic Test Municipality, NV Appendix A operative legal rules apply.');atomic(folder/'document.pdf',raw);atomic(folder/'closing.html',ROOT)
   save(folder/'bundle.json',{'schema':'icc-operator-bundle-1','identity':s['identity'],'genuine_publisher_downloads':True,'acquisition_method':'SYNTHETIC authorised publisher fixture delivery','files':[{'path':'document.pdf','sha256':digest(raw),'role':'asset','source_url':u,'retrieved_at':'2026-01-02T00:00:00+00:00','media_type':'application/pdf','identity_terms':['Appendix A']},{'path':'closing.html','sha256':digest(ROOT),'role':'root-end','source_url':CFG['url'],'retrieved_at':'2026-01-03T00:00:00+00:00','media_type':'text/html'}]})
   r=import_bundle(source,folder/'bundle.json',self.root/'imported');self.assertTrue(r['complete'],r);self.assertEqual(r['acquired_assets'],1);self.assertTrue(verify(self.root/'imported')['complete'])
  finally:SOURCES['https://ecode360.com/101']=original
 def test_generated_accessibility_ids_only_are_equivalent(self):
  from collectors.ecode.engine import equivalent_body
  ident='1__'+'a'*32;html=f'<section id="{ident}" aria-labelledby="{ident}__name"><span class="name" id="{ident}__name">Threshold.</span><a href="/rule">Rule</a><table><tr><td rowspan="2">3</td></tr></table></section>'
  native=html.replace(f' aria-labelledby="{ident}__name"','').replace(f' id="{ident}__name"','');a={'heading':'Rule','content_html':html};b={'heading':'Rule','content_html':native};self.assertTrue(equivalent_body(a,b))
  for changed in [native.replace('>3<','>4<'),native.replace('rowspan="2"','rowspan="1"'),native.replace('/rule','/different'),native.replace(f'id="{ident}"','id="different"')]:self.assertFalse(equivalent_body(a,{'heading':'Rule','content_html':changed}))
 def test_future_acquisition_timestamp_rejected(self):
  source=self.stopped();m=self.bundle(source);s=read(m);s['files'][0]['retrieved_at']='2999-01-01T00:00:00+00:00';save(m,s)
  with self.assertRaisesRegex(QualificationError,'future'):import_bundle(source,m,self.root/'imported')
 def test_configured_root_cannot_silently_migrate(self):
  calls=[]
  class Redirected(FakeBrowser):
   def fetch(self,url,method='GET'):
    calls.append(url);raw,meta=super().fetch(url,method);meta['url']='https://ecode360.com/ZZ9001';return raw,meta
   bootstrap=fetch
  with patch('collectors.ecode.browser.Browser',Redirected):r=collect(CFG,self.root/'wrong-alias')
  self.assertFalse(r['complete']);self.assertIn('Configured customer alias',str(r['errors']));self.assertEqual(len(calls),1)
  class RedirectedMC(FakeMC):
   def fetch(self,url):
    calls.append(url);raw,meta=super().fetch(url);meta['url']=MCBASE.replace('/Code','/UDO');return raw,meta
   bootstrap=fetch
  calls.clear();cfg={**CFG,'family':'municipal.codes','url':MCBASE,'publication':None,'jurisdiction':'Synthetic','state':'ZZ'}
  with patch('collectors.ecode.browser.Browser',RedirectedMC):r=collect(cfg,self.root/'wrong-mc-root')
  self.assertFalse(r['complete']);self.assertIn('Configured publication root',str(r['errors']));self.assertEqual(len(calls),1)
  calls.clear();cfg['publication']='Code'
  with patch('collectors.ecode.browser.Browser',RedirectedMC):r=collect(cfg,self.root/'wrong-mc-explicit')
  self.assertFalse(r['complete']);self.assertEqual(len(calls),1)
 def test_doctor_does_not_change_gate(self):
  gate=self.root/'gates';family=gate/'ecode360';family.mkdir(parents=True);save(family/'STOP.json',{'status':403,'automatic_retry':False});before=(family/'STOP.json').read_bytes()
  with patch.dict('os.environ',{'ICC_GATE_DIR':str(gate)}):r=doctor(CFG['url'])
  self.assertFalse(r['ready']);self.assertFalse(r['network_performed']);self.assertEqual(before,(family/'STOP.json').read_bytes())
 def test_doctor_retained_stop_blocks_ready_when_tmp_gate_absent(self):
  source=self.stopped()
  with patch.dict('os.environ',{'ICC_GATE_DIR':str(self.root/'absent-gates')}):r=doctor(CFG['url'],source)
  self.assertTrue(r['transport_gate_clear']);self.assertFalse(r['network_ready']);self.assertFalse(r['ready']);self.assertFalse(r['can_resume']);self.assertFalse((self.root/'absent-gates').exists())
 def test_doctor_wrong_customer_or_publication_rejected(self):
  source=self.stopped()
  with self.assertRaisesRegex(QualificationError,'Doctor URL'):doctor('https://ecode360.com/ZZ9001',source)
  cfg={**CFG,'family':'municipal.codes','url':MCBASE,'publication':'Code','jurisdiction':'Synthetic','state':'ZZ'};mc=self.root/'municipal'
  with patch('collectors.ecode.browser.Browser',FakeMC):collect(cfg,mc)
  with self.assertRaisesRegex(QualificationError,'Doctor URL'):doctor(MCBASE.replace('/Code','/UDO'),mc)
 def test_verifier_rebinds_config_alias_and_jurisdiction(self):
  source=self.stopped();s=read(source/'checkpoint.json');s['config']['url']='https://ecode360.com/ZZ9001';save(source/'checkpoint.json',s)
  with self.assertRaisesRegex(QualificationError,'Configured customer alias'):verify(source)
  s['config']['url']=CFG['url'];s['config']['state']='CA';save(source/'checkpoint.json',s)
  with self.assertRaises(QualificationError):verify(source)
 def test_statutory_reference_boundary_not_blanket_extensionless_skip(self):
  from collectors.ecode.engine import statutory_reference
  for u in ['https://municipal.codes/NY/GMU/806','https://municipal.codes/US/USC/42/6901','https://municipal.codes/US/CFR/47/1.6002','https://municipal.codes/US/Const/Amendment1']:
   self.assertTrue(statutory_reference(u,CFG['url'],'ecode360'))
  self.assertTrue(statutory_reference('https://phoenix.municipal.codes/AZ/ARS/9-471','https://phoenix.municipal.codes/Charter','municipal.codes'))
  for u in ['https://municipal.codes/US/UNKNOWN/42','https://municipal.codes/NY/UNKNOWN/806','https://municipal.codes/ZZ/GMU/806','https://unrelated.invalid/US/USC/42/6901','https://ecode360.com/AZ/ARS/9-471']:
   self.assertFalse(statutory_reference(u,CFG['url'],'ecode360'))
  original=SOURCES['https://ecode360.com/101']
  try:
   SOURCES['https://ecode360.com/101']=ONE.replace(b'Alpha legal text.',b'Alpha legal text. <a href="https://municipal.codes/US/USC/42/6901">42 USC 6901</a>')
   with patch('collectors.ecode.browser.Browser',FakeBrowser):r=collect(CFG,self.root/'references')
   self.assertTrue(r['complete'],r);self.assertEqual(r['unresolved_links'],[])
   SOURCES['https://ecode360.com/101']=SOURCES['https://ecode360.com/101'].replace(b'/US/USC/42/6901',b'/US/UNKNOWN/42')
   with patch('collectors.ecode.browser.Browser',FakeBrowser):r=collect(CFG,self.root/'unknown-reference')
   self.assertFalse(r['attachments_complete']);self.assertEqual(len(r['unresolved_links']),1)
  finally:SOURCES['https://ecode360.com/101']=original
 def test_standalone_two_family_full_bundle_without_checkpoint(self):
  for family in ['ecode360','municipal.codes']:
   folder=self.root/family;folder.mkdir();cfg=CFG if family=='ecode360' else {**CFG,'family':'municipal.codes','url':MCBASE,'publication':'Code','jurisdiction':'Synthetic','state':'ZZ'}
   sources=[('root',ROOT,'root-start',CFG['url']),('one',ONE,'content','https://ecode360.com/101'),('two',TWO,'content','https://ecode360.com/102'),('end',ROOT,'root-end',CFG['url'])] if family=='ecode360' else [('root',MCROOT,'root-start',MCBASE),('toc',MCTOC,'contents-start',MCBASE+'/contents'),('one',MCONE,'content',MCBASE+'/1'),('end',MCROOT,'root-end',MCBASE),('toc-end',MCTOC,'contents-end',MCBASE+'/contents')]
   files=[]
   for name,raw,role,url in sources:
    atomic(folder/(name+'.html'),raw);files.append({'path':name+'.html','role':role,'source_url':url,'sha256':digest(raw),'media_type':'text/html','retrieved_at':'2026-01-01T00:00:00+00:00'})
   manifest={'schema':'icc-operator-bundle-1','config':cfg,'genuine_publisher_downloads':True,'acquisition_method':'SYNTHETIC authorised whole structured source bundle, not real law','files':files};save(folder/'bundle.json',manifest)
   with patch('collectors.ecode.browser.Browser',side_effect=AssertionError('No browser')):r=import_bundle(None,folder/'bundle.json',folder/'out')
   self.assertTrue(r['complete'],r);self.assertEqual(r['operator_import']['origin'],'standalone_bundle');self.assertFalse(r['resumable']);self.assertTrue(verify(folder/'out')['complete'])
   adopt(folder/'out',folder/'replay',cfg,True);self.assertTrue(verify(folder/'replay')['complete'])
 def test_standalone_foreign_publication_selector_rejected(self):
  from collectors.ecode.operator import operator_config
  cfg={**CFG,'family':'municipal.codes','url':MCBASE,'publication':'https://foreign.municipal.codes/Code'}
  with self.assertRaisesRegex(QualificationError,'publisher host/family'):operator_config(cfg)
 def test_opening_after_substantive_acquisition_rejected(self):
  source=self.stopped();m=self.bundle(source);s=read(source/'checkpoint.json')
  for a in s['artifacts']:
   if a['role']=='root-start':a['retrieved_at']='2026-01-04T00:00:00+00:00'
  save(source/'checkpoint.json',s)
  with self.assertRaisesRegex(QualificationError,'[Oo]pening source postdates'):import_bundle(source,m,self.root/'late-opening')
 def test_standalone_missing_opening_and_wrong_family_rejected(self):
  source=self.stopped();m=self.bundle(source);s=read(m);s.pop('identity');s['config']=CFG;save(m,s)
  with self.assertRaisesRegex(QualificationError,'root-start'):import_bundle(None,m,self.root/'missing-opening')
  s['config']={**CFG,'family':'municipal.codes'};save(m,s)
  with self.assertRaisesRegex(QualificationError,'family'):import_bundle(None,m,self.root/'wrong-family')

if __name__=='__main__':unittest.main()
