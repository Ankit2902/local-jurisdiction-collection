"""Read-only consumer audit. Imports no candidate projection/parser modules."""
import sys
sys.dont_write_bytecode=True
import collections,csv,gzip,hashlib,io,json,re
from html.parser import HTMLParser
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def records(b):return [json.loads(x) for x in b.decode('utf-8').split('\n') if x]
def walk(items):
 for x in items:
  yield x
  yield from walk(x.get('children',[]))
class CanonicalHTML(HTMLParser):
 def __init__(self):
  super().__init__(convert_charrefs=True);self.stack=[];self.fragments=[];self.cells=[];self.counts=collections.Counter();self.text=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs);self.counts[tag]+=1
  assert tag not in {'img','svg','image','picture','source','object','embed','input','canvas','script','iframe'}
  for k,v in attrs:
   assert not k.lower().startswith('on')
   assert not re.search(r'data\s*:\s*image/|url\s*\(',v or '',re.I)
  n={'tag':tag,'attrs':a,'text':[]};self.stack.append(n)
  if 'data-source-fragment' in a:self.fragments.append(n)
  if tag in {'td','th'}:self.cells.append(n)
 def handle_data(self,data):
  self.text.append(data)
  for n in self.stack:n['text'].append(data)
 def handle_endtag(self,tag):
  assert self.stack and self.stack[-1]['tag']==tag,tag
  self.stack.pop()
 def finish(self):
  self.close();assert not self.stack
  for x in self.fragments+self.cells:x['plain']=''.join(x['text'])
