"""Independent retained-source list/consumer proof. No candidate/PDF imports."""
import pathlib,json,hashlib,csv,io,sys,copy,datetime
from html.parser import HTMLParser
P=pathlib.Path(sys.argv[1]).resolve();OUT=pathlib.Path(sys.argv[2]);h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());canon=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest();rows=lambda p:[json.loads(x)for x in p.read_text().splitlines()]
assert h(P/'MANIFEST.json')=='7891f16e4fb62b2dfd0348bda26e0a314a656ce39a507da259c6aaebecb36203';m=read(P/'MANIFEST.json')['files'];assert all(h(P/n)==s for n,s in m.items())
ID='82-0c6b3dc40877::printed-unit:54';SHA='915fe1fdf8ff5da33acfce7d08637808cb57886fbbc7f157b2b81bfcf970827c';assert h(P/'source/start.pdf')==SHA
old=read(P/'source/selected-record.json');w=read(P/'source/native-page26-glyph-witness.json');base=rows(P/'source/baseline172.jsonl');after=rows(P/'actual-default172/records.jsonl');assert base[54]==old and len(base)==len(after)==172
assert canon(w)=='2501d22a32e27da8f5a7de91968c635105879de4bc710afbd5e7ecabef5d812a'and w['source_sha256']==SHA and w['physical_page']==26 and w['record_id']==ID
fs=old['source_fragments'];assert canon(fs)=='ecf486499263aef952fce19f8a94661e0173da503d51fb5a34eb47b5deb56c01'
assert [f['block_index']for f in fs]==list(range(9,19));assert len(w['blocks'])==10
assert sum(len(g['glyphs'])for g in w['blocks'])==516
for f,g in zip(fs,w['blocks']):
 assert g['page']==f['page']==26 and g['block_index']==f['block_index']and g['bbox']==f['block']['bbox']and g['text']==f['block']['text']
 assert ''.join(''.join(x['text']for x in g['glyphs']).split())==''.join(g['text'].split())
for i in (4,5,8,9):assert w['blocks'][i]['glyphs'][0]['text']=='▸'and w['blocks'][i]['glyphs'][0]['fontname']=='DAAAAA+MS-PGothic'
assert fs[3]['block']['text'].startswith('a) ')and fs[6]['block']['text'].startswith('b) ')
assert fs[3]['block']['text'].endswith(':')and fs[7]['block']['text']=='bores and as follows:'
assert fs[3]['block']['bbox'][0]==fs[6]['block']['bbox'][0]==108
assert all(fs[i]['block']['bbox'][0]==126 for i in (4,5,7,8,9))
assert not fs[7]['block']['text'].startswith(('▸','a)','b)'))
class Tree(HTMLParser):
 def __init__(self):super().__init__();self.stack=[];self.lis=[];self.text=[];self.tags=[]
 def handle_starttag(self,t,a):
  self.stack.append(t);self.tags.append(t)
  if t=='li':self.lis.append((tuple(self.stack),dict(a)))
 def handle_endtag(self,t):assert self.stack.pop()==t
 def handle_data(self,t):self.text.append(t)
