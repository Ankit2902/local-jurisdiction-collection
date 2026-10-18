"""Independent stdlib-only all-source/all-row consumer; no PDF parser imports."""
import csv,hashlib,html.parser,io,json,pathlib,re,sys,urllib.parse
sys.dont_write_bytecode=True
sha=lambda b:hashlib.sha256(b).hexdigest()
def require(ok,message):
 if not ok:raise ValueError(message)
class SourceLinks(html.parser.HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.depth=0;self.links=[];self.anchor=None
 def handle_starttag(self,tag,attrs):
  attrs=dict(attrs)
  if tag=='div':
   if self.depth:self.depth+=1
   elif attrs.get('id')=='dnn_ctr8908_HtmlModule_lblContent':self.depth=1
  if self.depth and tag=='a'and attrs.get('href'):self.anchor=[attrs['href'],'']
 def handle_data(self,s):
  if self.anchor is not None:self.anchor[1]+=s
 def handle_endtag(self,tag):
  if tag=='a'and self.anchor is not None:self.links.append((self.anchor[0],' '.join(self.anchor[1].split())));self.anchor=None
  if tag=='div'and self.depth:self.depth-=1
def source_inventory(data,url):
 h=SourceLinks();h.feed(data.decode('utf-8-sig'));return [(urllib.parse.urljoin(url,u),t)for u,t in h.links]
def audit(method,job):
 method=pathlib.Path(method);job=pathlib.Path(job);run=job/'run';s=json.loads((run/'checkpoint.json').read_text());c=json.loads((run/'config.json').read_text());coverage=json.loads((run/'coverage.json').read_text());pins=json.loads((method/'native-pins.json').read_text())['documents']
 require(s['completed']and len(s['items'])==len(s['done'])==2,'Full two-source collector must be terminal')
 require({i['url']for i in s['items']}==set(pins),'Expected exact native source URLs')
 for n,h in s['scripts'].items():require(sha((method/'runtime'/n).read_bytes())==h==sha((run/'executed'/n).read_bytes()),'Exact executed runtime '+n)
 initial=source_inventory((run/s['identity']['source_ref']).read_bytes(),c['source_url']);closing=source_inventory((run/s['consistency']['raw_ref']).read_bytes(),c['source_url'])
 require(initial==closing and len(initial)==8,'All current/historical main-container links stable')
 expected={(u,t)for u,t in initial if t in ['Subdivision and Site Plan Review Regulations','Zoning Ordinance']}
 require(expected=={(i['url'],i['heading'])for i in s['items']},'Independent selected source inventory')
 require(sum(t=='2001 Zoning Ordinance'for _,t in initial)==1,'Explicit historical document not silently omitted')
 rows=[];sourcefiles=[]
 for i in s['items']:
  p=run/'items'/(sha(i['id'].encode())[:24]+'.json');d=json.loads(p.read_text());r=d['records'];pin=pins[i['url']]
  require(d['item']==i,'Exact item/inventory binding')
  b=(run/i['raw_ref']).read_bytes();require(b.startswith(b'%PDF-')and sha(b)==d['raw_sha256']==pin['sha256']and len(b)==pin['bytes'],'Original native pin')
  require(len(r)==pin['physical_pages']and [x['physical_page']for x in r]==list(range(1,len(r)+1)),'All ordered physical pages/no gaps')
  for x in r:require(x['document_id']==i['id']and x['raw_sha256']==pin['sha256']and x['source_url']==i['url']+'#page='+str(x['physical_page'])and x['page_count']==len(r),'Per-page native source identity')
  rows+=r;sourcefiles.append({'url':i['url'],'sha256':pin['sha256'],'bytes':len(b),'physical_pages':len(r)})
 require(len(rows)==336,'All336 actual pages')
 encoded=lambda r:json.dumps(r,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()+b'\n'
 require((run/'records.jsonl').read_bytes()==b''.join(encoded(r)for r in rows),'All canonical JSONL records exact')
 csv.field_size_limit(64*1024*1024);export=list(csv.DictReader(io.StringIO((run/'records.csv').read_text(),newline='')))
 require(len(export)==len(rows),'CSV count')
 for r,csvrow in zip(rows,export):require(all(csvrow[k]==str(r[k])for k in csvrow),'All canonical CSV fields exact')
 checks=s['item_consistency'];require(len(checks)==2 and all(x['matches_initial_content']and x['sha256']==pins[x['url']]['sha256']and sha((run/x['raw_ref']).read_bytes())==x['sha256']for x in checks),'Actual later full native closing checks')
 receipts=[]
 for p in sorted((run/'raw').glob('*.receipt.json')):
  m=json.loads(p.read_text());b=p.with_name(p.name.replace('.receipt.json','.bin')).read_bytes();require(m['status']==200 and not m.get('access_stop')and not m.get('policy_omitted_image')and sha(b)==m['sha256']and len(b)==m['bytes'],'Every actual successful source response')
  require(not re.search(r'\.(?:png|jpe?g|gif|svg|webp|bmp)(?:$|[?#])',m['url'],re.I),'No separate image request')
  require(not any(k.lower()=='content-type'and v.lower().startswith('image/')for k,v in m['headers'].items()),'No image response body')
  receipts.append({'path':str(p.relative_to(run)),'url':m['url'],'status':m['status'],'sha256':m['sha256'],'bytes':m['bytes']})
 bad={};q=[r['pdf_qualification']for r in rows]
 for field in ['source_word_ownership_complete','normalized_source_word_characters_agree','source_words_cover_deduplicated_glyph_characters','independent_text_engine_characters_agree']:
  bad[field]=[r['id']for r in rows if not r['pdf_qualification'].get(field)]
 tablebad=[r['id']for r in rows if r['pdf_qualification']['detected_table_cells']!=r['pdf_qualification']['independent_table_cells_agree']]
 cid=[r['id']for r in rows if r['pdf_qualification'].get('undecoded_cid_literals')];private=[r['id']for r in rows if r['pdf_qualification'].get('unmapped_or_private_use_codepoints')]
 for r in rows:require(r['text'].count('[IMAGE]')==r['image_placeholder_count'],'Exact [IMAGE] count in canonical text '+r['id'])
 require(all(coverage[f]is True for f in ['requested_coverage_complete','publication_file_coverage_complete','pdf_page_extraction_complete','source_consistency_complete']),'Requested native file/page coverage')
 require(coverage['legal_semantic_coverage_complete']is False and coverage['jurisdiction_complete']is False and coverage['manual_review_required']is True,'Remaining legal scope not promoted')
 return {'passed':True,'source_files':sourcefiles,'current_main_container_documents':7,'historical_documents':1,'selected_whole_native_documents':2,'physical_pages':336,'CSV_JSONL_all_fields_equal':True,'all_actual_receipts':receipts,'individual_native_closing_byte_equal':True,'source_words':sum(x['source_word_count']for x in q),'IMAGE_placeholders':sum(r['image_placeholder_count']for r in rows),'tables':sum(x['detected_table_count']for x in q),'detected_cells':sum(x['detected_table_cells']for x in q),'independently_agreeing_cells':sum(x['independent_table_cells_agree']for x in q),'failed_text_dimensions':bad,'detected_cell_failure_pages':tablebad,'CID_pages':cid,'private_codepoint_pages':private,'file_pages_complete':True,'legal_semantics_complete':False,'jurisdiction_complete':False,'native_parser_calls_by_auditor':0,'publisher_or_image_operations_by_auditor':0}
if __name__=='__main__':print(json.dumps(audit(sys.argv[1],sys.argv[2]),indent=2))
