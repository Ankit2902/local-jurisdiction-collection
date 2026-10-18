#!/usr/bin/env python3
"""Retain original-source official adapter qualifications; no inherited full-pass claims."""
import argparse,hashlib,json,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True);a=p.parse_args();index=json.loads((ROOT/'collectors/official/source-qualification.json').read_text());archive=HERE/'readiness-source-evidence.zip';qualified=HERE/'readiness-qualified-configs.json';data=json.loads(qualified.read_text())
 with zipfile.ZipFile(archive) as z:members={n:z.read(n) for n in z.namelist()}
 original={p['id']:p for p in json.loads((HERE/'original-publications.json').read_text())['publications']}
 for row in index['configs']:
  ident=row['target_id']+'-primary';cfgraw=(ROOT/row['config']).read_bytes();cfg=json.loads(cfgraw)
  if sha(cfgraw)!=row['config_sha256'] or cfg['source_url']!=row['source_url'] or not row['runnable_dispatch_config']:raise ValueError('Config binding '+ident)
  refs=row['relative_evidence_from_official_readiness_root'];files={'config.json':cfgraw,'qualification.json':json.dumps(row,sort_keys=True).encode()}
  if cfg['mode']=='legacy_codepublishing':
   files['document.html']=(a.evidence/refs['rendered_index']).read_bytes();files['receipt.json']=(a.evidence/refs['source_discovery']).read_bytes()
  else:
   run=a.evidence/refs['current_run'];files['document.html']=(run/'raw/fa44132b238e67958fb1.bin').read_bytes();files['receipt.json']=(run/'raw/fa44132b238e67958fb1.receipt.json').read_bytes();files['inventory.json']=(run/'inventory.json').read_bytes()
  receipt=json.loads(files['receipt.json'])
  if receipt['status']!=200 or receipt.get('final_url',cfg['source_url']).rstrip('/')!=cfg['source_url'].rstrip('/'):raise ValueError('Source200/canonicalroute '+ident)
  if cfg['mode']!='legacy_codepublishing' and sha(files['document.html'])!=receipt['sha256']:raise ValueError('Rawsource hash '+ident)
  prefix='qualified-configs/'+ident
  for name,raw in files.items():members[prefix+'/'+name]=raw
  data['publications'][ident]={'runnable':True,'unsupported_reason':None,'source_url':cfg['source_url'],'original_source_url':original[ident]['source_url'],'title':cfg['publication'],'observed_title':cfg['publication'],'adapter_config_path':row['config'],'publisher':'official','source_family':original[ident]['source_family'],'scope_kind':'publication','qualification_evidence':{'kind':'official-source-config','bundle':archive.name,'prefix':prefix,'source_mode':cfg['mode'],'scope':row['qualified_scope'],'full_live_verified':False,'owner_reported_complete_source_scope':row['whole_target_live_complete']}}
 with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
  for name,raw in sorted(members.items()):info=zipfile.ZipInfo(name,date_time=(2026,10,17,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,raw)
 (HERE/'readiness-source-evidence-manifest.json').write_text(json.dumps({'schema_version':1,'archive_sha256':sha(archive.read_bytes()),'files':[{'member':n,'bytes':len(b),'sha256':sha(b)} for n,b in sorted(members.items())]},indent=2)+'\n');qualified.write_text(json.dumps(data,indent=2)+'\n');print(json.dumps({'qualified_original_configs':len(index['configs']),'full_live_passes_inferred':0}))
if __name__=='__main__':main()
