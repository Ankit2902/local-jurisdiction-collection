"""municipal.codes typed-article/contents HTML projection. No source acquisition."""
import re
from html import escape
from html.parser import HTMLParser
from urllib.parse import urljoin,urlsplit,urlunsplit
from reader_utils import *

class Element:
 def __init__(self,tag='',attrs=(),parent=None):self.tag=tag;self.attrs=dict(attrs);self.parent=parent;self.children=[]
 def descendants(self):
  for c in self.children:
   if isinstance(c,Element):yield c;yield from c.descendants()
 def text(self):return ' '.join(x.strip() for x in self.tokens() if x.strip())
 def tokens(self):
  for c in self.children:
   if isinstance(c,str):yield c
   else:yield from c.tokens()
 def classes(self):return self.attrs.get('class','').split()
 def ancestors(self):
  p=self.parent
  while p:yield p;p=p.parent
class Document(HTMLParser):
 VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
 def __init__(self,raw):
  super().__init__(convert_charrefs=True);self.rawtext=raw.decode('utf-8',errors='strict');self.line_offsets=[0]
  for line in self.rawtext.split('\n')[:-1]:self.line_offsets.append(self.line_offsets[-1]+len(line)+1)
  self.root=Element();self.stack=[self.root];self.feed(self.rawtext);self.close()
 def handle_starttag(self,tag,attrs):
  require(len(attrs)==len(dict(attrs)),'Duplicate raw HTML attribute');n=Element(tag,attrs,self.stack[-1]);n.start=self.source_offset();n.end=n.start+len(self.get_starttag_text());self.stack[-1].children.append(n)
  if tag not in self.VOID:self.stack.append(n)
 def handle_startendtag(self,tag,attrs):self.handle_starttag(tag,attrs);self.handle_endtag(tag)
 def handle_endtag(self,tag):
  for i in range(len(self.stack)-1,0,-1):
   if self.stack[i].tag==tag:
    self.stack[i].end=self.rawtext.find('>',self.source_offset())+1;del self.stack[i:];break
 def source_offset(self):
  line,col=self.getpos();return self.line_offsets[line-1]+col
 def html(self,n):return self.rawtext[n.start:n.end]
 def handle_data(self,data):self.stack[-1].children.append(data)
 def all(self):return list(self.root.descendants())
def canonical_url(u):
 p=urlsplit(u);require(p.scheme=='https' and not p.username and not p.query,'Unsupported source URL');return urlunsplit((p.scheme,p.netloc,p.path.rstrip('/'),'',p.fragment))
def inside(u,base):
 p,b=urlsplit(u),urlsplit(base);return p.scheme=='https' and p.netloc==b.netloc and (p.path==b.path or p.path.startswith(b.path+'/')) and not p.query

def contents(raw,url,base):
 d=Document(raw);roots=[n for n in d.all() if n.tag=='ul' and 'contents-toc' in n.classes()];require(len(roots)==1,'Expected one literal full contents-toc')
 toc=roots[0];out=[];seen=set();li_identity={}
 for n in toc.descendants():
  if n.tag!='a' or 'href' not in n.attrs:continue
  u=canonical_url(urljoin(url,n.attrs['href']));require(inside(u,base) and not urlsplit(u).fragment,'Contents route outside selected publication')
  if u in [base,base+'/contents']:continue
  require(u not in seen,'Duplicate source contents route');seen.add(u)
  li=next((x for x in n.ancestors() if x.tag=='li'),None);require(li is not None,'Contents anchor without owning li')
  require(not any(x.tag=='a' for x in li.descendants() if x is not n and next((z for z in x.ancestors() if z.tag=='li'),None) is li),'Multiple direct anchors on contents item')
  parentli=next((x for x in li.ancestors() if x.tag=='li'),None);parent=li_identity.get(id(parentli));require(parentli is None or parent is not None,'Contents parent not previously observed')
  li_identity[id(li)]=u;out.append({'id':u,'heading':n.text(),'parent_id':parent,'source_classes':li.classes(),'source_href':n.attrs['href'],'source_identifier':li.attrs.get('data-identifier'),'source_product':li.attrs.get('data-product'),'ordinal':len(out)})
 require(out,'No publication inventory');return out

