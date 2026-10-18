"""Owned runtime and explicit publication jobs. No publisher access during setup/doctor."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DEFAULT_RUNTIME = ROOT / '.collection-runtime'
MARKER = 'local-jurisdiction-collection-runtime-v1'
FAMILIES = ('municode', 'american-legal', 'ecode', 'encodeplus', 'official', 'gridics')
STATE_ROOT = Path.home() / '.local' / 'state' / 'local-jurisdiction-collection'


class OperationError(Exception):
    pass


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp-' + str(os.getpid()))
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    os.replace(temporary, path)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def driver_hashes(node):
    driver = Path(node).parent
    files = [Path(node)] + [p for p in (driver / 'package').rglob('*') if p.is_file()]
    return {str(p.relative_to(driver)): sha(p) for p in sorted(files)}


def shim_hashes(runtime):
    runtime = Path(runtime)
    names = ('package.json', 'node_modules/playwright/package.json', 'node_modules/playwright/index.cjs')
    return {name: sha(runtime / name) for name in names}


def package_versions(packages):
    return {p['name'].lower().replace('_', '-'): p['version'] for p in packages}


def check_pins(packages):
    actual = package_versions(packages)
    for line in (HERE / 'requirements.txt').read_text().splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        name, version = line.strip().split('==')
        if actual.get(name.lower().replace('_', '-')) != version:
            raise OperationError('Installed dependency does not match the lock: ' + line + '. Rerun setup.')


def captured(argv, env=None, cwd=ROOT, timeout=120):
    result = subprocess.run([str(x) for x in argv], cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise OperationError('Command failed: ' + str(argv[0]) + '\n' + result.stderr[-4000:] + result.stdout[-1000:])
    return result.stdout


def runtime_paths(runtime):
    runtime = Path(runtime).resolve()
    return runtime, runtime / 'venv' / 'bin' / 'python'


def runtime_env(runtime):
    runtime, python = runtime_paths(runtime)
    receipt = read(runtime / 'runtime.json')
    if receipt.get('owner') != MARKER:
        raise OperationError('This directory is not an owned collection runtime. Run setup with a fresh path.')
    if not python.is_file():
        raise OperationError('Runtime Python is missing. Run setup again in the same owned directory.')
    # Ask the installed distribution for its own bundled driver; never choose system Node.
    driver = Path(captured([python, '-c', 'import pathlib,playwright;print(pathlib.Path(playwright.__file__).parent / "driver")']).strip())
    node = driver / 'node'
    if not node.is_file() or not (driver / 'package' / 'index.js').is_file():
        raise OperationError('The pinned Playwright wheel lacks its Node driver/API package.')
    env = dict(os.environ)
    env.update(PYTHON=str(python), NODE=str(node), NODE_BIN=str(node),
               COLLECTION_PLAYWRIGHT_CORE=str(driver / 'package'),
               PLAYWRIGHT_MODULE_ROOT=str(runtime / 'package.json'),
               NODE_PATH=str(runtime / 'node_modules'), PYTHONDONTWRITEBYTECODE='1')
    env['PATH'] = str(python.parent) + os.pathsep + str(driver) + os.pathsep + env.get('PATH', '')
    return python, node, env


def interpreter_version(python):
    version = json.loads(captured([python, '-c', 'import sys,json;print(json.dumps(list(sys.version_info[:3])))']))
    if not isinstance(version, list) or len(version) != 3 or any(type(part) is not int or part < 0 for part in version):
        raise OperationError('Python interpreter did not report a valid version triplet.')
    return version


def setup(runtime, python_command):
    if os.name != 'posix':
        raise OperationError('Current publisher gates require POSIX file locks. Use a macOS or Linux graphical host; Windows is not yet qualified.')
    runtime, python = runtime_paths(runtime)
    version = interpreter_version(python_command)
    if version[:2] != [3, 12]:
        raise OperationError('The integrated runtime is pinned to Python 3.12. Pass --python /path/to/python3.12.')
    marker = runtime / 'runtime.json'
    if runtime.exists() and any(runtime.iterdir()) and (not marker.is_file() or read(marker).get('owner') != MARKER):
        raise OperationError('Refusing to modify a nonempty directory not owned by this setup: ' + str(runtime))
    runtime.mkdir(parents=True, exist_ok=True)
    previous = read(marker) if marker.exists() else {}
    save(marker, dict(previous, owner=MARKER, setup_complete=False, updated_at=now()))
    if not python.exists():
        subprocess.run([python_command, '-m', 'venv', str(runtime / 'venv')], check=True)
    owned_version = interpreter_version(python)
    if owned_version[:2] != [3, 12]:
        raise OperationError('Owned runtime Python is not 3.12. Use a fresh runtime directory with Python 3.12; setup will not replace an existing interpreter.')
    log_path = runtime / 'install.log'
    print('Installing the pinned runtime. Log: ' + str(log_path), flush=True)
    with log_path.open('a') as log:
        result = subprocess.run([str(python), '-m', 'pip', 'install', '--disable-pip-version-check', '-r', str(HERE / 'requirements.txt')], stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise OperationError('Dependency installation failed. Inspect ' + str(log_path) + '; rerunning setup resumes the owned environment.')
    captured([python, '-m', 'pip', 'check'])
    # Existing collectors require the name "playwright". This small module forwards
    # that public API to the official playwright-core bundled in the pinned Python
    # wheel, keeping Python and Node browser clients on the same shipped revision.
    module = runtime / 'node_modules' / 'playwright'
    module.mkdir(parents=True, exist_ok=True)
    save(runtime / 'package.json', {'name': 'local-collection-runtime', 'private': True})
    python, node, env = runtime_env(runtime)
    core_metadata = read(Path(node).parent / 'package' / 'package.json')
    save(module / 'package.json', {'name': 'playwright', 'version': core_metadata['version'], 'private': True, 'main': 'index.cjs'})
    (module / 'index.cjs').write_text("module.exports = require(process.env.COLLECTION_PLAYWRIGHT_CORE);\n")
    browser = json.loads(captured([node, HERE / 'browser_check.cjs'], env=env))
    packages = json.loads(captured([python, '-m', 'pip', 'list', '--format=json']))
    check_pins(packages)
    receipt = dict(owner=MARKER, setup_complete=True, created_at=previous.get('created_at', now()),
                   updated_at=now(), python=str(python), python_version=owned_version, setup_python_version=version,
                   node=str(node), node_version=captured([node, '--version']).strip(),
                   requirements_sha256=sha(HERE / 'requirements.txt'), packages=packages,
                   shim_sha256=shim_hashes(runtime),
                   browser_driver_sha256=driver_hashes(node),
                   browser=browser, publisher_requests=0,
                   runtime_note='Node and playwright-core are supplied by the pinned official Python Playwright wheel.')
    save(marker, receipt)
    return receipt


def registry_plan(target, publication, python):
    argv = [python, '-B', ROOT / 'collectors/registry/collect.py', 'plan', '--target', target, '--python', python]
    if publication:
        argv += ['--publication', publication]
    plans = json.loads(captured(argv))['plans']
    if len(plans) != 1 or not plans[0].get('runnable'):
        raise OperationError('Publication is not runnable: ' + json.dumps(plans))
    return plans[0]


def catalog_publication(publication_id):
    path = ROOT / 'collectors/registry/catalog.py'
    spec = importlib.util.spec_from_file_location('collection_catalog', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for item in module.load_catalog()['publications']:
        if item['id'] == publication_id:
            return item
    raise OperationError('Publication missing from catalog: ' + publication_id)


def referenced_hosts(pub, output=None):
    hosts = set()
    def visit(value):
        if isinstance(value, str) and value.startswith(('http://', 'https://')):
            host = urlsplit(value).hostname
            if host:
                hosts.add(host)
        elif isinstance(value, dict):
            for key, child in value.items():
                visit(key)
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    visit(pub.get('source_url'))
    for key in ('adapter_config', 'dispatch_config'):
        config = pub.get(key) or {}
        for name in ('source_url', 'base', 'documents', 'files'):
            visit(config.get(name))
    if output:
        paths = [Path(output) / 'coverage.json']
        paths += list((Path(output) / 'publications').glob('*/coverage.json'))
        for path in paths:
            if path.is_file():
                coverage = read(path)
                for key in ('unresolved_required_assets', 'required_assets_unresolved', 'missing_assets', 'required_components_unresolved', 'required_assets'):
                    visit(coverage.get(key))
                for asset in coverage.get('assets', []) if isinstance(coverage.get('assets'), list) else []:
                    if isinstance(asset, dict) and asset.get('required') is True:
                        visit(asset.get('url'))
    return hosts


def access_state(pub, env, output=None):
    """Read the same shared gate as the adapter; never reset, create or relocate it."""
    family = pub['publisher']
    paths = []
    host_by_path = {}
    hosts = referenced_hosts(pub, output)
    if family == 'municode':
        gate = Path(env.get('MUNICODE_GATE_DIR', '/tmp/compliSolv-municode-rate-gate'))
        paths = [gate / 'browser-stop.json', gate / 'state.json']
        paths += [gate / ('external-stop-' + hashlib.sha256(host.encode()).hexdigest() + '.json') for host in hosts]
    elif family == 'american-legal':
        paths = [Path(env.get('AMLEGAL_GATE_DIR', '/tmp/compliSolv-american-legal-full-gate')) / 'browser-stop.json']
    elif family == 'ecode':
        paths = [Path(env.get('ICC_GATE_DIR', '/tmp/complisolv-icc-full-gate')) / pub['source_family'] / 'STOP.json']
    elif family == 'encodeplus':
        gate = Path(env.get('ENCODEPLUS_GATE_DIR', '/tmp/compliSolv-encodeplus-rate-gate'))
        paths = [gate / 'state.json']
        for host in hosts:
            path = gate / 'hosts' / hashlib.sha256(host.encode()).hexdigest() / 'state.json'
            paths.append(path)
            host_by_path[path] = host
    elif family == 'official':
        paths = [Path(env.get('OFFICIAL_GATE_DIR', '/tmp/compliSolv-official-publication-gate')) / hashlib.sha256(host.encode()).hexdigest()[:20] / 'state.json' for host in hosts]
    elif family == 'gridics':
        paths = [Path.home() / '.local/state/local-jurisdiction-collection/gridics/STOP.json']
    stops = []
    for path in paths:
        if not path.exists():
            continue
        data = read(path)
        blocked = path.name in ('STOP.json', 'browser-stop.json') or path.name.startswith('external-stop-') or data.get('stop') or data.get('stopped') or data.get('cooldown_until', 0) > time.time()
        if family == 'municode' and path.name == 'state.json':
            blocked = data.get('browser_access_stop') or (data.get('family_stop') and not data.get('browser_workflow_authorized')) or max(data.get('actual_rate_limit_until', 0), 0 if data.get('family_stop') else data.get('cooldown_until', 0)) > time.time()
        if blocked:
            stops.append({'path': str(path), 'state': data, 'scope_host': host_by_path.get(path)})
    # A fresh checkout must not forget checkpoint-observed access refusals merely
    # because the original host's /tmp or home-state files are absent.
    for advisory in pub.get('observed_access_advisories', []):
        if advisory.get('operator_review_required'):
            stops.append({'path': str(ROOT / 'collectors/registry/access-advisories.json'),
                          'state': {'stop': True, 'operator_release_required': True,
                                    'reason': advisory['reason'], 'observed_stop': advisory['observed_stop']},
                          'checkpoint_access_advisory': True})
    return retained_stops(pub, output, stops)


def retained_stops(pub, output, observed):
    """Mirror observed refusals durably without moving/changing active family gates.

    This prevents a reboot or a fresh output directory from erasing a refusal.
    Temporary enCodePlus cooldowns retain their original expiry; operator-release
    stops never expire automatically. No function here clears a gate or a mirror.
    """
    import fcntl
    family = pub['publisher']
    subfamily = pub.get('source_family', family) if family == 'ecode' else family
    relevant = referenced_hosts(pub, output)
    STATE_ROOT.mkdir(parents=True, exist_ok=True)
    path = STATE_ROOT / 'observed-access-stops.json'
    with (STATE_ROOT / 'observed-access-stops.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        ledger = read(path) if path.exists() else {'schema_version': 1, 'stops': {}}
        changed = False
        for item in observed:
            raw = item['state']
            source_path = Path(item['path'])
            detail = raw.get('stop') or raw.get('stop_reason') or raw
            host = item.get('scope_host')
            if family == 'official' or source_path.name.startswith('external-stop-') or 'hosts' in source_path.parts:
                host = host or detail.get('host') or urlsplit(detail.get('url', '')).hostname
            key = subfamily + ':' + (host or 'publisher')
            permanent = source_path.name in ('STOP.json', 'browser-stop.json') or source_path.name.startswith('external-stop-') or bool(raw.get('stop') or raw.get('stopped') or raw.get('browser_access_stop') or (raw.get('family_stop') and not raw.get('browser_workflow_authorized')))
            old = ledger['stops'].get(key)
            expires = None if permanent or (old and old['expires_at'] is None) else max(raw.get('cooldown_until', 0), old['expires_at'] if old else 0)
            value = {'family': family, 'subfamily': subfamily, 'host': host, 'expires_at': expires, 'source': item, 'first_observed_at': old['first_observed_at'] if old else now()}
            if old != value:
                ledger['stops'][key] = value
                changed = True
        if changed:
            save(path, ledger)
        result = list(observed)
        for key, item in ledger['stops'].items():
            if item['subfamily'] != subfamily or (item['host'] and item['host'] not in relevant):
                continue
            if item['expires_at'] is not None and item['expires_at'] <= time.time():
                continue
            if not any(x['path'] == item['source']['path'] for x in observed):
                result.append({'path': str(path), 'ledger_key': key, 'state': item, 'retained_after_original_gate_missing': True})
        return result


def doctor(runtime, target=None, publication=None, browser=False, output=None):
    runtime = Path(runtime).resolve()
    issues = []
    try:
        python, node, env = runtime_env(runtime)
        receipt = read(runtime / 'runtime.json')
        owned_version = interpreter_version(python)
        if owned_version[:2] != [3, 12]:
            issues.append('Owned runtime Python is not 3.12; use a fresh runtime directory created with Python 3.12.')
        if receipt.get('python_version') != owned_version:
            issues.append('Owned runtime Python version differs from the setup receipt; rerun setup before acquisition.')
        if not receipt.get('setup_complete'):
            issues.append('Setup did not finish; rerun setup.')
        if receipt.get('requirements_sha256') != sha(HERE / 'requirements.txt'):
            issues.append('Dependency lock changed; rerun setup before acquisition.')
        captured([python, '-m', 'pip', 'check'])
        installed = json.loads(captured([python, '-m', 'pip', 'list', '--format=json']))
        check_pins(installed)
        if package_versions(installed) != package_versions(receipt['packages']):
            issues.append('Installed package versions differ from the setup receipt; rerun setup.')
        if receipt.get('browser_driver_sha256') != driver_hashes(node):
            issues.append('Bundled browser driver bytes differ from the setup receipt; rerun setup.')
        if receipt.get('shim_sha256') != shim_hashes(runtime):
            issues.append('Owned Playwright alias bytes differ from the setup receipt; rerun setup.')
        report = {'runtime': str(runtime), 'python': str(python), 'node': str(node), 'publisher_requests': 0, 'runtime_ready': not issues, 'readiness_level': 'runtime_and_access_preflight_only', 'full_publication_validation_claimed': False}
        if browser and not issues:
            report['browser'] = json.loads(captured([node, HERE / 'browser_check.cjs'], env=env))
        elif browser:
            report['browser_skipped'] = 'Runtime integrity must pass before executing the browser alias'
        if target:
            plan = registry_plan(target, publication, python)
            report['plan'] = plan
            report['access_stops'] = access_state(catalog_publication(plan['publication_id']), env, output)
            if report['access_stops']:
                issues.append('Publisher access is stopped. Retain the stop and follow the publisher recovery/export instructions; no automatic retry is made.')
    except (OSError, ValueError, OperationError, subprocess.TimeoutExpired) as error:
        report = {'runtime': str(runtime), 'publisher_requests': 0, 'runtime_ready': False}
        issues.append(str(error))
    report.update(ready=not issues, issues=issues)
    return report


def code_binding(family):
    if family not in FAMILIES + ('originals',):
        raise OperationError('Unknown collector implementation: ' + str(family))
    files = [ROOT / 'collectors/registry' / name for name in ('collect.py', 'dispatch.py', 'catalog.py') if (ROOT / 'collectors/registry' / name).is_file()]
    files += [HERE / 'launcher.py', HERE / 'browser_check.cjs', HERE / 'requirements.txt']
    if (ROOT / 'collect.py').is_file():
        files += [ROOT / 'collect.py']
    files += [p for p in (ROOT / 'collectors' / family).glob('*') if p.suffix in ('.py', '.cjs')]
    files += [p for folder in ('configs', 'policies') for p in (ROOT / 'collectors' / family / folder).rglob('*.json')]
    if family == 'encodeplus':
        files.append(ROOT / 'collectors/encodeplus/targets.json')
        files.append(ROOT / 'collectors/encodeplus/infrastructure-multiline-native-geometry.json')
    if family == 'originals':
        # Source character/ownership profiles are parser inputs, not optional
        # reports. Bind them alongside the original-source adapter modules.
        files += list((ROOT / 'collectors' / family).glob('*.json'))
        files += list((ROOT / 'collectors' / family / 'profiles').rglob('*.json'))
    files += [p for p in (ROOT / 'collectors/registry').glob('*.json') if p.name not in ('source-evidence-manifest.json', 'original-source-evidence-manifest.json', 'readiness-source-evidence-manifest.json')]
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(set(files))}


def selected_runtime_config(plan):
    if plan.get('qualified_config_path'):
        if plan.get('named_config_path'):
            raise OperationError('Ambiguous selected configuration source')
        return read(ROOT / plan['qualified_config_path'])
    if plan.get('named_config_path'):
        path = (ROOT / plan['named_config_path']).resolve()
        if path != (ROOT / 'collectors/encodeplus/targets.json').resolve():
            raise OperationError('Unexpected named enCodePlus configuration file')
        configurations = read(path)
        key = plan.get('named_config_key')
        if not isinstance(configurations, dict) or key not in configurations or not isinstance(configurations[key], dict):
            raise OperationError('Selected named enCodePlus configuration is missing')
        return configurations[key]
    return plan.get('staged_config')


def implementation_family(pub):
    family = pub.get('adapter_family', pub['publisher'])
    if family == 'originals' and pub['publisher'] != 'official':
        raise OperationError('Original-source adapters require the official-source access gate')
    return family


def job_paths(out):
    out = Path(out).resolve()
    key = hashlib.sha256(str(out).encode()).hexdigest()[:16]
    folder = out.parent / '.collection-jobs' / key
    return out, folder, folder / 'job.json'


def dependency_inputs(values, pub):
    """Only exact catalog dependency IDs may supply proof paths; never URLs."""
    supplied = {}
    for value in values or []:
        if '=' not in value:
            raise OperationError('--dependency requires PUBLICATION_ID=/path/to/proof')
        ident, path = value.split('=', 1)
        if not ident or not path or ident in supplied:
            raise OperationError('Empty or duplicate dependency proof: ' + ident)
        supplied[ident] = str(Path(path).resolve())
    allowed = set()
    def walk(item, ancestry):
        for ident in item.get('required_publication_dependencies', []):
            if ident in ancestry:
                raise OperationError('Cyclic required publication dependency: ' + ident)
            if ident not in allowed:
                allowed.add(ident)
                walk(catalog_publication(ident), ancestry + [ident])
    walk(pub, [pub['id']])
    if set(supplied) - allowed:
        raise OperationError('Proof is not a required dependency of this publication: ' + ', '.join(sorted(set(supplied) - allowed)))
    return supplied


def evidence_hashes(output):
    """Bind the independently reverified proof, detecting concurrent mutation."""
    output = Path(output).resolve()
    if not output.is_dir():
        raise OperationError('Dependency proof directory is missing: ' + str(output))
    result = {}
    for path in sorted(output.rglob('*')):
        if path.is_symlink():
            raise OperationError('Dependency evidence contains a symbolic link: ' + str(path))
        if path.is_file():
            result[str(path.relative_to(output))] = sha(path)
    return result


def verify_dependencies(runtime, pub, proofs, ancestry):
    reports = []
    for ident in pub.get('required_publication_dependencies', []):
        if ident not in proofs:
            reports.append({'publication_id': ident, 'accepted': False, 'reason': 'No explicit --dependency proof path supplied'})
            continue
        if ident in ancestry:
            raise OperationError('Cyclic required publication dependency: ' + ident)
        dependency = catalog_publication(ident)
        output = Path(proofs[ident]).resolve()
        try:
            before = evidence_hashes(output)
            code, verification = execute_job(runtime, dependency['target_id'], ident, output,
                                            verify_only=True, dependency_proofs=proofs,
                                            _dependency_ancestry=ancestry + [ident])
            after = evidence_hashes(output)
            accepted = code == 0 and verification.get('acceptance', {}).get('publication_accepted') is True and before == after
            reports.append({'publication_id': ident, 'output': str(output), 'accepted': accepted,
                            'current_verification': verification, 'evidence_sha256': before,
                            'evidence_unchanged': before == after,
                            'reason': None if accepted else 'Dependency current offline verification, scope acceptance or immutable evidence binding failed'})
        except (OperationError, OSError, ValueError, KeyError) as error:
            reports.append({'publication_id': ident, 'output': str(output), 'accepted': False, 'reason': str(error)})
    return reports


def publication_acceptance(pub, output, dependencies=None):
    """Interpret explicit family coverage dimensions; exit zero alone proves no scope.

    Native-file/page validation is useful, but cannot satisfy a legal publication.
    Dependency books need explicit catalog-bound, current offline proof checks;
    a hyperlink or a dependency's cover is never proof of that book.
    """
    path = Path(output) / 'coverage.json'
    if not path.is_file():
        return {'publication_coverage_accepted': False, 'native_capture_verified': False,
                'acceptance_gaps': ['Missing coverage.json'],
                'unresolved_required_publication_dependencies': list(pub.get('required_publication_dependencies', []))}
    coverage = read(path)
    text = coverage.get('publication_text_complete') is True
    asset_field = {'municode': 'publication_attachments_complete',
                   'american-legal': 'attachment_complete', 'ecode': 'attachments_complete',
                   'encodeplus': 'attachments_complete', 'gridics': 'required_assets_complete'}.get(pub['publisher'])
    assets = coverage.get(asset_field) is True if asset_field else False
    semantic = True
    # Several adapters deliberately distinguish retained PDF/page bytes from
    # qualified legal text/table structure. Their explicit false dimensions
    # cannot disappear when an HTML parent and its required assets return zero.
    asset_integrity = coverage.get('asset_document_integrity', {})
    required_pdf_assets = {url: detail for url, detail in asset_integrity.items()
                           if isinstance(detail, dict) and str(detail.get('format', '')).upper() == 'PDF'} if isinstance(asset_integrity, dict) else {}
    pdf_present = bool(required_pdf_assets) or any(isinstance(coverage.get(key), (int, float)) and coverage.get(key) > 0 for key in
                      ('pdf_text_layer_pages_parsed', 'pdf_retained_asset_document_count',
                       'pdf_normalized_distinct_document_count'))
    pdf_dimensions = {}
    if pdf_present:
        for key in ('pdf_semantic_text_completeness_qualified', 'pdf_table_completeness_qualified'):
            if key in coverage:
                pdf_dimensions[key] = coverage[key]
        # Retained required PDFs are independently qualified documents, not
        # semantic credit supplied by their parent HTML or file integrity alone.
        for url, detail in required_pdf_assets.items():
            for key in ('pdf_semantic_text_completeness_qualified', 'pdf_table_completeness_qualified'):
                pdf_dimensions['asset_document_integrity[' + url + '].' + key] = detail.get(key)
        semantic = all(value is True for value in pdf_dimensions.values()) if pdf_dimensions else False
    details = coverage.get('pdf_details', {})
    if details.get('pages', 0) and 'pdf_table_semantics_complete' in details:
        pdf_dimensions['pdf_details.pdf_table_semantics_complete'] = details['pdf_table_semantics_complete']
        semantic = semantic and details['pdf_table_semantics_complete'] is True
    if pub['publisher'] == 'official':
        text = coverage.get('publication_html_text_coverage_complete') is True
        assets = (coverage.get('publication_file_coverage_complete') is True
                  and not coverage.get('required_assets_unresolved')
                  and not coverage.get('required_components_unresolved'))
        semantic = coverage.get('legal_semantic_coverage_complete') is True
    if pub.get('adapter_family') == 'originals':
        text = coverage.get('publication_text_complete') is True
        assets = coverage.get('attachments_complete') is True
        semantic = (coverage.get('legal_structure_qualified') is True
                    and coverage.get('source_consistency_complete') is True)
    # The integrity map contains required nonimage documents only. Unknown or
    # non-PDF formats need their own explicit text/structure qualification;
    # nonempty bytes, archive integrity or parent HTML are not that proof.
    nonpdf_dimensions = {}
    if isinstance(asset_integrity, dict):
        for url, detail in asset_integrity.items():
            if url in required_pdf_assets:
                continue
            detail = detail if isinstance(detail, dict) else {}
            for key in ('document_text_completeness_qualified', 'document_structure_completeness_qualified'):
                nonpdf_dimensions['asset_document_integrity[' + url + '].' + key] = detail.get(key)
    if nonpdf_dimensions:
        semantic = semantic and all(value is True for value in nonpdf_dimensions.values())
    native = any(coverage.get(key) is True for key in
                 ('native_document_complete', 'native_publication_files_complete',
                  'pdf_page_extraction_complete', 'publication_file_coverage_complete'))
    dependency_reports = dependencies or []
    accepted_dependencies = {p['publication_id'] for p in dependency_reports if p.get('accepted') is True}
    dependencies = [p for p in pub.get('required_publication_dependencies', []) if p not in accepted_dependencies]
    gaps = []
    if not text:
        gaps.append('Publication text coverage is not explicitly complete')
    if not assets:
        gaps.append('Required nonimage document coverage is not explicitly complete')
    if not semantic:
        gaps.append('Source format/legal structure remains unqualified for publication acceptance')
    if dependencies:
        gaps.append('Required separate publications lack bound verified dependency proofs')
    return {'publication_coverage_accepted': not gaps, 'publication_text_complete': text,
            'required_nonimage_documents_complete': assets,
            'legal_structure_qualified': semantic,
            'pdf_structure_dimensions': pdf_dimensions,
            'nonpdf_document_structure_dimensions': nonpdf_dimensions,
            'native_capture_verified': native,
            'edition_complete': coverage.get('edition_complete'),
            'unresolved_required_publication_dependencies': dependencies,
            'dependency_proofs': dependency_reports,
            'acceptance_gaps': gaps, 'coverage_sha256': sha(path),
            'jurisdiction_complete': False}


def execute_job(runtime, target, publication, output, verify_only=False, dependency_proofs=None, _dependency_ancestry=None, upgrade_code=False, native_export=None, retry_native_export=False):
    import fcntl
    python, node, env = runtime_env(runtime)
    plan = registry_plan(target, publication, python)
    pub = catalog_publication(plan['publication_id'])
    ep_html = pub['publisher'] == 'encodeplus' and pub.get('adapter_mode') != 'native_document'
    if upgrade_code and (verify_only or pub['publisher'] != 'encodeplus'):
        raise OperationError('Explicit code upgrade is supported only for an existing bound enCodePlus job')
    if native_export and (verify_only or not ep_html):
        raise OperationError('Native export is supported only for enCodePlus HTML publications')
    if retry_native_export and (verify_only or not ep_html or native_export is not True):
        raise OperationError('Explicit native retry requires an existing enCodePlus HTML job and --native-export')
    dependency_proofs = dependency_proofs or {}
    ancestry = _dependency_ancestry or [pub['id']]
    if not _dependency_ancestry:
        dependency_inputs([ident + '=' + str(path) for ident, path in dependency_proofs.items()], pub)
    out, folder, metadata = job_paths(output)
    if verify_only:
        # Verification can read sealed/legacy evidence. Its logs live in the owned
        # runtime, never beside or within the evidence being checked.
        health = doctor(runtime)
        if not health.get('runtime_ready'):
            raise OperationError('Runtime verification failed: ' + '; '.join(health['issues']))
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f')
        log = Path(runtime) / 'verifications' / (stamp + '.log')
        log.parent.mkdir(parents=True, exist_ok=True)
        argv = [str(python), '-B', str(ROOT / 'collectors/registry/collect.py'), 'verify', '--target', str(target), '--publication', pub['id'], '--out', str(out), '--python', str(python)]
        sources_before = code_binding(implementation_family(pub))
        evidence_before = evidence_hashes(out)
        runtime_before = sha(Path(runtime) / 'runtime.json')
        with log.open('w') as stream:
            result = subprocess.run(argv, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT)
        dependencies = verify_dependencies(runtime, pub, dependency_proofs, ancestry)
        sources_after = code_binding(implementation_family(pub))
        runtime_changed = runtime_before != sha(Path(runtime) / 'runtime.json') or not doctor(runtime).get('runtime_ready')
        source_changed = sources_before != sources_after or runtime_changed
        acceptance = publication_acceptance(pub, out, dependencies)
        acceptance['native_capture_verified'] = acceptance['native_capture_verified'] and result.returncode == 0 and not source_changed
        evidence_after = evidence_hashes(out)
        evidence_unchanged = evidence_before == evidence_after
        acceptance['native_capture_verified'] = acceptance['native_capture_verified'] and evidence_unchanged
        accepted = result.returncode == 0 and acceptance['publication_coverage_accepted'] and not source_changed and evidence_unchanged
        acceptance['publication_accepted'] = accepted
        receipt = {'status': 'source_changed_during_verification' if source_changed else ('verified_publication' if accepted else 'publication_acceptance_incomplete'), 'verification_exit': result.returncode, 'log': str(log), 'output': str(out), 'publication_id': pub['id'], 'publication': pub, 'selected_config': selected_runtime_config(plan), 'runtime_receipt_sha256': runtime_before, 'runtime_changed_during_run': runtime_changed, 'publisher_requests': 0, 'evidence_read_only': evidence_unchanged, 'evidence_sha256_before': evidence_before, 'evidence_sha256_after': evidence_after, 'verification_argv': [str(x) for x in argv], 'selected_plan': plan, 'runtime_receipt_path': str(Path(runtime) / 'runtime.json'), 'collector_sources_before': sources_before, 'collector_sources_after': sources_after, 'source_changed_during_run': source_changed, 'family_verifier_passed': result.returncode == 0, 'acceptance': acceptance}
        save(log.with_suffix('.json'), receipt)
        return (0 if accepted else (result.returncode or 2)), receipt
    if out == ROOT or ROOT in out.parents and out.relative_to(ROOT).parts[0] in ('collectors', 'packages', 'archives'):
        raise OperationError('Use a fresh output directory outside collector code and sealed evidence.')
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / 'job.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise OperationError('Another launcher owns this output job: ' + str(out))
        job = read(metadata) if metadata.exists() else None
        runtime_receipt = read(Path(runtime) / 'runtime.json')
        runtime_identity = {key: runtime_receipt.get(key) for key in ('packages', 'requirements_sha256', 'browser_driver_sha256', 'shim_sha256')}
        prior_native = bool(job and job['binding'].get('collection_options', {}).get('native_export'))
        want_native = prior_native if native_export is None else native_export
        binding = {'target_id': str(target), 'publication_id': pub['id'], 'out': str(out), 'publication': pub, 'collector_sources': code_binding(implementation_family(pub)), 'runtime_identity': runtime_identity, 'selected_config': selected_runtime_config(plan)}
        if want_native:
            binding['collection_options'] = {'native_export': True}
        if retry_native_export and (not job or not prior_native):
            raise OperationError('Native retry requires an existing matching launcher job originally created with --native-export')
        if upgrade_code and not job:
            raise OperationError('Code upgrade requires an existing matching launcher job; unowned outputs cannot be adopted')
        if (upgrade_code or retry_native_export) and not (out / 'checkpoint.json').is_file():
            raise OperationError('Explicit revision/export action requires the existing family checkpoint')
        if job and job['binding'] != binding:
            stable_keys = ('target_id', 'publication_id', 'out', 'publication', 'selected_config', 'collection_options')
            if not upgrade_code or any(job['binding'].get(key) != binding.get(key) for key in stable_keys):
                raise OperationError('Output job source/configuration changed. Use a fresh directory or the documented explicit family migration; automatic resume is refused.')
            prior_sha = sha(metadata)
            history = folder / 'job-history' / (prior_sha + '.json')
            history.parent.mkdir(parents=True, exist_ok=True)
            history.write_bytes(metadata.read_bytes())
            job.setdefault('code_upgrades', []).append({'prior_job_sha256': prior_sha, 'prior_binding': job['binding'], 'new_binding': binding, 'at': now(), 'reason': 'Explicit enCodePlus code/runtime upgrade; exact publication/configuration/options retained, family revalidates cached sources and reparses all content with a fresh closing generation'})
            job.update(binding=binding, complete=False, capture_verified=False, native_capture_verified=False)
        if not verify_only and not job and out.exists() and any(out.iterdir()):
            raise OperationError('Existing data has no matching launcher job. Use verify, or start a fresh directory; existing data is not overwritten.')
        if not job:
            job = {'schema_version': 1, 'binding': binding, 'created_at': now(), 'attempts': [], 'complete': False}
        health = doctor(runtime, target, publication, browser=False, output=out)
        if not health.get('runtime_ready'):
            raise OperationError('Runtime verification failed: ' + '; '.join(health['issues']))
        will_collect = not verify_only and not upgrade_code and not job.get('complete') and not job.get('capture_verified') and not job.get('native_capture_verified')
        if upgrade_code or retry_native_export:
            will_collect = True
        if will_collect and not health['ready']:
            job.update(status='blocked_preflight', preflight=health, updated_at=now())
            if health.get('access_stops'):
                job['retained_access_stops'] = health['access_stops']
            save(metadata, job)
            return 3, {'status': 'blocked_preflight', 'job': str(metadata), 'issues': health['issues'], 'access_stops': health.get('access_stops', [])}
        if will_collect and job.get('retained_access_stops'):
            # Gate files can disappear on reboot; an owned job must not forget a refusal.
            return 3, {'status': 'retained_access_stop', 'job': str(metadata), 'access_stops': job['retained_access_stops']}
        action = 'collect' if will_collect else 'verify'
        attempt = {'started_at': now(), 'action': action, 'runtime_receipt_sha256': sha(Path(runtime) / 'runtime.json'), 'collector_sources_before': binding['collector_sources']}
        attempt['requested_actions'] = {'upgrade_code': upgrade_code, 'native_export': bool(want_native), 'retry_native_export': retry_native_export}
        if (upgrade_code or retry_native_export) and (out / 'checkpoint.json').is_file():
            attempt['prior_family_checkpoint_sha256'] = sha(out / 'checkpoint.json')
            attempt['prior_native_export'] = read(out / 'checkpoint.json').get('native_export')
        index = len(job['attempts'])
        job['attempts'].append(attempt)
        job.update(status='running', updated_at=now())
        save(metadata, job)
        argv = [str(python), '-B', str(ROOT / 'collectors/registry/collect.py'), action, '--target', str(target), '--publication', pub['id'], '--out', str(out), '--python', str(python)]
        if action == 'collect' and out.exists() and any(out.iterdir()):
            argv += ['--resume']
            if upgrade_code:
                argv += ['--upgrade-code']
            if retry_native_export:
                argv += ['--retry-native-export']
        if action == 'collect' and want_native:
            argv += ['--native-export']
        attempt['argv'] = argv
        save(metadata, job)
        print('Publication: ' + pub['id'] + '\nOutput: ' + str(out) + '\nProgress log: ' + str(folder / (str(index) + '-acquire.log')), flush=True)
        with (folder / (str(index) + '-acquire.log')).open('w') as log:
            result = subprocess.run(argv, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        attempt['acquisition_exit'] = result.returncode
        stops = access_state(pub, env, out) if action == 'collect' else []
        if stops:
            job['retained_access_stops'] = stops
        verification_exit = result.returncode
        if action == 'collect' and out.exists():
            verify_argv = [str(python), '-B', str(ROOT / 'collectors/registry/collect.py'), 'verify', '--target', str(target), '--publication', pub['id'], '--out', str(out), '--python', str(python)]
            attempt['verify_argv'] = verify_argv
            with (folder / (str(index) + '-verify.log')).open('w') as log:
                verification_exit = subprocess.run(verify_argv, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
        dependencies = verify_dependencies(runtime, pub, dependency_proofs, ancestry)
        sources_after = code_binding(implementation_family(pub))
        runtime_changed = attempt['runtime_receipt_sha256'] != sha(Path(runtime) / 'runtime.json') or not doctor(runtime).get('runtime_ready')
        source_changed = binding['collector_sources'] != sources_after or runtime_changed
        acceptance = publication_acceptance(pub, out, dependencies)
        acceptance['native_capture_verified'] = acceptance['native_capture_verified'] and verification_exit == 0 and not source_changed
        attempt.update(verification_exit=verification_exit, finished_at=now(), collector_sources_after=sources_after, source_changed_during_run=source_changed, runtime_changed_during_run=runtime_changed, acceptance=acceptance)
        # Exit zero means the adapter's selected-scope acceptance criteria pass;
        # report semantics from its coverage rather than claiming jurisdiction completion.
        complete = result.returncode == 0 and verification_exit == 0 and not stops and not source_changed and acceptance['publication_coverage_accepted']
        acceptance['publication_accepted'] = complete
        status = 'source_changed_during_run' if source_changed else ('verified_publication' if complete else 'publication_acceptance_incomplete')
        capture = result.returncode == 0 and verification_exit == 0 and not stops and not source_changed and all(acceptance.get(k) is True for k in ('publication_text_complete', 'required_nonimage_documents_complete', 'legal_structure_qualified'))
        job.update(status=status, complete=complete, capture_verified=capture, native_capture_verified=acceptance['native_capture_verified'], updated_at=now())
        save(metadata, job)
        return (0 if complete else 2), {'status': job['status'], 'family_verifier_passed': verification_exit == 0, 'selected_scope_verifier_passed': verification_exit == 0 and not source_changed, 'publication_accepted': complete, 'acceptance': acceptance, 'jurisdiction_complete': False, 'job': str(metadata), 'output': str(out), 'acquisition_exit': result.returncode, 'verification_exit': verification_exit, 'access_stops': stops, 'coverage_report': str(out / 'coverage.json'), 'source_changed_during_run': source_changed, 'source_change_action': 'Retain captured evidence and executed snapshots; explicitly review or migrate into a fresh run before claiming current-code validation.' if source_changed else None}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', default=str(DEFAULT_RUNTIME))
    commands = parser.add_subparsers(dest='action', required=True)
    setup_parser = commands.add_parser('setup', help='Install isolated pinned dependencies and check ordinary headed Chrome')
    setup_parser.add_argument('--python', default=sys.executable)
    for name in ('plan', 'doctor', 'run', 'verify'):
        p = commands.add_parser(name)
        p.add_argument('--target', required=name in ('run', 'verify'))
        p.add_argument('--publication')
        if name == 'plan':
            p.add_argument('--all', action='store_true', help='Plan the primary publication for every selected target')
            p.add_argument('--all-publications', action='store_true', help='Plan all inventoried primary/secondary publications, including unqualified discoveries; no acquisition')
            p.add_argument('--cohort', choices=('expansion', 'original', 'all'), default='all')
        if name == 'doctor':
            p.add_argument('--browser', action='store_true')
            p.add_argument('--out', help='Inspect required external-source gates referenced by an existing run')
        if name in ('run', 'verify'):
            p.add_argument('--out', required=True)
            p.add_argument('--dependency', action='append', default=[], metavar='PUBLICATION_ID=PROOF_DIR', help='Read-only current verification of an exact required publication; repeat for transitive dependencies')
        if name == 'run':
            p.add_argument('--upgrade-code', action='store_true', help='Explicitly migrate an existing exact enCodePlus job; preserve prior lineage, revalidate cached bytes, reparse all content and acquire new closing witnesses')
            p.add_argument('--native-export', action='store_true', default=None, help='Request the visible enCodePlus HTML publication export on initial collection; retained job options are reused on ordinary resume')
            p.add_argument('--retry-native-export', action='store_true', help='Explicitly retry a previously requested native export on an existing exact enCodePlus HTML job; also requires --native-export')
    args = parser.parse_args(argv)
    try:
        if args.action == 'setup':
            result = setup(args.runtime, args.python)
            code = 0
        elif args.action == 'doctor':
            result = doctor(args.runtime, args.target, args.publication, args.browser, args.out)
            code = 0 if result['ready'] else 3
        elif args.action == 'plan':
            command = [sys.executable, '-B', str(ROOT / 'collectors/registry/collect.py'), 'plan']
            if args.target:
                command += ['--target', args.target]
            if args.publication:
                command += ['--publication', args.publication]
            if args.all:
                command += ['--all']
            if args.all_publications:
                command += ['--all-publications']
            command += ['--cohort', args.cohort]
            return subprocess.run(command, cwd=ROOT).returncode
        else:
            plan = registry_plan(args.target, args.publication, runtime_paths(args.runtime)[1])
            proofs = dependency_inputs(args.dependency, catalog_publication(plan['publication_id']))
            code, result = execute_job(args.runtime, args.target, args.publication, args.out, args.action == 'verify', proofs, upgrade_code=getattr(args, 'upgrade_code', False), native_export=getattr(args, 'native_export', None), retry_native_export=getattr(args, 'retry_native_export', False))
        print(json.dumps(result, indent=2))
        return code
    except (OperationError, OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(json.dumps({'status': 'action_required', 'error': str(error)}, indent=2), file=sys.stderr)
        return 3
