import sys,copy,unittest,hashlib,json,base64
from pathlib import Path
from unittest.mock import patch
from bs4 import BeautifulSoup
import argparse,os,socket,urllib.request,datetime
sys.dont_write_bytecode=True
argument_parser=argparse.ArgumentParser(description='13 source-navigation regressions. No publisher/image operations.')
argument_parser.add_argument('--source',type=Path,default=Path(os.environ.get('ORIGINALS_QA_SOURCE',str(Path(__file__).resolve().parents[1]/'originals'))))
argument_parser.add_argument('--receipt',type=Path)
options=argument_parser.parse_args();SOURCE=options.source.resolve()
if not (SOURCE/'source_navigation.py').is_file():raise SystemExit('Select reviewed originals source containing source_navigation.py with --source')
def snapshot():return {str(p.relative_to(SOURCE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(SOURCE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
BEFORE=snapshot()
def forbidden(*args,**kwargs):raise AssertionError('Navigation regression attempted network/browser/image operation')
socket.socket.connect=forbidden;socket.create_connection=forbidden;urllib.request.OpenerDirector.open=forbidden
import playwright.sync_api
playwright.sync_api.sync_playwright=forbidden
sys.path.insert(0,str(SOURCE))
from flagstaff_html_normalize import parse
from king_normalize import blocks
from source_navigation import assess
from model import image_asset
URL='https://www.codepublishing.com/AZ/Flagstaff/html/Test.html';CURRENCY='Exact fixture edition';HREF='Test.html#4.2';sha=lambda b:hashlib.sha256(b).hexdigest()
def fixture(collision=False,image=False,attachment=False):
 imagehtml='<img src="data:application/octet-stream;base64,PRIVATE_PIXEL_SENTINEL">' if image else ''
 appendix='<p><a href="https://example.invalid/required.pdf">Appendix required.</a></p>' if attachment else ''
 extra='<h3 id="duplicate">4-2 Other competing section</h3><p>Other mandatory body.</p>' if collision else ''
 raw=('<div id="mainContent"><h1 id="division">Title</h1><p><a href="'+HREF+'">4-2</a> first reference.</p>'+appendix+'<h3 id="2">2 Owner law</h3><p><a href="'+HREF+'">4-2</a> second reference.</p><p><a href="'+HREF+'">4-2</a> third reference.</p><h3 id="4.2\t"><a name="4.2\t">4-2\t</a> Target legal</h3><p>Mandatory A body.'+imagehtml+'</p><p class="HistoryNote">Ord. fixture.</p>'+extra+'</div>').encode()
 labels=[('Title','division'),('2 Owner law','2'),('4-2 Target legal','4.2')]+([('4-2 Other competing section','duplicate')] if collision else []);inventory=[{'edge_id':'edge-'+str(i),'source_url':URL+'#'+frag,'label':label} for i,(label,frag) in enumerate(labels)];records,audit=parse(raw,URL,inventory);target=next(r for r in records if r['heading']=='4-2 Target legal');units=list(blocks(BeautifulSoup(raw,'html.parser').select_one('#mainContent')));refs=[]
 for row in records:
  for ix,link in enumerate(row['links']):
   if link['url']!=URL+'#4.2':continue
   bi=next(i for i in row['block_indices'] if units[i].find('a',href=HREF));anchor=units[bi].find('a',href=HREF);refs.append({'owner_record_id':row['record_id'],'link_index':ix,'source_block_index':bi,'source_raw_href':HREF,'source_text':'4-2','source_anchor_sha256':sha(str(anchor).encode())})
 rule={'rule_id':'finite-fixture','source_url':URL,'source_sha256':sha(raw),'publication_currency':CURRENCY,'href_fragment':'4.2','printed_numeric_locator':'4-2','target_record_id':target['record_id'],'target_heading':target['heading'],'target_source_heading_ids':target['source_heading_ids'],'target_block_indices':target['block_indices'],'target_source_body_sha256':sha(''.join(str(units[i]) for i in target['block_indices']).encode()),'target_full_text_sha256':sha(target['full_text'].encode()),'target_semantic_html_sha256':sha(target['semantic_html'].encode()),'source_toc_edge_id':'edge-2','source_refs':refs};dependencies=[]
 for row in records:
  for asset in row['assets']:
   dep=dict(asset,owner_record_id=row['record_id'])
   if image_asset(dep):dep.update(required=False,status='policy_omitted_image')
   dependencies.append(dep)
 return {'records':records,'raw_documents':{URL:raw},'inventory':inventory,'audits':[audit],'dependencies':dependencies,'currency':CURRENCY,'rules':[rule],'reference_rules':[],'separate_prefixes':[],'blocks':blocks}
class SourceBoundNavigation(unittest.TestCase):
 def test_exact_source_witness_resolves_without_rewriting_literal_defect(self):
  x=fixture();before=copy.deepcopy(x['records']);raw=x['raw_documents'][URL];r=assess(**x);self.assertTrue(r['source_target_coverage_complete'],r['errors']);self.assertFalse(r['literal_browser_fragment_complete']);self.assertEqual(len(r['diagnostics']),3);self.assertEqual(len(r['resolutions']),3);self.assertEqual(x['records'],before);self.assertEqual(x['raw_documents'][URL],raw);self.assertTrue(all(z['target_source_heading_ids']==['4.2\t','4.2\t'] and not z['publisher_source_rewritten'] for z in r['resolutions']))
 def test_numeric_locator_collision_fails_even_with_correct_raw_hash(self):
  r=assess(**fixture(collision=True));self.assertFalse(r['source_target_coverage_complete']);self.assertTrue(any('ambiguous' in e for e in r['errors']))
 def test_reference_changed_to_other_valid_target_fails(self):
  x=fixture();ref=x['rules'][0]['source_refs'][0];row=next(r for r in x['records'] if r['record_id']==ref['owner_record_id']);row['links'][ref['link_index']]['url']=URL+'#division';r=assess(**x);self.assertFalse(r['source_target_coverage_complete']);self.assertTrue(r['errors'])
 def test_other_source_rule_cannot_qualify_same_looking_target(self):
  x=fixture();x['rules'][0]['source_url']='https://other.invalid/Test.html';r=assess(**x);self.assertFalse(r['source_target_coverage_complete']);self.assertEqual(len(r['resolutions']),0)
 def test_changed_source_hash_has_no_implicit_migration(self):
  x=fixture();x['rules'][0]['source_sha256']='0'*64;r=assess(**x);self.assertFalse(r['source_target_coverage_complete']);self.assertEqual(len(r['resolutions']),0)
 def test_different_edition_fails(self):
  x=fixture();x['currency']='Other edition';r=assess(**x);self.assertFalse(r['source_target_coverage_complete']);self.assertTrue(any('edition' in e for e in r['errors']))
 def test_missing_primary_document_or_duplicate_owned_block_fails(self):
  x=fixture();x['raw_documents']={};self.assertFalse(assess(**x)['source_target_coverage_complete']);x=fixture();x['records'][0]['block_indices'].append(1);self.assertFalse(assess(**x)['source_target_coverage_complete'])
 def test_unbound_required_dependency_cannot_hide_behind_three_resolutions(self):
  x=fixture();x['dependencies'].append({'required':True,'url':'https://example.invalid/required.pdf','status':'unresolved_nonimage_attachment'});r=assess(**x);self.assertEqual(len(r['resolutions']),3);self.assertFalse(r['source_target_coverage_complete']);self.assertFalse(r['dependency_coverage_complete'])
 def test_actual_required_source_attachment_stays_unqualified(self):
  x=fixture(attachment=True);r=assess(**x);self.assertEqual(len(r['resolutions']),3);self.assertFalse(r['source_target_coverage_complete']);self.assertFalse(r['dependency_coverage_complete'])
 def test_omitted_required_source_attachment_ledger_entry_fails(self):
  x=fixture(attachment=True);self.assertTrue(x['dependencies']);x['dependencies']=[];r=assess(**x);self.assertFalse(r['source_target_coverage_complete']);self.assertFalse(r['dependency_coverage_complete'])
 def test_changed_retained_target_text_fails(self):
  x=fixture();target=next(r for r in x['records'] if r['record_id']==x['rules'][0]['target_record_id']);target['full_text']+=' Unpublished addition.';r=assess(**x);self.assertFalse(r['source_target_coverage_complete']);self.assertTrue(any('body' in e or 'text' in e for e in r['errors']))
 def test_omitted_source_asset_and_dependency_cannot_claim_attachment_coverage(self):
  x=fixture(attachment=True)
  for row in x['records']:row['assets']=[]
  x['dependencies']=[];r=assess(**x);self.assertFalse(r['source_target_coverage_complete']);self.assertFalse(r['dependency_coverage_complete'])
 def test_image_context_never_decodes_and_remains_exact_placeholder(self):
  with patch.object(base64,'b64decode',side_effect=AssertionError('Image decoder forbidden')) as decoder:x=fixture(image=True);r=assess(**x)
  decoder.assert_not_called();self.assertTrue(r['source_target_coverage_complete'],r['errors']);self.assertNotIn('PRIVATE_PIXEL',json.dumps(r));self.assertEqual(sum(z['image_placeholder_count'] for z in x['records']),1)
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(SourceBoundNavigation))
 unchanged=snapshot()==BEFORE
 if not unchanged:raise AssertionError('Tested source changed')
 if options.receipt:
  receipt=options.receipt.resolve()
  if receipt.exists() or receipt==SOURCE or SOURCE in receipt.parents:raise FileExistsError('Fresh external QA receipt required')
  receipt.parent.mkdir(parents=True,exist_ok=True)
  receipt.write_text(json.dumps({'schema':'originals-portable-navigation-regressions-1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(SOURCE),'source_sha256':BEFORE,'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'passed':result.wasSuccessful(),'source_unchanged':unchanged,'publisher_requests':0,'browser_startup_blocked':True,'scope':'Synthetic negative/positive source-witness fixtures through actual parser/coverage code. No fullpublication transport claim; genuine source proof and exact finite3sourcepolicy retained separately.'},indent=2)+'\n')
 sys.exit(0 if result.wasSuccessful() else 1)
