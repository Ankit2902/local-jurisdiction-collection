import sys
sys.dont_write_bytecode=True
import argparse,types,importlib,json,unittest,copy,socket,subprocess,base64
from pathlib import Path
from unittest.mock import patch
from PIL import Image
ap=argparse.ArgumentParser();ap.add_argument('--collector-root',required=True,type=Path);ap.add_argument('--ledger',required=True,type=Path);args,rest=ap.parse_known_args();sys.argv=[sys.argv[0]]+rest
pkg=types.ModuleType('_candidate');pkg.__path__=[str(args.collector_root.resolve())];sys.modules['_candidate']=pkg;E=importlib.import_module('_candidate.engine');A=importlib.import_module('_candidate.adapters');rows=json.loads(args.ledger.read_text())['records'];BASE='https://ecode360.com/AL0934'
def link(row):
 # Source context wraps the exact authored anchor; no law text is fetched.
 context=row['source_parent_context'];source=row['source_anchor'];label=row['label'];pos=context.find(label);assert pos>=0;html='<p>'+context[:pos]+source+context[pos+len(label):]+'</p>';return A.link_refs(html,'https://ecode360.com/'+row['owner_id'],row['owner_id'])[0]
class SourceContext(unittest.TestCase):
 @classmethod
 def setUpClass(c):
  c.guards=[]
  def no(*a,**k):raise AssertionError('Network/image decode forbidden')
  for obj,name in [(socket,'create_connection'),(socket.socket,'connect'),(subprocess,'Popen'),(base64,'b64decode'),(Image,'open')]:g=patch.object(obj,name,no);g.start();c.guards.append(g)
 @classmethod
 def tearDownClass(c):
  for g in reversed(c.guards):g.stop()
 def yes(self,l):return E.statutory_reference(l['url'],BASE,'ecode360',l)
 def test_all21_exact_source_contexts(self):
  for row in rows:
   with self.subTest(url=row['url'],owner=row['owner_id']):self.assertTrue(self.yes(link(row)))
 def test_unknown_namespace_refuses(self):
  l=link(rows[0]);l['url']=l['url'].replace('/ABC/','/UNKNOWN/');l['source_statutory_evidence']['source_url']=l['url'];self.assertFalse(self.yes(l))
 def test_other_law_namespace_refuses(self):
  l=link(rows[0]);l['url']=l['url'].replace('/ABC/','/COR/');l['source_statutory_evidence']['source_url']=l['url'];self.assertFalse(self.yes(l))
 def test_cross_owner_refuses(self):
  l=link(rows[0]);l['owner_id']='other';self.assertFalse(self.yes(l))
 def test_missing_statref_refuses(self):
  l=link(rows[0]);l['source_statutory_evidence']['source_classes']=[];self.assertFalse(self.yes(l))
 def test_no_source_context_refuses(self):
  l=link(rows[0]);del l['source_statutory_evidence'];self.assertFalse(self.yes(l))
 def test_law_context_mismatch_refuses(self):
  l=link(rows[0]);l['source_statutory_evidence']['source_context_text']='Section140 of the local municipal code.';self.assertFalse(self.yes(l))
 def test_different_label_and_target_refuses(self):
  l=link(rows[0]);l['url']=l['url'].replace('/140','/141');l['source_statutory_evidence']['source_url']=l['url'];self.assertFalse(self.yes(l))
 def test_different_target_even_if_forged_label_refuses(self):
  l=link(rows[0]);l['url']=l['url'].replace('/140','/141');e=l['source_statutory_evidence'];e['source_url']=l['url'];e['source_label']=l['label']='141';self.assertFalse(self.yes(l))
 def test_download_and_mime_remain_required(self):
  for attr in ['download','type="application/pdf"']:
   l=A.link_refs('<p>Alcoholic Beverage Control Law § <a class="statref" '+attr+' href="https://municipal.codes/NY/ABC/140">140</a></p>',BASE,'1')[0];self.assertFalse(self.yes(l))
 def test_samehost_local_pdf_attachment_not_statute(self):
  for name in ['211a Appendix I','211b Appendix II','211c Appendix III','375a Table of Zoning Map Amendments']:
   self.assertFalse(E.statutory_reference('https://ecode360.com/attachment/336787/AL0934-'+name+'.pdf',BASE,'ecode360'))
 def test_forwarder_pdf_not_statute(self):self.assertFalse(E.statutory_reference('https://municipal.codes/NY/ABC/140.pdf',BASE,'ecode360',link(rows[0])))
 def test_pdf_namespace_route_with_matching_source_context_refuses(self):
  l=A.link_refs('<p>Alcoholic Beverage Control Law § <a class="statref" href="https://municipal.codes/NY/ABC/140.pdf">140.pdf</a></p>',BASE,'1')[0];self.assertFalse(self.yes(l));self.assertTrue(A.asset_refs('<a class="statref" href="https://municipal.codes/NY/ABC/140.pdf">140.pdf</a>',BASE,'1')[0]['required'])
 def test_lookalike_host_http_query_fragment_refuse(self):
  for u in ['http://municipal.codes/NY/ABC/140','https://municipal.codes.evil.invalid/NY/ABC/140','https://municipal.codes/NY/ABC/140?download=true','https://municipal.codes/NY/ABC/140#map']:
   l=link(rows[0]);l['url']=u;l['source_statutory_evidence']['source_url']=u;self.assertFalse(self.yes(l))
 def test_bare_USC_without_title_context_refuses(self):
  l=link(rows[1]);l['source_statutory_evidence']['source_context_text']='Download local attachment8.';self.assertFalse(self.yes(l))
 def test_article_context_required(self):
  row=next(r for r in rows if r['url'].endswith('/A6-A'));l=link(row);l['source_statutory_evidence']['source_context_text']='Real Property Law6-A.';self.assertFalse(self.yes(l))
 def test_hash_witness_missing_refuses(self):
  l=link(rows[0]);del l['source_statutory_evidence']['source_anchor_html_sha256'];self.assertFalse(self.yes(l))
 def test_SVG_multiline_payload_removed_from_new_context(self):
  source='<p><svg><text>DATA:IMAGE/PNG;base64,QUJD\nCONTINUATION_SENTINEL</text></svg>Alcoholic Beverage Control Law § <a class="statref" href="https://municipal.codes/NY/ABC/140">140</a></p>';l=A.link_refs(source,BASE,'1')[0];self.assertTrue(self.yes(l));e=l['source_statutory_evidence'];self.assertIn('[IMAGE]',e['source_context_text']);self.assertIn('Alcoholic Beverage Control Law',e['source_context_text']);self.assertNotIn('DATA:IMAGE',str(e));self.assertNotIn('CONTINUATION_SENTINEL',str(e));self.assertEqual(e['processed_owner_context_html_sha256'],A.digest(str(A.BeautifulSoup(source,'html.parser').p).encode()))
 def test_image_only_law_context_not_qualified(self):
  source='<p><svg><text>Alcoholic Beverage Control Law §140</text></svg><a class="statref" href="https://municipal.codes/NY/ABC/140">140</a></p>';l=A.link_refs(source,BASE,'1')[0];self.assertFalse(self.yes(l));self.assertEqual(l['source_statutory_evidence']['source_context_text'],'[IMAGE] 140')
 def test_malformed_graphic_anchor_context_refuses(self):
  source='<p><svg><text>DATA:IMAGE/PNG;base64,QUJD\nCONTINUATION_SENTINEL</text>Alcoholic Beverage Control Law §<a class="statref" href="https://municipal.codes/NY/ABC/140">140</a></p>';l=A.link_refs(source,BASE,'1')[0];self.assertNotIn('source_statutory_evidence',l);self.assertFalse(self.yes(l))
 def test_ordinary_context_legal_text_unchanged(self):
  l=link(rows[0]);self.assertEqual(l['source_statutory_evidence']['source_context_text'],rows[0]['source_parent_context']);self.assertTrue(self.yes(l))
 def test_actual_record_descendant_SVG_labels_no_payload(self):
  body='<div id="1_content" class="content"><p>Alcoholic Beverage Control Law § <a class="statref" href="https://municipal.codes/NY/ABC/140"><svg><text>data:image/png;base64,QUFB\nQkJC_SENTINEL</text></svg>140</a></p></div>';r=A._record('1','Rule','section',body,'https://ecode360.com/1');self.assertNotIn('data:image',str(r).lower());self.assertNotIn('QkJC_SENTINEL',str(r));self.assertEqual(r['links'][0]['label'],'[IMAGE] 140');self.assertEqual(r['links'][0]['source_statutory_evidence']['source_label'],'[IMAGE] 140');self.assertIn('[IMAGE]',r['semantic_html'])
 def test_actual_record_ordinary_image_anchor_caption_label(self):
  body='<div id="1_content" class="content"><p><a href="https://example.invalid/map.png">Map caption</a></p></div>';r=A._record('1','Rule','section',body,'https://ecode360.com/1');self.assertEqual(r['links'][0]['url'],'https://example.invalid/map.png');self.assertEqual(r['links'][0]['label'],'Map caption [IMAGE]');self.assertIn('Map caption[IMAGE]',r['text']);self.assertEqual(r['image_placeholder_count'],1)
 def test_actual_record_class_attribute_pixel_not_copied(self):
  source='<div class="content" id="1_content"><p>Alcoholic Beverage Control Law §<a class="statref DATA:IMAGE/PNG;base64,QUJD\nCLASS_PIXEL_SENTINEL" href="https://municipal.codes/NY/ABC/140">140</a></p></div>';r=A._record('1','Rule','section',source,'https://ecode360.com/1');self.assertNotIn('data:image/',str(r).lower());self.assertNotIn('CLASS_PIXEL_SENTINEL',str(r));self.assertNotIn('source_statutory_evidence',r['links'][0]);self.assertFalse(self.yes(r['links'][0]))
 def test_prior_known_namespace_behavior_unchanged(self):
  for u in ['https://municipal.codes/NY/GMU/103','https://municipal.codes/US/USC/26/501','https://phoenix.municipal.codes/AZ/ARS/1-201']:self.assertTrue(E.statutory_reference(u,'https://phoenix.municipal.codes/Charter','municipal.codes'))
if __name__=='__main__':unittest.main()
