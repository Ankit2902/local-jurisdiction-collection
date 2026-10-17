#!/usr/bin/env python3
"""Offline final parser qualification on retained live bodies; preserves initial output and acquisition snapshots."""
import pathlib,json,shutil,hashlib,platform,datetime
from normalize_final import normalize
ROOT=pathlib.Path(__file__).resolve().parents[1]
for folder in list(ROOT.glob('direct/*'))+list(ROOT.glob('supplemental/*')):
 if not (folder/'samples.json').exists() or not (folder/'receipt.json').exists():continue
 receipt=json.loads((folder/'receipt.json').read_text())
 if receipt.get('status')!='acquired':continue
 existing=folder/'final-normalization-phase.json'
 if existing.exists():
  old=json.loads(existing.read_text())
  if old.get('raw_samples_sha256')==hashlib.sha256((folder/'samples.json').read_bytes()).hexdigest() and old.get('parser_sha256')==hashlib.sha256((ROOT/'scripts/normalize_final.py').read_bytes()).hexdigest():continue
 if (folder/'normalized').exists() and not (folder/'normalized-initial').exists():shutil.copytree(folder/'normalized',folder/'normalized-initial')
 report=normalize(folder);phase={'phase':'offline final normalization of retained live API evidence','command':'python3 scripts/finalize_replay.py','runtime':platform.python_version(),'os':platform.platform(),'executed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'network_used':False,'raw_samples_sha256':report['raw_samples_sha256'],'parser_sha256':report['parser_sha256'],'outputs_sha256':report['outputs_sha256']}
 (folder/'final-normalization-phase.json').write_text(json.dumps(phase,indent=2)+'\n');versions=folder/'script-versions';versions.mkdir(exist_ok=True)
 for name in ['normalize_final.py','finalize_replay.py']:
  p=ROOT/'scripts'/name;shutil.copy2(p,versions/(hashlib.sha256(p.read_bytes()).hexdigest()+p.suffix))
 print(json.dumps({'folder':str(folder.relative_to(ROOT)),'record_count':report['record_count'],'table_count':report['table_count']}))
