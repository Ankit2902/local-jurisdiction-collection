#!/usr/bin/env python3
"""Register an operator's ordinary publisher SaveHTML file; no browser or network required.
Acquisition provenance is explicitly operator-attested, not independently proven by this command.
"""
import argparse,hashlib,json,shutil
from datetime import datetime
from pathlib import Path
from import_publisher_export import SLUGS
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--file',required=True);p.add_argument('--slug',choices=SLUGS,required=True);p.add_argument('--source-url',required=True);p.add_argument('--selection',required=True);p.add_argument('--retrieved-at',required=True,help='Actual download time with timezone, ISO8601');p.add_argument('--out',required=True);a=p.parse_args()
    dt=datetime.fromisoformat(a.retrieved_at.replace('Z','+00:00'))
    if dt.tzinfo is None:raise ValueError('Timezone required for actual retrieval time')
    out=Path(a.out)
    if out.exists() and any(out.iterdir()):raise ValueError('Immutable registered output exists')
    raw=Path(a.file).read_bytes();out.mkdir(parents=True,exist_ok=True);(out/'publisher-export.html').write_bytes(raw)
    receipt={'schema_version':1,'classification':'operator_attested_manual_publisher_download','metadata':{'slug':a.slug,'selection':a.selection},'source_url':a.source_url,'export_format':'HTML','finished_at':dt.isoformat(),'raw_artifact':'publisher-export.html','raw_sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'operator_browser_session_required':True,'unattended_acquisition':False,'operator_acquisition_attestation':'Operator supplies source URL, selection, and actual acquisition time; registration verifies local bytes only.','registration_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (out/'download-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
