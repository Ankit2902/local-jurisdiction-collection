#!/usr/bin/env python3
"""Bounded Code Publishing acquisition and hash-bound offline replay. Python 3.9+."""
import argparse
import copy
import csv
import hashlib
import json
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit, unquote

import requests
from bs4 import BeautifulSoup, NavigableString, Tag

VERSION = 'cp-handoff-1.0'
FIELDS = ('jurisdiction code_name division title subtitle chapter subchapter article part subpart '
          'section_number section_name citation full_text source_url scrape_date').split()
NUMBER = re.compile(r'^\s*(?:§\s*)?((?:\d+[A-Za-z]?)(?:[.-]\d+[A-Za-z]?)+)(?=\s|[.:]|$)')
CONTAINER = re.compile(r'^\s*(title|chapter|article|part|appendix|charter)\b', re.I)
BLOCKED = re.compile(r'just a moment|verify (?:you are|that you are) human|attention required|access denied', re.I)
SKIP = 'script,style,nav,footer,header,iframe,frame,.CiteTOC,.ctoc,.digCH,.TitleTOC_outer,.TitleTOC_inner,.CHTOC,.digTitle,[id^="cluetip"],a[id^="addthis"],a[href^="mailto:"],[hidden],[aria-hidden="true"]'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    tmp.replace(path)


def safe_path(base, value):
    p = (base / value).resolve()
    if p != base.resolve() and base.resolve() not in p.parents:
        raise ValueError('artifact path escapes package')
    return p


def allowed(root, candidate):
    r, c = urlsplit(root), urlsplit(candidate)
    root_path = r.path.rstrip('/') + '/'
    path = unquote(c.path)
    return (c.scheme == 'https' and c.hostname == r.hostname and
            (path.rstrip('/') == r.path.rstrip('/') or path.startswith(root_path)) and
            not any(part in ('.', '..') for part in path.split('/')) and
            not any(part in ('.', '..') for part in unquote(c.fragment).split('/')) and
            not c.username and not c.password)


def doc_key(url):
    """Retain SPA document identity; discard only its ordinary inner anchor."""
    p = urlsplit(url)
    frag = p.fragment
    if frag.startswith('!/'):
        frag = frag.split('#', 1)[0]
    elif frag.startswith('/'):
        frag = frag.split('#', 1)[0]
    else:
        frag = ''
    return urlunsplit((p.scheme, p.netloc, p.path, p.query, frag))


def anchor_url(url, anchor):
    key = doc_key(url)
    return key + ('#' if not urlsplit(key).fragment else '#') + anchor


def links(html, url, root):
    soup = BeautifulSoup(html, 'html.parser')
    result, seen = [], set()
    for el in soup.select('a[href], frame[src], iframe[src]'):
        href = el.get('href') or el.get('src')
        if not href or href.startswith(('javascript:', 'mailto:', 'tel:')):
            continue
        target = urljoin(url, href)
        if not allowed(root, target) or target in seen:
            continue
        seen.add(target)
        label = ' '.join(el.get_text(' ', strip=True).split()) or el.get('title') or el.get('name') or ''
        kind = 'frame' if el.name in ('frame', 'iframe') else 'link'
        for name in ('title', 'chapter', 'article', 'appendix', 'charter', 'handbook'):
            if re.search(r'\b' + name + r'\b', label, re.I):
                kind = name
                break
        result.append({'source_url': target, 'display_heading': label, 'node_kind': kind,
                       'requires_rendered_acquisition': bool(urlsplit(target).fragment.startswith(('!/', '/')))})
    return result


def decode(raw):
    """Honor retained HTML encoding. No replacement chars silently accepted."""
    soup = BeautifulSoup(raw, 'html.parser')
    text = str(soup)
    if '\ufffd' in text or any('\x80' <= c <= '\x9f' for c in text):
        raise ValueError('unresolved decoding anomaly')
    return text


