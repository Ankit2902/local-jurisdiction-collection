import sys
sys.dont_write_bytecode=True
import json,types,importlib,tempfile,socket,base64,unittest,argparse,ast,hashlib
from pathlib import Path
from unittest.mock import patch
B=Path(__file__).resolve().parent
_ap=argparse.ArgumentParser();_ap.add_argument('--collector-root',required=True,type=Path);_args,_remaining=_ap.parse_known_args();sys.argv=[sys.argv[0]]+_remaining;SOURCE=_args.collector_root.resolve()
pkg=types.ModuleType('_candidate');pkg.__path__=[str(SOURCE)];sys.modules['_candidate']=pkg
A=importlib.import_module('_candidate.adapters');C=importlib.import_module('_candidate.common')
IDENTITY={'family':'ecode360','customer_id':'ZZ9001','code_id':'10','currency_raw':'2026-01-01','current_code_id':'10','name':'Synthetic','state':'ZZ'}
def page(body,extra='',headers=''):
 return ('<html><body data-cust-id="ZZ9001" data-code-id="10" data-code-date="2026-01-01" data-current-code-id="10" data-customer-name="Synthetic" data-guid="101"><h1 id="pageTitle">§ 1 Rule</h1><div id="101_title" data-full-title="§ 1 Rule" data-code-content-type="section"></div><div id="childContent">'+headers+'</div><div id="codeContent"><div class="section_content content" id="101_content">'+body+'</div>'+extra+'</div></body></html>').encode()
def definition(href='123#123',target='123',content='Legal definition applies.',label='ZONING MAP'):
 return '<div class="section_content content" id="101_content"><section class="definition" id="'+target+'"><dfn class="term"><a class="termLink" onclick="return false;" href="'+href+'">'+label+'</a></dfn><div class="deftext">'+content+'</div></section></div>'
