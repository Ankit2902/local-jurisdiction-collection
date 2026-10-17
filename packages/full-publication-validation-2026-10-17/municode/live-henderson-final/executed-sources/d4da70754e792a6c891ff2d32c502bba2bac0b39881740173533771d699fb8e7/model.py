"""Deterministic Municode publication reconciliation. All coverage is recomputed from source bytes."""
import sys
sys.dont_write_bytecode=True
import csv,hashlib,json,re,os
from pathlib import Path
from urllib.parse import urlparse,urljoin,parse_qs
from html.parser import HTMLParser
from normalize import LegalHTML
SCHEMA=1
RUNTIME_FILES=['collect.py','model.py','normalize.py','browser.cjs','gate_cli.py','verify.py']
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def digest(x):return sha(canonical(x))
def atomic(path,data):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.tmp');tmp.write_bytes(data if isinstance(data,bytes) else json.dumps(data,ensure_ascii=False,indent=2).encode()+b'\n');os.replace(tmp,path)
def implementation(root=None):
 root=Path(root or Path(__file__).parent);return {n:sha((root/n).read_bytes()) for n in RUNTIME_FILES}
def flatten(tree):
 nodes=[];seen=set()
 def walk(n,path=[],parent=None):
  ident=str(n.get('Id',''))
  if not ident or ident in seen:raise ValueError('Missing/duplicate TOC ID '+ident)
  seen.add(ident);nodes.append({'id':ident,'heading':n.get('Heading') or '', 'path':path+[n.get('Heading') or ''],'parent_id':parent,'children':[str(c['Id']) for c in n.get('Children',[])],'data':n.get('Data') or {}})
  for c in n.get('Children',[]):walk(c,path+[n.get('Heading') or ''],ident)
 walk(tree);return nodes
