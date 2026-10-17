#!/usr/bin/env python3
"""Assemble the six group reports without changing their retained evidence."""
import collections
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GROUPS = ['municode-cities', 'municode-counties', 'american-legal', 'icc-ecode', 'official-sources', 'encodeplus']
EXCLUDE = {'.venv', 'node_modules', '__pycache__', '.git', '.DS_Store', 'browser.lock'}

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def qualify_paths(value, group):
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if key in ('evidence_paths', 'script_paths'):
                result[key] = [p if Path(p).parts[0] in GROUPS else str(Path(group) / p) for p in item]
            else:
                result[key] = qualify_paths(item, group)
        return result
    if isinstance(value, list):
        return [qualify_paths(v, group) for v in value]
    return value

def main():
    scope = json.loads((ROOT / 'scope43.json').read_text())
    expected = {r['sequence']: r for r in scope}
    rows = []
    for group in GROUPS:
        data = json.loads((ROOT / group / 'results.json').read_text())
        assert isinstance(data, list), group
        for row in data:
            item = qualify_paths(row, group)
            item['working_directory'] = group
            item['path_base'] = 'Aggregate evidence_paths/script_paths: handoff root; commands and other provenance paths: working_directory.'
            item['group_report'] = group + '/README.md'
            rows.append(item)
    rows.sort(key=lambda r: r['sequence'])
    assert [r['sequence'] for r in rows] == list(range(58, 101)), 'Missing or duplicate target'
    assert all(r['state'] == expected[r['sequence']]['state'] for r in rows)
    assert all(r['jurisdiction'] == expected[r['sequence']]['jurisdiction'] for r in rows)
    (ROOT / 'results43.json').write_text(json.dumps(rows, indent=2, ensure_ascii=False) + '\n')
    summary = {
        'as_of': '2026-10-17', 'scope_count': len(rows),
        'status_counts': dict(collections.Counter(r['status'] for r in rows)),
        'publisher_download_counts': dict(collections.Counter(r['publisher_download']['status'] for r in rows)),
        'complete_corpus_count': sum(r.get('complete_corpus') is True for r in rows),
        'groups': {g: dict(collections.Counter(r['status'] for r in rows if r['working_directory'] == g)) for g in GROUPS},
        'definitions': {
            'standalone_e2e_pass': 'Live acquisition through parsed normalized output for the stated bounded sample; no Codex runtime required.',
            'standalone_partial': 'A material acquisition or parsing limitation remains; read the row before running at scale.',
            'publisher_download': 'Separate native-export transport outcome; passed does not mean a whole jurisdiction or current edition.',
            'complete_corpus': 'All publications, amendments, attachments and parsing completeness verified; never inferred from a sample.'
        }
    }
    (ROOT / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    lines = ['# Wave 3: 43 expanded jurisdictions — validation index', '',
             'Validated on 17 October 2026. Commands run from the row\'s working directory. The linked group README gives installation, fresh-output and offline replay instructions. Every result is bounded; publisher download status is separate from normalized sample status.', '',
             '| # | Jurisdiction | State | Sample result | Native download | Group / instructions |',
             '|---:|---|---|---|---|---|']
    for r in rows:
        lines.append(f"| {r['sequence']} | {r['jurisdiction']} | {r['state']} | {r['status']} | {r['publisher_download']['status']} | [{r['working_directory']}]({r['group_report']}) |")
    lines += ['', 'For precise tested scope, commands, evidence paths, publication gaps and next actions, see [results43.json](results43.json). Record and table counts have different units across HTML and PDF methods and should not be summed as a legal-section coverage measure.', '']
    (ROOT / 'JURISDICTIONS.md').write_text('\n'.join(lines))
    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    main()
