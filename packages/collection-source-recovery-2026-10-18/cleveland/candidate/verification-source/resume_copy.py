#!/usr/bin/env python3
"""Resume retained publisher acquisition in a fresh directory, preserving the original.

Default execution uses collect.py and its ordinary headed browser/rate gate. A
prepare-only run performs no publisher requests. No source raw bytes are relabeled.
"""
import argparse,datetime,hashlib,json,shutil,subprocess,sys
from pathlib import Path
from model import IMAGE_POLICY

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def prepare(source,out,upgrade_assets=False,retry_assets=False):
 source=Path(source).resolve();out=Path(out).resolve();assert source.is_dir() and not out.exists(),'Existing --from and fresh --out required';assert source not in out.parents and out not in source.parents,'Operator output must be outside original source'
 old=json.loads((source/'run.json').read_text());assert old['image_policy']==IMAGE_POLICY,'Image policy differs; do not reuse superseded image acquisition';requests=json.loads((source/'requests.json').read_text())
 for key,e in requests.items():
  name=e['file'];assert not Path(name).is_absolute() and '..' not in Path(name).parts,'Unsafe retained source path';assert sha(source/name)==e['sha256'],'Corrupt source raw: '+key
 assert not upgrade_assets or old['assets_policy']=='reference-only','Asset upgrade only applies from reference-only to download'
 prior_files={str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file() and '__pycache__' not in p.parts and not p.name.endswith('.lock')};shutil.copytree(source,out,ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.lock'));assert all(sha(out/n)==h for n,h in prior_files.items()),'Copied evidence differs'
 origin=out/'operator-origin';assert not origin.exists(),'Already cloned operator source; choose original acquisition';origin.mkdir();shutil.copy2(out/'run.json',origin/'run.json');save(origin/'source-file-manifest.json',prior_files)
 cache=out/'pdf-tag-cache'
 if cache.exists():shutil.move(str(cache),origin/'pdf-tag-cache')
 meta=json.loads((out/'run.json').read_text());previous_error=meta.pop('error',None);meta['operator_source']={'source_directory_name':source.name,'source_run_sha256':sha(source/'run.json'),'source_requests_sha256':sha(source/'requests.json'),'prior_status':old['status'],'prior_error':previous_error,'kind':'Fresh directory reuse of original publisher bytes; original execution history and evidence preserved'}
 if upgrade_assets:meta['assets_policy']='download';meta['operator_source']['asset_policy_upgrade']='reference-only to download; image exclusion unchanged'
 meta['status']='operator-prepared';save(out/'run.json',meta);snap=out/'operator-scripts';snap.mkdir();shutil.copy2(__file__,snap/'resume_copy.py');args=[sys.executable,str(Path(__file__).with_name('collect.py')),'--url',meta['source_url'],'--jurisdiction',meta['expected_jurisdiction'],'--state',meta['expected_state'],'--publication',meta['publication_selector'],'--strategy',meta['strategy'],'--assets',meta['assets_policy'],'--out',str(out),'--resume']
 for alias in meta.get('identity_aliases',[]):args+=['--identity-alias',alias]
 if retry_assets:args+=['--retry-unavailable-assets']
 assert all(sha(source/n)==h for n,h in prior_files.items()),'Original source changed while cloning';save(out/'operator-lineage.json',{'schema_version':1,'kind':'Fresh-directory operator resume, not a new native export download','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_directory_name':source.name,'source_run_sha256':sha(source/'run.json'),'source_request_manifest_sha256':sha(source/'requests.json'),'operator_script_sha256':sha(Path(__file__)),'source_files_preserved':len(prior_files),'source_raw_request_count':len(requests),'source_status':old['status'],'native_export_sha256':requests.get('native-export',{}).get('sha256'),'resume_command':args,'image_policy':IMAGE_POLICY,'original_source_modified':False,'phase':'prepared_not_executed','publication_complete':False});return args

def main():
 p=argparse.ArgumentParser();p.add_argument('--from',dest='source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--prepare-only',action='store_true');p.add_argument('--upgrade-assets',action='store_true');p.add_argument('--retry-unavailable-assets',action='store_true');a=p.parse_args();command=prepare(a.source,a.out,a.upgrade_assets,a.retry_unavailable_assets)
 if a.prepare_only:print(json.dumps({'prepared':True,'publication_complete':False,'resume_command':command},indent=2));return 0
 result=subprocess.run(command);lineage=json.loads((a.out/'operator-lineage.json').read_text());lineage.update(phase='executed',exit_code=result.returncode,completed_at=datetime.datetime.now(datetime.timezone.utc).isoformat());save(a.out/'operator-lineage.json',lineage);return result.returncode
if __name__=='__main__':raise SystemExit(main())