class References(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.refs=[];self.embedded_ids=[]
 def handle_starttag(self,t,aa):
  a=dict(aa)
  if 'chunk-content' in a.get('class','').split() and a.get('id'):self.embedded_ids.append(a['id'])
  for k in ('src','poster','data','href','xlink:href'):
   if k in a and a[k] :self.refs.append({'tag':t,'attribute':k,'value':a[k],'attributes':a})
  if a.get('srcset'):
   for part in a['srcset'].split(','):
    self.refs.append({'tag':t,'attribute':'srcset','value':part.strip().split(' ')[0],'attributes':a})
  if a.get('style'):
   for u in re.findall(r'url\([\'\"]?([^\)\'\"]+)',a['style']):self.refs.append({'tag':t,'attribute':'style-url','value':u,'attributes':a})
class SubstantiveBody(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.suppressed=[];self.text=[]
 def handle_starttag(self,t,a):
  if t in ('h1','h2','h3','h4','h5','h6','script','style','template'):self.suppressed.append(t)
 def handle_endtag(self,t):
  if self.suppressed and t==self.suppressed[-1]:self.suppressed.pop()
 def handle_data(self,s):
  if not self.suppressed:self.text.append(s)
 def value(self):return re.sub(r'\s+',' ',''.join(self.text)).strip()

def references(records,base,policy=None):
 policy=policy or {}
 refs=[]
 for record in records:
  p=References();p.feed(record['html']);p.feed(record.get('footnotes_html') or '')
  for ref in p.refs:
   raw=ref['value'].strip();u=urljoin(base,raw);a=ref['attributes'];path=urlparse(u).path.lower()
   if raw.lower().startswith(('#','mailto:','tel:','javascript:','data:')):kind='inline_or_nonnetwork_reference';required=False
   elif ref['tag']=='a' and (a.get('data-nodeid') or a.get('data-node-id') or a.get('data-chunk-id') or ('nodeId=' in raw and urlparse(u).hostname=='library.municode.com')):kind='internal_legal_cross_reference';required=False
   elif ref['attribute'] not in ('href','xlink:href') or ref['tag']!='a' or re.search(r'\.(pdf|docx?|xlsx?|zip|png|jpe?g|gif|svg|webp|tiff?|bmp|csv|odt)(?:$|/)',path) or re.search(r'/documentcenter/|/showdocument/|/munidocs/|/api/assets/|/linkclick',path):kind='required_asset';required=True
   else:
    decision=policy.get(u,{})
    if decision.get('kind') in ['external_family_boundary','reference_hyperlink'] and decision.get('reason') and (not decision.get('owner_ids') or record['node_id'] in decision['owner_ids']):kind=decision['kind'];required=False
    else:kind='unclassified_external_hyperlink';required=True
   refs.append({'owner_id':record['node_id'],'url':u,'source_value':raw,'tag':ref['tag'],'attribute':ref['attribute'],'kind':kind,'required':required,**({'justification':policy[u]['reason']} if kind in ['external_family_boundary','reference_hyperlink'] else {})})
 return refs
def valid_asset(url,body,headers):
 path=urlparse(url).path.lower();mime=headers.get('content-type','').lower()
 if not body:return False
 if path.endswith('.png'):return body.startswith(b'\x89PNG\r\n\x1a\n')
 if path.endswith(('.jpg','.jpeg')):return body.startswith(b'\xff\xd8')
 if path.endswith('.gif'):return body[:6] in [b'GIF87a',b'GIF89a']
 if path.endswith('.pdf'):return body.startswith(b'%PDF-')
 if path.endswith(('.zip','.docx','.xlsx')):return body.startswith(b'PK')
 if path.endswith('.svg'):return b'<svg' in body[:4096].lower()
 if path.endswith('.css'):return 'text/css' in mime
 return not ('text/html' in mime or body.lstrip().lower().startswith((b'<html',b'<!doctype html')))

def read_response(folder,entry):
 receipt=json.loads((folder/entry['receipt']).read_text());body=(folder/receipt['body_file']).read_bytes()
 if sha(body)!=receipt['sha256'] or receipt['sha256']!=entry['sha256']:raise ValueError('Corrupt committed response '+entry['receipt'])
 if receipt['request']!=entry['request']:raise ValueError('Checkpoint request mismatch '+entry['receipt'])
 if receipt['status']!=200 or receipt.get('access_stop'):raise ValueError('Access failure cannot be accepted as source')
 return json.loads(body)
def reconcile_publication(folder,cp,product_id):
 pid=str(product_id);pub=cp['publications'][pid];tree=read_response(folder,cp['units'][pub['toc_unit']]);nodes=flatten(tree);byid={n['id']:n for n in nodes};product=read_response(folder,cp['units'][pub['product_unit']])['Model'];job=read_response(folder,cp['units'][pub['job_unit']]);errors=[];occurrences={};unit_results=[]
 if product['Client']['ClientName'] not in cp['expected_identity']['client_names'] or product['Client']['State']['StateAbbreviation']!=cp['expected_identity']['state']:errors.append('jurisdiction identity mismatch')
 if product['ProductID']!=int(pid) or product['Client']['ClientID']!=cp['client_id'] or job['ProductId']!=int(pid) or job['Id']!=pub['job_id']:errors.append('publication/job/client binding mismatch')
 if digest(tree)!=pub['toc_hash']:errors.append('pinned inventory hash mismatch')
 for name in pub.get('content_units',[]):
  entry=cp['units'][name];q=parse_qs(urlparse(entry['request']['url']).query)
  if q.get('productId')!=[pid] or q.get('jobId')!=[str(job['Id'])]:errors.append('content request edition mismatch: '+name)
  payload=read_response(folder,entry);docs=payload if isinstance(payload,list) else payload.get('Docs',[]);local=set()
  for d in docs:
   ident=str(d.get('Id',''))
   if ident in local:errors.append('duplicate Doc ID in response: '+ident)
   local.add(ident);occurrences.setdefault(ident,[]).append((name,d))
  unit_results.append({'unit':name,'returned_ids':list(local)})
 records=[];excluded=[];missing=[];duplicates=[];extra=sorted(set(occurrences)-set(byid));ownership=[]
 for node in nodes:
  ident=node['id'];items=occurrences.get(ident,[])
  if not items:
   if ident==pid and node['children'] and node['data'].get('DocType')==0 and pub.get('root_landing_unit'):
    landing=read_response(folder,cp['units'][pub['root_landing_unit']]);matches=[d for d in landing.get('Docs',[]) if str(d.get('Id'))==pid]
    if len(matches)==1 and matches[0].get('DocType')==4 and not matches[0].get('Content'):excluded.append({'id':ident,'reason':'structural publication landing page; explicit own response DocType4 has no legal content','evidence_unit':pub['root_landing_unit']});continue
   missing.append(ident);continue
  if len(items)>1:duplicates.append(ident);continue
  name,doc=items[0]
  if doc.get('DocType') not in (1,2):errors.append('unhandled source DocType '+str(doc.get('DocType'))+': '+ident)
  html=doc.get('Content') or '';parser=LegalHTML();parser.feed(html);text=parser.parsed();title=LegalHTML();title.feed(doc.get('TitleHtml') or doc.get('Title') or node['heading']);heading=title.parsed();refs=References();refs.feed(html)
  if refs.embedded_ids and any(i!=ident and i in byid for i in refs.embedded_ids):errors.append('nested descendant body has ambiguous ownership: '+ident)
  substantive=SubstantiveBody();substantive.feed(html)
  if not substantive.value() and not node['children'] and not re.search(r'reserved|repealed|deleted|omitted',heading,re.I):errors.append('unexplained empty leaf: '+ident)
  if not heading:errors.append('missing heading '+ident)
  record={'node_id':ident,'product_id':int(pid),'job_id':job['Id'],'heading':heading,'toc_heading':node['heading'],'path':node['path'],'parent_id':node['parent_id'],'is_container':bool(node['children']),'text':text,'html':html,'body_sha256':sha(html.encode()),'tables':parser.tables,'links':parser.links,'list_count':parser.lists,'footnotes_html':doc.get('Footnotes'),'notes':doc.get('Notes'),'doc_type':doc.get('DocType'),'chunk_group_starting_node_id':doc.get('ChunkGroupStartingNodeId'),'source_unit':name,'source_url':cp['source_url'].split('?')[0]+'?nodeId='+ident};records.append(record);ownership.append({'owner_id':ident,'parent_id':node['parent_id'],'child_ids':node['children'],'owns_body':bool(text),'body_sha256':record['body_sha256']})
 refs=references(records,cp.get('document_base_url',cp['source_url']),cp['binding'].get('reference_policy',{}));visited=set()
 while True:
  pending={r['url'] for r in refs if r['required']}-visited
  if not pending:break
  for url in sorted(pending):
   visited.add(url);entry=cp.get('assets',{}).get(digest(url));unit=cp['units'].get(entry.get('unit')) if entry else None
   if not unit:continue
   rr=json.loads((folder/unit['receipt']).read_text());body=(folder/rr['body_file']).read_bytes()
   if sha(body)!=unit['sha256']:raise ValueError('Corrupt dependency asset '+url)
   mime=rr['headers'].get('content-type','').lower();path=urlparse(url).path.lower();deps=[]
   if path.endswith('.css') or 'text/css' in mime:
    css=body.decode('utf8','replace');deps=re.findall(r'url\([\'\"]?([^\)\'\"]+)',css)+re.findall(r'@import\s+[\'\"]([^\'\"]+)',css)
   elif path.endswith('.svg') or 'image/svg+xml' in mime:
    parser=References();parser.feed(body.decode('utf8','replace'));deps=[r['value'] for r in parser.refs]
   owners=sorted({r['owner_id'] for r in refs if r['url']==url})
   for dep in deps:
    if not dep or dep.startswith(('data:','#')):continue
    for owner in owners:refs.append({'owner_id':owner,'url':urljoin(url,dep),'source_value':dep,'tag':'asset-dependency','attribute':'embedded-resource','kind':'required_asset','required':True,'parent_asset_url':url})
 asset_urls=sorted({r['url'] for r in refs if r['required']});assets=[]
 for url in asset_urls:
  aid=digest(url);entry=cp.get('assets',{}).get(aid)
  status='missing';reason=None
  if entry:
   if entry.get('unit'):
    unit=cp['units'][entry['unit']];rr=json.loads((folder/unit['receipt']).read_text());b=(folder/rr['body_file']).read_bytes()
    if sha(b)!=rr['sha256'] or unit['sha256']!=rr['sha256']:raise ValueError('Corrupt asset '+url)
    status='acquired' if rr['status']==200 and not rr.get('access_stop') and valid_asset(url,b,rr['headers']) else 'failed'
    if status=='failed':reason='HTTP/access failure or payload magic/type validation failed'
   else:status=entry.get('status','missing');reason=entry.get('reason')
  assets.append({'url':url,'asset_id':aid,'status':status,'reason':reason,'owner_ids':sorted({r['owner_id'] for r in refs if r['url']==url})})
 start=digest({'inventory':read_response(folder,cp['units']['inventory-start']),'product':read_response(folder,cp['units'][pub['product_unit']]),'job':job,'toc':tree});end=None
 if pub.get('end_units'):
  eu=pub['end_units'];end=digest({'inventory':read_response(folder,cp['units'][eu['inventory']]),'product':read_response(folder,cp['units'][eu['product']]),'job':read_response(folder,cp['units'][eu['job']]),'toc':read_response(folder,cp['units'][eu['toc']])})
 if pub['start_signature']!=start or (pub.get('end_signature') and pub.get('end_signature')!=end):errors.append('stored source-consistency signature mismatch')
 consistent=bool(end and start==end);limited=bool(cp.get('limit'));nodes_ok=not(missing or duplicates or extra or errors);text_complete=nodes_ok and consistent and not limited and cp.get('phase')=='finished';assets_complete=text_complete and all(a['status']=='acquired' for a in assets)
 report={'evidence_kind':cp.get('evidence_kind','unclassified'),'live_publication_complete':bool(cp.get('evidence_kind')=='live' and text_complete and assets_complete),'schema_version':SCHEMA,'product_id':int(pid),'job_id':job['Id'],'product_name':product['ProductName'],'inventory_hash':pub['toc_hash'],'inventory_node_count':len(nodes),'inventory_unique_id_count':len(byid),'acquired_unique_doc_ids':len(occurrences),'parsed_record_count':len(records),'parsed_container_count':sum(r['is_container'] for r in records),'missing_ids':missing,'duplicate_ids':duplicates,'extra_ids':extra,'justified_exclusions':excluded,'errors':errors,'container_ownership':ownership,'references':refs,'asset_ledger':assets,'required_asset_count':len(assets),'asset_failures':[a for a in assets if a['status']!='acquired'],'start_end_consistent':consistent,'start_signature':start,'end_signature':end,'limit_active':limited,'run_phase':cp.get('phase'),'inventory_reconciled':nodes_ok,'publication_text_complete':text_complete,'publication_attachments_complete':assets_complete,'publication_complete':text_complete and assets_complete,'jurisdiction_complete':False,'uncodified_ordinances_collected':False,'external_family_references':[r for r in refs if r['kind'] in ['external_family_boundary','reference_hyperlink']],'implementation_hash':digest(cp['binding']['implementation']),'scope':'One pinned publisher publication, all TOC nodes including container-owned content. Separately hosted families and uncodified ordinances are outside this publication scope.'}
 return records,report

def write_outputs(folder,cp):
 reports=[]
 for pid in cp['publications']:
  records,report=reconcile_publication(folder,cp,pid);out=folder/'publications'/pid;out.mkdir(parents=True,exist_ok=True);atomic(out/'sections.jsonl', ''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records).encode())
  import io
  stream=io.StringIO(newline='');fields=['node_id','product_id','job_id','heading','parent_id','is_container','text','body_sha256','source_url'];w=csv.DictWriter(stream,fieldnames=fields);w.writeheader();w.writerows({k:r[k] for k in fields} for r in records);atomic(out/'sections.csv',stream.getvalue().encode());atomic(out/'coverage.json',report);reports.append(report)
 overall={'schema_version':SCHEMA,'selected_product_ids':list(cp['publications']),'visible_publication_inventory':cp.get('visible_publications',[]),'selected_publication_count':len(reports),'publication_complete':bool(reports) and all(r['publication_complete'] for r in reports),'publication_text_complete':bool(reports) and all(r['publication_text_complete'] for r in reports),'publication_attachments_complete':bool(reports) and all(r['publication_attachments_complete'] for r in reports),'jurisdiction_complete':False,'record_count':sum(r['parsed_record_count'] for r in reports),'phase':cp['phase'],'limit':cp.get('limit'),'publications':[{'product_id':r['product_id'],'coverage_path':'publications/'+str(r['product_id'])+'/coverage.json','publication_complete':r['publication_complete']} for r in reports]};atomic(folder/'coverage.json',overall);return overall
