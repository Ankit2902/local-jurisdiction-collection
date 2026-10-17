"""Authoring capture/audit of shared request gate. Does not send requests or clear stops."""
import json,hashlib
from pathlib import Path
from datetime import datetime
ROOT=Path(__file__).resolve().parents[1]
source=Path('/tmp/compliSolv-municode-rate-gate');out=ROOT/'evidence/rate-gate';out.mkdir(exist_ok=True)
rows=[]
for line in (source/'requests.jsonl').read_text().splitlines():
 r=json.loads(line)
 if r.get('started_at','')>='2026-10-17T18:37:00':rows.append(r)
(out/'requests.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows));(out/'state.json').write_bytes((source/'state.json').read_bytes())
if (source/'browser-stop.json').exists():(out/'browser-stop.json').write_bytes((source/'browser-stop.json').read_bytes())
times=[datetime.fromisoformat(r['started_at']).timestamp() for r in rows];deltas=[b-a for a,b in zip(times,times[1:])];workflow=[datetime.fromisoformat(r['started_at']).timestamp() for r in rows if r.get('transport')=='ordinary-headed-browser-public-workflow'];wd=[b-a for a,b in zip(workflow,workflow[1:])];report={'browser_workflow_request_count':len(workflow),'browser_workflow_minimum_interval_seconds':min(wd) if wd else None,'browser_workflow_intervals_below_3_seconds':sum(d<3 for d in wd),'captured_requests':len(rows),'scope':'Shared publisher family, all coordinating groups, from Wave3 initial direct attempt onward; not only this package','nominal_guard_seconds':3.5,'minimum_logged_start_interval_seconds':min(deltas) if deltas else None,'intervals_below_3_seconds':sum(d<3 for d in deltas),'note':'Log event time can vary slightly from reservation state time. Atomic browser stops and retained direct stop are preserved; audit does not release them.','request_log_sha256':hashlib.sha256((out/'requests.jsonl').read_bytes()).hexdigest()};(out/'audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