def audit(p):
 before={x.relative_to(p).as_posix():sha(x) for x in p.rglob('*') if x.is_file()}
 m=json.loads((p/'MANIFEST.json').read_text())
 assert sha(p/'MANIFEST.json')=='ba06d8fbc4eb98aa2ac1f5add08828086353c6e4cd91d478f411f7c2ff19ec39'
 assert {x['path']:x['sha256'] for x in m['files']}=={k:v for k,v in before.items() if k!='MANIFEST.json'}
 data=gzip.decompress((p/'evidence/baseline-records.jsonl.gz').read_bytes())
 assert hashlib.sha256(data).hexdigest()=='8bf0cf6e1d319d900fbdafff16dd8f051e945f39a6102aaad035fe3a4001afe9'
 old=records(data);new=records((p/'actual/records.jsonl').read_bytes())
 assert len(old)==len(new)==172
 iv=json.loads((p/'evidence/full-source-inventory.json').read_text())
 inv={f['id']:f for f in iv['fragments']}
 csv.field_size_limit(64*1024*1024)
 crows=list(csv.DictReader(io.StringIO((p/'actual/records.csv').read_text(),newline='')))
 assert len(crows)==172
 allwords=[];sourceids=[];pages=set();unresolved=[];stats=collections.Counter();own={}
 changes={'ordered_blocks','html','canonical_structure_selection','superseded_printed_flow_diagnostics','source_printed_flow_evidence'}
 rowproof=[]
 for a,b,c in zip(old,new,crows):
  assert a['id']==b['id']==c['id']
  assert a['text']==b['text']==c['text']
  assert a['tables']==b['tables'] and a['source_fragments']==b['source_fragments']
  for k in set(a)|set(b):
   if k not in changes:assert a.get(k)==b.get(k),(b['id'],k)
  diagnostics=b['superseded_printed_flow_diagnostics']['original_fields']
  for k,v in diagnostics.items():assert k in a and a[k]==v,(b['id'],k,'diagnostic')
  assert c['html']==b['html'] and json.loads(c['source_pages'])==b['source_pages']
  h=CanonicalHTML();h.feed(b['html']);h.finish()
  nodes=list(walk(b['ordered_blocks']));leaves=[n for n in nodes if n['kind']=='source_leaf']
  assert len(leaves)==len(a['source_fragments'])==len(h.fragments)
  for f,n,e in zip(a['source_fragments'],leaves,h.fragments):
   fid=a['id']+'::source:'+str(f['page'])+':'+str(f['block_index'])
   assert fid==n['id']==e['attrs']['data-source-fragment']
   assert str(f['page'])==e['attrs']['data-source-page'] and f['page']==n['page']
   assert n['text']==f['block']['text'] and n['bbox']==f['block']['bbox']
   assert n['word_ids']==f['block'].get('word_ids',[])
   assert inv[fid]['text']==n['text'] and inv[fid]['word_ids']==n['word_ids'] and inv[fid]['role']==n['role']
   headcount=a['source_outline']['blocks'] if a['source_outline'] else 0
   position=a['source_fragments'].index(f)
   role=('running_page_control' if f['page_control'] else 'source_heading' if position<headcount else
         'image_placeholder' if f['block']['kind']=='image_placeholder' else 'printed_grid' if f['block']['kind']=='table' else
         'source_cover_line' if a['unit_type']=='frontmatter' else 'contents_line' if a['unit_type']=='table-of-contents' else 'body_text_line')
   assert n['role']==role
   if f['block']['kind']=='table':
    assert ''.join(e['plain'].split())==''.join(n['text'].split())
   else:assert e['plain']==n['text']
   sourceids.append(fid);allwords.extend(n['word_ids']);pages.add(n['page']);own[fid]=f
  cells=[cell for t in a['tables'] for cell in t['cells']]
  assert len(cells)==len(h.cells)
  for cell,e in zip(cells,h.cells):
   assert e['attrs']['data-source-cell']==cell['id']
   assert e['plain']==cell['text']
   assert int(e['attrs']['rowspan'])==cell['rowspan'] and int(e['attrs']['colspan'])==cell['colspan']
  ev=b['source_printed_flow_evidence']
  assert ev['whole_publication_qualified'] is False and ev['legal_list_paragraph_intent_qualified'] is False
  assert ev['source_fragments']==[n['id']for n in leaves]
  assert h.counts['h2']==bool(a['source_outline'])
  stats.update({'cells':len(cells),'tables':len(a['tables']),'paragraphs':h.counts['p'],
                'lists':h.counts['ul']+h.counts['ol'],'items':h.counts['li'],'headings':h.counts['h2'],
                'IMAGE':b['html'].count('[IMAGE]'),'nonlist':len(ev['source_explicit_nonlist_dispositions'])})
  assert b['html'].count('[IMAGE]')==a['text'].count('[IMAGE]')
  assert ev['list_count']==h.counts['ul']+h.counts['ol'] and ev['literal_marker_items']==h.counts['li']
  assert ev['printed_paragraph_groups']==h.counts['p']
  unresolved.extend(ev['unresolved'])
  rowproof.append({'id':b['id'],'source_fragments':len(leaves),'cells':len(cells),'html_sha256':hashlib.sha256(b['html'].encode()).hexdigest()})
 assert len(sourceids)==len(set(sourceids))==len(inv)==1776
 assert len(allwords)==len(set(allwords))==18662
 assert pages==set(range(1,63))
 assert stats=={'cells':79,'tables':5,'paragraphs':385,'lists':19,'items':85,'headings':171,'IMAGE':5,'nonlist':8},stats
 assert len(unresolved)==38
 for u in unresolved:
  assert u['kind']=='cross_page_paragraph_boundary' and u['qualification'] is False
  assert own[u['before']]['page']+1==own[u['after']]['page']
 capsule=p/'runtime/collectors/encodeplus/infrastructure-multiline-native-geometry.json'
 assert sha(capsule)=='ce34644c285715bfb453e40b0431413bb10fa29287cac362cee7fd9c3bc4b732'
 g=json.loads(capsule.read_text());assert g['source_sha256']==sha(p/'raw/source.pdf')=='915fe1fdf8ff5da33acfce7d08637808cb57886fbbc7f157b2b81bfcf970827c'
 assert g['target_pages']==[11,12,13,14] and len(g['fragments'])==9 and not g['whole_document_parse'] and not g['forbidden_image_or_network_calls']
 linecount=0
 for f in g['fragments']:
  src=own[f['source_fragment']]
  assert f['page']==src['page'] and f['block_index']==src['block_index'] and f['source_bbox']==src['block']['bbox']
  assert f['original_source_text']==src['block']['text'] and f['original_word_ids']==src['block']['word_ids']
  assert [w['id']for l in f['lines']for w in l['words']]==src['block']['word_ids']
  assert '\n'.join(l['text']for l in f['lines'])==src['block']['text']
  for l in f['lines']:
   assert len(l['native_query_bbox_pdf'])==4 and all(isinstance(v,(int,float))for v in l['native_query_bbox_pdf'])
   assert ''.join(l['text'].split())==''.join(l['independent_native_text'].split())
   assert l['independent_nonwhitespace_order_equal'] is True
   linecount+=1
 assert linecount==68
 # Previously source-qualified page26 nested membership must survive new flow.
 assert old[54]['source_nested_list_native_witness']==new[54]['source_nested_list_native_witness']
 membership=[]
 def nested(items,parents):
  for item in items:
   if item['kind']=='source_item':
    leaf=next(x for x in walk(item['children'])if x['kind']=='source_leaf')
    membership.append({'marker':item['literal_marker'],'block_index':leaf['block_index'],'parents':parents[:]})
    nested(item['children'],parents+[item['literal_marker']])
   else:nested(item.get('children',[]),parents)
 nested(new[54]['ordered_blocks'],[])
 assert membership==[{'marker':'a)','block_index':12,'parents':[]},{'marker':'▸','block_index':13,'parents':['a)']},{'marker':'▸','block_index':14,'parents':['a)']},{'marker':'b)','block_index':15,'parents':[]},{'marker':'▸','block_index':17,'parents':['b)']},{'marker':'▸','block_index':18,'parents':['b)']}]
 summary=json.loads((p/'VALIDATION-SUMMARY.json').read_text())
 d=summary['printed_flow_dimensions']
 for k in ['source_native_reading_order_complete','nested_list_hierarchy_complete','paragraph_continuation_semantics_complete','required_dependencies_complete','edition_complete','publication_complete']:
  assert d[k] is False,k
 assert d['unresolved_counts']=={'cross_page_paragraph_boundary':38}
 assert summary['whole_publication_accepted'] is False
 assert before=={x.relative_to(p).as_posix():sha(x)for x in p.rglob('*')if x.is_file()}
 return {'passed':True,'packet_manifest_sha256':sha(p/'MANIFEST.json'),'packet_files_unchanged':len(before),
  'source_units':172,'source_pages':62,'source_fragments_once':1776,'source_words_once':18662,'stats':dict(stats),
  'cross_page_relationships_unqualified':38,'multiline_geometry_fragments':9,'retained_native_queries_checked_metadata_only':68,
  'all_canonical_JSON_HTML_CSV_source_fields_and_superseded_fields_conserved':True,'page26_prior_source_membership_unchanged':membership,
  'whole_publication_accepted':False,'new_native_queries':0,'native_image_network_operations':0,'rows':rowproof}
if __name__=='__main__':
 result=audit(Path(sys.argv[1]).resolve());print(json.dumps(result,ensure_ascii=False,indent=2))
