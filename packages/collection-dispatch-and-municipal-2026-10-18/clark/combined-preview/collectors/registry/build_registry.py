"""Authoring only: compile compact source-backed registry from immutable bounded evidence."""
import json,re,hashlib,zipfile
from pathlib import Path
from urllib.parse import urlparse,urlunparse,parse_qs,quote
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
INDEX=ROOT/'expanded-scope-index.json'
def load(p):return json.loads(p.read_text())
def norm(x):return re.sub('[^a-z0-9]','',str(x).lower())
def clean_url(u):
 p=urlparse(u);path=p.path.rstrip('/')
 if 'library.municode.com' in p.netloc and '/codes/' in path:path='/'.join(path.split('/')[:5])
 elif p.netloc.endswith('municipal.codes'):path='/'+path.strip('/').split('/')[0]
 elif 'codelibrary.amlegal.com' in p.netloc:path=re.sub('/0-0-0-[0-9]+$','',path)
 elif 'codepublishing.com' in p.netloc:path=path+'/'
 return urlunparse((p.scheme,p.netloc,path,'','',''))
def adapter(u):
 h=urlparse(u).netloc.lower()
 if h=='library.municode.com':return 'municode'
 if h=='codelibrary.amlegal.com':return 'american-legal'
 if h=='ecode360.com' or h.endswith('municipal.codes'):return 'ecode'
 if 'encodeplus.com' in h or h=='codes.opkansas.org':return 'encodeplus'
 return 'official'
def canonical_secondary(u):
 p=urlparse(u)
 if 'encodeplus.com' in p.netloc and '/regs/' in p.path:
  return urlunparse((p.scheme,p.netloc,'/'.join(p.path.split('/')[:3])+'/','','','')) if 'doclibrary.aspx' not in p.path else u
 if p.netloc=='codes.opkansas.org' and 'doclibrary.aspx' not in p.path:return urlunparse((p.scheme,p.netloc,'/'+p.path.strip('/').split('/')[0]+'/','','',''))
 return u

def subtype(u):
 h=urlparse(u).netloc.lower()
 return 'municipal.codes' if h.endswith('municipal.codes') else 'ecode360' if h=='ecode360.com' else 'CodePublishing' if 'codepublishing.com' in h else adapter(u)
def title(u):
 p=urlparse(u)
 if '/codes/' in p.path and p.netloc=='library.municode.com':return p.path.split('/codes/')[1].split('/')[0].replace('_',' ').title()
 if p.netloc.endswith('municipal.codes'):return {'CC':'City Code','Code':'Code','EC':'Eugene Code','UDO':'Unified Development Ordinance','ZO':'Zoning Ordinance','Charter':'Charter'}.get(p.path.strip('/'),'Code')
 return 'Primary publication; exact title resolved from publisher source'
def rel(p):return str(p.relative_to(ROOT))

