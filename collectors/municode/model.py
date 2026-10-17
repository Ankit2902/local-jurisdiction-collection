"""Deterministic Municode publication reconciliation. All coverage is recomputed from source bytes."""
import sys
sys.dont_write_bytecode=True
import csv,hashlib,json,re,os,io,zipfile
from pathlib import Path
from urllib.parse import urlparse,urljoin,parse_qs
from html.parser import HTMLParser
from normalize import LegalHTML
from pdf_integrity import qualify_pdf
from image_policy import sanitize,image_ref,image_url,POLICY,safe_metadata
from notes import sanitize_notes
SCHEMA=1
RUNTIME_FILES=['collect.py','model.py','normalize.py','browser.cjs','gate_cli.py','verify.py','image_policy.py','pdf_integrity.py','runtime.py','notes.py','access_state.py','access-advisory.json']
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def digest(x):return sha(canonical(x))
def reference_url(base,value):
 # A bare external-looking hostname is not a relative publisher path. Preserve it
 # unresolved; guessing HTTPS or requesting a publisher-relative spelling is unsafe.
 raw=value.strip();parsed=urlparse(raw)
 malformed=not parsed.scheme and not raw.startswith('//') and bool(re.match(r'^(?:www\.[a-z0-9.-]+\.[a-z]{2,63}|[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com|org|gov|edu|net|us|io|ca))(?=[/\\:?#]|$)',raw,re.I))
 return (raw,True) if malformed else (urljoin(base,raw),False)
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
 def __init__(self):super().__init__(convert_charrefs=True);self.refs=[];self.embedded_ids=[];self.picture_depth=0
 def handle_starttag(self,t,aa):
  a=dict(aa)
  if t=='picture':self.picture_depth+=1
  if self.picture_depth:a['_in_picture']=True
  if 'chunk-content' in a.get('class','').split() and a.get('id'):self.embedded_ids.append(a['id'])
  for k in ('src','poster','data','href','xlink:href'):
   if k in a and a[k] :self.refs.append({'tag':t,'attribute':k,'value':a[k],'attributes':a})
  if a.get('srcset'):
   for part in ([a['srcset']] if 'data:image/' in a['srcset'].lower() else a['srcset'].split(',')):
    self.refs.append({'tag':t,'attribute':'srcset','value':part.strip().split(' ')[0],'attributes':a})
  if a.get('style'):
   for u in re.findall(r'url\([\'\"]?([^\)\'\"]+)',a['style']):self.refs.append({'tag':t,'attribute':'style-url','value':u,'attributes':a})
 def handle_endtag(self,t):
  if t=='picture':self.picture_depth=max(0,self.picture_depth-1)