def heading_image(e):
 tag=e.tag.rsplit(':',1)[-1];a=e.attrs;typ=a.get('type','').strip().lower();u=a.get('src',a.get('data',a.get('href','')))
 return tag in ['img','picture','svg','image','use'] or tag=='input' and typ=='image' or tag in ['object','embed','source'] and (typ.startswith('image/') or 'srcset' in a or re.search(r'^(?:data:image/)|\.(?:png|jpe?g|gif|svg|webp|avif|bmp|tiff?|ico)(?:[?#]|$)',u,re.I))
def heading_image_anchor(e):
 return e.tag=='a' and (e.attrs.get('type','').strip().lower().startswith('image/') or re.search(r'^(?:data:image/)|\.(?:png|jpe?g|gif|svg|webp|avif|bmp|tiff?|ico)(?:[?#]|$)',e.attrs.get('href',''),re.I))
def normalized_heading(html):
 # Keep every image-free actual source header byte-exact. No pixels are read.
 try:check_html(html);return html,0
 except ValueError:pass
 d=Document(html.encode());count=0
 def serialize(e):
  nonlocal count
  if isinstance(e,str):return escape(e,quote=False)
  if heading_image_anchor(e):count+=1;return ''.join(serialize(c) for c in e.children)+'[IMAGE]'
  if heading_image(e):count+=1;return '[IMAGE]'
  attrs=[];markers=0
  for k,v in e.attrs.items():
   if k in ['background','poster','srcset'] or k=='style' and re.search(r'url\s*\(',v or '',re.I):markers+=1;continue
   if re.search(r'data\s*:\s*image/',v or '',re.I):continue
   attrs.append(' '+k+('="'+escape(v,quote=True)+'"' if v is not None else ''))
  count+=markers;start='<'+e.tag+''.join(attrs)+'>';content='[IMAGE]'*markers+''.join(serialize(c) for c in e.children)
  return start+content+('' if e.tag in Document.VOID else '</'+e.tag+'>')
 result=''.join(serialize(c) for c in d.root.children);check_html(result);return result,count

def own_heading(rawbytes,pageurl,base,ident,known):
 d=Document(rawbytes);matches=[]
 for article in [e for e in d.all() if e.tag=='article']:
  rid=None;history=article.attrs.get('data-history')
  headers=[e for e in article.descendants() if e.tag=='header' and next((p for p in e.ancestors() if p.tag=='article'),None) is article]
  require(len(headers)==1,'Typed article needs unique own header witness');header=headers[0];share=header.attrs.get('data-share','')
  if history:
   require(history.endswith('/history'),'Unknown native history URL');rid=canonical_url(urljoin(pageurl,history[:-8]))
  elif share:
   require(share.endswith('/share'),'Unknown native share URL');rid=canonical_url(urljoin(pageurl,share[:-6]))
  else:
   value=article.attrs.get('id');require(value,'Typed article has no stable ID');candidate=base+'/'+value;rid=candidate if candidate in known else base+'#'+value
  if rid==ident:matches.append((article,header))
 require(len(matches)==1,'Unique raw typed owner/header witness missing');article,header=matches[0];rawhtml=d.html(header);html,heading_images=normalized_heading(rawhtml);links=[]
 for e in header.descendants():
  if e.tag!='a' or 'href' not in e.attrs:continue
  href=e.attrs['href']
  if heading_image_anchor(e):
   links.append({'source_href':'[IMAGE]','resolved_url':'[IMAGE]','encoded_reference_sha256':sha(href.encode()),'label':e.text(),'image':True,'policy':'Header image reference intentionally omitted; caption retained, no bytes fetched or decoded'});continue
  u=urljoin(pageurl,href);fragment=urlsplit(u).fragment;targets=[x for x in article.descendants() if fragment and x.attrs.get('id')==fragment and next((p for p in x.ancestors() if p.tag=='article'),None) is article]
  local=urlsplit(u)._replace(fragment='').geturl()==ident.split('#')[0]
  links.append({'source_href':href,'resolved_url':u,'label':e.text(),'classes':e.classes(),'same_owner_fragment':local and len(targets)==1,'target_id':fragment or None,'target_count_in_own_article':len(targets),'source_target_html_sha256':sha(d.html(targets[0]).encode()) if local and len(targets)==1 else None,'policy':'Original heading callout retained separately; canonical note body not appended'})
 return {'source_heading_html':html,'source_heading_html_sha256':sha(html.encode()),'source_heading_raw_html_sha256':sha(rawhtml.encode()),'source_heading_image_placeholders':heading_images,'source_heading_links':links,'source_article_id':article.attrs.get('id'),'source_article_type_classes':[x for x in article.classes() if x.startswith('type-')]}

