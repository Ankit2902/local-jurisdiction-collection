import sys;sys.dont_write_bytecode=True
import json,hashlib
from pathlib import Path
B=Path(__file__).resolve().parent;m=json.loads((B/'MANIFEST.json').read_text())
for f in m['files']:assert hashlib.sha256((B/f['path']).read_bytes()).hexdigest()==f['sha256'],f['path']
p=json.loads((B/'promotion.json').read_text());assert p['only_three_owned_Municode_files'] and not p['transport_changed'] and not p['Git_changed']
for name,h in p['promoted_files'].items():assert hashlib.sha256((B/'candidate'/name).read_bytes()).hexdigest()==h
assert 'Ran 34 tests' in (B/'after-tests.stderr').read_text() and (B/'after-tests.stderr').read_text().strip().endswith('OK')
assert 'Ran 3 tests' in (B/'production-tests.stderr').read_text() and (B/'production-tests.stderr').read_text().strip().endswith('OK')
assert 'FAIL:' in (B/'before-tests.stderr').read_text()
print(json.dumps({'passed':True,'files':len(m['files']),'isolated_tests':34,'exact_production_tests':3,'negative_before_patch_retained':True,'transport_change':False,'readonly':True}))
