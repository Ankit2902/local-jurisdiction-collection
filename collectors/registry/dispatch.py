"""No-network adapter dispatch. Only explicit, qualified publication configurations run."""
import json,re
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[2]
def read(p):return json.loads(p.read_text())
def normalized(u):
 p=urlparse(u);path=p.path.rstrip('/')
 for suffix in ['/doc-viewer.aspx','/doc-view.aspx','/ereader']:path=path.removesuffix(suffix)
 return p.netloc.lower()+path
class Unsupported(ValueError):pass
OFFICIAL_PRIMARY={18:'portland-code',20:'baltimore-code',21:'milwaukee-publications',56:'burlington',58:'arlington-tx-code',78:'spokane-code',80:'worcester-part1',99:'arlington-va-current-portal'}
def qualified(pub,target):
 family=pub['publisher'];url=pub['source_url'];identity=pub.get('expected_identity') or target['expected_identity'];detail={'publisher':family,'config':None,'config_path':None}
 if not pub.get('runnable',True):raise Unsupported(pub.get('unsupported_reason') or 'Publication not qualified')
 if family=='municode':
  pid=pub.get('publisher_product_id') or pub.get('selector',{}).get('product_id')
  if not pid or not identity.get('client_names'):raise Unsupported('An observed product ID and explicit client identity are required; default all-publications selection is not used by this registry')
  detail['product_id']=int(pid)
 elif family=='official':
  configs=ROOT/'collectors/official/configs';match=None
  if pub.get('adapter_config_path'):
   p=ROOT/pub['adapter_config_path']
   if p.parent!=configs or not p.is_file() or normalized(read(p).get('source_url',''))!=normalized(url):raise Unsupported('Explicit official config/source does not match qualified config directory')
   match=p
  if pub['role']=='primary':
   name=OFFICIAL_PRIMARY.get(target['sequence']);p=configs/(str(name)+'.json')
   if p.exists():match=p
  if not match:
   candidates=[p for p in sorted(configs.glob('*.json')) if normalized(read(p).get('source_url',''))==normalized(url)]
   if len(candidates)==1:match=candidates[0]
  if match:detail.update(config=read(match),config_path=str(match.relative_to(ROOT)))
  elif urlparse(url).path.lower().endswith('.pdf'):
   detail['config']={'schema':1,'id':pub['id'],'jurisdiction':target['jurisdiction'],'state':target['state'],'publication':pub['title'],'source_url':url,'mode':'pdf','transport':'http','scope_note':'One exact observed native PDF publication; page extraction is not semantic/section equivalence'}
  else:raise Unsupported('Known government route lacks a qualified publication inventory/content selector; it is not assumed to be a complete publication')
 elif family=='encodeplus':
  p=ROOT/'collectors/encodeplus/targets.json';known=read(p) if p.exists() else {};matches=[(k,v) for k,v in known.items() if normalized(v['base'])==normalized(url)]
  if len(matches)==1:detail.update(target_key=matches[0][0],config=matches[0][1])
  elif len([p for p in (ROOT/'collectors/encodeplus/configs').glob('*.json') if normalized(read(p).get('base',''))==normalized(url)])==1:
   p=next(p for p in (ROOT/'collectors/encodeplus/configs').glob('*.json') if normalized(read(p).get('base',''))==normalized(url));detail.update(target_key=pub['id'],config=read(p),custom_config=True,config_path=str(p.relative_to(ROOT)))
  elif pub.get('adapter_config',{}).get('identity'):detail.update(target_key=pub['id'],config=pub['adapter_config'],custom_config=True)
  else:raise Unsupported('Exact secondary enCodePlus TOC identity/base configuration remains unqualified; observed landing/link alone is insufficient')
 elif family=='ecode':
  if pub['source_family']=='ecode360' and not identity.get('customer_id'):raise Unsupported('Expected eCode customer identity required')
  if pub['source_family']=='municipal.codes' and len(urlparse(url).path.strip('/').split('/'))!=1:raise Unsupported('Select an observed publication root/tab, not a sampled chapter')
 elif family=='american-legal':
  if '/latest/' not in url:raise Unsupported('An observed American Legal library/publication route is required')
  if url.rstrip('/').endswith('/overview') and not pub.get('selector',{}).get('publication'):raise Unsupported('Library overview requires an exact observed publication selector')
 elif family=='gridics':
  config_path=pub.get('adapter_config_path');p=ROOT/config_path if config_path else None
  if not p or p.parent!=ROOT/'collectors/gridics/configs' or not p.is_file():raise Unsupported('Exact qualified Gridics publication config required')
  config=read(p)
  if config.get('source_url')!=url or config.get('state')!=target['state'] or config.get('jurisdiction')!=target['jurisdiction'] or not config.get('document_id'):raise Unsupported('Gridics publication/government/config binding mismatch')
  detail.update(config=config,config_path=str(p.relative_to(ROOT)))
 else:raise Unsupported('No collector adapter for '+family)
 return detail