def validate(x):
 assert x['text']==old['text']and x['source_fragments']==fs
 assert x['ordered_blocks'][:3]==old['ordered_blocks'][:3]and len(x['ordered_blocks'])==4
 b=x['ordered_blocks'][3];assert b['kind']=='nested_list'and b['ordered']is True
 assert [p['printed_marker']for p in b['items']]==['a)','b)']
 groups=[([12],[[13],[14]]),([15,16],[[17],[18]])];owned=[]
 for parent,(own,children)in zip(b['items'],groups):
  assert [f['source_block_index']for f in parent['own_fragments']]==own
  assert len(parent['children'])==2
  for f in parent['own_fragments']:owned.append(f)
  for child,indices in zip(parent['children'],children):
   assert child['printed_marker']=='▸'and child['children']==[]and[ f['source_block_index']for f in child['own_fragments']]==indices
   owned.extend(child['own_fragments'])
 assert [f['source_block_index']for f in owned]==list(range(12,19))
 for f in owned:assert f['source_page']==26 and f['block']==fs[f['source_block_index']-9]['block']
 assert b['text']=='\n'.join(f['block']['text']for f in fs[3:])
 assert b['word_ids']==[wid for f in fs[3:]for wid in f['block']['word_ids']]
 words=[wid for block in x['ordered_blocks']for wid in block['word_ids']];assert len(words)==len(set(words))==105
 assert x['superseded_flat_list_diagnostics']['original_fields']=={k:old[k]for k in ['text','ordered_blocks','qualification','canonical_structure_selection']}
 t=Tree();t.feed(x['html']);assert not t.stack and t.tags.count('ol')==1 and t.tags.count('ul')==2 and len(t.lis)==6
 assert [p.count('li')for p,a in t.lis]==[1,2,2,1,2,2]
 assert ''.join(''.join(t.text).split())==''.join(old['text'].split())
 assert not set(t.tags)&{'img','picture','svg','object','embed','canvas'}
 assert x['qualification']['nested_list_hierarchy_qualified']is True and x['qualification']['paragraph_continuation_semantics_qualified']is False and x['qualification']['whole_publication_complete']is False
 return True
validate(after[54]);faults=[]
for label,change in [('lost child',lambda x:x['ordered_blocks'][3]['items'][0]['children'].pop()),('continuation child misownership',lambda x:x['ordered_blocks'][3]['items'][1]['own_fragments'].pop()),('lost canonical HTML text',lambda x:x.update(html=x['html'].replace('bores and as follows:','')) )]:
 x=copy.deepcopy(after[54]);change(x)
 try:validate(x)
 except AssertionError:faults.append(label)
 else:raise AssertionError('Fault accepted:'+label)
assert len(faults)==3
for dirname,src,count,changedidx,images in [('actual-default172','baseline172.jsonl',172,54,5),('mixed828','baseline828.jsonl',828,226,201)]:
 a=(P/'source'/src).read_bytes().splitlines();b=(P/dirname/'records.jsonl').read_bytes().splitlines();assert len(a)==len(b)==count
 assert [i for i,(aa,bb)in enumerate(zip(a,b))if aa!=bb]==[changedidx]
 rs=[json.loads(x)for x in b];assert rs[changedidx]['id']==ID;validate(rs[changedidx])
 cs=list(csv.DictReader((P/dirname/'records.csv').open()));assert len(cs)==count
 for x,c in zip(rs,cs):assert x['id']==c['id']and x['text']==c['text']and x.get('html','')==c['html']
 assert sum(x['text'].count('[IMAGE]')for x in rs)==images
 assert rs[0]['source_document_evidence']['nested_list_hierarchy_qualified']is False
proof=read(P/'actual-proof.json');assert proof['details']['nested_list_hierarchy_qualified']is False and proof['details']['source_logical_structure_qualified']is False
for k in ['required_external_legal_dependencies_complete','edition_currentness_qualified','paragraph_continuation_semantics_qualified','source_native_reading_order_complete']:assert proof['details'][k]is False
assert all(h(P/n)==s for n,s in m.items())
report={'passed':True,'reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'packet_manifest_sha256':h(P/'MANIFEST.json'),'files_unchanged':len(m),'source_sha256':SHA,'native_glyph_witness_digest':canon(w),'source_page':26,'source_blocks':10,'source_words_once':105,'native_text_glyphs':516,'outer_items':2,'literal_arrow_children':4,'unmarked_continuation_owning_parent':'b)','sameindent_continuation_not_child':True,'canonical_HTML_text_and_nested_structure_exact':True,'canonical_JSON_CSV_text_HTML_exact':True,'byte_identical_default_records':171,'byte_identical_mixed_records':827,'only_changed_default_index':54,'only_changed_mixed_index':226,'image_positions_owners_unchanged':201,'independent_consumer_faults_refused':faults,'global_hierarchy_order_edition_dependencies_complete':False,'native_parse_performed':False,'candidate_imported':False,'network_or_image_operations':False,'scope':'Only exact source §5.3 physical26 literal list. Prior full62 source lineage preserved; no whole-publication or new current-acquisition qualification.'}
OUT.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