def content(html, selector):
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.title.get_text(' ', strip=True) if soup.title else ''
    if BLOCKED.search(title) or soup.select_one('#challenge-running, #cf-wrapper'):
        raise ValueError('challenge/error shell cannot be parsed as legal text')
    visible = soup.get_text(' ', strip=True)
    if re.search(r'(?:code|publication).{0,40}(?:now hosted|moved to|migrated to)', visible, re.I):
        raise ValueError('provider migration notice; re-discover current publisher')
    matches = soup.select(selector)
    if len(matches) != 1:
        raise ValueError('content selector must resolve exactly one legal container')
    node = matches[0]
    for el in list(node.select(SKIP)):
        el.decompose()
    for el in list(node.select('[style]')):
        if re.search(r'display\s*:\s*none', el.get('style', ''), re.I):
            el.decompose()
    return node


def heading_nodes(node, page, slug):
    """Inventory legal headings before reading their bodies; IDs never use citation alone."""
    out, stack, counts = [], [], {}
    for i, h in enumerate(node.select('h1,h2,h3,h4,h5,h6')):
        if h.find_parent(['table']):
            continue
        label = ' '.join(h.get_text(' ', strip=True).split())
        if not label:
            continue
        a = h.find('a', attrs={'name': True})
        anchor = h.get('id') or (a.get('name') if a else None)
        loc = {'kind': ('html-id' if h.get('id') else 'html-anchor-name') if anchor else 'heading-index', 'value': str(anchor) if anchor else str(i)}
        ident = doc_key(page['url']) + '::' + loc['kind'] + ':' + loc['value']
        counts[ident] = counts.get(ident, 0) + 1
        if counts[ident] > 1:
            raise ValueError('duplicate source locator in one document')
        rank = int(h.name[1])
        while stack and stack[-1][0] >= rank:
            stack.pop()
        n = NUMBER.match(label)
        kind = 'section' if n else (CONTAINER.match(label).group(1).lower() if CONTAINER.match(label) else 'unnumbered')
        out.append({'jurisdiction_slug': slug, 'publication_id': page['publication_id'],
                    'node_id': ident, 'parent_node_id': stack[-1][1] if stack else None,
                    'source_order': i, 'node_kind': kind, 'display_number': n.group(1) if n else '',
                    'display_heading': label, 'source_url': anchor_url(page['url'], str(anchor)) if anchor else page['url'],
                    'raw_artifact_path': page['path'], 'raw_sha256': page['sha256'],
                    'locator': loc, '_heading': h})
        stack.append((rank, ident))
    return out


def semantic(nodes):
    """One DOM traversal: retain nested HTML; image placeholders stay in source order."""
    s = BeautifulSoup(''.join(str(x) for x in nodes), 'html.parser')
    for im in list(s.select('img')):
        im.replace_with(NavigableString('[IMAGE]' + (' ' + im.get('alt') if im.get('alt') else '')))
    return str(s).strip()


def plain(html):
    s = BeautifulSoup(html, 'html.parser')
    for br in s.select('br'):
        br.replace_with('\n')
    for el in s.select('p,div,li,tr,blockquote'):
        el.append('\n')
    return re.sub(r'\n[ \t]*\n+', '\n\n', s.get_text()).strip()


