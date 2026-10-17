"""Gridics native-tree normalization, with independent rendered DOM comparison."""
import hashlib
import html
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlsplit, parse_qs
from bs4 import BeautifulSoup, NavigableString, Tag, Comment


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
    if str(receipt.get('content_type', '')).startswith('image/'):
        raise Invalid('Separate image receipt is forbidden')
    return raw


def plain(markup):
    # Inline tags never introduce arbitrary spaces inside words.
    soup = BeautifulSoup(markup, 'html.parser')
    def number(value, style):
        if style in {'upper-alpha','lower-alpha','upper-latin','lower-latin'} and value > 0:
            label=''
            while value:
                value, remainder=divmod(value-1,26)
                label=chr(65+remainder)+label
            return label.lower() if style.startswith('lower') else label
        if style in {'upper-roman','lower-roman'} and 0 < value < 4000:
            label=''
            for amount,letters in [(1000,'M'),(900,'CM'),(500,'D'),(400,'CD'),(100,'C'),(90,'XC'),(50,'L'),(40,'XL'),(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]:
                while value>=amount:
                    label+=letters;value-=amount
            return label.lower() if style=='lower-roman' else label
        return str(value)
    for ordered in soup.find_all('ol'):
        children=ordered.find_all('li',recursive=False)
        value=int(ordered.get('start',len(children) if ordered.has_attr('reversed') else 1))
        step=-1 if ordered.has_attr('reversed') else 1
        match=re.search(r'list-style-type\s*:\s*([a-z-]+)',ordered.get('style',''),re.I)
        style=match.group(1) if match else {'A':'upper-alpha','a':'lower-alpha','I':'upper-roman','i':'lower-roman'}.get(ordered.get('type'),'decimal')
        for li in children:
            value=int(li.get('value',value))
            if style!='none':
                li.insert(0,number(value,style)+'. ')
            value+=step
    for cell in soup.find_all(['td','th']):
        cell.append('\t')
    for br in soup.find_all('br'):
        br.replace_with('\n')
    for node in soup.find_all(['p', 'div', 'li', 'tr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'dd', 'dt']):
        node.append('\n')
    return '\n'.join(' '.join(line.split()) for line in soup.get_text().splitlines() if line.strip())


def normalize(markup, base):
    images, links = [], []
    allowed = {'p','div','span','section','article','table','caption','thead','tbody','tfoot','tr','td','th','ol','ul','li','dl','dt','dd','blockquote','br','hr','sup','sub','em','strong','b','i','u','s','a','h1','h2','h3','h4','h5','h6'}
    def marker(node, kind):
        locator=node.get('src') or node.get('data') or node.get('background') or node.get('style')
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
        image_resource = str(node.get('type','')).startswith('image/') or re.search(r'(?:^data:image/|\.(?:png|jpe?g|gif|svg|webp|avif)(?:[?#]|$))',image_url,re.I)
        if node.name in {'img','svg','picture','canvas'} or (node.name in {'object','embed'} and image_resource) or (node.name == 'input' and node.get('type') == 'image') or (node.name=='source' and (node.get('srcset') or image_resource)):
            return marker(node, node.name)
        if node.name=='style' and re.search(r'(?:url\s*\(|(?:repeating-)?(?:linear|radial|conic)-gradient\s*\()',node.get_text(),re.I):
            return marker(node,'stylesheet_image')
        if node.name in {'script','style','noscript','button','input','source'}:
            return ''
        css_image = node.get('background') or re.search(r'(?:url\s*\(|(?:repeating-)?(?:linear|radial|conic)-gradient\s*\()', node.get('style',''), re.I)
        contents = (marker(node, 'css') if css_image else '') + ''.join(render(c) for c in node.children)
        if node.name not in allowed:
            return contents
        attrs = {}
        if node.name in {'td','th'}:
            attrs = {k: node[k] for k in ('rowspan','colspan','scope','headers') if node.has_attr(k)}
        if node.name in {'ol','li'}:
            attrs.update({k: node[k] for k in ('start','type','value','reversed') if node.has_attr(k)})
            style = re.search(r'list-style-type\s*:\s*([a-z-]+)', node.get('style',''), re.I)
            if style:
                attrs['style'] = 'list-style-type:' + style.group(1)
        if node.get('id'):
            attrs['id'] = node['id']
        if node.name == 'a' and node.get('href'):
            url = urljoin(base, node['href'])
            if urlsplit(url).scheme in {'https','http','mailto'}:
                attrs['href'] = url
                links.append({'url': url, 'label': plain(contents)})
        encoded = ''.join(' ' + k + '="' + html.escape(' '.join(v) if isinstance(v,list) else str(v), quote=True) + '"' for k,v in attrs.items())
        return '<'+node.name+encoded+'>'+contents+('' if node.name in {'br','hr'} else '</'+node.name+'>')
    output = ''.join(render(x) for x in BeautifulSoup(markup,'html.parser').contents)
    soup = BeautifulSoup(output,'html.parser')
    tables = []
    for table in soup.find_all('table'):
        rows = []
        for tr in table.find_all('tr'):
            if tr.find_parent('table') is not table:
                continue
            rows.append([{'tag': cell.name, 'text': plain(str(cell)), 'rowspan': str(cell.get('rowspan','1')), 'colspan': str(cell.get('colspan','1'))} for cell in tr.find_all(['td','th'],recursive=False)])
        tables.append(rows)
    return {'html': output, 'text': plain(output), 'images': images, 'links': links, 'tables': tables}


def native_records(tree, config, root_path):
    if not isinstance(tree,list) or len(tree) != 1 or tree[0]['path'] != root_path:
        raise Invalid('Native subtree root mismatch')
    records, seen, blocks = [], set(), set()
    def walk(node, parent=None):
        key = node['id']
        if key in seen or node.get('docId') != str(config['document_id']):
            raise Invalid('Duplicate native ID or wrong publication')
        seen.add(key)
        if not node.get('path','').endswith('/'+key) or parent and (node['ref'].get('parent') != parent['id'] or not node['path'].startswith(parent['path']+'/')):
            raise Invalid('Broken native hierarchy')
        attrs = node['li_attr']
        if attrs.get('dataTag') == 'BodyM':
            if node.get('children'):
                raise Invalid('Unrecognized nested BodyM')
            return
        if attrs.get('tag') not in {'h1','h2','h3','h4','h5','h6'}:
            raise Invalid('Unrecognized Gridics source type: '+str(attrs))
        body = [c for c in node.get('children',[]) if c['li_attr'].get('dataTag') == 'BodyM']
        normalized = normalize(''.join(c['text'] for c in body), config['source_url'])
        children = [c['id'] for c in node.get('children',[]) if c['li_attr'].get('dataTag') != 'BodyM']
        heading = normalize(node['text'],config['source_url'])
        disposition = 'body' if normalized['text'] else 'container' if children else 'reserved' if re.search(r'\breserved\b', heading['text'],re.I) else 'source_empty_unresolved'
        records.append(dict(source_id=key, source_path=node['path'], source_url=config['source_url'].split('#')[0]+'#'+node['path'], document_id=node['docId'], parent_id=parent['id'] if parent else None, heading=heading['text'], heading_html=heading['html'], heading_images=heading['images'], heading_tag=attrs['tag'], body_block_ids=[c['id'] for c in body], child_ids=children, source_sequence=[c['id'] for c in node.get('children',[])], disposition=disposition, **normalized))
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


def analyze(output, config):
    output = Path(output)
    phases = [read(output/(phase+'-checkpoint.json')) for phase in ('start','end')]
    ledger=read(output/'responses.json')
    ledger_by_path={r['path']:r for r in ledger if r.get('path')}
    if len(ledger_by_path)!=len([r for r in ledger if r.get('path')]):
        raise Invalid('Duplicate acquisition receipt paths')
    latest_opening=max(r['at'] for r in ledger if r.get('phase')=='start')
    def bind_receipt(receipt,phase,kind):
        if ledger_by_path.get(receipt['path'])!=receipt or receipt.get('phase')!=phase or not receipt.get('epoch') or not receipt.get('at'):
            raise Invalid('Checkpoint receipt is not bound to its acquisition phase/ledger')
        if phase=='end' and receipt['at']<=latest_opening:
            raise Invalid('Closing receipt predates end of opening acquisition')
        url=urlsplit(receipt['url']);query=parse_qs(url.query)
        if url.scheme!='https' or url.hostname!='codehub.gridics.com' or url.path!='/api/v1/codehub/'+str(config['document_id']):
            raise Invalid('Wrong native publisher endpoint/document')
        if query.get(kind)!=['1'] or not query.get('revision'):
            raise Invalid('Missing native response type/revision')
    inventories, all_records, errors, summaries, refs = [], [], [], [], []
    paths_by_phase = []
    for phase in phases:
        if not phase.get('phase_complete'):
            raise Invalid('Acquisition phase is unfinished')
        inventory_receipt = phase['roots_response']
        bind_receipt(inventory_receipt,phase['phase'],'topLevel')
        inventory = json.loads(checked(output, inventory_receipt))
        inventories.append(inventory)
        if [x['id'] for x in inventory] != [x['root']['id'] for x in phase['roots']]:
            raise Invalid('Checkpoint does not exhaust source root inventory')
        if len({x['id'] for x in inventory}) != len(inventory):
            raise Invalid('Duplicate top-level root')
        receipts = [inventory_receipt['path']]
        phase_records = []
        for row in phase['roots']:
            receipt = row['tree_response']
            bind_receipt(receipt,phase['phase'],'tree')
            query = parse_qs(urlsplit(receipt['url']).query)
            inv_query = parse_qs(urlsplit(inventory_receipt['url']).query)
            if query.get('revision') != inv_query.get('revision') or query.get('pathes[]') != [row['root']['path'].lstrip('/')]:
                # Publisher versions may retain the leading slash in pathes[].
                if query.get('revision') != inv_query.get('revision') or query.get('pathes[]') != [row['root']['path']]:
                    raise Invalid('Native response revision/path mismatch')
            receipts.append(receipt['path'])
            native, counts = native_records(json.loads(checked(output,receipt)),config,row['root']['path'])
            dom_path = (output / row['dom_path']).resolve()
            if not dom_path.is_relative_to(output.resolve()) or digest(dom_path.read_bytes()) != row['dom_sha256']:
                raise Invalid('Rendered witness changed')
            dom = dom_records(dom_path.read_text(),config)
            if set(dom) != {x['source_path'] for x in native}:
                errors.append({'phase':phase['phase'],'root':row['root']['id'],'error':'Native/rendered inventory differs'})
            for rec in native:
                witness = dom.get(rec['source_path'],{})
                for field in ('heading','text','tables'):
                    # Whitespace layout can differ; all actual text must agree.
                    left,right = rec.get(field),witness.get(field)
                    if field in ('heading','text'):
                        left,right = ' '.join((left or '').split()),' '.join((right or '').split())
                    if left != right:
                        errors.append({'phase':phase['phase'],'source_id':rec['source_id'],'field':field,'error':'Native/rendered content differs'})
                if len(rec['images']) != len(witness.get('images',[])):
                    errors.append({'phase':phase['phase'],'source_id':rec['source_id'],'error':'Image placeholder coverage differs'})
            phase_records.extend(native)
            if phase['phase'] == 'start':
                summaries.append(dict(root_id=row['root']['id'],records=len(native),**counts))
        if len({r['source_id'] for r in phase_records}) != len(phase_records):
            raise Invalid('Duplicate source ID across roots')
        paths_by_phase.append(set(receipts))
        all_records.append(phase_records)
    if paths_by_phase[0] & paths_by_phase[1]:
        errors.append({'error':'Closing witness reused opening response bytes instead of independently acquiring'})
    stable = inventories[0] == inventories[1] and all_records[0] == all_records[1]
    if not stable:
        errors.append({'error':'Publication changed between full opening and closing traversals'})
    ids = {x['source_path'] for x in all_records[0]}
    for rec in all_records[0]:
        for link in rec['links']:
            parsed = urlsplit(link['url'])
            if parsed.scheme == 'mailto':
                disposition='contact_reference'
            elif parsed.hostname == 'codehub.gridics.com' and parsed.fragment in ids:
                disposition='included_internal_provision'
            else:
                disposition='unresolved_scope_or_required_document'
            refs.append(dict(owner_id=rec['source_id'],disposition=disposition,**link))
    unresolved = [x['source_id'] for x in all_records[0] if x['disposition']=='source_empty_unresolved']
    coverage = dict(schema_version=1, source_url=config['source_url'],document_id=config['document_id'],roots=len(inventories[0]),records=len(all_records[0]),root_counts=summaries,start_end_consistent=stable,source_errors=errors,unexplained_empty_source_ids=unresolved,publication_text_complete=not errors and not unresolved,required_assets_complete=not any(x['disposition']=='unresolved_scope_or_required_document' for x in refs),jurisdiction_complete=False,separate_image_downloads=0,image_placeholders=sum(len(x['images'])+len(x['heading_images']) for x in all_records[0]),normalized_output_contains_image_binaries=False,scope_note='All observed native top-level roots and descendants; external references remain conservatively unresolved until source-qualified.')
    coverage['complete'] = coverage['publication_text_complete'] and coverage['required_assets_complete']
    return all_records[0], refs, coverage
