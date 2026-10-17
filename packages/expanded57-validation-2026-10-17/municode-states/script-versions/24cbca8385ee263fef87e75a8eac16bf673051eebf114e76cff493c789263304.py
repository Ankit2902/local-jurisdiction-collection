#!/usr/bin/env python3
"""Verify retained acquisition hashes and deterministically replay exact legal samples offline."""
import csv,hashlib,json,pathlib,tempfile,sys
from normalize_initial import normalize as initial_normalize
from normalize_final import normalize as final_normalize
ROOT=pathlib.Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
errors=[];checked=0;replays=0
for receipt in list(ROOT.glob('supplemental/*/*.receipt.json'))+list(ROOT.glob('direct/*/*.receipt.json'))+list(ROOT.glob('probes/*.receipt.json'))+list(ROOT.glob('official-pdf/*/source.pdf.receipt.json')):
 r=json.loads(receipt.read_text());raw=receipt.with_name(receipt.name.removesuffix('.receipt.json'))
 if not raw.exists() or sha(raw)!=r.get('sha256'):errors.append('Source hash mismatch '+str(receipt.relative_to(ROOT)))
 checked+=1
for receipt in ROOT.glob('routes/*/receipt.json'):
 r=json.loads(receipt.read_text());raw=receipt.parent/'official.html'
 if sha(raw)!=r['sha256']:errors.append('Official route hash mismatch '+str(receipt))
 checked+=1
for folder in list(ROOT.glob('direct/*'))+list(ROOT.glob('live/*'))+list(ROOT.glob('supplemental/*')):
 if not (folder/'receipt.json').exists():continue
 rec=json.loads((folder/'receipt.json').read_text())
 for r in rec.get('responses',[]):
  if not (folder/r['file']).exists() or sha(folder/r['file'])!=r['sha256']:errors.append('Browser response hash mismatch '+str(folder/r['file']))
  checked+=1
 for key in ('script_sha256','gate_script_sha256'):
  h=rec.get(key)
  if h and not list((folder/'script-versions').glob(h+'.*')) and not list((ROOT/'script-versions').glob(h+'.*')):errors.append('Missing executed script snapshot '+str(h))
 if rec.get('status')!='acquired':continue
 try:
  expected=json.loads((folder/'normalized/verification.json').read_text())
  with tempfile.TemporaryDirectory() as td:
   parser_file=ROOT/'scripts/normalize_final.py'
   replay=final_normalize if sha(parser_file)==expected['parser_sha256'] else initial_normalize
   report=replay(folder,pathlib.Path(td))
   if report['outputs_sha256']!=expected['outputs_sha256']:errors.append('Offline replay changed normalized output '+str(folder))
   if 'supplemental' not in str(folder) and report['record_count']<2:errors.append('Fewer than 2 legal sample records '+str(folder))
  records=[json.loads(x) for x in (folder/'normalized/sections.jsonl').read_text().splitlines()]
  with (folder/'normalized/sections.csv').open() as f:csvrows=list(csv.DictReader(f))
  assert len(records)==len(csvrows)
  for r,c in zip(records,csvrows):
   for k in c:assert str(r[k])==c[k],(k,str(folder))
  replays+=1
 except Exception as e:errors.append(str(folder)+': '+str(e))
results=json.loads((ROOT/'results.json').read_text()) if (ROOT/'results.json').exists() else []
for r in results:
 for p in r['evidence_paths']+r['script_paths']+r['publisher_download'].get('evidence_paths',[]):
  if not (ROOT/p).is_file():errors.append('Missing result path '+p)
 if r['complete_corpus'] is not False:errors.append('Unexpected corpus completeness claim')
report={'passed':not errors,'raw_hashes_checked':checked,'legal_samples_replayed':replays,'result_count':len(results),'errors':errors,'network_used':False}
(ROOT/'offline-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));sys.exit(bool(errors))