def parse_page(raw, page, snapshot):
    node = content(decode(raw), page.get('content_selector', '#mainContent'))
    expected = page.get('expected_heading_id')
    if expected and not any(h.get('id') == expected for h in node.select('h3,h4,h5,h6')):
        raise ValueError('requested route legal heading not present; stale rendered content')
    inventory = heading_nodes(node, page, snapshot['jurisdiction_slug'])
    if not inventory:
        raise ValueError('no inventoried legal headings; explicit parser qualification required')
    by_element = {id(n['_heading']): i for i, n in enumerate(inventory)}
    buckets = [[] for _ in inventory]
    preamble = []
    current = -1
    def walk(el):
        nonlocal current
        if id(el) in by_element:
            current = by_element[id(el)]
        elif isinstance(el, Tag) and any(id(d) in by_element for d in el.descendants):
            for child in el.children:
                walk(child)
        else:
            (preamble if current < 0 else buckets[current]).append(copy.copy(el))
    for child in node.children:
        walk(child)
    if plain(semantic(preamble)):
        raise ValueError('substantive text before first legal heading requires explicit inventory node')
    records, dispositions, provenance = [], [], []
    clean_nodes = []
    by_id = {n['node_id']: n for n in inventory}
    publication = next((p for p in snapshot['publications'] if p['publication_id'] == page['publication_id']), None)
    if publication is None:
        raise ValueError('page publication not inventoried')
    for n, body in zip(inventory, buckets):
        n.pop('_heading')
        n['source_version'] = page.get('publisher_version')
        n['snapshot_id'] = snapshot['snapshot_id']
        html = semantic(body)
        txt = plain(html)
        status = 'reserved_or_repealed' if re.search(r'\b(reserved|repealed)\b', n['display_heading'], re.I) and not txt else ('included' if txt else ('structural' if n['node_kind'] != 'section' else 'unresolved'))
        rid = digest(encoded([snapshot['jurisdiction_slug'], page['publication_id'], n['node_id']]))
        dispositions.append({'node_id': n['node_id'], 'publication_id': page['publication_id'], 'disposition': status,
                             'record_ids': [rid] if txt else [], 'reason': 'cached DOM heading and owned body range'})
        clean_nodes.append(n)
        if not txt:
            continue
        row = dict.fromkeys(FIELDS, '')
        row.update(jurisdiction=snapshot['jurisdiction'], code_name=publication.get('title') or page['publication_id'],
                   section_number=n['display_number'], section_name=n['display_heading'], citation=n['display_heading'],
                   full_text=html, source_url=n['source_url'], scrape_date=snapshot.get('retrieved_at', '')[:10])
        for field, value in page.get('hierarchy', {}).items():
            if field in FIELDS and field not in ('full_text', 'source_url', 'section_number', 'citation'):
                row[field] = value
        ancestors = []
        ancestor = n
        while ancestor:
            ancestors.append(ancestor)
            ancestor = by_id.get(ancestor['parent_node_id'])
        for ancestor in reversed(ancestors):
            if ancestor['node_kind'] in ('title', 'chapter', 'article', 'part'):
                row[ancestor['node_kind']] = ancestor['display_heading']
        number_match = NUMBER.match(n['display_heading'])
        if number_match:
            row['section_name'] = n['display_heading'][number_match.end():].strip(' .:—–-')
        records.append(row)
        provenance.append({'record_id': rid, 'node_id': n['node_id'], 'publication_id': page['publication_id'],
                           'raw_artifact_path': page['path'], 'raw_sha256': page['sha256'], 'locator': n['locator'],
                           'extraction_version': VERSION, 'structured_representation': 'HTML fragment in full_text',
                           'plain_text': txt})
    if not records and not any(d['disposition'] == 'reserved_or_repealed' for d in dispositions):
        raise ValueError('navigation/empty document has no substantive legal bodies')
    return {'records': records, 'nodes': clean_nodes, 'dispositions': dispositions, 'provenance': provenance}


def binding(snapshot, raw):
    return digest(encoded({'snapshot_sha256': digest(raw), 'parser': VERSION,
                           'parser_sha256': digest(Path(__file__).read_bytes())}))


