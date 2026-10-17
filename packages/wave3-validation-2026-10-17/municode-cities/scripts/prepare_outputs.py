"""Explicit offline build step; preserves earlier parser output trials, regenerates final normalized outputs."""
import sys
sys.dont_write_bytecode=True
import json,re,hashlib,shutil,subprocess
from pathlib import Path
from normalize import normalize
ROOT=Path(__file__).resolve().parents[1]
for d in list((ROOT/'live').iterdir())+list((ROOT/'supplemental').iterdir())+(list((ROOT/'recovery').iterdir()) if (ROOT/'recovery').exists() else []):
 if not (d/'samples.json').exists() or not (d/'receipt.json').exists():continue
 receipt=json.loads((d/'receipt.json').read_text())
 if receipt.get('status')!='acquired' or receipt.get('access_stop'):continue
 out=d/'normalized'
 if out.exists():
  v=json.loads((out/'verification.json').read_text());old=v['parser_sha256'];cur=hashlib.sha256((ROOT/'scripts/normalize.py').read_bytes()).hexdigest()
  if old!=cur:
   trial=d/'parser-trials'/old
   if not trial.exists():shutil.copytree(out,trial)
 (d/'executed-final-normalize.py').write_bytes((ROOT/'scripts/normalize.py').read_bytes())
 normalize(d)
 print('NORMALIZED',d.relative_to(ROOT),flush=True)