def command(pub,target,out,python='python3',resume=False,max_items=None,verify=False):
 q=qualified(pub,target);family=q['publisher'];url=pub['source_url'];identity=pub.get('expected_identity') or target['expected_identity'];config=q.get('config')
 if family=='municode':
  if verify:argv=[python,'collectors/municode/verify.py',out,'--offline']
  else:
   argv=[python,'collectors/municode/collect.py','--url',url,'--state',target['state'],'--product-id',str(q['product_id']),'--out',out]
   for name in identity['client_names']:argv+=['--client-name',name]
   if identity.get('publisher_client_id'):argv+=['--client-id',str(identity['publisher_client_id'])]
 elif family=='official':argv=[python,'collectors/official/verify.py',out] if verify else [python,'collectors/official/collect.py','--config',q['config_path'] or '{CONFIG}','--out',out]
 elif family=='encodeplus':
  argv=[python,'-m','collectors.encodeplus.verify',out] if verify else [python,'-m','collectors.encodeplus.collect',q['target_key'],'--out',out]
  if not verify and q.get('custom_config'):argv+=['--config','{CONFIG}']
 elif family=='ecode':
  argv=[python,'-m','collectors.ecode.cli','verify','--out',out] if verify else [python,'-m','collectors.ecode.cli','collect','--url',url,'--out',out,'--family',pub['source_family'],'--jurisdiction',target['jurisdiction'],'--state',target['state']]
  if not verify and pub['source_family']=='municipal.codes':argv+=['--publication',urlparse(url).path.strip('/')]
 elif family=='american-legal':
  argv=[python,'collectors/american-legal/verify.py',out,'--offline'] if verify else [python,'collectors/american-legal/collect.py','--url',url,'--out',out,'--jurisdiction',target['jurisdiction'],'--state',target['state']]
  if not verify and pub.get('selector',{}).get('publication'):argv+=['--publication',pub['selector']['publication']]
  if not verify:
   for alias in identity.get('identity_aliases',[]):argv+=['--identity-alias',alias]
   if pub.get('acquisition_strategy'):
    if pub['acquisition_strategy'] not in ('native','traverse'):raise Unsupported('Unknown explicit American Legal acquisition strategy')
    argv+=['--strategy',pub['acquisition_strategy']]
 elif family=='gridics':
  if max_items is not None:raise Unsupported('Gridics has no qualified bounded mode; full inventory/traversal is required')
  argv=[python,'-m','collectors.gridics.collect','verify' if verify else 'collect','--config',q['config_path'],'--out',out]
 if not verify:
  if resume:argv+=['--resume']
  if max_items is not None:argv+=['--max-items',str(max_items)]
 return {'argv':argv,'staged_config':config if '{CONFIG}' in argv else None,'qualified_config_path':q.get('config_path'),'publication_id':pub['id'],'publication_title':pub['title'],'publication_expected_identity':identity,'required_for_jurisdiction':pub['required_for_jurisdiction'],'jurisdiction_scope':pub.get('jurisdiction_scope'),'edition_scope':pub.get('edition_scope'),'required_publication_dependencies':pub.get('required_publication_dependencies',[]),'configuration_alias_of':pub.get('configuration_alias_of'),'scope':pub['scope_kind'],'image_policy':pub.get('image_policy'),'jurisdiction_complete':False}

def bind_run(pub,target,out):
 """Fail before dispatch if retained run belongs to another selected publication.

 This checks expected scope only. The family verifier still reconstructs and validates
 raw source evidence, so rewriting a checkpoint cannot establish a passing run.
 """
 q=qualified(pub,target);out=Path(out);family=q['publisher'];identity=pub.get('expected_identity') or target['expected_identity'];url=pub['source_url']
 def require(ok,why):
  if not ok:raise Unsupported('Selected target/publication does not match retained run: '+why)
 if family=='official':require(read(out/'config.json')==q['config'],'exact official publication config')
 elif family=='encodeplus':require(read(out/'checkpoint.json')['config']==q['config'],'exact enCodePlus publication config')
 elif family=='municode':
  cp=read(out/'checkpoint.json');b=cp['binding'];require(normalized(cp['source_url'])==normalized(url),'Municode source route');require(b.get('state')==target['state'] and b.get('client_names')==identity['client_names'],'Municode expected client/state');require(b.get('product_ids')==[q['product_id']],'explicit Municode product scope')
  if identity.get('publisher_client_id'):require(b.get('expected_client_id')==identity['publisher_client_id'],'Municode client ID')
 elif family=='american-legal':
  m=read(out/'run.json');require(normalized(m['source_url'])==normalized(url),'American Legal publication route');require(m['expected_jurisdiction']==target['jurisdiction'] and m['expected_state']==target['state'],'American Legal government/state');require(m.get('publication_selector')==pub.get('selector',{}).get('publication'),'American Legal explicit publication selector')
 elif family=='ecode':
  cp=read(out/'checkpoint.json');c=cp['config'];require(c['family']==pub['source_family'] and normalized(c['url'])==normalized(url),'eCode source family/route');require(c.get('jurisdiction')==target['jurisdiction'] and c.get('state')==target['state'],'eCode government/state');require(not c.get('subtree'),'whole-publication scope required')
  if pub['source_family']=='municipal.codes':require(normalized(cp['publication_url'])==normalized(url),'municipal publication tab')
  if identity.get('customer_id'):require(str(cp['identity'].get('customer_id'))==str(identity['customer_id']),'eCode customer identity')
 elif family=='gridics':require(read(out/'acquisition.json')['config']==q['config'],'exact Gridics publication/source/config')
 return True
