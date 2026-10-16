#!/usr/bin/env python3
"""Verify every delivered artifact bound in the validation report."""
from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parent
report=json.loads((root/'VALIDATION-REPORT.json').read_text())
failures=[]
for path,expected in report['artifact_hashes'].items():
 p=root/path
 if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=expected:failures.append(path)
if failures:raise SystemExit('Hash mismatch/missing: '+', '.join(failures))
print('Verified %d artifact hashes; whole_corpus_validated=%s'%(len(report['artifact_hashes']),report['whole_corpus_validated']))