def replay(snapshot_path, out, checkpoint=None, stop_after=None):
    snapshot_path, out = Path(snapshot_path), Path(out)
    raw = snapshot_path.read_bytes()
    s = json.loads(raw)
    required = ('jurisdiction_slug', 'jurisdiction', 'snapshot_id', 'pages', 'publications', 'root_url')
    if any(k not in s for k in required):
        raise ValueError('snapshot missing required identity/config fields')
    frozen = binding(s, raw)
    state = {'binding': frozen, 'done': []}
    # Verify all bytes before trusting checkpoint, including already processed pages.
    seen = set()
    for nav in s.get('navigation_evidence', []):
        if digest(safe_path(snapshot_path.parent, nav['path']).read_bytes()) != nav['sha256']:
            raise ValueError('navigation artifact hash mismatch')
    for p in s['pages']:
        if not allowed(s['root_url'], p['url']):
            raise ValueError('page outside jurisdiction scope')
        key = (p['publication_id'], doc_key(p['url']))
        if key in seen:
            raise ValueError('duplicate acquisition document; reconcile route aliases explicitly')
        seen.add(key)
        if digest(safe_path(snapshot_path.parent, p['path']).read_bytes()) != p['sha256']:
            raise ValueError('raw artifact hash mismatch')
    if checkpoint and Path(checkpoint).exists():
        state = json.loads(Path(checkpoint).read_text())
        if state.get('binding') != frozen:
            raise ValueError('checkpoint snapshot/parser/config binding mismatch')
    processed = 0
    for p in s['pages'][len(state['done']):]:
        parsed = parse_page(safe_path(snapshot_path.parent, p['path']).read_bytes(), p, s)
        state['done'].append(parsed)
        if checkpoint:
            save(checkpoint, state)
        processed += 1
        if stop_after and processed >= stop_after:
            return {'status': 'interrupted', 'pages_processed': len(state['done'])}
    result = {k: [x for page in state['done'] for x in page[k]] for k in ('records', 'nodes', 'dispositions', 'provenance')}
    out.mkdir(parents=True, exist_ok=True)
    save(out/'input-snapshot.json', s)
    for p in s['pages'] + s.get('navigation_evidence', []):
        target = safe_path(out, p['path'])
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.resolve() != safe_path(snapshot_path.parent, p['path']):
            shutil.copyfile(safe_path(snapshot_path.parent, p['path']), target)
    for name, key in [('source-nodes', 'nodes'), ('node-dispositions', 'dispositions'), ('record-provenance', 'provenance')]:
        (out / (name + '.jsonl')).write_text(''.join(json.dumps(v, ensure_ascii=False) + '\n' for v in result[key]), encoding='utf-8')
    save(out/'publications.json', s['publications'])
    exceptions = [d for d in result['dispositions'] if d['disposition'] == 'unresolved']
    exceptions.append({'kind': 'coverage', 'reason': 'bounded cached-page replay; publication inventory, scope and coherent version are not established'})
    (out/'exceptions.jsonl').write_text(''.join(json.dumps(v) + '\n' for v in exceptions), encoding='utf-8')
    def export(prefix, rows):
        for kind in ('fulltext', 'toc'):
            values = [dict(r, full_text='') for r in rows] if kind == 'toc' else rows
            stem = out / (prefix + kind)
            save(str(stem)+'.json', {'metadata': {'snapshot_id': s['snapshot_id'], 'parser': VERSION, 'coverage': 'bounded_pages'}, 'provisions': values})
            with Path(str(stem)+'.csv').open('w', encoding='utf-8-sig', newline='') as f:
                w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(values)
            with Path(str(stem)+'.csv').open(encoding='utf-8-sig', newline='') as f:
                if list(csv.DictReader(f)) != values:
                    raise ValueError('CSV/JSON mismatch')
    export('aggregate-', result['records'])
    for pub in s['publications']:
        pid = pub['publication_id']
        if not re.fullmatch(r'[a-z0-9-]+', pid):
            raise ValueError('unsafe publication identifier')
        export('publications/'+pid+'/', [r for r, prov in zip(result['records'], result['provenance']) if prov['publication_id'] == pid])
    report = {'status': 'bounded_replay_passed', 'whole_corpus_complete': False, 'snapshot_binding': frozen,
              'pages': len(s['pages']), 'records': len(result['records']), 'source_nodes': len(result['nodes']),
              'unresolved_nodes': len([x for x in result['dispositions'] if x['disposition'] == 'unresolved']),
              'csv_json_equal': True, 'limitations': [exceptions[-1]['reason']]}
    save(out/'validation-report.json', report)
    artifacts = {str(p.relative_to(out)): digest(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'run-manifest.json'}
    save(out/'run-manifest.json', {'adapter_version': VERSION, 'snapshot_binding': frozen, 'snapshot_id': s['snapshot_id'],
                                  'jurisdiction_slug': s['jurisdiction_slug'], 'configuration_sha256': digest(raw),
                                  'completion_status': 'incomplete_bounded_replay', 'counts': report, 'artifact_sha256': artifacts})
    return report


def fetch(url, root, directory, sequence):
    """Sequential ordinary HTTPS. Retain failures; never reinterpret hash shells as bodies."""
    if not allowed(root, url):
        raise ValueError('request outside jurisdiction scope')
    if urlsplit(url).fragment.startswith(('!/', '/')):
        raise ValueError('SPA hash route requires a retained browser-rendered snapshot')
    session = requests.Session()
    chain = []
    for redirect in range(6):
        r = session.get(url, timeout=30, allow_redirects=False, headers={'User-Agent': 'CompliSolv extraction qualification/1.0'})
        chain.append({'url': url, 'status': r.status_code})
        if r.status_code in (301, 302, 303, 307, 308):
            target = urljoin(url, r.headers.get('Location', ''))
            if not allowed(root, target):
                raise ValueError('provider migration/out-of-scope redirect: ' + target)
            url = target
            continue
        break
    else:
        raise ValueError('redirect limit reached')
    directory = Path(directory); (directory/'raw').mkdir(parents=True, exist_ok=True)
    artifact = 'raw/%03d.html' % sequence
    (directory/artifact).write_bytes(r.content)
    receipt = {'url': url, 'requested_url': chain[0]['url'], 'redirect_chain': chain, 'http_status': r.status_code,
               'retrieved_at': datetime.now(timezone.utc).isoformat(), 'headers': dict(r.headers),
               'path': artifact, 'sha256': digest(r.content), 'bytes': len(r.content)}
    save(directory/('request-%03d.json' % sequence), receipt)
    if r.status_code != 200:
        return receipt, None
    html = decode(r.content)
    if BLOCKED.search(BeautifulSoup(html, 'html.parser').title.get_text() if BeautifulSoup(html, 'html.parser').title else ''):
        receipt['rejection'] = 'challenge shell'; save(directory/('request-%03d.json' % sequence), receipt)
        return receipt, None
    return receipt, html


def discover(root, out, max_pages=3):
    """Inventory-only crawl, capped by operator. Frames are queued as explicit documents."""
    queue, visited, artifacts, inventory, errors = [root], set(), [], [], []
    while queue and len(artifacts) < max_pages:
        url = queue.pop(0)
        key = doc_key(url)
        if key in visited:
            continue
        visited.add(key)
        if urlsplit(url).fragment.startswith(('!/', '/')):
            errors.append({'url': url, 'reason': 'requires supported browser-rendered acquisition'}); continue
        try:
            receipt, html = fetch(url, root, out, len(artifacts))
        except (ValueError, requests.RequestException) as exc:
            errors.append({'url': url, 'reason': str(exc)})
            break
        artifacts.append(receipt)
        if html is None:
            errors.append({'url': url, 'reason': 'HTTP failure or challenge'}); break
        items = links(html, url, root)
        inventory.extend(dict(item, parent_url=url, raw_sha256=receipt['sha256']) for item in items)
        for item in items:
            if item['node_kind'] in ('frame', 'title', 'chapter', 'charter', 'handbook', 'appendix'):
                queue.append(item['source_url'])
        time.sleep(1)
    result = {'status': 'blocked' if errors else 'bounded_discovery_only', 'root_url': root,
              'whole_inventory_complete': False, 'artifacts': artifacts, 'observed_links': inventory,
              'pending_urls': queue, 'errors': errors}
    save(Path(out)/'discovery.json', result)
    return result


def acquire(plan_path, out):
    """Acquire a bounded explicit plan whose URLs occur in retained navigation evidence.

    Browser-rendered artifacts may be imported with their observed rendered_url.
    This trusts the operator's browser receipt; it never launches a replacement browser.
    """
    plan_path, out = Path(plan_path), Path(out)
    plan = json.loads(plan_path.read_text())
    if not 1 <= len(plan['pages']) <= 20:
        raise ValueError('bounded acquisition requires 1–20 planned documents')
    pages = []
    navigation = []
    for index, spec in enumerate(plan['pages']):
        evidence = spec['navigation_evidence']
        raw_nav = safe_path(plan_path.parent, evidence['path']).read_bytes()
        if digest(raw_nav) != evidence['sha256']:
            raise ValueError('navigation evidence hash mismatch')
        candidates = links(decode(raw_nav), evidence['url'], plan['root_url'])
        if not any(doc_key(x['source_url']) == doc_key(spec['url']) for x in candidates):
            raise ValueError('planned document was not observed in retained navigation')
        nav_path = 'raw/navigation-%03d.html' % index
        (out/'raw').mkdir(parents=True, exist_ok=True)
        (out/nav_path).write_bytes(raw_nav)
        navigation.append(dict(evidence, path=nav_path))
        if spec.get('rendered_artifact'):
            rendered = spec['rendered_artifact']
            if doc_key(rendered['rendered_url']) != doc_key(spec['url']):
                raise ValueError('rendered route does not match requested document')
            raw = safe_path(plan_path.parent, rendered['path']).read_bytes()
            if digest(raw) != rendered['sha256']:
                raise ValueError('rendered artifact hash mismatch')
            path = 'raw/%03d.html' % index
            (out/path).write_bytes(raw)
            receipt = {'url': spec['url'], 'path': path, 'sha256': digest(raw),
                       'retrieved_at': rendered['retrieved_at'], 'transport': 'operator-retained-rendered-DOM'}
            save(out/('request-%03d.json' % index), receipt)
        else:
            receipt, html = fetch(spec['url'], plan['root_url'], out, index)
            if html is None:
                save(out/'acquisition-failure.json', {'status':'blocked','receipt':receipt})
                raise ValueError('acquisition blocked; no replay snapshot produced')
        page = {key: spec[key] for key in ('publication_id', 'content_selector')}
        page.update({key:receipt[key] for key in ('url','path','sha256')})
        if spec.get('rendered_artifact') and not spec.get('expected_heading_id'):
            raise ValueError('rendered import requires observed expected_heading_id readiness check')
        page['expected_heading_id'] = spec.get('expected_heading_id')
        page['publisher_version'] = spec.get('publisher_version')
        page['hierarchy'] = spec.get('hierarchy', {})
        # Readiness must validate the retained content before admitting it to snapshot.
        parse_page((out/page['path']).read_bytes(), page, dict(plan, snapshot_id=plan['snapshot_id']))
        pages.append(page)
        if index + 1 < len(plan['pages']):
            time.sleep(1)
    snapshot = {key:plan[key] for key in ('jurisdiction_slug','jurisdiction','root_url','snapshot_id','publications')}
    snapshot.update(pages=pages, navigation_evidence=navigation, inventory_complete=False,
                    coherent_publication_version=False, retrieved_at=receipt['retrieved_at'])
    save(out/'snapshot.json', snapshot)
    return {'status':'bounded_acquisition_complete', 'pages':len(pages), 'whole_corpus_complete':False}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='command', required=True)
    p = sub.add_parser('discover'); p.add_argument('--root', required=True); p.add_argument('--out', required=True); p.add_argument('--max-pages', type=int, default=3)
    p = sub.add_parser('acquire'); p.add_argument('--plan', required=True); p.add_argument('--out', required=True)
    p = sub.add_parser('replay'); p.add_argument('--snapshot', required=True); p.add_argument('--out', required=True); p.add_argument('--checkpoint'); p.add_argument('--stop-after', type=int)
    a = ap.parse_args()
    if a.command == 'discover':
        if not 1 <= a.max_pages <= 20:
            ap.error('bounded inventory discovery permits 1–20 pages per invocation')
        answer = discover(a.root, a.out, a.max_pages)
    elif a.command == 'acquire':
        answer = acquire(a.plan, a.out)
    else:
        answer = replay(a.snapshot, a.out, a.checkpoint, a.stop_after)
    print(json.dumps(answer, indent=2))

if __name__ == '__main__':
    main()
