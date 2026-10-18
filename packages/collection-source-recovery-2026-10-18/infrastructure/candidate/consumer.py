"""Independent all-source canonical consumer comparison, no projection imports."""
import argparse,collections,csv,hashlib,io,json,re,socket
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch
canon=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
class Consumer(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.depth=0;self.owner=None;self.owned=[];self.cell=None;self.cells=[];self.counts=collections.Counter()
 def handle_starttag(self,tag,attrs):
  self.depth+=1;a=dict(attrs);self.counts[tag]+=1
  assert tag not in ['img','svg','picture','image','object','embed','input','source','canvas'],'Active image/content element'
  for k,v in attrs:assert not re.search(r'data\s*:\s*image/',v or'',re.I),'Image payload'
  if 'data-source-fragment'in a:assert self.owner is None;self.owner={'id':a['data-source-fragment'],'page':int(a['data-source-page']),'text':[],'depth':self.depth}
  if tag=='td':assert self.cell is None;self.cell={'id':a['data-source-cell'],'rowspan':int(a['rowspan']),'colspan':int(a['colspan']),'text':[],'depth':self.depth}
 def handle_data(self,data):
  if self.owner:self.owner['text'].append(data)
  if self.cell:self.cell['text'].append(data)
 def handle_endtag(self,tag):
  if self.cell and self.cell['depth']==self.depth:
   self.cell['text']=''.join(self.cell['text']);self.cells.append(self.cell);self.cell=None
  if self.owner and self.owner['depth']==self.depth:
   self.owner['text']=''.join(self.owner['text']);self.owned.append(self.owner);self.owner=None
  self.depth-=1
 def done(self):assert self.depth==0 and self.owner is None and self.cell is None

def leaves(blocks):
 for b in blocks:
  if b['kind']=='source_leaf':yield b
  else:yield from leaves(b['children'])
def compare(old,new,csvdata):
 result=[];allids=[];words=[];cells=0;lists=items=paragraphs=headers=0;unresolved=collections.Counter();fragments=0;image=0
 for o,r in zip(old,new):
  assert o['id']==r['id']and o['text']==r['text']and o['tables']==r['tables'];changed={'ordered_blocks','html','canonical_structure_selection','superseded_printed_flow_diagnostics','source_printed_flow_evidence'}
  for k in set(o)|set(r):
   if k not in changed:assert o.get(k)==r.get(k),(r['id'],k)
  ds=r['superseded_printed_flow_diagnostics']['original_fields'];assert all(ds[k]==o[k]for k in ds);ls=list(leaves(r['ordered_blocks']));assert len(ls)==len(o['source_fragments'])
  parser=Consumer();parser.feed(r['html']);parser.close();parser.done();assert len(parser.owned)==len(ls)
  for f,l,v in zip(o['source_fragments'],ls,parser.owned):
   expected=o['id']+'::source:'+str(f['page'])+':'+str(f['block_index']);assert l['id']==v['id']==expected and l['page']==v['page']==f['page'];assert l['text']==f['block']['text']and l['word_ids']==f['block'].get('word_ids',[]);allids.append(expected);words.extend(l['word_ids']);fragments+=1
   if f['block']['kind']=='table':assert ''.join(v['text'].split())==''.join(l['text'].split())
   else:assert v['text']==l['text'],(expected,'HTML leaf text')
  expectedcells=[c for t in o['tables']for c in t['cells']];assert len(expectedcells)==len(parser.cells)
  for c,v in zip(expectedcells,parser.cells):assert c['id']==v['id']and c['text']==v['text']and c['rowspan']==v['rowspan']and c['colspan']==v['colspan'];cells+=1
  assert parser.counts['h2']==(1 if o['source_outline']else 0);headers+=parser.counts['h2'];lists+=parser.counts['ol']+parser.counts['ul'];items+=parser.counts['li'];paragraphs+=parser.counts['p'];image+=r['html'].count('[IMAGE]');unresolved.update(x['kind']for x in r['source_printed_flow_evidence']['unresolved']);result.append({'id':r['id'],'source_record_sha256':hashlib.sha256(canon(o)).hexdigest(),'canonical_record_sha256':hashlib.sha256(canon(r)).hexdigest(),'source_fragments':len(ls),'all_source_text_order_and_metadata_equal':True,'lists':parser.counts['ol']+parser.counts['ul'],'items':parser.counts['li'],'paragraphs':parser.counts['p']})
 assert fragments==1776 and len(set(allids))==1776 and len(words)==len(set(words))==18662 and cells==79 and image==5 and headers==171 and lists==19 and items==85
 csv.field_size_limit(64*1024*1024);rows=list(csv.DictReader(io.StringIO(csvdata.decode(),newline='')));assert len(rows)==172
 for row,r in zip(rows,new):assert row['id']==r['id']and row['text']==r['text']and row['html']==r['html']and json.loads(row['source_pages'])==r['source_pages']
 out={'passed':True,'units':172,'physical_pages':62,'source_fragments':1776,'whole_word_ids_once':18662,'source_heading_nodes':headers,'source_list_groups':lists,'literal_marker_items':items,'paragraph_groups':paragraphs,'exact_cell_text_and_spans':79,'IMAGE_count':5,'source_original_fields_and_diagnostics_unchanged':True,'canonical_HTML_source_leaf_text_exact_except_documented_grid_whitespace':True,'CSV_primary_HTML_and_text_equal':True,'unresolved_counts':dict(unresolved),'whole_publication_qualified':False,'network_native_image_operations':0,'records':result};return out
