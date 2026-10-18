"""Read-only sealed proof/registry identity/root CLI peer; never imports native parser."""
import sys
sys.dont_write_bytecode=True
import hashlib,json,os,subprocess,zipfile
from pathlib import Path
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def obj(p):return json.loads(p.read_text())
def main(packet,repo,out):
 before={f.relative_to(packet).as_posix():digest(f)for f in packet.rglob('*')if f.is_file()}
 assert digest(packet/'MANIFEST.json')=='b269b6e7099329d615d78d3c71c28bfe70e56754a252da9392bd307314140015'
 sealed=repo/'packages/collection-source-recovery-2026-10-18/clark/full30'
 assert digest(sealed/'MANIFEST.json')=='f138e7116c4552c242c79177fae024b6eb0158617b821c72a8818db539008537'
 sm=obj(sealed/'MANIFEST.json')
 # Hash native originals as opaque files; do not parse/decode content.
 for name,r in sm['files'].items():
  f=sealed/name;assert f.stat().st_size==r['bytes']and digest(f)==r['sha256'],name
 assert len(sm['files'])==253 and len([n for n in sm['files']if n.startswith('run/')])==177
 rt=packet/'candidate';cfgpath='collectors/official/configs/clark-title30-current-associated-documents.json'
 assert (rt/cfgpath).read_bytes()==(sealed/'config.json').read_bytes()==(sealed/'run/config.json').read_bytes()
 cp=obj(sealed/'run/checkpoint.json');bridge=obj(packet/'proof-bridge.json')
 assert cp['scripts']=={n:r['sealed']for n,r in bridge['executed_scripts'].items()}
 modulechecks={}
 for name,expected in cp['scripts'].items():
  hashes=[digest(root/name)for root in [sealed/'run/executed',rt/'collectors/official',repo/'collectors/official']]
  assert hashes==[expected]*3,(name,hashes)
  modulechecks[name]=expected
 assert len(modulechecks)==16
 with zipfile.ZipFile(rt/'collectors/registry/clark-title30-source-evidence.zip')as z:
  for name in z.namelist():
   target=sealed/name.removeprefix('full30/')if name.startswith('full30/')else sealed.parent/name
   assert z.read(name)==target.read_bytes(),name
  members=z.namelist()
 assert len(members)==93 and not any(n.lower().endswith(('.pdf','.png','.jpg','.jpeg','.gif','.webp'))for n in members)
 cov=obj(sealed/'run/coverage.json');vr=obj(sealed/'verify.stdout')
 assert cov['requested_level']=='file_pages'and cov['requested_coverage_complete']and cov['pdf_page_extraction_complete']
 assert cov['parsed_record_count']==381 and cov['image_placeholder_count']==229
 assert cov['legal_semantic_coverage_complete']is False and cov['jurisdiction_complete']is False
 assert vr['all_run_files_unchanged']and vr['run_file_count']==177 and vr['forbidden_calls']==[]
 assert len(cp['items'])==len(cp['done'])==len(cp['item_consistency'])==30
 assert (sealed/'run'/cp['identity']['source_ref']).read_bytes()==(sealed/'run'/cp['consistency']['raw_ref']).read_bytes()
 env=dict(os.environ,PYTHONPATH=str(packet/'tripwire'),PYTHONDONTWRITEBYTECODE='1')
 commands=[]
 def cli(name,args,expected):
  rr=subprocess.run([sys.executable,'-B',str(rt/'collect.py'),*args],cwd=rt,env=env,text=True,capture_output=True)
  (out/(name+'.stdout')).write_text(rr.stdout);(out/(name+'.stderr')).write_text(rr.stderr)
  assert rr.returncode==expected,(name,rr.returncode,rr.stderr)
  commands.append({'name':name,'args':args,'exit_code':rr.returncode,'guard':'candidate tripwire/sitecustomize.py'})
  return json.loads(rr.stdout)if rr.returncode==0 else rr
 allp=cli('peer-plan-all',['plan','--all-publications'],0)
 assert allp['publication_count']==225 and allp['runnable_config_count']==196
 assert sum(bool(x['observed_access_advisories'])for x in allp['plans'])==154
 c=next(x for x in allp['plans']if x['publication_id']=='96-7e8795b1baee')
 assert c['qualified_config_path']==cfgpath and c['publisher']=='official' and c['target_id']=='96'
 selected=cli('peer-plan-selected',['plan','--target','96','--publication','96-7e8795b1baee'],0)
 assert len(selected['plans'])==1
 assert all(c.get(k)==v for k,v in selected['plans'][0].items()),'Selected plan dispatch fields differ from all-publication plan'
 primary=cli('peer-plan-primary',['plan','--all'],0);assert primary['targets']==130
 cli('peer-wrong-owner',['plan','--target','95','--publication','96-7e8795b1baee'],2)
 missing=out/'ABSENT-RUNTIME';dest=out/'ABSENT-OUTPUT'
 refused=cli('peer-correct-run',['--runtime',str(missing),'run','--target','96','--publication','96-7e8795b1baee','--out',str(dest)],3)
 assert 'invalid choice'not in refused.stderr and not missing.exists()and not dest.exists()
 # No current common verification is executed or fabricated by this review.
 assert before=={f.relative_to(packet).as_posix():digest(f)for f in packet.rglob('*')if f.is_file()}
 for name,r in sm['files'].items():assert digest(sealed/name)==r['sha256']
 return {'passed':True,'candidate_manifest_sha256':digest(packet/'MANIFEST.json'),'candidate_files_unchanged':len(before),
 'sealed_manifest_sha256':digest(sealed/'MANIFEST.json'),'all253_sealed_files_hash_verified_unchanged':True,'sealed_run_files':177,
 'configuration_sha256':digest(rt/cfgpath),'exact16_sealed_executed_candidate_current_production_modules':modulechecks,
 'portable_archive_members_exact_sealed_bytes':93,'portable_archive_contains_native_PDF_or_image_files':False,
 'actual_root_cli_cases':commands,'catalog':{'governments':130,'publications':225,'dispatchable':196,'advisories':154},
 'requested_level':'file_pages','selected_documents':30,'physical_pages':381,'IMAGE_count':229,
 'base_validation_level':'mapped_only','legal_semantic_coverage_complete':False,'jurisdiction_complete':False,
 'fresh_current_common_verification':False,'publisher_requests':0,'native_pages_parsed':0,'image_decode_render_extract_OCR':0}
if __name__=='__main__':print(json.dumps(main(*map(Path,sys.argv[1:])),indent=2))
