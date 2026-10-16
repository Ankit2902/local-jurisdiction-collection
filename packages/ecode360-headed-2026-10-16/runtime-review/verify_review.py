#!/usr/bin/env python3
"""Verify the local audit artifact manifest and run its offline fake-runtime tests."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def main():
 report=json.loads((ROOT/'RUNTIME-REVIEW.json').read_text())
 for item in report['artifacts']:
  p=ROOT/item['path'];actual=hashlib.sha256(p.read_bytes()).hexdigest()
  if actual!=item['sha256']:raise SystemExit('Artifact hash mismatch: '+item['path'])
 print('Artifact manifest verified:',len(report['artifacts']),flush=True)
 return subprocess.call([sys.executable,str(ROOT/'test_runtime_guards.py')],cwd=ROOT)
if __name__=='__main__':raise SystemExit(main())
