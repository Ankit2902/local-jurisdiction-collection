#!/usr/bin/env python3
"""Bounded acquisition and fail-closed replay for Municipal.codes. No database writes."""
from __future__ import annotations
import argparse, copy, csv, datetime, hashlib, json, re, sys, time
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit, unquote
import requests
from bs4 import BeautifulSoup, Tag, NavigableString

VERSION = 'municipal-codes-validation-1.2'
FIELDS = 'jurisdiction code_name division title subtitle chapter subchapter article part subpart section_number section_name citation full_text source_url scrape_date'.split()
ROUTES = {
 'berkeley-ca': ('Berkeley','https://berkeley.municipal.codes/','https://berkeley.municipal.codes/BMC'),
 'petaluma-ca': ('Petaluma','https://petaluma.municipal.codes/Code','https://petaluma.municipal.codes/Code'),
 'sonoma-ca': ('Sonoma','https://sonoma.municipal.codes/SMC','https://sonoma.municipal.codes/SMC'),
 'bellingham-wa': ('Bellingham','https://bellingham.municipal.codes/BMC/contents','https://bellingham.municipal.codes/BMC'),
 'everett-wa': ('Everett','https://everett.municipal.codes/EMC/contents','https://everett.municipal.codes/EMC')}
class QualificationError(ValueError): pass

def sha(b): return hashlib.sha256(b).hexdigest()
def canonical(v): return json.dumps(v, sort_keys=True, ensure_ascii=False, separators=(',',':')).encode()
def write_json(p,v): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def read_json(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def jsonl(p,rows): p.write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rows),encoding='utf-8')
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def allowed(url, base):
    u,b=urlsplit(url),urlsplit(base)
    path=unquote(u.path).rstrip('/'); prefix=unquote(b.path).rstrip('/')
    if u.scheme!='https' or u.netloc.lower()!=b.netloc.lower() or u.query or u.username: return False
    if any(x in {'.','..'} for x in path.split('/')) or '//' in path: return False
    return path==prefix or path.startswith(prefix+'/')
def publication_base(url):
    u=urlsplit(url);p=u.path.rstrip('/')
    if p.endswith('/contents'):p=p[:-9]
    if not p: raise QualificationError('Publication base must be observed independently of host root')
    return urlunsplit((u.scheme,u.netloc,p,'',''))
def challenge(html):
    s=BeautifulSoup(html,'html.parser'); title=s.title.get_text(' ',strip=True) if s.title else ''
    return bool(re.search('just a moment|attention required|access denied|verify.*human',title,re.I) or s.select_one('#challenge-form, #cf-challenge-running, #cf-error-details') or 'window._cf_chl_opt' in html)
def soup_ok(html):
    if '<html' in html.lower() and '</html>' not in html.lower():raise QualificationError('Truncated full-document snapshot; closing html missing')
    if challenge(html):raise QualificationError('Access challenge/error document; no legal content accepted')
    s=BeautifulSoup(html,'html.parser')
    if not s.select_one('main'):raise QualificationError('No main legal/discovery container; shell rejected')
    return s

def acquire(url, out, base=None, retries=1):
    """One URL only. Persist every response; no TLS weakening/challenge bypass."""
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    if base and not allowed(url,base):raise QualificationError('URL outside observed publication boundary')
    session=requests.Session(); redirects=[]; current=url
    for hop in range(6):
        for attempt in range(retries+1):
            r=session.get(current,timeout=30,allow_redirects=False)
            artifact=out/('response-%02d-%02d.html'%(hop,attempt));artifact.write_bytes(r.content)
            receipt={'requested_url':url,'response_url':r.url,'http_status':r.status_code,'retrieved_at':now(),'headers':dict(r.headers),'raw_artifact_path':artifact.name,'sha256':sha(r.content),'redirects':list(redirects)}
            write_json(artifact.with_suffix('.json'),receipt)
            if r.status_code in (429,503) and attempt<retries:
                time.sleep(min(5,2**attempt));continue
            break
        if r.is_redirect:
            target=urljoin(current,r.headers['Location'])
            if urlsplit(target).scheme!='https' or (base and not allowed(target,base)) or (not base and urlsplit(target).netloc!=urlsplit(url).netloc):
                raise QualificationError('Redirect leaves approved host/publication; recorded but not followed')
            redirects.append({'url':current,'status':r.status_code,'location':target});current=target;continue
        receipt['accepted']=r.status_code==200 and not challenge(r.text)
        if receipt['accepted']:
            try:soup_ok(r.text)
            except QualificationError:receipt['accepted']=False
        receipt['reason']=None if receipt['accepted'] else 'HTTP error or access challenge'
        write_json(out/'receipt.json',receipt)
        if not receipt['accepted']:raise QualificationError(receipt['reason'])
        soup_ok(r.text)
        return receipt
    raise QualificationError('Redirect limit exceeded')

