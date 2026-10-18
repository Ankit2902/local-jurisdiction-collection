"""Pure exact same-publication CodePublishing router/anchor reconciliation."""
import hashlib,re
from urllib.parse import urlsplit,unquote
from bs4 import BeautifulSoup

def digest(data):return hashlib.sha256(data).hexdigest()
def router_target(url,config):
 if not config.get('resolve_internal_router_references') or config.get('mode')!='legacy_codepublishing':return None
 base,target=urlsplit(config['source_url']),urlsplit(url)
 if (target.scheme,target.netloc,target.path,target.query)!=(base.scheme,base.netloc,base.path,base.query) or target.username or target.password:return None
 fragment=target.fragment
 if not fragment.startswith('!/') or '#' not in fragment:return None
 route,anchor=fragment[2:].split('#',1)
 if not re.fullmatch(r'[A-Za-z0-9_-]+/[A-Za-z0-9_.-]+\.html',route) or any(p in ['.','..']for p in unquote(route).split('/')) or not anchor:return None
 return {'document_url':url.split('#',1)[0]+'#!/'+route,'source_anchor':unquote(anchor),'route':route}

def resolve(assets,documents,config):
 """documents contain verified retained raw bytes and source-bound record IDs."""
 result=[];parsed={}
 for original in assets:
  asset=dict(original);target=router_target(asset.get('url',''),config)
  if not target:result.append(asset);continue
  proof={**target,'reference_url':asset['url']};doc=documents.get(target['document_url'])
  asset.update(classification='internal_legal_cross_reference',status='unresolved',requires_manual_review=True,reason='Exact internal router target is not acquired in the selected publication',internal_reference=proof)
  if not doc:result.append(asset);continue
  data=doc['data'];actual=digest(data)
  if actual!=doc['raw_sha256']:raise ValueError('Internal router target raw-source hash mismatch')
  proof.update(target_document_id=doc['id'],target_raw_ref=doc['raw_ref'],target_source_sha256=actual,target_record_ids=doc['record_ids'])
  if doc['id'] not in parsed:
   soup=BeautifulSoup(data,'html.parser');nodes=soup.select(config.get('content_selector','#mainContent'))
   if len(nodes)!=1:raise ValueError('Internal router target legal body absent/nonunique')
   parsed[doc['id']]=nodes[0]
  node=parsed[doc['id']];hits=[e for e in [node]+node.select('[id],[name]') if e.get('id')==target['source_anchor'] or e.get('name')==target['source_anchor']]
  # A heading id and its nested legacy name-anchor are one source target;
  # unrelated repeated IDs are ambiguous and must remain incomplete.
  roots=[e for e in hits if not any(parent in hits for parent in e.parents)]
  proof.update(source_target_count=len(hits),exclusive_source_target_count=len(roots),source_target_tags=[e.name for e in hits],source_target_sha256=[digest(str(e).encode())for e in roots])
  if len(roots)==1:
   asset.update(status='retained_internal_reference',requires_manual_review=False,reason='Exact same-publication router document and exclusive legal-body anchor exist in hash-bound retained source')
  elif not roots:asset['reason']='Referenced router document acquired, but exact legal-body anchor is absent in publisher source'
  else:asset['reason']='Referenced legal-body anchor is nonunique outside nested alias ancestry'
  result.append(asset)
 return result
