import copy,csv,io,json,pathlib,socket,unittest
from unittest.mock import patch
from html.parser import HTMLParser
from . import infrastructure_nested_list as m
HERE=pathlib.Path(__file__).resolve().parent
class HTMLTree(HTMLParser):
 def __init__(self):super().__init__();self.tags=[];self.text=[];self.stack=[];self.paths=[]
 def handle_starttag(self,t,a):
  self.tags.append(t);self.stack.append(t)
  if t=='li':self.paths.append(tuple(self.stack))
 def handle_endtag(self,t):assert self.stack.pop()==t
 def handle_data(self,d):self.text.append(d)
class ExactSourceList(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.w=json.loads((HERE/'fixtures/infrastructure-printed-native/native-page26-list-witness.json').read_text())
  # This record is the previous exact production-shaped172 projection; independent native witness is separate.
  cls.r=json.loads((HERE/'fixtures/infrastructure-printed-native/utility-potholes-source-unit.json').read_text())
 def setUp(self):
  p=patch.object(socket,'socket',side_effect=AssertionError('No network'));p.start();self.addCleanup(p.stop)
 def test_actual_two_outer_four_child_items_canonical(self):
  r=m.project(self.r,self.w);b=r['ordered_blocks'][3];self.assertEqual(b['kind'],'nested_list');self.assertEqual([p['printed_marker'] for p in b['items']],['a)','b)']);self.assertEqual([len(p['children']) for p in b['items']],[2,2]);self.assertEqual(sum(len(x['word_ids']) for x in r['ordered_blocks']),105);self.assertEqual(r['text'],self.r['text'])
 def test_hanging_continuation_is_not_child(self):
  b=m.project(self.r,self.w)['ordered_blocks'][3];parent=b['items'][1];self.assertEqual([f['source_block_index'] for f in parent['own_fragments']],[15,16]);self.assertTrue(m.own_text(parent).endswith('bores and as follows:'));self.assertEqual([c['own_fragments'][0]['source_block_index'] for c in parent['children']],[17,18])
 def test_native_marker_is_real_text_no_image_html(self):
  r=m.project(self.r,self.w);h=HTMLTree();h.feed(r['html']);self.assertEqual(h.tags.count('ol'),1);self.assertEqual(h.tags.count('ul'),2);self.assertEqual(h.tags.count('li'),6);self.assertEqual(sum(p.count('li')==2 for p in h.paths),4);self.assertFalse(set(h.tags)&{'img','picture','svg','object','canvas'});self.assertEqual(''.join(''.join(h.text).split()),''.join(r['text'].split()))
 def test_raw_owner_and_source_mutations_fail_closed(self):
  for k,v in [('document_id','wrong'),('raw_sha256','0'*64),('raw_ref','wrong.pdf'),('source_document_url','https://example.org'),('source_pages',[27]),('heading','other'),('state','MO')]:
   r=copy.deepcopy(self.r);r[k]=v
   with self.subTest(k=k),self.assertRaises(AssertionError):m.project(r,self.w)
 def test_each_marker_word_geometry_mutation_refuses(self):
  for i in range(3,10):
   for k,v in [('text','changed'),('bbox',[0,0,1,1]),('word_ids',['invented'])]:
    r=copy.deepcopy(self.r);r['source_fragments'][i]['block'][k]=v
    with self.subTest(i=i,k=k),self.assertRaises(AssertionError):m.project(r,self.w)
 def test_native_glyph_font_order_owner_mutations_refuse(self):
  for change in [lambda w:w['blocks'][4]['glyphs'][0].update(text='image'),lambda w:w['blocks'][4]['glyphs'][0].update(fontname='Other'),lambda w:w['blocks'].reverse(),lambda w:w.update(source_sha256='0'*64),lambda w:w['blocks'][4]['glyphs'][0].update(x0=1)]:
   w=copy.deepcopy(self.w);change(w)
   with self.assertRaises(AssertionError):m.project(self.r,w)
 def test_original_diagnostics_word_and_global_gates_preserved(self):
  r=m.project(self.r,self.w);self.assertEqual(r['superseded_flat_list_diagnostics']['original_fields'],{k:self.r[k] for k in ['text','ordered_blocks','qualification','canonical_structure_selection']});self.assertEqual(r['source_fragments'],self.r['source_fragments']);self.assertTrue(r['qualification']['nested_list_hierarchy_qualified']);self.assertFalse(r['qualification']['whole_publication_complete']);self.assertFalse(r['qualification']['paragraph_continuation_semantics_qualified'])
 def test_csv_html_and_json_primary_align(self):
  r=m.project(self.r,self.w);out=m.outputs([r]);j=json.loads(out['records.jsonl']);c=list(csv.DictReader(io.StringIO(out['records.csv'].decode())))[0];self.assertEqual(c['text'],j['text']);self.assertEqual(c['html'],j['html']);self.assertEqual(j['ordered_blocks'][3]['kind'],'nested_list')
 def test_nonmatching_unit_is_exact_noop(self):
  r=copy.deepcopy(self.r);r['id']='other';self.assertEqual(m.project(r,{}),r)
 def test_wrong_native_bytes_refuse_before_parser(self):
  with patch('pdfplumber.open',side_effect=AssertionError('Must not parse')) as parser:
   with self.assertRaises(AssertionError):m.native_witness(b'wrong',self.r)
   parser.assert_not_called()
if __name__=='__main__':unittest.main(verbosity=2)