class Focused(unittest.TestCase):
 def setUp(self):
  self.g=[]
  def no(*a,**k):raise AssertionError('Network/image decoder forbidden')
  for obj,key in [(socket.socket,'connect'),(socket,'create_connection'),(base64,'b64decode')]:
   g=patch.object(obj,key,no);g.start();self.g.append(g)
 def tearDown(self):
  for g in reversed(self.g):g.stop()
 def refs(self,html,owner='101'):return A.asset_refs(html,'https://ecode360.com/101',owner)
 def test_exact_self_anchor_not_required(self):
  ref=self.refs(definition())[0];self.assertFalse(ref['required']);self.assertEqual(ref['kind'],'owned_definition_self_anchor');self.assertEqual(ref['source_target']['definition_id'],'123')
 def test_cross_owner_still_required(self):self.assertTrue(self.refs(definition(),owner='999')[0]['required'])
 def test_target_mismatch_still_required(self):self.assertTrue(self.refs(definition(target='124'))[0]['required'])
 def test_foreign_host_still_required(self):self.assertTrue(self.refs(definition(href='https://other.invalid/123#123'))[0]['required'])
 def test_different_fragment_still_required(self):self.assertTrue(self.refs(definition(href='123#124'))[0]['required'])
 def test_true_MAP_PDF_still_required(self):self.assertTrue(self.refs(definition(href='123.pdf#123'))[0]['required'])
 def test_empty_definition_still_required(self):self.assertTrue(self.refs(definition(content=''))[0]['required'])
 def test_duplicate_target_still_required(self):self.assertTrue(self.refs(definition().replace('</section>','</section><div id="123">Duplicate</div>'))[0]['required'])
 def test_nonself_sameURL_required_in_bothorders(self):
  for before in [True,False]:
   link='<a href="https://ecode360.com/123">Download map</a>';html=definition();html=html.replace('<section',link+'<section',1) if before else html.replace('</section>','</section>'+link)
   self.assertTrue(self.refs(html)[0]['required'])
 def test_nested_definition_list_is_preserved(self):
  body='<section class="definition" id="123"><div class="deftext">A rule:</div><div class="defitem_content content"><p>Mandatory item one.</p></div><div class="litem_content content">Mandatory item two.</div></section>'
  r=A.parse_ecode(page(body),'https://ecode360.com/101',IDENTITY)['records'][0];self.assertIn('Mandatory item one.',r['text']);self.assertIn('Mandatory item two.',r['semantic_html']);self.assertIn('defitem_content content',r['content_html'])
 def test_independent_nestedGUID_has_unique_owner(self):
  headers='<div class="contentTitle" data-guid="102" data-parent-guid="101" data-code-content-type="section" data-full-title="§ 2 Child"></div>'
  body='<p>Parent own text.</p><div class="section_content content" id="102_content">Child mandatory text.</div>'
  rows=A.parse_ecode(page(body,headers=headers),'https://ecode360.com/101',IDENTITY)['records'];self.assertEqual(len(rows),2);self.assertNotIn('Child mandatory text.',rows[0]['text']);self.assertIn('Child mandatory text.',rows[1]['text'])
 def test_unowned_content_outside_owner_refuses_even_empty(self):
  for content in ['Outside mandatory law.','']:
   with self.assertRaisesRegex(C.QualificationError,'Unowned legal content container'):A.parse_ecode(page('Own text.',extra='<div class="mystery content">'+content+'</div>'),'https://ecode360.com/101',IDENTITY)
 def test_unknown_content_cannot_hide_as_heading_or_UI(self):
  for classes in ['content contentTitle','content actions','content selection-control']:
   for text in ['Outside mandatory law.','']:
    with self.assertRaisesRegex(C.QualificationError,'Unowned legal content container'):A.parse_ecode(page('Own text.',extra='<div class=\"'+classes+'\">'+text+'</div>'),'https://ecode360.com/101',IDENTITY)
 def test_image_in_definition_remains_placeholder(self):
  r=A.parse_ecode(page('<div class="defitem_content content">Caption<img src="/map.png"></div>'),'https://ecode360.com/101',IDENTITY)['records'][0];self.assertEqual(r['image_placeholder_count'],1);self.assertIn('Caption[IMAGE]',r['text']);self.assertNotIn('<img',r['content_html'])
 def test_municipal_parser_unchanged(self):
  node=next(n for n in ast.parse((SOURCE/'adapters.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='parse_municipal')
  self.assertEqual(hashlib.sha256(ast.get_source_segment((SOURCE/'adapters.py').read_text(),node).encode()).hexdigest(),'053dd204cdc09e8973c5a97d09d4d4b2b88b2b3a8a5f376b89aafaa88aa15b8f')
 def test_nested_legal_nonGUID_wrapper_same_owner_qualifies(self):
  source=definition().replace('<section','<div class="litem_content content"><section',1).replace('</section>','</section></div>');ref=self.refs(source)[0];self.assertFalse(ref['required']);self.assertEqual(ref['kind'],'owned_definition_self_anchor')
 def test_nested_distinct_GUID_owner_refuses_qualification(self):
  source=definition().replace('<section','<div class="section_content content" id="999_content"><section',1).replace('</section>','</section></div>');self.assertTrue(self.refs(source)[0]['required'])
 def test_municipal_nestedarticle_behavior_unchanged(self):
  base='https://synthetic.municipal.codes/Code';raw=b'<html><title>Synthetic Code</title><body><p>The Synthetic Code is current through Ordinance1.</p><main><article class="type-Chapter" id="1" data-history="/Code/1/history"><header>Chapter1</header><div>Parent own text.</div><article class="type-Section" id="1.1" data-history="/Code/1.1/history"><header>Section1.1</header><p>Child mandatory text.<img src="/map.png"></p></article></article></main></body></html>'
  identity=A.identity(raw,base,'municipal.codes',base);rows=A.parse_municipal(raw,base+'/1',base,identity)['records'];self.assertEqual(len(rows),2);self.assertNotIn('Child mandatory text.',rows[0]['text']);self.assertIn('Child mandatory text.',rows[1]['text']);self.assertIn('[IMAGE]',rows[1]['text'])
if __name__=='__main__':unittest.main()