def clean(node,remove_header=False):
    node=copy.deepcopy(node)
    for x in node.select('script,nav,button,input,select,textarea,.actions,.selection-control,.levelnodeactions,.track-indicator,.toc,.tocHeading'):x.decompose()
    if remove_header:
        for h in node.find_all(['header','h1','h2','h3','h4','h5','h6'],recursive=False):h.decompose()
    return node

def semantic(node):
    """Single recursive traversal. Tables/lists retained as HTML with spans/numbering."""
    if isinstance(node,NavigableString):return str(node)
    if not isinstance(node,Tag):return ''
    if node.name=='img':return '[IMAGE]'+(' '+node.get('alt') if node.get('alt') else '')
    if node.name=='br':return '\n'
    if node.name in ('table','ul','ol'):
        c=copy.deepcopy(node)
        for im in c.select('img'):im.replace_with('[IMAGE]'+(' '+im.get('alt') if im.get('alt') else ''))
        return '\n'+str(c)+'\n'
    v=''.join(semantic(c) for c in node.children)
    if node.name in ('sup','sub'):return '<'+node.name+'>'+v+'</'+node.name+'>'
    if node.name in ('p','div','section','article','blockquote','header','h1','h2','h3','h4','h5','h6','pre'):return '\n'+v.strip()+'\n'
    return v

def text(node):return re.sub(r'\n[ \t]*\n+', '\n\n', semantic(node)).strip()
def node_identity(node,page_url,base):
    history=node.get('data-history','')
    if history:
        if not history.endswith('/history'):raise QualificationError('Unexpected data-history format')
        canonical_url=urljoin(page_url,history[:-8])
        if not allowed(canonical_url,base):raise QualificationError('Card identity points outside publication')
    else:
        header=node.select_one('header[data-share]')
        share=header.get('data-share','') if header else ''
        canonical_url=urljoin(page_url,share[:-6]) if share.endswith('/share') else ''
        if canonical_url and not allowed(canonical_url,base):raise QualificationError('Container identity outside publication')
    identity=node.get('data-node-id') or node.get('data-id') or node.get('id')
    if identity:
        node_id='dom:'+str(identity)
        loc={'kind':'html-id' if node.get('id') else 'attribute','attribute':'id' if node.get('id') else ('data-node-id' if node.get('data-node-id') else 'data-id'),'value':identity}
    elif canonical_url:node_id='url:'+canonical_url;loc={'kind':'data-history','value':history}
    else:raise QualificationError('Card lacks observed stable identity; citation-only identity forbidden')
    return node_id,canonical_url or (page_url.split('#')[0]+'#'+str(identity) if node.get('id') else page_url),loc

def parse_page(html,page_url,base):
    s=soup_ok(html); main=s.select_one('main'); records=[];notes=[]
    articles=main.select('article')
    for card in articles:
        kinds=[x[5:] for x in card.get('class',[]) if x.startswith('type-')]
        if not kinds:continue
        kind=kinds[0]
        if kind not in ('Section','Chapter','Title','Article','Part','Subtitle','Subchapter','Appendix','AppendixSection','BackAppendices','Division'):
            notes.append({'status':'unresolved','reason':'Unknown article type '+kind});continue
        try: node_id,url,locator=node_identity(card,page_url,base)
        except QualificationError as e:notes.append({'status':'unresolved','reason':str(e)});continue
        own=copy.deepcopy(card)
        for child in own.select('article'):child.decompose()
        own=clean(own)
        heading=own.select_one('header') or own.find(re.compile('^h[1-6]$'))
        num=own.select_one('header .num');name=own.select_one('header .name')
        number=num.get_text(' ',strip=True) if num else card.get('data-short-cite','').strip()
        label=heading.get_text(' ',strip=True) if heading else ''
        name_text=name.get_text(' ',strip=True) if name else label
        if number and not name and name_text.startswith(number):name_text=name_text[len(number):].strip()
        body=clean(own,True)
        # Nested headings are retained; only the card's own heading is excluded above.
        if heading and heading.name!='header':
            own_heading=body.find(re.compile('^h[1-6]$'))
            if own_heading and own_heading.get_text(' ',strip=True)==label:own_heading.decompose()
        body_text=text(body)
        if not body_text:
            notes.append({'node_id':node_id,'status':'structural' if kind!='Section' else 'unresolved','reason':'No independent body'});continue
        if kind!='Section' and not heading:
            notes.append({'node_id':node_id,'status':'unresolved','reason':'Substantive container lacks own heading'});continue
        citation=label or ' '.join(x for x in (number,name_text) if x)
        records.append({'node_id':node_id,'source_url':url,'locator':locator,'node_kind':kind.lower(),'section_number':number if kind=='Section' else '', 'section_name':name_text,'citation':citation,'full_text':(citation+'\n\n'+body_text).strip(),'content_html':str(own),'body_sha256':sha(canonical({'citation':citation,'body':body_text}))})
    if not records and not notes:
        notes.append({'status':'structural' if main.select_one('a[href]') else 'unresolved','reason':'Contents/navigation emits no provision; unprofiled main text requires source review'})
    return records,notes