class SubstantiveBody(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.suppressed=[];self.text=[]
 def handle_starttag(self,t,a):
  if t in ('h1','h2','h3','h4','h5','h6','script','style','template'):self.suppressed.append(t)
 def handle_endtag(self,t):
  if self.suppressed and t==self.suppressed[-1]:self.suppressed.pop()
 def handle_data(self,s):
  if not self.suppressed:self.text.append(s)
 def value(self):return re.sub(r'\s+',' ',''.join(self.text)).strip()

def references(records,base,policy=None,known_images=()):
 policy=policy or {}
 refs=[]
 for record in records:
  p=References();p.feed(record['html']);p.feed(record.get('footnotes_html') or '')
  for ref in p.refs:
   raw=ref['value'].strip();u,malformed=reference_url(base,raw);a=ref['attributes'];path=urlparse(u).path.lower()
   if image_ref(ref,base,known_images):kind='image_omitted';required=False
   elif malformed:kind='malformed_external_reference';required=True
   elif raw.lower().startswith(('#','mailto:','tel:','javascript:','data:')):kind='inline_or_nonnetwork_reference';required=False
   elif ref['tag']=='a' and (a.get('data-nodeid') or a.get('data-node-id') or a.get('data-chunk-id') or ('nodeId=' in raw and urlparse(u).hostname=='library.municode.com')):kind='internal_legal_cross_reference';required=False
   elif ref['attribute'] not in ('href','xlink:href') or ref['tag']!='a' or re.search(r'\.(pdf|docx?|xlsx?|zip|png|jpe?g|gif|svg|webp|tiff?|bmp|csv|odt)(?:$|/)',path) or re.search(r'/documentcenter/|/showdocument/|/munidocs/|/api/assets/|/linkclick',path):kind='required_asset';required=True
   else:
    decision=policy.get(u,{})
    if decision.get('kind') in ['external_family_boundary','reference_hyperlink'] and decision.get('reason') and (not decision.get('owner_ids') or record['node_id'] in decision['owner_ids']):kind=decision['kind'];required=False
    else:kind='unclassified_external_hyperlink';required=True
   inline=safe_metadata(raw,'reference:'+record['node_id']+':'+ref['attribute']);public_url='inline-image:'+sha(raw.encode()) if isinstance(inline,dict) else u
   refs.append({'owner_id':record['node_id'],'url':public_url,'source_value':inline,'tag':ref['tag'],'attribute':ref['attribute'],'kind':kind,'required':required,**({'justification':policy[u]['reason']} if kind in ['external_family_boundary','reference_hyperlink'] else {})})
 return refs
def asset_qualification(url,body,headers):
 """File integrity only. Unsupported binary formats cannot satisfy attachment coverage."""
 path=urlparse(url).path.lower();mime=headers.get('content-type','').lower().split(';')[0].strip()
 if not body:return 'failed','Empty attachment body'
 if path.endswith('.pdf') or mime=='application/pdf' or body.startswith(b'%PDF-'):
  result=qualify_pdf(body);return result['status'],result['reason']
 if path.endswith(('.zip','.docx','.xlsx','.odt')) or mime in ('application/zip','application/vnd.openxmlformats-officedocument.wordprocessingml.document','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'):
  try:
   with zipfile.ZipFile(io.BytesIO(body)) as z:
    if not z.namelist() or z.testzip() is not None:return 'failed','Archive empty or CRC integrity failure'
    if path.endswith(('.docx','.xlsx')) and '[Content_Types].xml' not in z.namelist():return 'failed','Office archive content-type manifest missing'
  except (ValueError,zipfile.BadZipFile,RuntimeError,NotImplementedError,EOFError):return 'failed','Archive format or integrity failure'
  return 'acquired','Full archive central-directory and member CRC integrity checked; no semantic assertion'
 if mime in ('text/plain','text/css','text/csv','application/json'):
  try:
   text=body.decode('utf-8-sig')
   if not text.strip() or '\x00' in text:raise ValueError('Empty/binary text')
   if mime=='application/json':json.loads(text)
   if text.lstrip().lower().startswith(('<html','<!doctype html')):raise ValueError('HTML error body')
  except (UnicodeError,ValueError):return 'failed','Text decoding/type validation failed'
  return 'acquired','Nonempty UTF-8 text/type validated; no legal-semantic assertion'
 return 'unqualified','Unsupported nonimage format retained; byte/format integrity unqualified'
def valid_asset(url,body,headers):return asset_qualification(url,body,headers)[0]=='acquired'

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
 known_images=set()
 for asset in cp.get('assets',{}).values():
  if asset.get('status')!='image_omitted':continue
  entry=cp['units'][asset['unit']];rr=json.loads((folder/entry['receipt']).read_text());body=(folder/rr['body_file']).read_bytes()
  if body or sha(body)!=entry['sha256'] or rr['sha256']!=entry['sha256'] or rr['status']!=200 or rr.get('access_stop') or not rr.get('image_omitted') or rr['request']['url']!=asset['url'] or not (image_url(asset['url']) or rr['headers'].get('content-type','').lower().startswith('image/')):raise ValueError('Unsubstantiated image omission')
  known_images.add(asset['url'])
 source_records=[];base=cp.get('document_base_url',cp['source_url'])
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
  source_html=doc.get('Content') or '';html,image_omissions=sanitize(source_html,base,known_images);footnotes_html,footnote_images=sanitize(doc.get('Footnotes') or '',base,known_images);source_records.append({'node_id':ident,'html':source_html,'footnotes_html':doc.get('Footnotes')});parser=LegalHTML();parser.feed(html);text=parser.parsed();title_html,title_images=sanitize(doc.get('TitleHtml') or doc.get('Title') or node['heading'],base,known_images);image_omissions.extend(title_images);title=LegalHTML();title.feed(title_html);heading=title.parsed();refs=References();refs.feed(html)
  if refs.embedded_ids and any(i!=ident and i in byid for i in refs.embedded_ids):errors.append('nested descendant body has ambiguous ownership: '+ident)
  substantive=SubstantiveBody();substantive.feed(html)
  if not substantive.value() and '[IMAGE]' not in text and not node['children'] and not re.search(r'reserved|repealed|deleted|omitted',heading,re.I):errors.append('unexplained empty leaf: '+ident)
  if not heading:errors.append('missing heading '+ident)
  notes,note_images,note_html=sanitize_notes(doc.get('Notes'),base,known_images)
  for omission in note_images:
   if omission.get('qualification_error'):errors.append('unqualified note image boundary: '+ident+': '+omission['source_field'])
  source_records.extend({'node_id':ident,'html':h} for h in note_html)
  record={'node_id':ident,'product_id':int(pid),'job_id':job['Id'],'heading':heading,'toc_heading':node['heading'],'path':node['path'],'parent_id':node['parent_id'],'is_container':bool(node['children']),'text':text,'html':html,'body_sha256':sha(source_html.encode()),'normalized_html_sha256':sha(html.encode()),'image_policy':POLICY,'image_omissions':image_omissions+footnote_images+note_images,'tables':parser.tables,'links':parser.links,'list_count':parser.lists,'footnotes_html':footnotes_html,'notes':notes,'doc_type':doc.get('DocType'),'chunk_group_starting_node_id':doc.get('ChunkGroupStartingNodeId'),'source_unit':name,'source_url':cp['source_url'].split('?')[0]+'?nodeId='+ident}
  if doc.get('Notes'):record['notes_source_sha256']=digest(doc['Notes'])
  records.append(record);ownership.append({'owner_id':ident,'parent_id':node['parent_id'],'child_ids':node['children'],'owns_body':bool(text),'body_sha256':record['body_sha256']})
 refs=references(source_records,base,cp['binding'].get('reference_policy',{}),known_images);visited=set()
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
    resolved,malformed=reference_url(url,dep)
    for owner in owners:refs.append({'owner_id':owner,'url':resolved,'source_value':dep,'tag':'asset-dependency','attribute':'embedded-resource','kind':'image_omitted' if image_url(dep) else ('malformed_external_reference' if malformed else 'required_asset'),'required':not image_url(dep),'parent_asset_url':url})
 asset_urls=sorted({r['url'] for r in refs if r['required']});assets=[]
 for url in asset_urls:
  aid=digest(url);entry=cp.get('assets',{}).get(aid)
  status='missing';reason=None
  malformed=any(r['url']==url and r['kind']=='malformed_external_reference' for r in refs)
  if malformed:status='unresolved_malformed_source_reference';reason='Scheme-less external-looking source locator retained exactly; no scheme guessed and no transport request allowed'
  if entry and not malformed:
   if entry.get('unit'):
    unit=cp['units'][entry['unit']];rr=json.loads((folder/unit['receipt']).read_text());b=(folder/rr['body_file']).read_bytes()
    if sha(b)!=rr['sha256'] or unit['sha256']!=rr['sha256']:raise ValueError('Corrupt asset '+url)
    status,reason=asset_qualification(url,b,rr['headers']) if rr['status']==200 and not rr.get('access_stop') else ('failed','HTTP/access failure')
   else:status=entry.get('status','missing');reason=entry.get('reason')
  assets.append({'url':url,'asset_id':aid,'status':status,'reason':reason,**({'malformed_source_reference':True} if malformed else {}),**({'format_qualification':qualify_pdf(b)} if not malformed and entry and entry.get('unit') and (urlparse(url).path.lower().endswith('.pdf') or rr['headers'].get('content-type','').lower().startswith('application/pdf') or b.startswith(b'%PDF-')) else {}),'owner_ids':sorted({r['owner_id'] for r in refs if r['url']==url})})
 start=digest({'inventory':read_response(folder,cp['units']['inventory-start']),'product':read_response(folder,cp['units'][pub['product_unit']]),'job':job,'toc':tree});end=None
 if pub.get('end_units'):
  eu=pub['end_units'];end=digest({'inventory':read_response(folder,cp['units'][eu['inventory']]),'product':read_response(folder,cp['units'][eu['product']]),'job':read_response(folder,cp['units'][eu['job']]),'toc':read_response(folder,cp['units'][eu['toc']])})
 if pub['start_signature']!=start or (pub.get('end_signature') and pub.get('end_signature')!=end):errors.append('stored source-consistency signature mismatch')
 consistent=bool(end and start==end);limited=bool(cp.get('limit'));nodes_ok=not(missing or duplicates or extra or errors);text_complete=nodes_ok and consistent and not limited and cp.get('phase')=='finished';assets_complete=text_complete and all(a['status']=='acquired' for a in assets)
 report={'evidence_kind':cp.get('evidence_kind','unclassified'),'live_publication_complete':bool(cp.get('evidence_kind')=='live' and text_complete and assets_complete),'schema_version':SCHEMA,'product_id':int(pid),'job_id':job['Id'],'product_name':product['ProductName'],'inventory_hash':pub['toc_hash'],'inventory_node_count':len(nodes),'inventory_unique_id_count':len(byid),'source_document_count':sum(len(v) for v in occurrences.values()),'source_title_count':sum(bool(d.get('TitleHtml') or d.get('Title')) for items in occurrences.values() for name,d in items),'source_nonempty_body_count':sum(bool(d.get('Content')) for items in occurrences.values() for name,d in items),'unknown_exclusion_count':0,'acquired_unique_doc_ids':len(occurrences),'parsed_record_count':len(records),'parsed_container_count':sum(r['is_container'] for r in records),'missing_ids':missing,'duplicate_ids':duplicates,'extra_ids':extra,'justified_exclusions':excluded,'errors':errors,'container_ownership':ownership,'references':refs,'asset_ledger':assets,'image_policy':POLICY,'image_omission_count':sum(len(r['image_omissions']) for r in records),'image_omitted_urls':sorted({r['url'] for r in refs if r['kind']=='image_omitted'}),'required_nonimage_attachment_count':len(assets),'required_asset_count':len(assets),'asset_failures':[a for a in assets if a['status']!='acquired'],'publication_edition_consistent':consistent,'start_end_consistent':consistent,'start_signature':start,'end_signature':end,'limit_active':limited,'run_phase':cp.get('phase'),'inventory_reconciled':nodes_ok,'publication_text_complete':text_complete,'publication_attachments_complete':assets_complete,'publication_complete':text_complete and assets_complete,'jurisdiction_complete':False,'uncodified_ordinances_collected':False,'external_family_references':[r for r in refs if r['kind'] in ['external_family_boundary','reference_hyperlink']],'implementation_hash':digest(cp['binding']['implementation']),'scope':'Images deliberately replaced by literal [IMAGE]; no separate image binaries acquired. One pinned publisher publication, all TOC nodes including container-owned content. Separately hosted families and uncodified ordinances are outside this publication scope.'}
 return records,report

def write_outputs(folder,cp):
 reports=[]
 for pid in cp['publications']:
  records,report=reconcile_publication(folder,cp,pid);out=folder/'publications'/pid;out.mkdir(parents=True,exist_ok=True);atomic(out/'sections.jsonl', ''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records).encode())
  import io
  stream=io.StringIO(newline='');fields=['node_id','product_id','job_id','heading','parent_id','is_container','text','body_sha256','source_url'];w=csv.DictWriter(stream,fieldnames=fields);w.writeheader();w.writerows({k:r[k] for k in fields} for r in records);atomic(out/'sections.csv',stream.getvalue().encode());atomic(out/'coverage.json',report);reports.append(report)
 overall={'schema_version':SCHEMA,'selected_product_ids':list(cp['publications']),'visible_publication_inventory':cp.get('visible_publications',[]),'selected_publication_count':len(reports),'publication_complete':bool(reports) and all(r['publication_complete'] for r in reports),'publication_text_complete':bool(reports) and all(r['publication_text_complete'] for r in reports),'publication_attachments_complete':bool(reports) and all(r['publication_attachments_complete'] for r in reports),'jurisdiction_complete':False,'image_policy':POLICY,'image_omission_count':sum(r['image_omission_count'] for r in reports),'record_count':sum(r['parsed_record_count'] for r in reports),'phase':cp['phase'],'limit':cp.get('limit'),'publications':[{'product_id':r['product_id'],'coverage_path':'publications/'+str(r['product_id'])+'/coverage.json','publication_complete':r['publication_complete']} for r in reports]};atomic(folder/'coverage.json',overall);return overall