def read_projection(root,proof,family):
 root=envelope(root,proof,family,'municipal-codes');cp=load(root/'checkpoint.json');cfg=cp['config'];cov=load(root/'coverage.json');pubid=proof['publication_id'];base=cp['publication_url'];identity=cp['identity']
 require(cp.get('schema_version')=='icc-full-1.0' and cfg==proof['selected_config'] and cfg.get('family')=='municipal.codes' and not cfg.get('subtree') and not cfg.get('max_items'),'Only verified whole-publication municipal.codes acquisition scope')
 require(family.get('verified') is True and {k:v for k,v in family.items() if k!='verified'}==cov,'Wrong standard reconstruction/coverage report')
 require(canonical_url(cfg['url'])==base==identity['publication_base'] and identity['family']=='municipal.codes' and identity['currency_raw'] and urlsplit(base).netloc.endswith('.municipal.codes'),'Publication identity/root/currency not bound')
 require(cov['identity']==identity and cov['scope']=='whole_publication' and not cov['limits_applied'] and not cov['extra_ids'] and not cov['unresolved_ids'] and not cov['conflicting_duplicate_bodies'],'Unprofiled source ownership or bounded scope')
 for n,h in cp['code_fingerprint'].items():require(proof['collector_sources_before'].get(n)==h,'Wrong explicit standard verifier revision');raw(root,'executed-source/'+n,h)
 arts={a['path']:a for a in cp['artifacts']};require(len(arts)==len(cp['artifacts']),'Duplicate raw artifact path')
 for a in arts.values():
  raw(root,a['path'],a['sha256']);require(safe(root,a['path']).stat().st_size==a['bytes'],'Raw byte size mismatch');require(not a.get('headers',{}).get('content-type','').strip().lower().startswith('image/'),'Separate image response forbidden')
 inv=load(root/'inventory.json');ds=load(root/'dispositions.json');records=lines(root/'records.jsonl');by={n['id']:n for n in inv};disps={d['id']:d for d in ds};rmap={r['id']:r for r in records};missing=set(cov['missing_ids'])
 require(len(by)==len(inv)==cov['inventory_nodes'] and len(disps)==len(ds) and len(rmap)==len(records)==cov['normalized_records']==cov['owned_content_nodes'],'Duplicate/missing inventory, disposition or record')
 require(set(by)==set(disps)|missing and not set(disps)&missing,'All source inventory must reconcile resolved OR explicitly missing')
 require(set(rmap)=={n for n,d in disps.items() if d['classification']=='owned_content'},'Owned body omitted/foreign/unsupported nontext body')
 require(all(d['classification'] in ['owned_content','structural_empty','reserved_or_repealed_empty'] for d in ds),'Unsupported resolved disposition')
 starts=[a for a in arts.values() if a['role']=='contents-start' and a['status']==200];roots=[a for a in arts.values() if a['role']=='root-start' and a['status']==200];require(len(starts)==len(roots)==1,'Unique opening root/full contents required');start=starts[0];opening=roots[0]
 ordered=contents(safe(root,start['path']).read_bytes(),start['url'],base);tocmap={n['id']:n for n in ordered}
 for n in ordered:
  require(n['id'] in by and n['heading']==by[n['id']]['heading'] and n['parent_id']==by[n['id']].get('parent_id') and n['source_classes']==by[n['id']].get('source_classes'),'Literal source contents differs from retained inventory')
 # Only explicitly typed, root-owned preface may precede the full contents tree.
 extras=set(by)-set(tocmap)-{base};front=[];doc=Document(safe(root,opening['path']).read_bytes())
 for e in doc.all():
  if e.tag!='article':continue
  ident=e.attrs.get('id');u=base+'#'+ident if ident else None
  if u not in extras:continue
  require('type-Preface' in e.classes() and not e.attrs.get('data-history') and not any(x.tag=='article' for x in e.ancestors()),'Unordered non-TOC body is not root frontmatter');front.append(u)
 require(len(front)==len(set(front)) and set(front)==extras,'Source order unavailable for non-TOC descriptor')
 orderids=[base]+front+[n['id'] for n in ordered];require(len(orderids)==len(by),'Source order reconciliation mismatch')
 positions={n:i for i,n in enumerate(orderids)}
 # Closing checks remain mandatory for complete input too, not only this partial proof.
 closes=[a for a in arts.values() if a['role']=='contents-end' and a['status']==200];endroots=[a for a in arts.values() if a['role']=='root-end' and a['status']==200]
 if cov['complete']:
  require(not missing and not cov['errors'] and not cov['missing_assets'] and not cov['unresolved_links'] and cov['publication_text_complete'] and cov['attachments_complete'] and cov['start_end_inventory_consistent'] and cov['edition_complete'],'Complete source gates inconsistent')
  require(len(closes)==len(endroots)==1,'Complete input requires actual source closing inventory/root');require(contents(safe(root,closes[0]['path']).read_bytes(),closes[0]['url'],base)==ordered,'Closing source inventory/order drift')
  require(endroots[0]['retrieved_at']>=max(a['retrieved_at'] for a in arts.values() if a['role'] in ['root-start','contents-start','content','asset','native'] and a['status']==200),'Closing source precedes acquired bodies/assets')
 def ancestry(ident):
  chain=[];seen=set()
  while ident:
   require(ident in by and ident not in seen,'Unknown/cyclic source parent');seen.add(ident);chain.insert(0,by[ident]);ident=rmap.get(ident,{}).get('parent_id') or by[ident].get('parent_id')
  return chain
 version={'snapshot_id':'sha256:'+file_hash(root/'checkpoint.json'),'publisher_identity':identity,'publisher_currency_raw':identity['currency_raw'],'edition_complete':cov['edition_complete'],'interpretation':'Exact source labels and actual inherited closing gates; no legal-effective-date inference'}
 nodes=[];dispositions=[];rows=[];provenance=[];exceptions=[]
 for pos,ident in enumerate(orderids):
  n=by[ident];r=rmap.get(ident);parent=(r or {}).get('parent_id') or n.get('parent_id') or (base if ident!=base else None);a=opening if ident==base or ident in front else start
  witness={'raw_artifact_path':'evidence/input/'+a['path'],'raw_sha256':a['sha256'],'kind':'opening root typed-preface DOM order' if ident in front else ('publication wrapper' if ident==base else 'full contents-toc literal anchor preorder'),'source_contents_entry':tocmap.get(ident)}
  nodes.append({'node_id':'source:'+ident,'publication_id':pubid,'parent_node_id':'source:'+parent if parent else None,'source_order':pos,'source_order_domain':'Opening root frontmatter DOM followed by independent full contents DOM preorder','source_order_witness':witness,'node_kind':n['kind'],'display_heading':n['heading'],'source_url':n['url'],'publisher_descriptor':n,'source_version':version['snapshot_id'],'raw_artifact_path':witness['raw_artifact_path'],'raw_sha256':a['sha256'],'locator':{'kind':'municipal.codes observed publication route/typed article','url':ident}})
  cl=disps.get(ident,{}).get('classification');dispositions.append({'node_id':'source:'+ident,'disposition':'unresolved' if ident in missing else {'owned_content':'included','structural_empty':'structural','reserved_or_repealed_empty':'reserved_or_repealed'}[cl],'record_ids':[pubid+':'+ident] if r else [],'evidence':disps.get(ident,{'id':ident,'classification':'missing_unacquired','evidence':'Independent contents inventory; no source body/disposition acquired before access stop'})})
 ordinals={r['id']:i for i,r in enumerate(records)}
 for r in sorted(records,key=lambda r:positions[r['id']]):
  ident=r['id'];chain=ancestry(ident);require(r['path']==[n['heading'] for n in chain],'Source body ancestry/path mismatch');require(r['source_url']==ident and r['edition']=={k:v for k,v in identity.items() if k not in ['name','state']},'Wrong body source/edition')
  require(r['raw_witnesses'] and all(x in arts and arts[x]['role'] in ['root-start','content','native'] and arts[x]['status']==200 for x in r['raw_witnesses']),'Body has no successful explicit raw witness');a=arts[r['raw_witnesses'][0]];html=r['semantic_html'];check_html(html);require(r['body_sha256']==sha(canonical({'heading':r['heading'],'html':html})),'Canonical body hash mismatch');require(html.count('[IMAGE]')==r['image_placeholder_count'],'Image placeholder ownership mismatch')
  heading_source=own_heading(safe(root,a['path']).read_bytes(),a['url'],base,ident,by)
  row,fields,conflicts=corpus_row(cfg['jurisdiction'],identity['name'],chain,r['heading'],html,ident,a['retrieved_at']);rows.append(row);rid=pubid+':'+ident
  provenance.append({'record_id':rid,'node_ids':['source:'+ident],'source_version':version,'source_order':positions[ident],**heading_source,'source_order_domain':'Literal opening-frontmatter/contents DOM composite order; retained IR ordinal separate','raw_artifact_path':'evidence/input/'+a['path'],'raw_sha256':a['sha256'],'raw_witnesses':[{'path':'evidence/input/'+x,'sha256':arts[x]['sha256'],'retrieved_at':arts[x]['retrieved_at']} for x in r['raw_witnesses']],'locator':{'kind':'exclusive typed article','canonical_url':ident},'rich_ir':{'path':'evidence/input/records.jsonl','line_ordinal':ordinals[ident],'record_sha256':sha(canonical(r))},'canonical_html_field':'semantic_html','canonical_html_sha256':sha(html.encode()),'notes_html':r['notes_html'],'tables_html':r['tables_html'],'links':r['links'],'assets':r['assets'],'image_references':r['image_references'],'image_placeholder_count':r['image_placeholder_count'],'hierarchy_chain':chain,'field_source_components':fields,'hierarchy_conflicts':conflicts,'extraction_versions':cp['code_fingerprint']})
  exceptions.extend({'kind':'hierarchy_scalar_conflict','record_id':rid,**c} for c in conflicts)
 exceptions.extend({'kind':'missing_source_body','source_url':ident} for ident in orderids if ident in missing);exceptions.extend({'kind':'inherited_source_error','evidence':e} for e in cov['errors']);exceptions.extend({'kind':'unqualified_required_nonimage_document','source_url':u} for u in cov['missing_assets'])
 if not cov['start_end_inventory_consistent']:exceptions.append({'kind':'missing_or_inconsistent_closing_source','qualification':False})
 accepted=cov.get('publication_accepted',False) is True
 pubs=[{'publication_id':pubid,'official_title':identity['name'],'root':base,'stable_identity':identity,'source_version':version,'scope_disposition':'Every retained inventory node and acquired canonical own body; missing nodes explicit','publication_accepted':accepted,'complete':cov['complete'],'jurisdiction_discovery_complete':False,'scope_evidence':'evidence/input/coverage.json'}]
 times=[a['retrieved_at'] for a in arts.values()];meta={'jurisdiction':cfg['jurisdiction'],'source_config':cfg,'source_version':version,'acquisition_interval':{'started_at':min(times),'finished_at':max(times),'role':'Original retained source receipts, not export time'},'reader_scope':'Whole-publication-capable typed article/full-contents projection; real qualification limited incomplete Phoenix Charter acquisition','publication_accepted':accepted,'complete':cov['complete'],'source_order_qualified':True,'source_order_nodes':len(orderids),'missing_source_nodes':len(missing),'notes_policy':'Canonical own-body notes once; typed arrays retained as provenance','source_verification_mode':'Actual exact explicitly selected standard engine raw reconstruction; no inferred source completeness'}
 return finish(pubid,rows,pubs,nodes,dispositions,provenance,exceptions,meta,cov)