def inventory(html,page_url,base,selector):
    s=soup_ok(html);roots=s.select(selector)
    if len(roots)!=1:raise QualificationError('Inventory selector must select exactly one independently captured TOC')
    toc=roots[0];nodes=[];seen=set()
    for a in toc.select('a[href]'):
        u=urljoin(page_url,a['href']);u=u.split('#')[0]
        if not allowed(u,base) or u.rstrip('/') in (base.rstrip('/'),base.rstrip('/')+'/contents'):continue
        if u in seen:continue
        seen.add(u);parent=None
        li=a.find_parent('li')
        if li:
            parent_li=li.find_parent('li')
            if parent_li:
                pa=parent_li.find('a',href=True,recursive=False) or parent_li.select_one('a[href]')
                if pa:parent=urljoin(page_url,pa['href']).split('#')[0]
        nodes.append({'node_id':'url:'+u,'parent_node_id':'url:'+parent if parent else None,'source_order':len(nodes),'source_url':u,'display_heading':a.get_text(' ',strip=True),'node_kind':next(({'level2':'title','level4':'chapter','level6':'section'}[x] for x in (li.get('class',[]) if li else []) if x in ('level2','level4','level6')),'unclassified'),'display_number':(a.select_one('.num').get_text(' ',strip=True) if a.select_one('.num') else ''),'locator':{'kind':'href','value':a['href']}})
    pending=len(toc.select('[aria-expanded="false"], [data-lazy], button'))
    return {'publication_base':base,'source_url':page_url,'source_sha256':sha(html.encode()),'nodes':nodes,'pending_controls':pending,'completeness':'unverified','warning':'One DOM cannot prove full publication inventory. Retain expanded tree, discovery families and start/end comparison; classify nodes before full run.'}

def binding(manifest):
    immutable={k:v for k,v in manifest.items() if k not in ('snapshots','retrieved_at')}
    immutable['parser_sha256']=sha(Path(__file__).read_bytes());immutable['snapshots']=[{'source_url':s['source_url'],'sha256':s['sha256']} for s in manifest['snapshots']]
    return sha(canonical(immutable))
def inventory_matches_record(node,record):
    if node['node_id']==record['node_id'] or node['source_url']==record['source_url']:return True
    # Publisher HTML exports may strip data-history while retaining a real HTML id.
    # Match only the fetched selected-section URL + its observed id anchor when
    # that exact id is also the final route component in independent inventory.
    u=urlsplit(record['source_url']);identity=record['node_id'][4:] if record['node_id'].startswith('dom:') else None
    return bool(identity and record['locator'].get('kind')=='html-id' and u.fragment==identity and urlunsplit((u.scheme,u.netloc,u.path,u.query,''))==node['source_url'] and unquote(u.path.rsplit('/',1)[-1])==identity)

