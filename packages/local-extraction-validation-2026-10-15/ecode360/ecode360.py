#!/usr/bin/env python3
"""Portable, fail-closed eCode360 acquisition and deterministic snapshot replay.

A TOC observed in an HTML page is only an inventory candidate. The independent
inventory must be reviewed, frozen and supplied explicitly for replay/collection.
No private APIs, fingerprint changes, challenges or security bypasses are used.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import html as html_lib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit
import requests
from bs4 import BeautifulSoup, NavigableString, Tag

VERSION = 'ecode360-handoff-1.0.0'
FIELDS = 'jurisdiction code_name division title subtitle chapter subchapter article part subpart section_number section_name citation full_text source_url scrape_date'.split()
TITLE_SELECTOR = '.contentTitle[data-code-content-type][data-guid]'
DISPOSITIONS = {'structural','reserved_or_repealed','editorial_reference','excluded_by_scope'}

class ValidationError(ValueError):
    pass

def now():
    return datetime.now(timezone.utc).isoformat()

def digest(data):
    return hashlib.sha256(data).hexdigest()

def canonical_json(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')

def dump(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def jsonl(path, rows):
    Path(path).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')

def text(node):
    return ' '.join(node.get_text(' ', strip=True).split()) if node else ''

def fetch_url(url):
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or parsed.hostname != 'ecode360.com' or parsed.port or parsed.username or parsed.password or parsed.query:
        raise ValidationError('unsupported or unsafe publisher URL: ' + url)
    if not re.fullmatch(r'/(?:\d+|[A-Z]{2}\d{4})/?', parsed.path):
        raise ValidationError('not an observed eCode360 code route: ' + url)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path.rstrip('/'), '', ''))

def safe_path(base, relative):
    p = (Path(base) / relative).resolve()
    if not p.is_relative_to(Path(base).resolve()):
        raise ValidationError('artifact path escapes package')
    return p

def reject_shell(soup):
    title = text(soup.title).lower()
    if any(x in title for x in ('just a moment','access denied','attention required','page not found','sign in','log in')):
        raise ValidationError('challenge/error/login page: ' + title)
    if soup.select_one('#challenge-running, #cf-challenge-running, .cf-error-details, #challenge-form'):
        raise ValidationError('challenge/error page')

def page_identity(soup):
    reject_shell(soup)
    b = soup.body
    if not b:
        raise ValidationError('missing publisher body identity')
    required = ('data-cust-id','data-code-id','data-code-date')
    if any(not b.get(k) for k in required):
        raise ValidationError('missing publisher customer/code/date version identity')
    return {'customer_id': b['data-cust-id'], 'code_id': b['data-code-id'], 'currency_raw': b['data-code-date']}

def node_key(jurisdiction, publication, node):
    return jurisdiction + ':' + publication + ':' + str(node)

def _html_semantics(node, base_url, images):
    """Whitelist semantic HTML, retaining table geometry and all inline text."""
    if isinstance(node, NavigableString):
        return html_lib.escape(str(node))
    if not isinstance(node, Tag) or node.name in {'script','style','button','input','svg','noscript'}:
        return ''
    if node.name == 'img':
        images.append({'order':len(images)+1, 'url':urljoin(base_url,node.get('src','')), 'alt':node.get('alt','')})
        return '[IMAGE]' + (' ' + html_lib.escape(node['alt']) if node.get('alt') else '')
    contents = ''.join(_html_semantics(c, base_url, images) for c in node.children)
    allowed = {'table','caption','thead','tbody','tfoot','tr','td','th','ol','ul','li','p','blockquote','sup','sub','em','strong','b','i','br','a','dl','dt','dd','div','section','dfn'}
    if node.name not in allowed:
        return contents
    attrs = ''
    if node.name in {'div','section'} and node.get('class'):
        attrs += ' class="' + html_lib.escape(' '.join(node['class']),quote=True) + '"'
    if node.name in {'td','th'}:
        for name in ('rowspan','colspan','scope','headers'):
            if node.get(name): attrs += ' ' + name + '="' + html_lib.escape(node[name],quote=True) + '"'
    if node.name in {'ol','li'}:
        for name in ('start','type','value'):
            if node.get(name): attrs += ' ' + name + '="' + html_lib.escape(node[name],quote=True) + '"'
    if node.name == 'a' and node.get('href'):
        attrs += ' href="' + html_lib.escape(urljoin(base_url,node['href']),quote=True) + '"'
    return '<' + node.name + attrs + '>' + contents + ('' if node.name == 'br' else '</' + node.name + '>')

def serialize(node, base_url):
    images = []
    def walk(n, depth=0):
        if isinstance(n, NavigableString): return re.sub(r'\s+', ' ', str(n))
        if not isinstance(n,Tag) or n.name in {'script','style','button','input','svg','noscript'}: return ''
        if n.name == 'img': return _html_semantics(n,base_url,images)
        if n.name in {'table','ol','ul'}: return '\n' + _html_semantics(n,base_url,images) + '\n'
        if n.name in {'sup','sub'}: return '<'+n.name+'>'+''.join(walk(c,depth) for c in n.children)+'</'+n.name+'>'
        if n.name == 'br': return '\n'
        cls = n.get('class',[])
        if 'litem' in cls:
            label = n.find(class_='litem_number',recursive=False)
            content = n.find(class_='litem_content',recursive=False)
            return '\n' + '  '*depth + text(label) + ' ' + (walk(content,depth+1).strip() if content else ''.join(walk(c,depth+1) for c in n.children).strip()) + '\n'
        result = ''.join(walk(c,depth) for c in n.children)
        if n.name in {'div','p','section','blockquote','dl','dt','dd','li'}: return '\n'+result.strip()+'\n'
        return result
    full_text = re.sub(r'\n[ \t]+\n','\n\n', walk(node)).strip()
    full_text = re.sub(r'\n{3,}','\n\n',full_text)
    semantic_images = []
    structured_html = _html_semantics(node,base_url,semantic_images)
    return {'full_text':full_text,'semantic_html':structured_html,'images':images}

def parse_page(html, url, expected_identity=None):
    soup = BeautifulSoup(html, 'html.parser')
    identity = page_identity(soup)
    if expected_identity and identity != expected_identity:
        raise ValidationError('publication version/customer mismatch: '+str(identity))
    canonical = soup.select_one('link[rel=canonical][href]')
    content_url = fetch_url(urljoin(url, canonical['href'])) if canonical else fetch_url(url)
    found = {}
    # Navigation headings repeat the legal headers; only actual header/body pairs emit.
    for title in soup.select('header ' + TITLE_SELECTOR):
        node_id = str(title['data-guid'])
        body = soup.find(id=node_id+'_content')
        if body is None:
            continue
        # Never borrow a neighboring section body. Nested descendant body containers
        # are removed when serializing an independent parent's own operative body.
        clone = BeautifulSoup(str(body),'html.parser')
        for nested in clone.select('.section_content .section_content, .section_content article'):
            nested.decompose()
        result = serialize(clone,content_url)
        label = title.get('data-full-title') or text(title)
        number = text(title.select_one('.titleNumber')).removeprefix('§').strip()
        name = text(title.select_one('.titleTitle'))
        if not name: name = label
        item = {'node_id':node_id,'node_kind':title['data-code-content-type'],
                'display_number':number,'display_heading':name,'citation':label,
                'source_url':'https://ecode360.com/'+node_id+'#'+node_id,
                'locator':{'kind':'html-id','value':node_id+'_content'}, **result}
        if node_id in found and found[node_id] != item:
            raise ValidationError('conflicting duplicate source node '+node_id)
        found[node_id] = item
    # Data-guid is also used by inline references; never emit them as legal nodes.
    return identity, list(found.values())

def inventory_candidate(html, url):
    soup = BeautifulSoup(html,'html.parser')
    identity = page_identity(soup)
    toc = soup.select_one('#toc')
    if not toc: raise ValidationError('no observed TOC container; no permissive link fallback')
    nodes, seen = [], set()
    for title in toc.select(TITLE_SELECTOR):
        nid = str(title['data-guid'])
        if nid in seen: continue
        seen.add(nid)
        a = title.select_one('a.titleLink[href]')
        if not a: continue
        candidate_url = urljoin(url,a['href'])
        route = fetch_url(candidate_url)
        if route.rsplit('/',1)[-1] != nid:
            # Fragment-only chapter TOCs identify child nodes canonically by GUID.
            if urlsplit(candidate_url).fragment != nid: raise ValidationError('TOC GUID/route disagree')
            route = 'https://ecode360.com/'+nid
        parent = title.get('data-parent-guid')
        if not parent:
            parent_tag = title.find_parent(attrs={'data-parent-guid':True})
            if parent_tag: parent = parent_tag['data-parent-guid']
        nodes.append({'node_id':nid,'parent_node_id':parent,'source_order':len(nodes),
            'node_kind':title['data-code-content-type'],'display_number':text(title.select_one('.titleNumber')),
            'display_heading':text(title.select_one('.titleTitle')),'source_url':route+'#'+nid,
            'classification':'unresolved','classification_evidence':'','hierarchy':{}})
    unresolved_controls = len(toc.select('[aria-expanded="false"], .collapsed, .lazy'))
    return {'schema_version':1,'identity':identity,'inventory_complete':False,
            'inventory_review':None,'toc_url':url,'toc_sha256':digest(html.encode()),
            'unexpanded_control_count':unresolved_controls,'nodes':nodes,
            'unclassified_family_candidates':[{'node_id':str(t['data-guid']),'display_heading':text(t),'source_url':urljoin(url,t.select_one('a.titleLink[href]')['href'])}
                for t in toc.select('.contentTitle[data-guid]:not([data-code-content-type])') if t.select_one('a.titleLink[href]')],
            'warning':'Candidate only; page may contain a partial/lazy tree. Scope and complete hierarchy require independent review.'}

def validate_inventory(inv):
    for k in ('jurisdiction_slug','jurisdiction','publication_id','code_name','identity','source_version','inventory_complete','nodes','inventory_evidence','scrape_date'):
        if k not in inv: raise ValidationError('inventory missing '+k)
    if not re.fullmatch(r'[a-z0-9-]+', inv['publication_id']): raise ValidationError('unsafe publication ID')
    if not inv['source_version'] or not inv['inventory_evidence']: raise ValidationError('version and independent inventory evidence required')
    if not inv['nodes']: raise ValidationError('empty inventory')
    seen=set()
    for n in inv['nodes']:
        nid=str(n['node_id'])
        if nid in seen: raise ValidationError('duplicate inventory source-node identity '+nid)
        seen.add(nid)
        if fetch_url(n['source_url']) != 'https://ecode360.com/'+nid:
            raise ValidationError('node canonical URL/GUID mismatch')
        if n['classification'] not in DISPOSITIONS | {'substantive','unresolved'}: raise ValidationError('unknown node classification')
        if n['classification'] in DISPOSITIONS and not n.get('classification_evidence'):
            raise ValidationError('non-substantive disposition requires evidence')
    for n in inv['nodes']:
        if n.get('parent_node_id') and str(n['parent_node_id']) not in seen:
            # A bounded pilot may begin below a parent. Full inventories may not.
            if inv['inventory_complete']: raise ValidationError('missing inventory parent '+str(n['parent_node_id']))
    return inv

def binding(inv, artifacts):
    return digest(canonical_json({'parser':VERSION,'parser_sha256':digest(Path(__file__).read_bytes()),'inventory':inv,'artifacts':artifacts}))

def write_exports(out, records, publication_id):
    def pair(stem, rows):
        dump(out/(stem+'.json'), {'metadata':{'parser':VERSION,'status':'validation_sample'},'provisions':rows})
        with (out/(stem+'.csv')).open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
        with (out/(stem+'.csv')).open(encoding='utf-8-sig',newline='') as f:
            if list(csv.DictReader(f)) != rows: raise ValidationError('CSV/JSON mismatch')
    pub=out/'publications'/publication_id;pub.mkdir(parents=True,exist_ok=True)
    toc=[dict(r,full_text='') for r in records]
    pair('aggregate-fulltext',records);pair('aggregate-toc',toc)
    for name, rows in [('fulltext',records),('toc',toc)]:
        dump(pub/(name+'.json'),{'metadata':{'parser':VERSION,'status':'validation_sample'},'provisions':rows})
        with (pub/(name+'.csv')).open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)

def replay(inventory_path, artifacts_path, out, *, stop_after=None, release=False):
    inv=validate_inventory(load(inventory_path));manifest=load(artifacts_path)
    base=Path(artifacts_path).parent;out=Path(out);out.mkdir(parents=True,exist_ok=True)
    artifacts=manifest['artifacts'];bound=binding(inv,manifest)
    cp=out/'checkpoint.json'
    if cp.exists() and load(cp)['binding'] != bound:
        raise ValidationError('checkpoint inventory/version/parser/artifact binding mismatch; use a new run directory')
    old=load(cp) if cp.exists() else {'binding':bound,'processed':[],'parsed':{},'origins':{},'errors':[]}
    parsed=old['parsed'];origins=old['origins'];errors=old['errors'];processed=set(old['processed'])
    allowed={str(n['node_id']) for n in inv['nodes']}
    for i,a in enumerate(artifacts):
        if i in processed: continue
        try:
            path=safe_path(base,a['path']);raw=path.read_bytes()
            if digest(raw)!=a['sha256']: raise ValidationError('artifact SHA-256 mismatch '+a['path'])
            # Strict UTF-8 avoids silent replacement corruption. Browser snapshots use UTF-8.
            identity,items=parse_page(raw.decode('utf-8'),a['url'],inv['identity'])
            for item in items:
                nid=item['node_id']
                if nid not in allowed:
                    errors.append({'artifact':a['path'],'node_id':nid,'error':'rendered node absent from independent inventory; not emitted'})
                    continue
                if nid in parsed and parsed[nid]!=item:
                    raise ValidationError('same source identity has conflicting content '+nid)
                parsed[nid]=item
                origins.setdefault(nid,[])
                origin={'artifact':a['path'],'sha256':a['sha256'],'url':a['url']}
                if origin not in origins[nid]:origins[nid].append(origin)
        except (OSError,UnicodeError,ValidationError) as exc:
            errors.append({'artifact':a['path'],'error':str(exc)})
        processed.add(i)
        dump(cp,{'binding':bound,'processed':sorted(processed),'parsed':parsed,'origins':origins,'errors':errors})
        if stop_after is not None and len(processed)>=stop_after:
            return {'status':'interrupted','processed_artifacts':len(processed),'binding':bound}
    records=[];provenance=[];dispositions=[];nodes=[]
    for n in inv['nodes']:
        nid=str(n['node_id']);key=node_key(inv['jurisdiction_slug'],inv['publication_id'],nid)
        nodes.append(dict(n,jurisdiction_slug=inv['jurisdiction_slug'],publication_id=inv['publication_id'],source_version=inv['source_version']))
        item=parsed.get(nid);classification=n['classification']
        own_body=bool(item and item['full_text'])
        if own_body and classification in {'structural','excluded_by_scope','editorial_reference'}:
            if not n.get('allow_body_exclusion',False):
                errors.append({'node_id':nid,'error':'operative body would be hidden by non-substantive disposition'})
                classification='unresolved'
        if classification in DISPOSITIONS:
            dispositions.append({'node_key':key,'node_id':nid,'disposition':classification,'evidence':n['classification_evidence'],'record_ids':[]})
            continue
        if not own_body or classification=='unresolved':
            dispositions.append({'node_key':key,'node_id':nid,'disposition':'unresolved','record_ids':[],'reason':'missing body or unresolved inventory classification'})
            continue
        rec={k:'' for k in FIELDS}
        rec.update({'jurisdiction':inv['jurisdiction'],'code_name':inv['code_name'],
                    'section_number':item['display_number'],'section_name':item['display_heading'],
                    'citation':item['citation'],'full_text':item['full_text'],'source_url':item['source_url'],'scrape_date':inv['scrape_date']})
        rec.update({k:v for k,v in n.get('hierarchy',{}).items() if k in FIELDS and k not in {'full_text','source_url','jurisdiction','code_name','scrape_date'}})
        records.append(rec);rid=digest(key.encode())
        provenance.append({'record_id':rid,'node_key':key,'node_id':nid,'publication_id':inv['publication_id'],
                           'source_version':inv['source_version'],'locator':item['locator'],'origins':origins[nid],
                           'extraction_version':VERSION,'semantic_html':item['semantic_html'],'images':item['images']})
        dispositions.append({'node_key':key,'node_id':nid,'disposition':'included','record_ids':[rid]})
    unresolved=sum(d['disposition']=='unresolved' for d in dispositions)
    report={'status':'validation_sample','inventory_complete':inv['inventory_complete'],
            'source_node_count':len(nodes),'included_record_count':len(records),'unresolved_node_count':unresolved,
            'artifact_count':len(artifacts),'errors':errors,'binding':bound,
            'full_collection_verified':False,'release_eligible':False}
    # Full collection needs end-of-run independent version/inventory comparison,
    # official routing/scope review and source-sensitive human comparisons. This
    # method-validation package deliberately cannot certify those from row counts.
    dump(out/'validation-report.json',report)
    dump(out/'publications.json',[{k:inv[k] for k in ('publication_id','code_name','identity','source_version','inventory_evidence')}])
    jsonl(out/'source-nodes.jsonl',nodes);jsonl(out/'node-dispositions.jsonl',dispositions)
    jsonl(out/'record-provenance.jsonl',provenance);jsonl(out/'exceptions.jsonl',errors)
    dump(out/'run-manifest.json',{'parser':VERSION,'binding':bound,'status':'validation_sample','inventory_sha256':digest(canonical_json(inv)),
                                 'source_version':inv['source_version'],'started_or_resumed_at':now(),'counts':report})
    if release: raise ValidationError('release refused: method validation cannot attest full inventory/version/human-review completion')
    write_exports(out,records,inv['publication_id'])
    return report

def acquire(url, out, retries=2, timeout=30):
    """One public HTTP request with bounded rate-limit/temporary-error retries."""
    url=fetch_url(url);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    events=[];raw=b'';final=url;status=None
    for attempt in range(retries+1):
        try:
            # Follow only validated publisher code redirects; requests does not
            # automatically transmit headers to a different host or login endpoint.
            current=url;chain=[]
            for _ in range(6):
                r=requests.get(current,headers={'User-Agent':'CompliSolv municipal-code method validation/1.0'},timeout=timeout,allow_redirects=False)
                chain.append({'url':current,'status':r.status_code,'location':r.headers.get('Location')})
                if r.is_redirect:
                    current=fetch_url(urljoin(current,r.headers['Location']));continue
                break
            else: raise ValidationError('redirect limit exceeded')
            raw=r.content;final=current;status=r.status_code
            events.append({'attempt':attempt+1,'time':now(),'redirect_chain':chain,'status':status,
                           'headers':{k:v for k,v in r.headers.items() if k.lower() in {'content-type','etag','last-modified','retry-after','cf-ray'}}})
            if status in {429,503} and attempt<retries:
                value=r.headers.get('Retry-After','')
                wait=min(int(value),60) if value.isdigit() else min(2**(attempt+1),30)
                time.sleep(wait);continue
            break
        except (requests.RequestException,ValidationError) as exc:
            events.append({'attempt':attempt+1,'time':now(),'error':str(exc)})
            break
    rawpath=out/(digest(raw)+'.html')
    if raw: rawpath.write_bytes(raw)
    result={'requested_url':url,'final_url':final,'http_status':status,'events':events,
            'raw_path':rawpath.name if raw else None,'raw_sha256':digest(raw) if raw else None,
            'retrieved_at':now(),'route_verified':False,'inventory_verified':False,'representative_text_verified':False,
            'full_collection_verified':False}
    if status==200:
        try:
            html=raw.decode('utf-8');ident,items=parse_page(html,final)
            result.update({'route_verified':True,'identity':ident,'representative_text_verified':any(x['full_text'] for x in items),'parsed_records':len(items)})
            try: result['inventory_candidate']=inventory_candidate(html,final)
            except ValidationError as exc: result['inventory_error']=str(exc)
        except (ValidationError,UnicodeError) as exc:result['error']=str(exc)
    else:result['error']='public request blocked or failed; retain response; supported browser/operator export required'
    dump(out/'receipt.json',result);return result

def import_snapshot(inventory_path, html_path, url, out, retrieved_at=None):
    """Register a user/operator saved browser DOM, enforcing hash/version/scope."""
    inv=validate_inventory(load(inventory_path));out=Path(out);out.mkdir(parents=True,exist_ok=True)
    permitted={fetch_url(n['source_url']) for n in inv['nodes']}
    permitted.update(fetch_url(a['url']) for a in inv.get('acquisition_units',[]) if a.get('evidence'))
    if fetch_url(url) not in permitted: raise ValidationError('snapshot URL is absent from frozen publication inventory')
    raw=Path(html_path).read_bytes();parse_page(raw.decode('utf-8'),url,inv['identity'])
    sha=digest(raw);relative='raw/'+sha+'.html';target=out/relative;target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(raw)
    manifest_path=out/'artifacts.json';manifest=load(manifest_path) if manifest_path.exists() else {'inventory_binding':digest(canonical_json(inv)),'artifacts':[]}
    if manifest['inventory_binding']!=digest(canonical_json(inv)): raise ValidationError('import inventory binding mismatch')
    entry={'path':relative,'sha256':sha,'url':fetch_url(url),'retrieved_at':retrieved_at,'transport':'operator_saved_rendered_dom'}
    if entry not in manifest['artifacts']:manifest['artifacts'].append(entry)
    dump(manifest_path,manifest);return {'status':'registered','sha256':sha,'artifacts_path':str(manifest_path),'retrieval_date_unverified':retrieved_at is None}

def collect(inventory_path,out,max_pages=1,delay=1.5):
    """Acquire only observed, explicitly inventoried units, with resumable receipts.

    This is bounded validation, never an implicit whole-publication crawler.
    Blocked units stop the queue. Retry uses a new run directory, preserving evidence.
    """
    inv=validate_inventory(load(inventory_path));out=Path(out);out.mkdir(parents=True,exist_ok=True)
    units=inv.get('acquisition_units',[])
    if not units: raise ValidationError('inventory must supply observed acquisition_units with evidence')
    if max_pages<1: raise ValidationError('max-pages must be positive')
    for u in units:
        fetch_url(u['url'])
        if not u.get('evidence'):raise ValidationError('acquisition unit lacks observed route evidence')
    statepath=out/'acquisition-checkpoint.json';bound=digest(canonical_json({'inventory':inv,'parser':VERSION,'parser_sha256':digest(Path(__file__).read_bytes())}))
    state=load(statepath) if statepath.exists() else {'binding':bound,'completed':[],'artifacts':[],'status':'in_progress'}
    if state['binding']!=bound:raise ValidationError('acquisition checkpoint version/config binding mismatch')
    if state['status']=='blocked':raise ValidationError('previous acquisition blocked; use a new run directory after route/operator review')
    completed=set(state['completed']);taken=0
    for i,unit in enumerate(units):
        if i in completed:continue
        folder=out/'requests'/str(i);receipt=acquire(unit['url'],folder)
        if not receipt['route_verified'] or receipt.get('identity')!=inv['identity']:
            state.update(status='blocked',blocking_receipt=str((folder/'receipt.json').relative_to(out)))
            dump(statepath,state);return {'status':'blocked','receipt':state['blocking_receipt'],'full_collection_verified':False}
        state['artifacts'].append({'path':str((folder/receipt['raw_path']).relative_to(out)),'sha256':receipt['raw_sha256'],'url':receipt['final_url'],'retrieved_at':receipt['retrieved_at']})
        completed.add(i);state['completed']=sorted(completed);taken+=1
        dump(statepath,state);dump(out/'artifacts.json',{'inventory_binding':bound,'artifacts':state['artifacts']})
        if taken>=max_pages:break
        time.sleep(max(0,delay))
    state['status']='bounded_acquisition_finished' if len(completed)==len(units) else 'paused_at_bound'
    dump(statepath,state)
    return {'status':state['status'],'acquired_artifacts':len(completed),'known_units':len(units),'full_collection_verified':False}

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='command',required=True)
    p=sub.add_parser('fetch');p.add_argument('url');p.add_argument('--out',required=True)
    p=sub.add_parser('probe');p.add_argument('--routes',default=str(Path(__file__).with_name('routes.json')));p.add_argument('--out',required=True);p.add_argument('--delay',type=float,default=1.5)
    p=sub.add_parser('inspect');p.add_argument('html');p.add_argument('--url',required=True);p.add_argument('--out',required=True)
    p=sub.add_parser('import-snapshot');p.add_argument('--inventory',required=True);p.add_argument('--html',required=True);p.add_argument('--url',required=True);p.add_argument('--out',required=True);p.add_argument('--retrieved-at')
    p=sub.add_parser('collect');p.add_argument('--inventory',required=True);p.add_argument('--out',required=True);p.add_argument('--max-pages',type=int,default=1);p.add_argument('--delay',type=float,default=1.5)
    p=sub.add_parser('replay');p.add_argument('--inventory',required=True);p.add_argument('--artifacts',required=True);p.add_argument('--out',required=True);p.add_argument('--stop-after',type=int);p.add_argument('--release',action='store_true')
    args=ap.parse_args(argv)
    try:
        if args.command=='fetch': result=acquire(args.url,args.out)
        elif args.command=='probe':
            routes=load(args.routes);results=[]
            for route in routes:
                results.append({'slug':route['slug'],**acquire(route['discovery_url'],Path(args.out)/route['slug'],retries=0)})
                time.sleep(max(0,args.delay))
            dump(Path(args.out)/'probe-results.json',results);result={'routes':len(results),'verified':sum(x['route_verified'] for x in results)}
        elif args.command=='collect': result=collect(args.inventory,args.out,args.max_pages,args.delay)
        elif args.command=='import-snapshot': result=import_snapshot(args.inventory,args.html,args.url,args.out,args.retrieved_at)
        elif args.command=='inspect':
            raw=Path(args.html).read_bytes();candidate=inventory_candidate(raw.decode('utf-8'),args.url)
            dump(args.out,candidate);result={'candidate_nodes':len(candidate['nodes']),'inventory_complete':False}
        else:result=replay(args.inventory,args.artifacts,args.out,stop_after=args.stop_after,release=args.release)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    except (ValidationError,OSError,KeyError) as exc:
        print(json.dumps({'status':'failed_closed','error':str(exc)}),file=sys.stderr);return 2

if __name__=='__main__':sys.exit(main())
