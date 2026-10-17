#!/usr/bin/env python3
"""Zero-network integrity + deterministic replay verification."""
import hashlib,json,pathlib,tempfile
import validate
BASE=pathlib.Path(__file__).resolve().parent
if __name__=='__main__':
 manifest=json.loads((BASE/'run_manifest.json').read_text())
 for name,expected in manifest['script_sha256'].items():
  assert hashlib.sha256((BASE/name).read_bytes()).hexdigest()==expected,'Script/package changed: '+name
 with tempfile.TemporaryDirectory(prefix='official-source-replay-') as d:
  out=pathlib.Path(d);validate.run(out)
  names={p.name for p in out.iterdir() if p.is_file()}
  assert names==set(manifest['parsed_sha256']),'Replay output set changed'
  for name,expected in manifest['parsed_sha256'].items():
   assert hashlib.sha256((out/name).read_bytes()).hexdigest()==expected,'Replay differs: '+name
 print('OFFLINE REPLAY PASS: raw integrity, final scripts, and all normalized outputs match.')
