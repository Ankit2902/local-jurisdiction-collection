"""enCodePlus server-rendered document contract; bounded requested-node normalization."""
import json,re,hashlib,csv,gzip
from urllib.parse import urljoin,urlparse,parse_qs
from bs4 import BeautifulSoup
from html_semantics import LegalHTML

def sha(b):return hashlib.sha256(b).hexdigest()
def decode(data,headers=None):
 enc=next((v for k,v in (headers or {}).items() if k.lower()=='content-encoding'),'')
 if enc=='br':
  import brotli
  data=brotli.decompress(data)
 elif enc=='gzip':data=gzip.decompress(data)
 return data.decode('utf-8-sig',errors='strict')
def clean(s):return ' '.join(str(s).split())
def inventory(html,base,expected_identity):
 soup=BeautifulSoup(html,'html.parser');head=soup.select_one('#toc-pagehead');assert head and expected_identity.lower() in head.get_text(' ',strip=True).lower(),'Publication identity missing/mismatched'
 nodes=[];stack=[];seen=set();anomalies=[]
 for li in soup.select('#toc-list li.tocLink'):
  ident=re.fullmatch(r'secid-x(\d+)',li.get('id',''))
  if not ident:continue
  ident=ident.group(1);a=li.select_one('a[href*="secid="]');label=li.select_one('.toc-item');assert a and label
  assert ident not in seen,'Duplicate TOC ID';seen.add(ident)
  ul=li.find_parent('ul');m=re.search(r'toc-level(\d+)',' '.join(ul.get('class',[])));assert m,'TOC depth absent';depth=int(m.group(1))
  while stack and stack[-1]['depth']>=depth:stack.pop()
  if depth>(stack[-1]['depth']+1 if stack else 0):anomalies.append({'section_id':ident,'declared_depth':depth,'closest_lower_depth':stack[-1]['depth'] if stack else None,'reason':'Publisher TOC depth gap; parent/path are best-effort only, canonical breadcrumbs required for sampled body'})
  node={'section_id':ident,'heading':clean(label.get_text(' ',strip=True)),'depth':depth,'parent_id':stack[-1]['section_id'] if stack else None,'path':[x['heading'] for x in stack],'has_children':bool(re.search(r",\s*true\s*\)",a.get('onclick',''))),'source_viewer_url':urljoin(base,a['href'])}
  nodes.append(node);stack.append(node)
 assert len(nodes)>10,'No substantive TOC inventory'
 return {'publication_identity':clean(head.get_text(' ',strip=True)),'nodes':nodes,'node_count':len(nodes),'raw_toc_sha256':sha(html.encode()),'hierarchy_anomalies':anomalies,'hierarchy_complete':not anomalies,'hierarchy_method':'closest lower declared toc-level; gaps retained, not silently repaired'}
def parse_section(html,node,url,jurisdiction,raw_hash):
 soup=BeautifulSoup(html,'html.parser');page=soup.select_one('#thePage');assert page is not None,'Missing legal document container'
 assert page.get('secid')==node['section_id'],'Requested document identity mismatch'
 candidates=page.select('section[data-secid="'+node['section_id']+'"]');assert len(candidates)==1,'Absent/ambiguous requested legal node'
 target=candidates[0];assert not target.select('section[data-secid]'),'Nested source-node ownership requires separate qualification'
 source_html=str(target);heading=target.find(re.compile('^h[1-6]$'));assert heading,'Legal heading missing'
 hclone=BeautifulSoup(str(heading),'html.parser')
 for sup in hclone.select('sup'):sup.decompose()
 h=clean(hclone.get_text(' ',strip=True));assert h==node['heading'],'TOC/body heading mismatch: '+repr((h,node['heading']))
 body=BeautifulSoup(source_html,'html.parser');bodyheading=body.find(re.compile('^h[1-6]$'));bodyheading.decompose();omitted=[]
 for el in body.select('.archiveNotice.nullValue'):
  omitted.append({'text':clean(el.get_text(' ',strip=True)),'classes':el.get('class',[]),'reason':'publisher nullValue/sentinel metadata; not an authoritative effective date'});el.decompose()
 effective=[clean(el.get_text(' ',strip=True)) for el in target.select('.archiveNotice') if 'nullValue' not in el.get('class',[])]
 body_html=str(body);sem=LegalHTML();sem.feed(body_html);text=sem.parsed();assert len(text)>30,'Empty/TOC-only/insubstantive body'
 source_tables=body.find_all('table');table_checks=[]
 assert len(source_tables)==len(sem.tables)
 for table,normalized in zip(source_tables,sem.tables):
  trs=table.find_all('tr');assert len(trs)==len(normalized),'Table row mismatch'
  for tr,row in zip(trs,normalized):
   cells=tr.find_all(['td','th']);assert len(cells)==len(row),'Table cell count mismatch'
   for cell,ncell in zip(cells,row):
    assert clean(cell.get_text(' ',strip=True))==clean(ncell['text']),'Independent table text mismatch'
    assert str(cell.get('rowspan','1'))==ncell['rowspan'] and str(cell.get('colspan','1'))==ncell['colspan'],'Table span mismatch'
    ncell['html']=str(cell)
  table_checks.append({'rows':len(trs),'cells':sum(len(x) for x in normalized),'independent_text_span_match':True})
 links=[]
 for a in body.find_all('a'):
  attrs=dict(a.attrs);href=urljoin(url,attrs.get('href','')) if attrs.get('href') else '';m=re.search(r'(?:secid=|#secid-)(\d+)',href);links.append({'text':clean(a.get_text(' ',strip=True)),'attributes':attrs,'resolved_href':href,'target_section_id':m.group(1) if m else None})
 match=re.match(r'^(?:DFD\s+)?([\d.]+)',h)
 record={'jurisdiction':jurisdiction,'record_kind':'operative_provision','section_id':node['section_id'],'section_number':match.group(1).rstrip('.') if match else None,'heading':h,'citation':h,'path':[clean(a.get_text(' ',strip=True)) for a in soup.select('#pageControls .breadCrumbs .breadCrumbs a')][:-1],'toc_path_best_effort':node['path'],'full_text':text,'body_html':body_html,'source_html':source_html,'html_serialization':'BeautifulSoup html.parser; retained original response bytes are authoritative','tables':sem.tables,'links':links,'list_count':sem.lists,'effective_date_notices':effective,'omitted_placeholder_metadata':omitted,'source_url':url,'raw_sha256':raw_hash,'complete_corpus':False}
 check={'section_id':node['section_id'],'requested_container_id_exact':True,'toc_heading_matches_body':True,'nonempty_operative_body':True,'table_count':len(sem.tables),'table_checks':table_checks,'cross_references_retained':sum(bool(x['target_section_id']) for x in links),'publisher_placeholder_dates_excluded':len(omitted)}
 return record,check,page.get('tocid')
def write_outputs(records,checks,out):
 out.mkdir(parents=True,exist_ok=True);assert len(set(r['section_id'] for r in records))==len(records)
 (out/'sections.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records))
 fields=['jurisdiction','record_kind','section_id','section_number','heading','citation','full_text','source_url','raw_sha256']
 with (out/'sections.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:r[k] for k in fields} for r in records)
 return {'record_count':len(records),'record_unit':'requested operative provision','table_count':sum(len(r['tables']) for r in records),'checks':checks,'complete_corpus':False,'outputs_sha256':{p.name:sha(p.read_bytes()) for p in [out/'sections.jsonl',out/'sections.csv']}}
