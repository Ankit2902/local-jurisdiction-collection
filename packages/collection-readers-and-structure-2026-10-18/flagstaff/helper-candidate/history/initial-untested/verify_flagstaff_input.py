"""Create portable Flagstaff corpus proof through the selected common verifier.

No acquisition, upgrade or source normalization is requested. The common verifier
performs its standard read-only raw replay. Original receipt/report bytes are
preserved; a derivative receipt adds only safe relative report selection.
"""
import sys
sys.dont_write_bytecode = True
import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

TARGET = 'original-flagstaff-az'
PUBLICATION = TARGET + '-primary'
SOURCE = 'https://www.codepublishing.com/AZ/Flagstaff/'

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()

def require(condition, message):
    if not condition:
        raise ValueError(message)

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def disjoint(a, b):
    return not a.is_relative_to(b) and not b.is_relative_to(a)

def files(root):
    result = {}
    for path in sorted(root.rglob('*')):
        require(not path.is_symlink(), 'Symlink evidence is unsupported')
        if path.is_file():
            result[path.relative_to(root).as_posix()] = sha(path)
    return result

def run(source, collector, runtime, out):
    for path in (source, collector, runtime):
        require(not path.is_symlink(), 'Symlink root is unsupported')
    source, collector, runtime, out = (p.resolve() for p in (source, collector, runtime, out))
    require(source.is_dir() and collector.is_dir() and runtime.is_dir(), 'Existing input, collector and runtime directories required')
    require(not out.exists() and all(disjoint(out, p) for p in (source, collector, runtime)), 'Fresh output disjoint from input, collector and runtime required')
    entry = collector / 'collect.py'
    require(entry.is_file() and (collector / 'collectors/ops/launcher.py').is_file(), 'collector-root must be the repository containing the common launcher')
    cfg = load(source / 'checkpoint.json').get('config', {})
    require(cfg.get('profile') == 'flagstaff_html' and cfg.get('target_id') == TARGET and cfg.get('source_url') == SOURCE and cfg.get('required_formats') == ['html'], 'Only the exact Flagstaff primary HTML profile is supported')
    runtime_receipt = runtime / 'runtime.json'
    require(runtime_receipt.is_file(), 'Run common runtime setup first')
    before = files(source)
    require(before, 'Empty input')
    runtime_sha = sha(runtime_receipt)
    helper_sha = sha(Path(__file__))
    argv = [sys.executable, '-B', str(entry), '--runtime', str(runtime), 'verify', '--target', TARGET, '--publication', PUBLICATION, '--out', str(source)]
    out.mkdir(parents=True)
    (out / 'invocation.json').write_bytes(encoded({'argv': argv, 'input': str(source), 'collector_root': str(collector), 'runtime': str(runtime), 'helper_sha256': helper_sha, 'action': 'verify only; no acquisition or upgrade'}))
    try:
        result = subprocess.run(argv, cwd=collector, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), capture_output=True)
        (out / 'common-readonly.json').write_bytes(result.stdout)
        (out / 'common.stderr').write_bytes(result.stderr)
        require(result.returncode in (0, 2), 'Common verification failed; see retained stdout/stderr')
        receipt = json.loads(result.stdout)
        require(receipt.get('publication_id') == PUBLICATION and receipt.get('selected_config') == cfg, 'Common verification selected another publication/config')
        require(Path(receipt.get('output', '')).resolve() == source, 'Common verification input mismatch')
        require(receipt.get('verification_exit') in (0, 2), 'Family verification did not return a valid complete/incomplete result')
        require(receipt.get('evidence_read_only') is True and receipt.get('publisher_requests') == 0 and receipt.get('source_changed_during_run') is False and receipt.get('runtime_changed_during_run') is False, 'Common verification is not unchanged/read-only')
        after = files(source)
        require(before == after == receipt.get('evidence_sha256_before') == receipt.get('evidence_sha256_after'), 'Input evidence changed or proof map mismatched')
        sources = receipt.get('collector_sources_before')
        require(isinstance(sources, dict) and sources and sources == receipt.get('collector_sources_after'), 'Missing or changed collector source binding')
        for name, expected in sources.items():
            rel = Path(name)
            require(not rel.is_absolute() and '..' not in rel.parts, 'Unsafe collector source reference')
            path = collector / rel
            require(path.resolve().is_relative_to(collector) and path.is_file() and sha(path) == expected, 'Selected collector source changed')
        require(receipt.get('runtime_receipt_sha256') == runtime_sha == sha(runtime_receipt), 'Runtime receipt changed')
        require(Path(receipt.get('runtime_receipt_path', '')).resolve() == runtime_receipt, 'Common verification used another runtime')
        log = Path(receipt.get('log', ''))
        require(log.is_absolute() and not log.is_symlink() and log.resolve().is_relative_to(runtime / 'verifications') and log.is_file(), 'Family report must be a real log inside the selected runtime verification directory')
        family_bytes = log.read_bytes()
        family = json.loads(family_bytes)
        require(isinstance(family, dict) and family.get('full_raw_replay_equal') is True and family.get('input_files_modified') is False and family.get('source_route_ledger_verified') is True and family.get('opening_body_closing_chronology_verified') is True, 'Family raw replay/route/chronology is not qualified')
        require(family.get('publication_config') == cfg, 'Family report configuration differs')
        require(sha(Path(__file__)) == helper_sha, 'Helper source changed')
        (out / 'family-verification.json').write_bytes(family_bytes)
        proof = dict(receipt)
        proof.update(family_verification_path='family-verification.json', family_verification_sha256=hashlib.sha256(family_bytes).hexdigest(), proof_origin={'original_common_receipt_path': 'common-readonly.json', 'original_common_receipt_sha256': hashlib.sha256(result.stdout).hexdigest(), 'derivative_changes': ['relative family report path', 'family report SHA256', 'this lineage object'], 'original_common_receipt_unchanged': True})
        (out / 'read-only-proof.json').write_bytes(encoded(proof))
        terminal = {'verification_adapter_complete': True, 'common_exit': result.returncode, 'publication_id': PUBLICATION, 'primary_publication_accepted': receipt.get('acceptance', {}).get('publication_accepted'), 'jurisdiction_complete': receipt.get('acceptance', {}).get('jurisdiction_complete'), 'publication_acceptance_added': False, 'source_files': len(before), 'collector_sources': len(sources), 'source_unchanged': True, 'publisher_requests': 0, 'proof': 'read-only-proof.json', 'family_report': 'family-verification.json', 'runtime_receipt_sha256': runtime_sha, 'helper_sha256': helper_sha}
        (out / 'terminal.json').write_bytes(encoded(terminal))
        return terminal
    except BaseException as error:
        failure = {'verification_adapter_complete': False, 'error': type(error).__name__ + ': ' + str(error), 'input_unchanged': files(source) == before, 'runtime_receipt_unchanged': sha(runtime_receipt) == runtime_sha, 'source_not_deleted_or_rewritten': True}
        (out / 'verification-failure.json').write_bytes(encoded(failure))
        raise

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--collector-root', required=True, type=Path)
    parser.add_argument('--runtime', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(run(args.input, args.collector_root, args.runtime, args.out), indent=2))
        return 0
    except Exception as error:
        print(json.dumps({'verification_adapter_complete': False, 'error': type(error).__name__ + ': ' + str(error)}))
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
