"""Serial identity-bound browser acquisition; direct HTTP remains stopped. Fresh paths required."""
import argparse,json,os,re,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
from normalize import normalize
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--sequence',type=int);p.add_argument('--skip-sequence',type=int,action='append',default=[]);p.add_argument('--out-root',type=Path,default=ROOT/'live');p.add_argument('--offline',action='store_true');a=p.parse_args()
for row in json.loads((ROOT/'targets.json').read_text()):
 if (a.sequence and row['sequence']!=a.sequence) or row['sequence'] in a.skip_sequence:continue
 out=a.out_root/re.sub('[^a-z0-9]+','-',row['jurisdiction'].lower()).strip('-')
 if a.offline:
  if (out/'samples.json').exists():print(json.dumps(normalize(out)),flush=True)
  continue
 if (out/'receipt.json').exists():print('EXISTING',row['jurisdiction'],'use fresh --out-root for another live run',flush=True);continue
 if Path(os.environ.get('MUNICODE_GATE_DIR','/tmp/compliSolv-municode-rate-gate'),'browser-stop.json').exists():print('FAMILY STOP active; remaining targets untouched',flush=True);break
 print('START',row['jurisdiction'],flush=True);env={**os.environ,'MUNICODE_EXPECTED_CLIENT_NAMES':json.dumps(row['expected_client_names']),'MUNICODE_EXPECTED_STATE':row['state']};cmd=[os.environ.get('NODE','node'),str(ROOT/'scripts/collect_browser.cjs'),row['source_url'],str(out),'3'];proc=subprocess.run(cmd,env=env,capture_output=True,text=True);out.mkdir(parents=True,exist_ok=True);(out/'command.log').write_text(json.dumps({'command':cmd,'expected_client_names':row['expected_client_names'],'state':row['state'],'stdout':proc.stdout,'stderr':proc.stderr,'returncode':proc.returncode},indent=2));print('FINISH',row['jurisdiction'],proc.returncode,proc.stdout[:300],flush=True)
 if (out/'samples.json').exists() and json.loads((out/'receipt.json').read_text()).get('status')=='acquired':
  try:
   (out/'executed-normalize.py').write_bytes((ROOT/'scripts/normalize.py').read_bytes())
  except Exception as e: print('PARSER SNAPSHOT FAILED',str(e),flush=True)
  try:print('NORMALIZED',row['jurisdiction'],normalize(out)['record_count'],flush=True)
  except Exception as e:print('PARSE FAILED',str(e),flush=True)
 if Path(os.environ.get('MUNICODE_GATE_DIR','/tmp/compliSolv-municode-rate-gate'),'browser-stop.json').exists():print('FAMILY STOP after target; no further requests',flush=True);break