def main():
 idx=load(INDEX)['jurisdictions'];assign={};rows={};ident={};catalogs={};ledger={a['sequence']:[] for a in idx};pubs={}
 for p in sorted((ROOT/'packages').glob('*/*/assignment.json')):
  a=load(p)
  if isinstance(a,list):
   for r in a:
    if isinstance(r,dict) and 'sequence' in r:assign[r['sequence']]=r
 for r in idx:
  seq=r['sequence'];p=ROOT/r['working_directory']/'results.json';detail=next(x for x in load(p) if x.get('sequence')==seq);rows[seq]=detail
  for ep in detail.get('evidence_paths',[]):
   fp=p.parent/ep
   if fp.name=='receipt.json' and fp.is_file():
    try:v=load(fp)
    except Exception:continue
    if v.get('product') and clean_url(v.get('url',''))==clean_url(r['validated_source_url']):
     ident[seq]={'client_names':[v['product']['Client']['ClientName']],'state':v['product']['Client']['State']['StateAbbreviation'],'publisher_client_id':v['product']['Client']['ClientID'],'publisher_product_name':v['product']['ProductName'],'publisher_product_id':v['product']['ProductID'],'publisher_publication_id':next((x.get('publicationId') for x in v.get('publications',[]) if x.get('productId')==v['product']['ProductID']),None),'evidence_path':rel(fp)}
     catalogs[seq]=v.get('publications',[])
  # Some older detail packages retain current proof in a named primary folder outside evidence list.
  if adapter(r['validated_source_url'])=='municode' and seq not in ident:
   for fp in sorted(p.parent.glob('**/receipt.json')):
    try:v=load(fp)
    except Exception:continue
    if v.get('product') and clean_url(v.get('url',''))==clean_url(r['validated_source_url']):
     ident[seq]={'client_names':[v['product']['Client']['ClientName']],'state':v['product']['Client']['State']['StateAbbreviation'],'publisher_client_id':v['product']['Client']['ClientID'],'publisher_product_name':v['product']['ProductName'],'publisher_product_id':v['product']['ProductID'],'publisher_publication_id':next((x.get('publicationId') for x in v.get('publications',[]) if x.get('productId')==v['product']['ProductID']),None),'evidence_path':rel(fp)};catalogs[seq]=v.get('publications',[])
  pi=detail.get('publication_inventory')
  if pi:ledger[seq].append((pi,rel(p)))
 # Structured prior inventories. None is an exhaustive jurisdiction inventory.
 files=[p for p in (ROOT/'packages').glob('*/*/*.json') if p.name in ['publication-inventory.json','scope-inventory.json','source-scope-inventory.json','code-families.json','publication-families.json']]
 files+=list((ROOT/'packages').glob('*/*/research/publication-inventory.json'))
 for p in sorted(set(files)):
  data=load(p)
  if isinstance(data,dict):entries=[{'jurisdiction':k,**v} for k,v in data.items() if isinstance(v,dict)]
  else:entries=data
  for ent in entries:
   if not isinstance(ent,dict):continue
   seq=ent.get('sequence');key=norm(ent.get('jurisdiction',ent.get('job','')))
   if seq not in ledger:
    candidates=[r['sequence'] for r in idx if key and (norm(r['jurisdiction'])==key or key in norm(r['jurisdiction']) or norm(r['jurisdiction']) in key)]
    if len(candidates)!=1:continue
    seq=candidates[0]
   ledger[seq].append((ent,rel(p)))
 # Auroras migration inventory is separate from the original group inventory.
 ap=ROOT/'packages/expanded57-validation-2026-10-17/municode-major/aurora-current/publication-inventory.json'
 if ap.exists():
  v=load(ap);ledger[35].append((v,rel(ap)))
 targets=[]
 for r in idx:
  seq=r['sequence'];d=rows[seq];a=assign.get(seq,{});u=clean_url(r['validated_source_url']);family=adapter(u);identity=ident.get(seq,{'client_names':[r['jurisdiction']],'state':r['state']});primary_id=f'{seq}-primary';observed_al_codes=[];al_evidence=None
  primary={'id':primary_id,'target_id':str(seq),'title':identity.get('publisher_product_name',title(u)),'observed_title':identity.get('publisher_product_name'),'source_url':u,'publisher':family,'source_family':subtype(u),'scope_kind':'publication','role':'primary','required_for_jurisdiction':True,'expected_identity':identity,'publisher_product_id':identity.get('publisher_product_id'),'publisher_publication_id':identity.get('publisher_publication_id'),'selector':{},'runnable':True,'unsupported_reason':None,'validation_level':'mapped_only','full_live_verified':False,'evidence_paths':['expanded-scope-index.json',r['working_directory']+'/results.json']}
  if family=='american-legal':
   for ep in d.get('evidence_paths',[]):
    rp=ROOT/r['working_directory']/ep
    if rp.name!='receipt.json':continue
    overview=rp.parent/'overview.html'
    if not overview.exists():continue
    match=re.search(r'window\._redux_state\s*=\s*JSON\.parse\(("(?:[^"\\]|\\.)*")',overview.read_text())
    if not match:continue
    codes=json.loads(json.loads(match[1]))['codes'];client=codes['currClient'];version=codes['selectedVersion'];slug=urlparse(u).path.split('/')[4];selected=next((c for c in version['toc'] if c['slug']==slug),None)
    if selected:
     identity.update(publisher_client_name=client['name'],identity_aliases=[client['name']],publisher_code_slug=slug,evidence_path=rel(overview));primary.update(title=selected['title'],observed_title=selected['title'],selector={'publication':slug});primary['evidence_paths'].append(rel(overview));observed_al_codes=version['toc'];al_evidence=rel(overview);break
  if family=='municode':primary['selector']={'product_id':identity.get('publisher_product_id')}
  elif subtype(u)=='municipal.codes':primary['selector']={'publication_path':urlparse(u).path}
  pubs[primary_id]=primary
  known=[];seen=set()
  def add(label,url=None,relationship='unresolved',evidence=None,extra=None):
   label=str(label)
   if url and adapter(url)=='encodeplus':
    parsed=urlparse(url)
    if re.search(r'(?:search|archive|autotabs|calculators|about|landuselookup|page[/.])',parsed.path,re.I) or re.search(r'^Skip|^View Code$|^Search|^Resources$|^About$',label,re.I):
     relationship='publication_control'
    elif '#secid-' in url and parsed.netloc=='codes.opkansas.org' and parsed.path.startswith('/municipal-code/'):relationship='embedded_primary'
   key=(norm(label),url,relationship)
   if not label.strip() or key in seen:return
   seen.add(key);item={'label':label,'relationship':relationship,'source_url':url,'evidence_path':evidence,'required_for_jurisdiction':True,'full_live_verified':False}
   if extra:item['metadata']=extra
   if relationship=='publication_control':item.update(required_for_jurisdiction=False,runnable=False,unsupported_reason='Search/archive/navigation control, not an independently published legal unit.')
   elif relationship=='embedded_primary':item.update(covered_by_publication_id=primary_id,runnable_via=primary_id)
   elif relationship=='separate_publisher_product' and extra and family=='municode':
    sid=f'{seq}-product-'+str(extra['productId']);entry={'id':sid,'target_id':str(seq),'title':label,'source_url':u,'source_route_kind':'client context with explicit observed product selector','publisher':'municode','source_family':'municode','scope_kind':'publication','role':'secondary','required_for_jurisdiction':not bool(extra.get('hideInLibrary')) and not bool(re.search(r'previous|historical|superseded',label,re.I)),'expected_identity':identity,'publisher_product_id':extra['productId'],'publisher_publication_id':extra.get('publicationId'),'selector':{'product_id':extra['productId']},'runnable':not bool(extra.get('hideInLibrary')),'unsupported_reason':'Hidden publication is not a qualified current source' if extra.get('hideInLibrary') else None,'validation_level':'mapped_only','full_live_verified':False,'evidence_paths':[evidence] if evidence else []};pubs[sid]=entry;item.update(publication_id=sid,runnable=entry['runnable'],required_for_jurisdiction=entry['required_for_jurisdiction'],unsupported_reason=entry['unsupported_reason'])
   elif url and url.startswith(('https://','http://')):
    sid=f'{seq}-'+hashlib.sha256((label+'|'+url).encode()).hexdigest()[:12];su=clean_url(url) if 'codelibrary.amlegal.com' in url else url.split('#')[0] if 'ecode360.com' in url else url
    target_adapter=adapter(su)
    if target_adapter=='encodeplus' and 'doclibrary.aspx' not in url:
     su=canonical_secondary(su);sid=f'{seq}-'+hashlib.sha256(su.encode()).hexdigest()[:12]
    entry={'id':sid,'target_id':str(seq),'title':label,'source_url':su,'publisher':target_adapter,'source_family':subtype(su),'scope_kind':'publication_candidate','role':'secondary','required_for_jurisdiction':True,'expected_identity':identity,'selector':{},'runnable':True,'unsupported_reason':None,'validation_level':'mapped_only','full_live_verified':False,'evidence_paths':[evidence] if evidence else []}
    if extra and extra.get('adapter_config_path'):entry['adapter_config_path']=extra['adapter_config_path']
    if extra and extra.get('publication_selector'):entry.update(selector={'publication':extra['publication_selector']},observed_title=label)
    if target_adapter=='american-legal' and '/latest/' in su and not su.rstrip('/').endswith('/overview'):entry['selector']={'publication':urlparse(su).path.split('/')[4]}
    if target_adapter=='official' and 'gridics.com' in url:entry.update(runnable=False,unsupported_reason='Gridics dynamic publication requires a qualified adapter/current inventory; generic official HTML is not assumed to cover it.')
    if urlparse(su).path.lower().endswith('.pdf'):entry['adapter_config']={'mode':'pdf','publication':label,'source_url':su,'jurisdiction':r['jurisdiction'],'state':r['state']}
    if re.search(r'Lancaster County|Johnson County|Oxford Township',label,re.I):entry.update(required_for_jurisdiction=False,jurisdiction_scope='external county/township reference; not automatically Lincoln or Overland Park law')
    if re.search(r'prior|historical|superseded|archive|legacy',label,re.I):entry.update(required_for_jurisdiction=False,edition_scope='historical reference')
    if extra and extra.get('covered_by_primary'):entry.update(required_for_jurisdiction=False,covered_by_publication_id=primary_id)
    pubs.setdefault(sid,entry);item.update(publication_id=sid,runnable=entry['runnable'],required_for_jurisdiction=entry['required_for_jurisdiction'],unsupported_reason=entry['unsupported_reason'])
   else:item.update(runnable=False,unsupported_reason='No exact separately published source URL/selector qualified in retained inventory; discovery required.')
   known.append(item)
  # Walk only publication/family objects, not individual code leaf records.
  def walk(obj,evidence,parentkey=''):
   if isinstance(obj,list):
    for x in obj:walk(x,evidence,parentkey)
   elif isinstance(obj,dict):
    if 'productName' in obj and 'productId' in obj:
     catalogs.setdefault(seq,[])
     if obj['productId']!=identity.get('publisher_product_id'):add(obj['productName'],None,'separate_publisher_product',evidence,obj)
    label=obj.get('name') or obj.get('label') or obj.get('display_heading')
    url=obj.get('url') or obj.get('route') or obj.get('base') or obj.get('source_url')
    if label:
     note=str(obj.get('relationship',obj.get('scope','')))
     if 'node_id' in obj or ('id' in obj and 'heading' in obj):relation='embedded_primary'
     elif re.search('within same|embedded|same code|same publication',note,re.I):relation='embedded_primary'
     else:relation='separate_or_unresolved'
     if url and clean_url(url)==u:relation='embedded_primary'
     if url and 'ecode360.com' in url and family=='ecode' and subtype(u)=='ecode360':relation='embedded_primary'
     if url and 'codepublishing.com' in url and subtype(u)=='CodePublishing':relation='embedded_primary'
     if url and '/latest/overview' in url and family=='american-legal' and re.search('bounded|one publisher|same code',note,re.I) and not re.search('independent|separate',note,re.I):relation='embedded_primary'
     add(label,url,relation,evidence,obj)
    if 'heading' in obj and 'id' in obj and re.search(r'charter|zoning|development code|unified development|appendi',obj['heading'],re.I):add(obj['heading'],u+'?nodeId='+quote(str(obj['id'])),'embedded_primary',evidence,{'node_id':obj['id']})
    for key,val in obj.items():
     if key in ['families','linked_families','publisher_publications','all_publisher_publications','top_level_inventory','publisher_top_level_nodes','primary_full_toc_top_level_families','family_headings_within_primary_toc','additional_official_routes']:
      if isinstance(val,list) and all(isinstance(x,str) for x in val):
       for text in val:add(text,None,'unresolved',evidence)
      else:walk(val,evidence,key)
  for item,evidence in ledger[seq]:walk(item,evidence)
  for cat in catalogs.get(seq,[]):
   if cat.get('productId')!=identity.get('publisher_product_id'):add(cat['productName'],None,'separate_publisher_product',identity.get('evidence_path'),cat)
  for book in observed_al_codes:
   if book['slug']!=primary['selector'].get('publication'):
    route='/'.join(u.split('/')[:6])+'/'+book['slug'];add(book['title'],route,'separate_publisher_publication',al_evidence,{'publication_selector':book['slug'],'publisher_code_uuid':book['uuid']})
  if seq==37:add('Comprehensive Zoning Ordinance','https://czo.nola.gov/print-all/','separate_publication','packages/expanded57-validation-2026-10-17/municode-major/native/new-orleans-czo/source.html.receipt.json')
  if seq==29:add('Miami21 current official CodeHUB','https://codehub.gridics.com/us/fl/miami','separate_publication','packages/expanded57-validation-2026-10-17/municode-major/code-families.json')
  if seq==35:
   for label,path in [('Unified Development Ordinance','UDO'),('Charter','Charter')]:add(label,'https://aurora.municipal.codes/'+path,'separate_publication','packages/expanded57-validation-2026-10-17/municode-major/aurora-current/publication-inventory.json')
  if seq==99:add('Legacy posted chapter PDF set; not the current 80-document portal','https://www.arlingtonva.us/Government/Departments/County-Board/County-Code','historical_alternative','collectors/official/configs/arlington-va-posted-chapters.json')
  concrete={18:['portland-zoning-pdfs'],20:['baltimore-charter'],21:['milwaukee-volume2'],80:['worcester-publications']}
  for key in concrete.get(seq,[]):
   config_path='collectors/official/configs/'+key+'.json';cfg=load(ROOT/config_path);add(cfg['publication'],cfg['source_url'],'separately_configured_publication',config_path,{'adapter_config_path':config_path,'covered_by_primary':key=='milwaukee-volume2'})
  if seq==100:add('Fairfax County Zoning Ordinance','https://online.encodeplus.com/regs/fairfaxcounty-va/','separate_publication','collectors/encodeplus/targets.json')
  # Retain pending-law scope as unresolved; never close a government by collecting one book.
  known.append({'label':'Uncodified enactments, separately incorporated standards and yet-undiscovered current families','relationship':'unresolved_required_scope','source_url':None,'runnable':False,'unsupported_reason':'Prior inventories are bounded/nonexhaustive; publication text closure cannot establish all current jurisdiction law.','required_for_jurisdiction':True,'full_live_verified':False})
  targets.append({'id':str(seq),'sequence':seq,'jurisdiction':r['jurisdiction'],'state':r['state'],'entity_type':a.get('entity_type',d.get('entity_type','City')),'boundary_note':a.get('boundary_note',d.get('boundary_note','')),'publisher':family,'source_family':subtype(u),'source_url':u,'primary_publication_id':primary_id,'primary_publication':primary,'expected_identity':identity,'adapter_config':{},'known_publications':known,'required_publication_ids':list(dict.fromkeys([primary_id]+[x['publication_id'] for x in known if x.get('publication_id') and x['required_for_jurisdiction']])),'jurisdiction_inventory_complete':False,'jurisdiction_complete':False,'validation_level':'mapped_only','full_live_verified':False,'prior_validation':{'kind':'bounded_sample_only','sample_status':r['sample_status'],'complete_corpus':False,'evidence_path':r['working_directory']+'/results.json','limitations':r['limitations']},'runnable':True,'unsupported_reason':None})
 # Exact source-corroborated eCode customer identity, not numeric sample subtree scope.
 ep=ROOT/'packages/wave3-validation-2026-10-17/icc-ecode/publication-inventory.json'
 for row in load(ep):
  if row.get('identity'):
   target=next(x for x in targets if norm(row['job'])==norm(x['jurisdiction']) or norm(row['job']) in norm(x['jurisdiction']));target['expected_identity'].update(row['identity']);target['primary_publication']['expected_identity'].update(row['identity'])
 for seq,customer in [(38,'NE4043'),(39,'AN6998')]:next(t for t in targets if t['sequence']==seq)['expected_identity']['customer_id']=customer
 for target in targets:
  if target['source_family']=='ecode360':
   old=target['source_url'];root='https://ecode360.com/'+target['expected_identity']['customer_id'];target['source_url']=root;target['primary_publication'].update(source_url=root,selector={'publication_url':root});target['source_route_correction']={'prior_bounded_url':old,'reason':'Numeric chapter/sample URL replaced by observed customer identity alias for whole current publication; adapter owner confirmed scope semantics.'}
 # One runnable publication per exact source+selector/config scope. Retain label aliases
 # in the family ledger without counting Aurora's two observed labels as four books.
 canonical={};redirect={}
 for p in list(pubs.values()):
  if p['role']!='secondary':continue
  key=(p['target_id'],p['publisher'],p['source_url'].rstrip('/'),json.dumps(p.get('selector',{}),sort_keys=True),p.get('adapter_config_path'))
  if key in canonical:
   old=pubs[canonical[key]];old.setdefault('observed_label_aliases',[]).append(p['title']);old['evidence_paths']=list(dict.fromkeys(old['evidence_paths']+p['evidence_paths']));redirect[p['id']]=old['id'];del pubs[p['id']]
  else:canonical[key]=p['id']
 for target in targets:
  for known in target['known_publications']:
   if known.get('publication_id') in redirect:known['publication_id']=redirect[known['publication_id']]
  target['required_publication_ids']=list(dict.fromkeys(redirect.get(x,x) for x in target['required_publication_ids']))
 from dispatch import qualified,Unsupported
 bytarget={t['id']:t for t in targets}
 for pub in pubs.values():
  pub['image_policy']={'mode':'literal_placeholder','placeholder':'[IMAGE]','download_images':False,'source_id_heading_retained':True,'native_originals_may_contain_images':True,'scope_note':'Image-only units are retained. Intentional image omission is not an unresolved required nonimage attachment.'}
  try:
   q=qualified(pub,bytarget[pub['target_id']]);pub['runnable']=True;pub['unsupported_reason']=None;pub['qualified_config_path']=q.get('config_path');pub['adapter_config_key']=q.get('target_key')
   if q.get('config') and q['publisher'] in ['official','encodeplus']:
    cfg=q['config'];pub['title']=cfg.get('publication',cfg.get('identity',pub['title']));pub['observed_title']=pub['title'];pub['dispatch_config']=cfg
    if pub['role']=='primary' and cfg.get('source_url'):pub['source_url']=cfg['source_url'];bytarget[pub['target_id']]['source_url']=cfg['source_url']
    if cfg.get('mode') in ['pdf_set','portland_titles']:pub['scope_kind']='publication_document_set'
  except Unsupported as ex:pub.update(runnable=False,unsupported_reason=str(ex))
 for target in targets:
  primary=pubs[target['primary_publication_id']];target['runnable']=primary['runnable'];target['unsupported_reason']=primary['unsupported_reason']
  target['image_policy']=primary['image_policy']
  for known in target['known_publications']:
   if known.get('publication_id') in pubs:
    pub=pubs[known['publication_id']];known.update(runnable=pub['runnable'],unsupported_reason=pub['unsupported_reason'])
 blob={'schema_version':1,'purpose':'Runnable full-publication plans; historical bounded passes are not full validation','targets':targets}
 (OUT/'targets.json').write_text(json.dumps(blob,indent=2,ensure_ascii=False)+'\n');(OUT/'publications.json').write_text(json.dumps({'schema_version':1,'publications':list(pubs.values())},indent=2,ensure_ascii=False)+'\n')
 # Compact raw identity/inventory evidence makes a relocated collectors-only audit
 # independent of access to original multi-gigabyte validation packages.
 source_paths={p['expected_identity'].get('evidence_path') for p in pubs.values()}|{e for p in pubs.values() for e in p['evidence_paths']}|{'expanded-scope-index.json'};source_paths.discard(None);manifest=[]
 with zipfile.ZipFile(OUT/'source-evidence.zip','w',zipfile.ZIP_DEFLATED) as archive:
  for path in sorted(source_paths):
   data=(ROOT/path).read_bytes();info=zipfile.ZipInfo(path,date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;archive.writestr(info,data);manifest.append({'path':path,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
 (OUT/'source-evidence-manifest.json').write_text(json.dumps({'schema_version':1,'archive_sha256':hashlib.sha256((OUT/'source-evidence.zip').read_bytes()).hexdigest(),'files':manifest},indent=2)+'\n')
 print(json.dumps({'targets':len(targets),'adapters':{k:sum(x['publisher']==k for x in targets) for k in sorted({x['publisher'] for x in targets})},'publication_candidates':len(pubs),'municode_missing_primary_product_id':[x['id'] for x in targets if x['publisher']=='municode' and not x['primary_publication'].get('publisher_product_id')]}))
if __name__=='__main__':main()
