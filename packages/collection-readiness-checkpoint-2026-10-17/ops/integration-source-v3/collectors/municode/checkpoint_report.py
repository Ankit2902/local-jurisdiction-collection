"""Read-only source-bound progress snapshot; never promotes pending/incomplete books."""
import sys
sys.dont_write_bytecode = True
import argparse, collections, datetime, hashlib, json, os
from pathlib import Path
from model import RUNTIME_FILES

HERE = Path(__file__).resolve().parent
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):
    return json.loads(path.read_text())
def report(batch, evidence_root):
    batch = batch.resolve(); evidence_root = evidence_root.resolve()
    status_path = batch / 'status.json'; status_bytes = status_path.read_bytes(); status = json.loads(status_bytes)
    relative = lambda p: os.path.relpath(p, evidence_root)
    jobs = []
    for key, job in status['jobs'].items():
        run = (batch / job['run_path']).resolve()
        item = {k: job.get(k) for k in ['publication_id', 'target_id', 'product_id', 'role', 'source_url', 'status', 'evidence_origin', 'full_publication_live_verified', 'exit_code', 'verification_exit_code']}
        item['run_path'] = relative(run)
        if (run / 'checkpoint.json').exists():
            cp = read(run / 'checkpoint.json'); implementation = cp['binding']['implementation']
            item['checkpoint_sha256'] = sha(run / 'checkpoint.json')
            item['source_binding'] = {k: cp['binding'].get(k) for k in ['source_url', 'client_names', 'state', 'expected_client_id', 'product_ids', 'reference_policy']}
            item['executed_implementation'] = implementation
            item['executed_sources_match'] = all((run / 'executed-sources' / digest / name).is_file() and sha(run / 'executed-sources' / digest / name) == digest for name, digest in implementation.items())
            item['checkpoint_phase_at_snapshot'] = cp['phase']
            item['publications'] = []
            for pid, publication in cp.get('publications', {}).items():
                path = run / 'publications' / pid / 'coverage.json'
                if not path.exists():
                    continue
                coverage = read(path)
                compact = {k: v for k, v in coverage.items() if not isinstance(v, (dict, list))}
                for k in ['missing_ids', 'duplicate_ids', 'extra_ids', 'justified_exclusions', 'errors', 'asset_failures']:
                    compact[k] = coverage.get(k)
                item['publications'].append({'product_id': int(pid), 'job_id': publication['job_id'], 'toc_hash': publication['toc_hash'], 'coverage_path': relative(path), 'coverage_sha256': sha(path), 'coverage': compact})
        jobs.append(item)
    files = [*RUNTIME_FILES, 'batch.py', 'export.py', 'requirements.txt', 'package.json', 'package-lock.json']
    return {
        'schema_version': 2, 'frozen': False, 'goal_active': True,
        'generated_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'implementation_status': 'Serialized full-publication live validation in progress; pending and incomplete configurations remain unqualified.',
        'evidence_path_base': 'Relative to collection-readiness-2026-10-17 package root',
        'batch_status': relative(status_path), 'batch_status_sha256': hashlib.sha256(status_bytes).hexdigest(),
        'batch_phase': status['phase'], 'dispatchable_configuration_count': len(jobs),
        'status_counts': dict(collections.Counter(j['status'] for j in jobs)),
        'publication_complete_count': sum(j['status'] == 'complete' and j['full_publication_live_verified'] is True for j in jobs),
        'all_configurations_complete': all(j['status'] == 'complete' and j['full_publication_live_verified'] is True for j in jobs),
        'jurisdiction_complete': False,
        'current_implementation': {name: sha(HERE / name) for name in files},
        'runtime': status['runtime'],
        'qa_artifacts': {str(p.relative_to(HERE)): sha(p) for p in sorted(HERE.glob('proof-receipts/*.json'))},
        'batch_executed_source': {'sha256': status['binding']['batch_sha256'], 'path': relative(batch / 'executed-batch' / status['binding']['batch_sha256'] / 'batch.py')},
        'image_policy': {'separate_image_downloads': False, 'placeholder': '[IMAGE]', 'inline_data_metadata': 'MIME, source locator, SHA256 and character count only; full payload confined to original source', 'image_contents_transcribed': False},
        'verification': 'Each complete job passed current read-only verifier. Exact acquisition module bytes are retained per child; a current hash does not retroactively describe an earlier child.',
        'remaining_gaps': ['Unstarted and active configurations require publication-wide live acquisition and verification.', 'Unexplained empty source bodies fail closed; exact independently corroborated grouping labels are under review, without a generic heading exemption.', 'Required nonimage attachments, unsupported formats and unknown external references can still block individual books.', 'A complete native PDF file is not segmented legal-text completeness or whole-jurisdiction completeness.'],
        'jobs': jobs,
    }
def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--batch', type=Path, required=True); p.add_argument('--evidence-root', type=Path, required=True); p.add_argument('--out', type=Path)
    a = p.parse_args(); data = json.dumps(report(a.batch, a.evidence_root), indent=2) + '\n'
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True); a.out.write_text(data)
    else:
        print(data, end='')
if __name__ == '__main__':
    main()
