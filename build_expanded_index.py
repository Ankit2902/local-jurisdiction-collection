#!/usr/bin/env python3
"""Join the frozen 100-target discovery scope to the sealed validation reports."""
import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PACKAGES = ['expanded57-validation-2026-10-17', 'wave3-validation-2026-10-17']

def main():
    scope = json.loads((ROOT / 'packages/local-jurisdiction-expansion-2026-10-17/recommendations.json').read_text())['recommendations']
    expected = {r['sequence']: r for r in scope}
    results = {}
    for package, name in zip(PACKAGES, ['results57.json', 'results43.json']):
        for row in json.loads((ROOT / 'packages' / package / name).read_text()):
            seq = row['sequence']
            assert seq not in results and row['state'] == expected[seq]['state']
            results[seq] = (package, row)
    assert sorted(expected) == sorted(results) == list(range(1, 101))
    rows = []
    for seq, original in sorted(expected.items()):
        package, result = results[seq]
        rows.append({
            'sequence': seq, 'wave': original['collection_wave'],
            'jurisdiction': original['jurisdiction'], 'state': original['state'],
            'selection_rationale': original['selection_rationale'],
            'discovery_source_family': original['source_family'],
            'validated_source_family': result['source_family'],
            'validated_source_url': result['source_url'],
            'sample_status': result['status'],
            'publisher_download_status': result['publisher_download']['status'],
            'complete_corpus': result['complete_corpus'],
            'tested_scope': result['tested_scope'],
            'limitations': result['limitations'], 'next_action': result['next_action'],
            'instructions': 'packages/' + package + '/' + result['group_report'],
            'detailed_results': 'packages/' + package + ('/results57.json' if seq <= 57 else '/results43.json'),
            'working_directory': 'packages/' + package + '/' + result['working_directory'],
        })
    summary = {
        'targets': len(rows),
        'sample_status_counts': dict(collections.Counter(r['sample_status'] for r in rows)),
        'publisher_download_status_counts': dict(collections.Counter(r['publisher_download_status'] for r in rows)),
        'complete_corpus_count': sum(r['complete_corpus'] is True for r in rows),
    }
    (ROOT / 'expanded-scope-index.json').write_text(json.dumps({'summary': summary, 'jurisdictions': rows}, indent=2, ensure_ascii=False) + '\n')
    lines = ['# Expanded scope: all 100 validation results', '',
             'Selection order and wave come from the frozen recommendation inventory. Source families and outcomes come from the later live validation reports; routing migrations are preserved in those reports. All results are bounded samples. A publisher download pass is not proof of whole-code currency or complete ingestion.', '',
             '| # | Wave | Jurisdiction | State | Sample | Publisher download | Instructions |',
             '|---:|---:|---|---|---|---|---|']
    for r in rows:
        lines.append(f"| {r['sequence']} | {r['wave']} | {r['jurisdiction']} | {r['state']} | {r['sample_status']} | {r['publisher_download_status']} | [Runbook]({r['instructions']}) |")
    lines += ['', 'The [machine-readable index](expanded-scope-index.json) includes selection rationale, tested scope, limitations and next actions. Exact commands, evidence paths and checks are in each linked package’s detailed results. Record counts are intentionally not added across incompatible units such as PDF pages and HTML provisions.', '']
    (ROOT / 'EXPANDED-SCOPE.md').write_text('\n'.join(lines))
    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    main()
