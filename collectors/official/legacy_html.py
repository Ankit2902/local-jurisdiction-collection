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

from bs4 import BeautifulSoup, NavigableString, Tag

VERSION = 'cp-handoff-1.2'
# Legal reference tables can exceed Python csv's default128KiB field cap.
csv.field_size_limit(16 * 1024 * 1024)
FIELDS = ('jurisdiction code_name division title subtitle chapter subchapter article part subpart '
          'section_number section_name citation full_text source_url scrape_date').split()
NUMBER = re.compile(r'^\s*(?:§\s*)?((?:\d+[A-Za-z]?)(?:[.-]\d+[A-Za-z]?)+)(?=\s|[.:]|$)')
CONTAINER = re.compile(r'^\s*(title|chapter|article|part|appendix|charter)\b', re.I)
BLOCKED = re.compile(r'just a moment|verify (?:you are|that you are) human|attention required|access denied', re.I)
SKIP = 'p[class$="TOC"],script,style,nav,footer,header,iframe,frame,.CiteTOC,.ctoc,.digCH,.TitleTOC_outer,.TitleTOC_inner,.CHTOC,.digTitle,[id^="cluetip"],a[id^="addthis"],a[href^="mailto:"],[hidden],[aria-hidden="true"]'


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
        if el.attrs is not None and re.search(r'display\s*:\s*none', el.get('style', ''), re.I):
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
        a_id = h.find('a', attrs={'id': True})
        a_name = h.find('a', attrs={'name': True})
        anchor = h.get('id') or (a_id.get('id') if a_id else None) or (a_name.get('name') if a_name else None)
        loc = {'kind': ('html-id' if h.get('id') or a_id else 'html-anchor-name') if anchor else 'heading-index', 'value': str(anchor) if anchor else str(i)}
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
    from model import sanitize_images
    s = sanitize_images(s)
    for im in list(s.select('img')):
        im.replace_with(NavigableString('[IMAGE]'))
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
    if expected and not any(h.get('id') == expected for h in node.select('h1,h2,h3,h4,h5,h6')):
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
    pretext=plain(semantic(preamble))
    if pretext and not re.fullmatch(r'(?:PART|DIVISION|SUBPART)\s+[IVXLC0-9]+',pretext,re.I):
        proto=copy.deepcopy(inventory[0]);proto.update(node_id=doc_key(page['url'])+'::document-preamble',parent_node_id=None,source_order=-1,node_kind='preamble',display_number='',display_heading='Document preamble',source_url=page['url'],locator={'kind':'document-preamble','value':'before-first-heading'})
        inventory.insert(0,proto);buckets.insert(0,preamble)
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

