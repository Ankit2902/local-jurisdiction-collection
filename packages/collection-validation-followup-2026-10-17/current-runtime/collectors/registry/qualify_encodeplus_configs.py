#!/usr/bin/env python3
"""Author source-backed exact enCodePlus config qualifications from owner proof index."""
import argparse,hashlib,json,zipfile
from pathlib import Path
from urllib.parse import urlsplit
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--index',type=Path,required=True);ap.add_argument('--project',type=Path,required=True);a=ap.parse_args();rows=json.loads(a.index.read_text());pubs={p['id']:p for p in json.loads((HERE/'publications.json').read_text())['publications']};existing=HERE/'readiness-qualified-configs.json';qual=json.loads(existing.read_text())['publications'] if existing.exists() else {};archive=HERE/'readiness-source-evidence.zip'
 with zipfile.ZipFile(archive) as z:members={name:z.read(name) for name in z.namelist()}
 for row in rows:
  pub=pubs[row['id']];cfg=json.loads((ROOT/row['config']).read_text());raw=(a.project/row['proof']).read_bytes();receipt_path=Path(str(a.project/row['proof'])+'.receipt.json');receipt=json.loads(receipt_path.read_text());norm=lambda url:(urlsplit(url).hostname,urlsplit(url).path.rstrip('/'))
  if cfg['identity']!=row['identity'] or cfg['base']!=row['base'] or cfg['identity'] not in raw.decode() or receipt['sha256']!=hashlib.sha256(raw).hexdigest() or receipt['http_status']!=200 or receipt.get('challenge'):raise ValueError('Unqualified source/header/receipt '+row['id'])
  if not receipt['final_url'].startswith(cfg['base']):raise ValueError('TOC final response outside pinned source '+row['id'])
  if norm(pub['source_url'])!=norm(cfg['base']):raise ValueError('Different source book '+row['id'])
  prefix='qualified-configs/'+row['id'];members[prefix+'/toc.html']=raw;members[prefix+'/receipt.json']=receipt_path.read_bytes();members[prefix+'/config.json']=(ROOT/row['config']).read_bytes()
  q={'runnable':True,'unsupported_reason':None,'observed_title':cfg['identity'],'title':cfg['identity'],'source_url':cfg['base'],'original_source_url':pub['source_url'],'scope_kind':'publication','adapter_config_path':row['config'],'qualification_evidence':{'bundle':'readiness-source-evidence.zip','prefix':prefix,'scope':'Exact TOC identity/configuration only; full publication not yet acquired','inventory_nodes':row['inventory_nodes']}}
  if pub.get('jurisdiction_scope'):q['expected_identity']={'client_names':['Lancaster County'],'state':'NE'}
  qual[row['id']]=q
 with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
  for name,data in sorted(members.items()):info=zipfile.ZipInfo(name,date_time=(2026,10,17,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,data)
 (HERE/'readiness-source-evidence-manifest.json').write_text(json.dumps({'schema_version':1,'files':[{'member':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()} for name,data in sorted(members.items())],'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest()},indent=2)+'\n')
 (HERE/'readiness-qualified-configs.json').write_text(json.dumps({'schema_version':1,'publications':qual},indent=2)+'\n')
if __name__=='__main__':main()
