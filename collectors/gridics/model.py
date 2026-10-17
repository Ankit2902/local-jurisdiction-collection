"""Gridics native-tree normalization, with independent rendered DOM comparison."""
import hashlib
import datetime
import html
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlsplit, parse_qs
from bs4 import BeautifulSoup, NavigableString, Tag, Comment
from .list_markers import list_metadata, insert_markers
from .image_content import is_image_content
from .publisher import RENDERER_SHA256, ROUTER_SHA256, script_role, body_for_rendering, fragment_path


class Invalid(ValueError):
    pass


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    tmp.replace(path)


def checked(base, receipt):
    path = (Path(base) / receipt['path']).resolve()
    if not path.is_relative_to(Path(base).resolve()):
        raise Invalid('Receipt escapes output')
    raw = path.read_bytes()
    if digest(raw) != receipt['sha256'] or len(raw) != receipt['bytes']:
        raise Invalid('Receipt bytes changed: ' + receipt['path'])
    if receipt.get('status') != 200:
        raise Invalid('Source response not HTTP 200')
    if is_image_content(receipt.get('content_type',''),raw[:2048]):
        raise Invalid('Separate image receipt is forbidden')
    return raw


def plain(markup):
    # Inline tags never introduce arbitrary spaces inside words.
    soup = BeautifulSoup(markup, 'html.parser')
    insert_markers(soup)
    for cell in soup.find_all(['td','th']):
        cell.append('\t')
    for br in soup.find_all('br'):
        br.replace_with('\n')
    for node in soup.find_all(['p', 'div', 'section', 'article', 'blockquote', 'caption', 'table', 'ol', 'ul', 'dl', 'li', 'tr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'dd', 'dt']):
        # A nested list or another block can follow inline source text without
        # literal whitespace. Both boundaries are needed; inline tags still
        # never split a word (for example co<em>de</em>).
        node.insert(0,'\n')
        node.append('\n')
    return '\n'.join(' '.join(line.split()) for line in soup.get_text().splitlines() if line.strip())


def normalize(markup, base, collect_links=True):
    images, links = [], []
    source_soup=BeautifulSoup(markup,'html.parser')
    source_lists=list_metadata(source_soup)
    list_by_node={id(node):row for node,row in zip(source_soup.find_all(['ol','ul']),source_lists)}
    allowed = {'p','div','span','section','article','table','caption','thead','tbody','tfoot','tr','td','th','ol','ul','li','dl','dt','dd','blockquote','br','hr','sup','sub','em','strong','b','i','u','s','a','h1','h2','h3','h4','h5','h6'}
    def marker(node, kind):
        locator=node.get('poster') if kind == 'video_poster' else node.get('src') or node.get('data') or node.get('background') or node.get('style')
        # Omission metadata must not smuggle source image payload into normalized records.
        if locator and re.search(r'data\s*:',locator,re.I):
            locator={'embedded_data_omitted':True,'source_attribute_sha256':digest(locator.encode())}
        alt=node.get('alt')
        if alt and re.search(r'data\s*:',alt,re.I):
            alt={'embedded_data_omitted':True,'source_attribute_sha256':digest(alt.encode())}
        images.append({'order': len(images)+1, 'kind': kind, 'source_locator': locator, 'alt': alt})
        return '[IMAGE]'
    def render(node):
        if isinstance(node,Comment):
            return ''
        if isinstance(node, NavigableString):
            return html.escape(str(node))
        if not isinstance(node, Tag):
            return ''
        image_url=node.get('data') or node.get('src') or ''
        image_resource = str(node.get('type','')).strip().lower().startswith('image/') or re.search(r'(?:^data:image/|\.(?:png|jpe?g|gif|svg|webp|avif)(?:[?#]|$))',image_url,re.I)
        if node.name in {'img','svg','picture','canvas'} or (node.name in {'object','embed'} and image_resource) or (node.name == 'input' and str(node.get('type','')).lower() == 'image') or (node.name=='source' and (node.get('srcset') or image_resource)):
            return marker(node, node.name)
        if node.name=='style' and re.search(r'(?:url\s*\(|(?:repeating-)?(?:linear|radial|conic)-gradient\s*\()',node.get_text(),re.I):
            return marker(node,'stylesheet_image')
        if node.name in {'script','style','noscript','button','input','source'}:
            return ''
        css_image = node.get('background') or re.search(r'(?:url\s*\(|(?:repeating-)?(?:linear|radial|conic)-gradient\s*\()', node.get('style',''), re.I)
        contents = (marker(node, 'video_poster') if node.name == 'video' and node.get('poster') else '') + (marker(node, 'css') if css_image else '') + ''.join(render(c) for c in node.children)
        if node.name not in allowed:
            return contents
        attrs = {}
        if node.name in {'td','th'}:
            attrs = {k: node[k] for k in ('rowspan','colspan','scope','headers') if node.has_attr(k)}
        if node.name in {'ol','ul','li'}:
            attrs.update({k: node[k] for k in ('start','type','value','reversed') if node.has_attr(k) and not re.search(r'data\s*:\s*image/',str(node[k]),re.I)})
            classes=[v for v in node.get('class',[]) if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_-]*',v)]
            if classes:attrs['class']=classes
            style = re.search(r'list-style-type\s*:\s*([a-z-]+)', node.get('style',''), re.I)
            if style:
                attrs['style'] = 'list-style-type:' + style.group(1)
            if node.name in {'ol','ul'} and not list_by_node[id(node)]['marker_format_qualified']:
                attrs['data-list-marker-unqualified']='true'
        if node.get('id'):
            attrs['id'] = node['id']
        if node.name == 'a' and node.get('href'):
            url = urljoin(base, node['href'])
            if urlsplit(url).scheme in {'https','http','mailto'}:
                attrs['href'] = url
                if collect_links:
                    context = node.find_parent('tr') or node.find_parent(['p', 'li'])
                    link = {'url': url, 'label': plain(contents)}
                    if context:
                        link.update(source_context_kind=context.name,source_context_text=normalize(str(context),base,collect_links=False)['text'],source_context_sha256=digest(str(context).encode()))
                        if context.name == 'tr':
                            link['source_context_cells'] = [normalize(str(cell),base,collect_links=False)['text'] for cell in context.find_all(['td','th'],recursive=False)]
                    links.append(link)
        encoded = ''.join(' ' + k + '="' + html.escape(' '.join(v) if isinstance(v,list) else str(v), quote=True) + '"' for k,v in attrs.items())
        return '<'+node.name+encoded+'>'+contents+('' if node.name in {'br','hr'} else '</'+node.name+'>')
    output = ''.join(render(x) for x in source_soup.contents)
    soup = BeautifulSoup(output,'html.parser')
    tables = []
    for table in soup.find_all('table'):
        rows = []
        for tr in table.find_all('tr'):
            if tr.find_parent('table') is not table:
                continue
            rows.append([{'tag': cell.name, 'text': plain(str(cell)), 'rowspan': str(cell.get('rowspan','1')), 'colspan': str(cell.get('colspan','1'))} for cell in tr.find_all(['td','th'],recursive=False)])
        tables.append(rows)
    return {'html': output, 'text': plain(output), 'images': images, 'links': links, 'tables': tables,'lists':source_lists}


def native_records(tree, config, root_path, project_renderer=False):
    if not isinstance(tree,list) or len(tree) != 1 or tree[0]['path'] != root_path:
        raise Invalid('Native subtree root mismatch')
    records, seen, blocks = [], set(), set()
    body_types = {'BodyM', 'BodyImage'}
    def field_markup(value):
        if re.match(r'^\s*data\s*:\s*image/',value,re.I):
            return '<img src="'+html.escape(value,quote=True)+'">'
        return value
    def safe_type(value):
        if value is not None and not isinstance(value,str):
            return {'unrecognized_source_type':type(value).__name__,'source_sha256':digest(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())}
        if isinstance(value,str) and re.search(r'data\s*:\s*image/',value,re.I):
            return {'embedded_image_omitted':True,'source_sha256':digest(value.encode())}
        return value
    def data_tag(node):
        attrs=node.get('li_attr')
        value=attrs.get('dataTag') if isinstance(attrs,dict) else None
        return value if isinstance(value,str) else None
    def walk(node, parent=None):
        key = node['id']
        if key in seen or node.get('docId') != str(config['document_id']):
            raise Invalid('Duplicate native ID or wrong publication')
        seen.add(key)
        if not node.get('path','').endswith('/'+key) or parent and (node['ref'].get('parent') != parent['id'] or not node['path'].startswith(parent['path']+'/')):
            raise Invalid('Broken native hierarchy')
        original_attrs=node.get('li_attr')
        attrs=original_attrs if isinstance(original_attrs,dict) else {}
        kind=data_tag(node)
        if kind in body_types and parent is not None:
            if node.get('children'):
                raise Invalid('Unrecognized nested body block')
            return
        qualifications=[]
        heading_type = isinstance(attrs.get('tag'),str) and attrs.get('tag') in {'h1','h2','h3','h4','h5','h6'}
        if not isinstance(original_attrs,dict):
            qualifications.append('Missing or malformed source li_attr object')
        if not heading_type:
            qualifications.append('Unknown or missing source heading tag')
        if kind not in {'section','subsection'}:
            qualifications.append('Unknown or missing source dataTag')
        original_text={'present':'text' in node,'value':node.get('text')}
        original_text_sha256=digest(json.dumps(original_text,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
        source_text=node.get('text')
        if not isinstance(source_text,str):
            qualifications.append('Missing or nontext source heading')
            source_text=''
        body = [c for c in node.get('children',[]) if data_tag(c) in body_types]
        def body_markup(child):
            value=child.get('text')
            if not isinstance(value,str):
                qualifications.append('Missing or nontext body block: '+child['id'])
                value=''
            if data_tag(child)=='BodyImage':
                return '<img src="'+html.escape(value,quote=True)+'">'
            value=field_markup(value)
            return body_for_rendering(value,kind) if project_renderer else value
        # Unknown own-text is still retained under its own source ID. It cannot
        # silently become a heading or disappear just because the client hides it.
        own_untyped_text=source_text if not heading_type else ''
        own_markup=field_markup(own_untyped_text)
        if kind=='BodyImage' and parent is None:
            own_markup='<img src="'+html.escape(source_text,quote=True)+'">'
        normalized = normalize(own_markup+''.join(body_markup(c) for c in body), config['source_url'])
        if any(not row['marker_format_qualified'] for row in normalized['lists']):
            qualifications.append('Custom or unsupported list marker formatting is unqualified')
        children = [c['id'] for c in node.get('children',[]) if data_tag(c) not in body_types]
        heading = normalize(field_markup(source_text) if heading_type else '',config['source_url'])
        if not heading['text']:
            qualifications.append('Empty source heading')
        disposition = 'source_unqualified' if qualifications else 'body' if normalized['text'] else 'container' if children else 'reserved' if re.search(r'\breserved\b', heading['text'],re.I) else 'source_empty_unresolved'
        source_body=''.join(c.get('text') if isinstance(c.get('text'),str) else json.dumps(c.get('text'),ensure_ascii=False,sort_keys=True) for c in body)
        record=dict(source_id=key, source_path=node['path'], source_url=config['source_url'].split('#')[0]+'#'+node['path'], document_id=node['docId'], parent_id=parent['id'] if parent else None, heading=heading['text'], heading_html=heading['html'], heading_images=heading['images'], heading_tag=safe_type(attrs.get('tag')), body_block_ids=[c['id'] for c in body], source_body_sha256=digest((own_untyped_text+source_body).encode()), child_ids=children, source_sequence=[c['id'] for c in node.get('children',[])], disposition=disposition, **normalized)
        if qualifications:
            record.update(source_qualification_errors=qualifications,source_text_field_present='text' in node,source_data_tag=safe_type(attrs.get('dataTag')),source_own_text_sha256=digest(source_text.encode()))
        record['source_original_text_sha256']=original_text_sha256
        record['source_own_fields_sha256']=digest(json.dumps({k:v for k,v in node.items() if k!='children'},ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
        records.append(record)
        blocks.update(c['id'] for c in body)
        for child in node.get('children',[]):
            walk(child,node)
    walk(tree[0])
    return records, {'native_node_count':len(seen), 'body_block_count':len(blocks)}


def dom_records(markup, config):
    soup = BeautifulSoup(markup,'html.parser')
    records = {}
    for section in soup.select('div.section[data-path]'):
        key = section['data-path']
        if key in records:
            raise Invalid('Duplicate rendered source path')
        copy = BeautifulSoup(str(section),'html.parser').find('div')
        for nested in copy.select('div.section[data-path]'):
            nested.decompose()
        heading = copy.find(re.compile('^h[1-6]$'))
        if not heading:
            raise Invalid('Rendered heading missing')
        title = normalize(str(heading),config['source_url'])['text']
        anchor = heading.parent
        if anchor.name == 'div' and str(anchor.get('id','')).startswith('anchor-'):
            anchor.decompose()
        else:
            heading.decompose()
        for controls in copy.select('.share-print'):
            controls.decompose()
        normalized = normalize(''.join(str(x) for x in copy.contents),config['source_url'])
        records[key] = dict(heading=title, **normalized)
    return records


def index_reference_kind(record, link):
    """Only the source's explicit two-column ordinance inventory is editorial.

    OUTPUT-CONTRACT permits non-code references and uncodified ordinances to be
    inventoried without importing their text into the codified publication.
    Unknown rows, links in operative provisions, and attachments stay unresolved.
    """
    if record['parent_id'] is not None or record['heading'] != 'COMPREHENSIVE ORDINANCE LIST':
        return None
    if not any(table and [c['text'] for c in table[0]] == ['Ord. No.', 'Action'] for table in record['tables']):
        return None
    cells = link.get('source_context_cells', [])
    # The retained index includes numeric ordinances, explicitly prefixed
    # ordinances/resolutions, and the historic Roman-numbered III and XII.
    if len(cells) == 2 and cells[0] == link['label'] and re.match(r'^(?:\d|Ord\. No\. \d|Res\. \d|[IVXLCDM]+$)', cells[0]):
        return 'ordinance_index_reference'
    if link['label'] == 'Search Ordinances' and urlsplit(link['url']).path.endswith('/Browse.aspx'):
        return 'editorial_search_reference'
    return None


def stylesheet_evidence(output, ledger, phases, config):
    """Verify observed original CSS receipts; no CSS interpretation or URL fetching.

    CSS originals may embed image references. They are never normalized legal
    output, never imported, and do not qualify custom marker punctuation.
    """
    result=[]
    source=urlsplit(config['source_url'])
    phase_epochs={p['phase']:p['roots_response']['epoch'] for p in phases}
    for receipt in ledger:
        if receipt.get('response_role')!='stylesheet' and receipt.get('resource_type')!='stylesheet':
            continue
        url=urlsplit(receipt.get('url',''))
        owner=urlsplit(receipt.get('source_document_url') or '')
        if url.scheme!='https' or url.hostname!='codehub.gridics.com' or receipt.get('resource_type')!='stylesheet' or receipt.get('response_role')!='stylesheet':
            raise Invalid('Stylesheet is not an observed first-party stylesheet response')
        if receipt.get('phase') not in phase_epochs or receipt.get('epoch')!=phase_epochs[receipt['phase']] or not receipt.get('at'):
            raise Invalid('Stylesheet lacks acquisition phase/epoch binding')
        raw=checked(output,receipt)
        if receipt.get('content_type','').split(';')[0].strip().lower()!='text/css':
            raise Invalid('Observed stylesheet does not have qualified CSS MIME')
        bound=(owner.scheme,owner.netloc,owner.path,owner.query)==(source.scheme,source.netloc,source.path,source.query)
        result.append({k:receipt[k] for k in ('url','path','sha256','bytes','phase','epoch','at','source_document_url') if k in receipt})
        result[-1].update(source_document_bound=bound,marker_rules_interpreted=False,qualification='original_source_only' if bound else 'original_source_owner_unqualified',image_assets_imported=0)
    return result


def analyze(output, config):
    output = Path(output)
    phases = [read(output/(phase+'-checkpoint.json')) for phase in ('start','end')]
    ledger=read(output/'responses.json')
    stylesheets=stylesheet_evidence(output,ledger,phases,config)
    ledger_by_path={r['path']:r for r in ledger if r.get('path')}
    if len(ledger_by_path)!=len([r for r in ledger if r.get('path')]):
        raise Invalid('Duplicate acquisition receipt paths')
    def instant(value):
        parsed=datetime.datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            raise Invalid('Receipt timestamp lacks time zone')
        return parsed.astimezone(datetime.timezone.utc)
    latest_opening=max(instant(r['at']) for r in ledger if r.get('phase')=='start')
    def bind_receipt(receipt,phase,kind):
        if ledger_by_path.get(receipt['path'])!=receipt or receipt.get('phase')!=phase or not receipt.get('epoch') or not receipt.get('at'):
            raise Invalid('Checkpoint receipt is not bound to its acquisition phase/ledger')
        if phase=='end' and instant(receipt['at'])<=latest_opening:
            raise Invalid('Closing receipt predates end of opening acquisition')
        url=urlsplit(receipt['url']);query=parse_qs(url.query)
        if url.scheme!='https' or url.hostname!='codehub.gridics.com' or url.path!='/api/v1/codehub/'+str(config['document_id']):
            raise Invalid('Wrong native publisher endpoint/document')
        if query.get(kind)!=['1'] or not query.get('revision'):
            raise Invalid('Missing native response type/revision')
    inventories, all_records, errors, summaries, refs = [], [], [], [], []
    profiles, reconciliations, native_only, native_trees = [], [], [], []
    paths_by_phase = []
    for phase in phases:
        if not phase.get('phase_complete'):
            raise Invalid('Acquisition phase is unfinished')
        inventory_receipt = phase['roots_response']
        bind_receipt(inventory_receipt,phase['phase'],'topLevel')
        profile = {}
        for receipt in ledger:
            role = script_role(receipt.get('url', ''))
            if role and receipt.get('phase') == phase['phase'] and receipt.get('epoch') == inventory_receipt['epoch']:
                raw = checked(output, receipt)
                expected = RENDERER_SHA256 if role == 'renderer' else ROUTER_SHA256
                if digest(raw) == expected:
                    profile[role] = {'path': receipt['path'], 'sha256': expected}
        profiles.append({'phase': phase['phase'], **profile})
        inventory = json.loads(checked(output, inventory_receipt))
        inventories.append(inventory)
        if [x['id'] for x in inventory] != [x['root']['id'] for x in phase['roots']]:
            raise Invalid('Checkpoint does not exhaust source root inventory')
        if len({x['id'] for x in inventory}) != len(inventory):
            raise Invalid('Duplicate top-level root')
        if any(row['root']!=root for row,root in zip(phase['roots'],inventory)):
            raise Invalid('Source root descriptor changed from native inventory')
        receipts = [inventory_receipt['path']]
        phase_records, phase_trees = [], []
        for row in phase['roots']:
            receipt = row['tree_response']
            bind_receipt(receipt,phase['phase'],'tree')
            if receipt['epoch']!=inventory_receipt['epoch']:
                raise Invalid('Native tree belongs to another acquisition epoch than phase inventory')
            query = parse_qs(urlsplit(receipt['url']).query)
            inv_query = parse_qs(urlsplit(inventory_receipt['url']).query)
            if query.get('revision') != inv_query.get('revision') or query.get('pathes[]') != [row['root']['path'].lstrip('/')]:
                # Publisher versions may retain the leading slash in pathes[].
                if query.get('revision') != inv_query.get('revision') or query.get('pathes[]') != [row['root']['path']]:
                    raise Invalid('Native response revision/path mismatch')
            receipts.append(receipt['path'])
            raw_tree=json.loads(checked(output,receipt));phase_trees.append(raw_tree)
            native, counts = native_records(raw_tree,config,row['root']['path'])
            projected = {r['source_id']: r for r in native}
            if 'renderer' in profile:
                projected = {r['source_id']: r for r in native_records(json.loads(checked(output,receipt)),config,row['root']['path'],project_renderer=True)[0]}
            unqualified=[{'source_id':r['source_id'],'reasons':r['source_qualification_errors']} for r in native if r.get('source_qualification_errors')]
            if unqualified:
                errors.append({'phase':phase['phase'],'root':row['root']['id'],'error':'Source headings, types or list marker formatting are unqualified','source_nodes':unqualified})
            render_status=row.get('render_status','captured')
            if render_status!='captured':
                from .publisher import section_renderability
                if render_status not in {'source_unrenderable','dom_unavailable'} or row.get('dom_path') is not None or row.get('dom_sha256') is not None or not row.get('render_diagnostic'):
                    raise Invalid('Malformed native-only render diagnostic')
                eligibility=section_renderability(row['root'])
                if row.get('renderability')!=eligibility or render_status=='source_unrenderable' and eligibility['eligible']:
                    raise Invalid('Unsubstantiated source-unrenderable classification')
                if render_status=='source_unrenderable' and 'renderer' not in profile:
                    raise Invalid('Source-unrenderable disposition requires exact same-phase publisher renderer')
                diagnostic=(output/row['diagnostic_dom_path']).resolve()
                if not diagnostic.is_relative_to(output.resolve()) or digest(diagnostic.read_bytes())!=row['diagnostic_dom_sha256']:
                    raise Invalid('Native-only diagnostic DOM witness changed')
                gap={'phase':phase['phase'],'root':row['root']['id'],'error':'No independent rendered section witness','render_status':render_status,'source_tree_sha256':receipt['sha256']}
                errors.append(gap);native_only.append(gap);dom={}
            else:
                dom_path = (output / row['dom_path']).resolve()
                if not dom_path.is_relative_to(output.resolve()) or digest(dom_path.read_bytes()) != row['dom_sha256']:
                    raise Invalid('Rendered witness changed')
                dom = dom_records(dom_path.read_text(),config)
            if render_status=='captured' and set(dom) != {x['source_path'] for x in native}:
                errors.append({'phase':phase['phase'],'root':row['root']['id'],'error':'Native/rendered inventory differs'})
            for rec in native:
                if render_status!='captured':
                    continue
                witness = dom.get(rec['source_path'],{})
                for field in ('heading','text','tables'):
                    # Whitespace layout can differ; all actual text must agree.
                    left,right = projected[rec['source_id']].get(field),witness.get(field)
                    if field in ('heading','text'):
                        left,right = ' '.join((left or '').split()),' '.join((right or '').split())
                    if left != right:
                        errors.append({'phase':phase['phase'],'source_id':rec['source_id'],'field':field,'error':'Native/rendered content differs'})
                    elif projected[rec['source_id']].get(field) != rec.get(field):
                        reconciliations.append({'phase':phase['phase'],'source_id':rec['source_id'],'field':field,'reason':'Exact retained publisher renderer projection agrees with independently captured DOM; original native text retained','renderer_sha256':profile['renderer']['sha256']})
                if len(rec['images']) != len(witness.get('images',[])):
                    errors.append({'phase':phase['phase'],'source_id':rec['source_id'],'error':'Image placeholder coverage differs'})
            phase_records.extend(native)
            if phase['phase'] == 'start':
                summaries.append(dict(root_id=row['root']['id'],records=len(native),**counts))
        if len({r['source_id'] for r in phase_records}) != len(phase_records):
            raise Invalid('Duplicate source ID across roots')
        paths_by_phase.append(set(receipts))
        all_records.append(phase_records)
        native_trees.append(phase_trees)
    if paths_by_phase[0] & paths_by_phase[1]:
        errors.append({'error':'Closing witness reused opening response bytes instead of independently acquiring'})
    raw_stable=inventories[0] == inventories[1] and native_trees[0] == native_trees[1]
    stable = raw_stable and all_records[0] == all_records[1]
    if not stable:
        errors.append({'error':'Publication changed between full opening and closing traversals'})
    ids = {x['source_path'] for x in all_records[0]}
    source_url = urlsplit(config['source_url'])
    router_qualified = all('router' in profile for profile in profiles)
    for rec in all_records[0]:
        for link in rec['links']:
            parsed = urlsplit(link['url'])
            index_kind = index_reference_kind(rec, link)
            if parsed.scheme == 'mailto':
                disposition='contact_reference'
            elif (parsed.scheme, parsed.netloc, parsed.path, parsed.query) == (source_url.scheme, source_url.netloc, source_url.path, source_url.query) and (parsed.fragment in ids or router_qualified and fragment_path(parsed.fragment) in ids):
                disposition='included_internal_provision'
            elif index_kind:
                disposition=index_kind
            else:
                disposition='unresolved_scope_or_required_document'
            refs.append(dict(owner_id=rec['source_id'],owner_heading=rec['heading'],owner_source_body_sha256=rec['source_body_sha256'],disposition=disposition,**link))
    unresolved = [x['source_id'] for x in all_records[0] if x['disposition']=='source_empty_unresolved']
    coverage = dict(schema_version=1, source_url=config['source_url'],document_id=config['document_id'],roots=len(inventories[0]),records=len(all_records[0]),root_counts=summaries,start_end_consistent=stable,source_errors=errors,unexplained_empty_source_ids=unresolved,publication_text_complete=not errors and not unresolved,required_assets_complete=not any(x['disposition']=='unresolved_scope_or_required_document' for x in refs),jurisdiction_complete=False,separate_image_downloads=0,image_placeholders=sum(len(x['images'])+len(x['heading_images']) for x in all_records[0]),normalized_output_contains_image_binaries=False,scope_note='All observed native top-level roots and descendants; external references remain conservatively unresolved until source-qualified.')
    coverage['complete'] = coverage['publication_text_complete'] and coverage['required_assets_complete']
    coverage['publisher_client_profiles'] = profiles
    coverage['publisher_rendering_reconciliations'] = reconciliations
    coverage['ordinance_index_reference_count'] = sum(r['disposition']=='ordinance_index_reference' for r in refs)
    coverage['ordinance_scope_note'] = 'All ordinance-index rows and source locators retained. Separate uncodified/predecessor ordinance documents are inventoried, not included in this codified publication; jurisdiction scope remains open.'
    coverage['native_only_roots'] = native_only
    coverage['unqualified_source_ids'] = [r['source_id'] for r in all_records[0] if r.get('source_qualification_errors')]
    coverage['native_source_complete'] = stable
    coverage['native_inventory_capture_complete'] = True
    coverage['raw_native_start_end_consistent'] = raw_stable
    coverage['rendered_publication_qa_complete'] = not native_only and not errors
    coverage['source_qualification_complete'] = not coverage['unqualified_source_ids']
    coverage['list_marker_qualification_gaps'] = [{'owner_id':r['source_id'],'list_order':v['order'],'source_list_sha256':v['source_list_sha256'],'source_attributes':v['source_attributes'],'reasons':v['qualification_errors']} for r in all_records[0] for v in r['lists'] if not v['marker_format_qualified']]
    coverage['observed_stylesheet_sources'] = stylesheets
    coverage['stylesheet_scope_note'] = 'Only actually observed first-party CSS original responses retained; no CSS URLs fetched/imported, image assets imported zero. Custom marker interpretation remains unqualified.'
    return all_records[0], refs, coverage
