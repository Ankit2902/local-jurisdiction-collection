"""Bind discovery candidates to retained source context without waiving scope.

A link in publisher navigation is not by itself evidence that the destination is
a legal publication. This audit preserves every catalog entry and its existing
requirements; it makes no destination request or publication-acceptance claim.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'collectors/registry'))
from catalog import load_catalog


def sha(data):
    return hashlib.sha256(data).hexdigest()


def context(anchor):
    ancestors = list(anchor.parents)
    if (anchor.get('id') == 'footer-citylink'
            and any(node.get('id') == 'main-body-footer' for node in ancestors)):
        placement = 'publisher-footer-city-homepage-link'
    elif any(node.get('id') == 'doc-lib-ctnr' for node in ancestors):
        placement = 'publisher-document-library-list'
    elif any(node.get('id') == 'nav1' for node in ancestors):
        placement = 'publisher-primary-navigation'
    else:
        placement = 'other-source-context'
    return {
        'label': ' '.join(anchor.stripped_strings),
        'literal_href': anchor.get('href'),
        'placement': placement,
        'anchor_sha256': sha(str(anchor).encode()),
        'ancestors': [
            {'tag': node.name, 'id': node.get('id'), 'classes': node.get('class', [])}
            for node in ancestors[:6]
        ],
        'legal_publication_established_by_link_alone': False,
    }


def audit(source, receipt_path, catalog, target_id):
    raw = source.read_bytes()
    receipt_raw = receipt_path.read_bytes()
    receipt = json.loads(receipt_raw)
    if receipt.get('sha256') != sha(raw) or receipt.get('http_status') != 200:
        raise ValueError('Retained successful source receipt/hash is required')
    base = receipt.get('final_url', receipt['url'])
    soup = BeautifulSoup(raw, 'html.parser')
    anchors = {}
    for anchor in soup.select('a[href]'):
        anchors.setdefault(urljoin(base, anchor['href']), []).append(context(anchor))
    rows = []
    for publication in catalog['publications']:
        if publication['target_id'] != target_id:
            continue
        matches = anchors.get(publication['source_url'], [])
        footer_only = bool(matches) and all(
            item['placement'] == 'publisher-footer-city-homepage-link' for item in matches)
        rows.append({
            'publication_id': publication['id'],
            'title': publication['title'],
            'source_url': publication['source_url'],
            'catalog_scope_kind': publication['scope_kind'],
            'catalog_required_for_jurisdiction': publication['required_for_jurisdiction'],
            'source_matches': matches,
            'finding': ('footer-navigation-only-in-this-witness' if footer_only
                        else 'destination-publication-qualification-separate' if matches
                        else 'not-linked-by-this-witness'),
            'scope_override_applied': False,
        })
    return {
        'schema_version': 1,
        'read_only': True,
        'network_requests_sent': 0,
        'source': {'url': base, 'sha256': sha(raw), 'bytes': len(raw),
                   'receipt_sha256': sha(receipt_raw)},
        'auditor_sha256': sha(Path(__file__).read_bytes()),
        'catalog_sha256': sha(json.dumps(catalog, sort_keys=True).encode()),
        'target_id': target_id,
        'entries': rows,
        'footer_only_candidates': [r['publication_id'] for r in rows
                                   if r['finding'] == 'footer-navigation-only-in-this-witness'],
        'claims': ('Source link placement only. All catalog entries and requirements '
                   'are preserved. Neither a document-library link nor a navigation '
                   'link establishes destination content, incorporation, edition, '
                   'full publication coverage, or an exclusion from legal scope.'),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--target', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error('Use a fresh report path; prior evidence is immutable')
    result = audit(args.source, args.receipt, load_catalog(), args.target)
    if not result['entries']:
        parser.error('Target has no catalog entries')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'entries': len(result['entries']),
                      'footer_only_candidates': result['footer_only_candidates'],
                      'scope_override_applied': False}))


if __name__ == '__main__':
    main()
