#!/usr/bin/env python3
"""Fresh-output wrapper for the publisher's normal browser API workflow; no direct HTTP fallback."""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--sequence',type=int,choices=[63,100],required=True);p.add_argument('--sample-count',type=int,default=3);a=p.parse_args();out=a.out.resolve()
if out.exists():p.error('--out must not already exist')
root=Path(__file__).resolve().parents[1];name,state,slug=('Cincinnati','OH','cincinnati') if a.sequence==63 else ('Fairfax County','VA','fairfax_county');url=f'https://library.municode.com/{state.lower()}/{slug}/codes/code_of_ordinances';env=dict(os.environ,MUNICODE_EXPECTED_CLIENT_NAMES=json.dumps([name]),MUNICODE_EXPECTED_STATE=state)
out.mkdir(parents=True);b=Path(__file__).read_bytes();(out/('executed-wrapper-'+hashlib.sha256(b).hexdigest()+'.py')).write_bytes(b)
subprocess.run([env.get('NODE_BIN','node'),str(root/'scripts/collect_browser.cjs'),url,str(out),str(a.sample_count)],env=env,check=True)
from replay import municode
r=municode(str(out),name,state,True);print(json.dumps(r,indent=2))