def replay(manifest_path,out,stop_after=None):
    manifest_path=Path(manifest_path);m=read_json(manifest_path);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    required=('jurisdiction_slug','jurisdiction','publication_id','publication_title','publication_base','source_version','inventory','snapshots')
    for k in required:
        if not m.get(k):raise QualificationError('Manifest requires '+k)
    if m['publication_base']!=publication_base(m['publication_base']):raise QualificationError('Bad publication base')
    inv=read_json(manifest_path.parent/m['inventory']['path'])
    if sha(canonical(inv))!=m['inventory']['sha256']:raise QualificationError('Inventory hash mismatch')
    if m['inventory'].get('raw_path') and sha((manifest_path.parent/m['inventory']['raw_path']).read_bytes())!=m['inventory'].get('raw_sha256'):raise QualificationError('Inventory raw hash mismatch')
    if inv['publication_base']!=m['publication_base']:raise QualificationError('Inventory publication mismatch')
    ids=[n['node_id'] for n in inv['nodes']]
    if len(ids)!=len(set(ids)):raise QualificationError('Duplicate inventory node identity')
    key=binding(m);cp=out/'checkpoint.json'
    state=read_json(cp) if cp.exists() else {'binding':key,'next_index':0,'records':[],'notes':[],'sources':{}}
    if state['binding']!=key:raise QualificationError('Checkpoint version/parser/config/inventory mismatch')
    # Validate ALL snapshots on every replay, including previously processed artifacts.
    for snap in m['snapshots']:
        if not allowed(snap['source_url'],m['publication_base']):raise QualificationError('Snapshot outside publication')
        if sha((manifest_path.parent/snap['path']).read_bytes())!=snap['sha256']:raise QualificationError('Snapshot hash mismatch')
    count=0
    for i in range(state['next_index'],len(m['snapshots'])):
        snap=m['snapshots'][i];raw=(manifest_path.parent/snap['path']).read_bytes()
        rows,notes=parse_page(raw.decode('utf-8-sig'),snap['source_url'],m['publication_base'])
        indexed={r['node_id']:r for r in state['records']}
        for r in rows:
            old=indexed.get(r['node_id'])
            if old and old['body_sha256']!=r['body_sha256']:raise QualificationError('Conflicting bodies for stable node '+r['node_id'])
            if not old:state['records'].append(r);indexed[r['node_id']]=r
            # Every repeated acquisition remains in raw-to-record lineage.
            state['sources'].setdefault(r['node_id'],[]).append({'raw_artifact_path':snap['path'],'raw_sha256':snap['sha256'],'source_url':snap['source_url'],'locator':r['locator']})
        state['notes'].extend(notes);state['next_index']=i+1;write_json(cp,state);count+=1
        if stop_after and count>=stop_after:return {'status':'interrupted','next_index':i+1}
    rows=[];provenance=[];dispositions=[];exceptions=[];matched=set()
    order={n['node_id']:n['source_order'] for n in inv['nodes']}
    def matched_node(r):
        candidates=[n for n in inv['nodes'] if inventory_matches_record(n,r)]
        if len(candidates)!=1:return None
        return candidates[0]
    for r in state['records']:
        n=matched_node(r)
        if n is None:exceptions.append({'status':'unresolved','node_id':r['node_id'],'reason':'Parsed body absent/ambiguous in independent inventory'});continue
        if n['node_id'] in matched:raise QualificationError('Multiple identities resolve to one inventory node')
        matched.add(n['node_id']);record_id=sha(canonical([m['jurisdiction_slug'],m['publication_id'],r['node_id']]))
        row={k:'' for k in FIELDS};row.update(jurisdiction=m['jurisdiction'],code_name=m['publication_title'],section_number=r['section_number'],section_name=r['section_name'],citation=r['citation'],full_text=r['full_text'],source_url=r['source_url'],scrape_date=m.get('retrieved_at',''))
        for k in 'division title subtitle chapter subchapter article part subpart'.split():row[k]=n.get(k,'')
        rows.append((order[n['node_id']],row));provenance.append({'record_id':record_id,'node_id':n['node_id'],'publisher_node_id':r['node_id'],'source_version':m['source_version'],'extraction_version':VERSION,'sources':state['sources'][r['node_id']],'content_html':r['content_html']})
        dispositions.append({'node_id':n['node_id'],'disposition':'included','record_ids':[record_id]})
    for n in inv['nodes']:
        if n['node_id'] in matched:continue
        d=n.get('disposition')
        if d in ('structural','editorial_reference','excluded_by_scope','reserved_or_repealed') and n.get('evidence'):
            dispositions.append({'node_id':n['node_id'],'disposition':d,'evidence':n['evidence'],'record_ids':[]})
        else:dispositions.append({'node_id':n['node_id'],'disposition':'unresolved','reason':'No acquired independent body or reviewed structural/scope evidence','record_ids':[]})
    exceptions.extend(n for n in state['notes'] if n.get('status')=='unresolved')
    rows=[r for _,r in sorted(rows,key=lambda x:x[0])]
    metadata={'status':'incomplete_source_validation','source_version':m['source_version'],'inventory_completeness':inv.get('completeness','unverified'),'whole_corpus_validated':False,'binding':key,'record_count':len(rows)}
    pub=out/'publications'/m['publication_id'];pub.mkdir(parents=True,exist_ok=True)
    for folder,stem in ((pub,'fulltext'),(out,'aggregate-fulltext')):
        write_json(folder/(stem+'.json'),{'metadata':metadata,'provisions':rows})
        with (folder/(stem+'.csv')).open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
    tocrows=[dict(r,full_text='') for r in rows]
    for folder,stem in ((pub,'toc'),(out,'aggregate-toc')):
        write_json(folder/(stem+'.json'),{'metadata':metadata,'provisions':tocrows})
        with (folder/(stem+'.csv')).open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(tocrows)
    jsonl(out/'source-nodes.jsonl',inv['nodes']);jsonl(out/'node-dispositions.jsonl',dispositions);jsonl(out/'record-provenance.jsonl',provenance);jsonl(out/'exceptions.jsonl',exceptions)
    write_json(out/'publications.json',m.get('discovered_publications') or [{k:m[k] for k in ('publication_id','publication_title','publication_base','source_version')}])
    write_json(out/'validation-report.json',dict(metadata,inventory_nodes=len(ids),unresolved_dispositions=sum(d['disposition']=='unresolved' for d in dispositions),exceptions=len(exceptions),parser_scope='bounded cached replay; independent full-tree/source version qualification required'))
    # Deliver portable immutable raw snapshots inside output, rewriting sidecar paths.
    rawdir=out/'raw';rawdir.mkdir(exist_ok=True)
    write_json(rawdir/'inventory.json',inv)
    if m['inventory'].get('raw_path'):(rawdir/'inventory-source.html').write_bytes((manifest_path.parent/m['inventory']['raw_path']).read_bytes())
    for snap in m['snapshots']:(rawdir/(snap['sha256']+'.html')).write_bytes((manifest_path.parent/snap['path']).read_bytes())
    for p in provenance:
        for source in p['sources']:source['raw_artifact_path']='raw/'+source['raw_sha256']+'.html'
    jsonl(out/'record-provenance.jsonl',provenance)
    write_json(out/'run-manifest.json',dict(metadata,jurisdiction_slug=m['jurisdiction_slug'],parser_version=VERSION,scope='source-validation-only',artifact_hashes={str(p.relative_to(out)):sha(p.read_bytes()) for p in out.rglob('*') if p.is_file() and p.name not in ('run-manifest.json','checkpoint.json')}))
    return metadata

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('routes');a.add_argument('--out',required=True)
    a=sub.add_parser('acquire');a.add_argument('--slug',choices=ROUTES,required=True);a.add_argument('--url');a.add_argument('--out',required=True);a.add_argument('--discovery',action='store_true')
    a=sub.add_parser('inventory');a.add_argument('--html',required=True);a.add_argument('--url',required=True);a.add_argument('--base',required=True);a.add_argument('--selector',required=True);a.add_argument('--out',required=True)
    a=sub.add_parser('replay');a.add_argument('--manifest',required=True);a.add_argument('--out',required=True);a.add_argument('--stop-after',type=int)
    args=p.parse_args()
    try:
        if args.command=='routes':write_json(Path(args.out),{s:{'jurisdiction':r[0],'discovery_url':r[1],'publication_base':r[2],'route_currently_confirmed':False} for s,r in ROUTES.items()})
        elif args.command=='acquire':
            r=ROUTES[args.slug];print(json.dumps(acquire(args.url or r[1],args.out,None if args.discovery else r[2]),indent=2))
        elif args.command=='inventory':write_json(Path(args.out),inventory(Path(args.html).read_text(encoding='utf-8-sig'),args.url,publication_base(args.base),args.selector))
        elif args.command=='replay':print(json.dumps(replay(args.manifest,args.out,args.stop_after),indent=2))
    except (QualificationError,requests.RequestException,UnicodeError) as e:print('BLOCKED: '+str(e),file=sys.stderr);return 2
    return 0
if __name__=='__main__':sys.exit(main())
