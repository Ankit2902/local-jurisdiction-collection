"""Read-only environment/known-gate/source-resume preflight; never probes publisher network."""
import argparse,importlib.util,importlib.metadata,json,platform,shutil,sys
from pathlib import Path
from urllib.parse import urlsplit
from source_common import *
from king_acquire import URL as KING
FLAG='https://www.codepublishing.com/AZ/Flagstaff/'
TARGETS={'original-flagstaff-az':{'source_url':FLAG,'hosts':['www.codepublishing.com'],'packages':['beautifulsoup4','playwright'],'modules':['bs4','playwright'],'browser_required':True},'original-king-county-wa':{'source_url':KING,'hosts':['kingcounty.gov','aqua.kingcounty.gov'],'packages':['beautifulsoup4','pypdf'],'modules':['bs4','pypdf'],'browser_required':False}}
def required_data(root=None):
 root=Path(root) if root is not None else Path(__file__).parent;errors=[]
 expected={'configs.json':None,'source_dispositions.json':'king-source-dispositions-1','source_character_dispositions.json':'king-finite-source-character-profiles-1'}
 for name,schema in expected.items():
  try:
   obj=load(root/name)
   if schema and obj.get('schema')!=schema:errors.append('Unsupported mandatory source-profile schema: '+name)
   if name=='configs.json' and obj.get('schema_version')!=1:errors.append('Unsupported target configuration schema')
  except (OSError,ValueError,TypeError):errors.append('Missing or invalid mandatory configuration/source profile: '+name)
 return errors

def run(target,source=None):
 cfg=TARGETS[target];data_errors=required_data();missing=[name for name in cfg['modules'] if not importlib.util.find_spec(name)];versions={}
 for package in cfg['packages']:
  try:versions[package]=importlib.metadata.version(package)
  except importlib.metadata.PackageNotFoundError:versions[package]=None
 browser=next((p for p in ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',shutil.which('google-chrome'),shutil.which('google-chrome-stable'),shutil.which('chrome')] if p and Path(p).is_file()),None);stops=[]
 for host in cfg['hosts']:
  gate=transport.ROOT/sha(host.encode())[:20]/'state.json'
  if gate.is_file() and load(gate).get('stop'):stops.append({'host':host,'gate':str(gate),'stop':load(gate)['stop']})
 source_reasons=[]
 if source:
  folder=Path(source);state=load(folder/'checkpoint.json')
  if state.get('source_url')!=cfg['source_url']:source_reasons.append('Retained publication identity differs from selected target')
  if state.get('blocked') or state.get('errors'):source_reasons.append('Retained failure/access stop: collector refuses automatic resume')
  for name,digest in state.get('code_fingerprint',{}).items():
   candidate=Path(__file__).parent/name
   if not candidate.is_file() or sha(candidate.read_bytes())!=digest:source_reasons.append('Acquisition revision differs: '+name)
  for a in state.get('artifacts',[]):
   path=folder/a['path']
   if not path.is_file() or sha(path.read_bytes())!=a['sha256']:source_reasons.append('Retained source bytes missing/corrupt: '+a['path'])
 ready=not missing and not stops and (browser is not None or not cfg['browser_required']) and not source_reasons and not data_errors
 return {'target':target,'source_url':cfg['source_url'],'read_only':True,'publisher_requests':0,'ready_to_attempt_collection':ready,'network_ready':not stops and not source_reasons and not data_errors,'mandatory_source_data_errors':data_errors,'source_resume_ready':ready if source else None,'fully_verified_publication':False,'qualification_note':'Operational readiness is not a source completeness/edition claim; actual collection/verification may return incomplete','missing_modules':missing,'package_versions':versions,'chrome_path':browser,'browser_required':cfg['browser_required'],'known_host_stops':stops,'source_reasons':source_reasons,'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'gate_root':str(transport.ROOT)}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--target',choices=list(TARGETS),required=True);p.add_argument('--source');a=p.parse_args()
 try:r=run(a.target,a.source);print(json.dumps(r,indent=2));sys.exit(0 if r['ready_to_attempt_collection'] else 3)
 except Exception as e:print(json.dumps({'ready_to_attempt_collection':False,'publisher_requests':0,'error':str(e)}));sys.exit(1)
