#!/usr/bin/env python3
"""Read-only offline replay of declared final live scopes plus compact fault tests."""
import argparse,hashlib,json,pathlib,subprocess,sys
sys.dont_write_bytecode=True
import model,verify
BASE=pathlib.Path(__file__).resolve().parent

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def under(root,relative):
 p=(root/relative).resolve()
 if not p.is_relative_to(root.resolve()):raise ValueError('Evidence path outside supplied root')
 return p

def run(root,summary,tests=True):
 rows=[]
 for name,expected in summary['current_runtime_hashes'].items():
  if digest(BASE/name)!=expected:raise ValueError('Current implementation revision mismatch: '+name)
 for entry in summary['selected_final_proofs']:
  folder=under(root,entry['path']);coverage=verify.verify(folder);brief=__import__('collect').brief(coverage)
  for key,value in entry['expected'].items():
   if brief.get(key)!=value:raise ValueError(entry['path']+': unexpected '+key+': '+repr(brief.get(key)))
  for name,value in entry['hashes'].items():
   if digest(under(folder,name))!=value:raise ValueError(entry['path']+': sealed evidence mismatch '+name)
  if any(a.get('status')=='acquired' and model.image_asset(a) for a in coverage['assets']):raise ValueError('Acquired image asset in normalized ledger')
  receipts=list((folder/'raw').glob('*.receipt.json'))
  for receipt in receipts:
   m=json.loads(receipt.read_text());raw=receipt.with_name(receipt.name.replace('.receipt.json','.bin'));data=raw.read_bytes();headers={k.lower():v for k,v in m.get('headers',{}).items()}
   if data.startswith((b'\x89PNG\r\n\x1a\n',b'\xff\xd8\xff',b'GIF87a',b'GIF89a')):raise ValueError('Separate retained image bytes forbidden')
   if m.get('request_name','').startswith('asset:') and model.image_asset({'url':m['url'],'kind':'a'}):raise ValueError('Explicit image asset request forbidden')
   if headers.get('content-type','').lower().startswith('image/') and data:raise ValueError('Image response body retained')
  rows.append({'path':entry['path'],'offline_replay':'passed','receipt_count':len(receipts),'coverage':brief})
 test_result=None
 if tests:
  child=subprocess.run([sys.executable,'-B',str(BASE/'test_offline.py')],capture_output=True,text=True)
  if child.returncode:raise ValueError('Offline fault qualification failed: '+child.stdout+child.stderr)
  test_result={'status':'passed','command':[sys.executable,'-B','test_offline.py'],'output':child.stdout+child.stderr}
 return {'schema':1,'offline':True,'read_only':True,'selected_final_proofs':rows,'offline_tests':test_result,'image_audit':'No separate retained raster image bytes, acquired image ledger entries or explicit image asset requests. Native PDFs/HTML/ZIP may contain original embedded images; normalized images are policy omissions/placeholders.'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--evidence',type=pathlib.Path,required=True);p.add_argument('--summary',type=pathlib.Path,default=BASE/'validation-summary.json');p.add_argument('--skip-tests',action='store_true');a=p.parse_args()
 try:print(json.dumps(run(a.evidence,json.loads(a.summary.read_text()),not a.skip_tests),indent=2));raise SystemExit(0)
 except Exception as error:print(json.dumps({'offline':True,'read_only':True,'error':str(error)}));raise SystemExit(3)
