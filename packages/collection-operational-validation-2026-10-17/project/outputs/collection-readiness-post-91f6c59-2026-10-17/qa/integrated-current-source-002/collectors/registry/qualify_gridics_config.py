#!/usr/bin/env python3
"""Author exact Gridics acquisition qualification from retained ordinary-browser bytes."""
import argparse,hashlib,json,zipfile
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--publication',required=True);p.add_argument('--config',required=True);p.add_argument('--run',type=Path,required=True);p.add_argument('--evidence-path',required=True);a=p.parse_args()
 cfg=json.loads((ROOT/a.config).read_text());acq=json.loads((a.run/'acquisition.json').read_text());coverage=json.loads((a.run/'coverage.json').read_text());receipts=json.loads((a.run/'responses.json').read_text())
 if acq['config']!=cfg:raise ValueError('Executed configuration differs')
 doc=next(x for x in receipts if x['phase']=='start' and x['url']==cfg['source_url'].split('#')[0]);inv=next(x for x in receipts if x['phase']=='start' and x['url'].startswith('https://codehub.gridics.com/api/v1/codehub/'+cfg['document_id']+'?') and 'topLevel=1' in x['url'])
 document=(a.run/doc['path']).read_bytes();inventory=(a.run/inv['path']).read_bytes();nodes=json.loads(inventory)
 if doc['status']!=200 or inv['status']!=200 or sha(document)!=doc['sha256'] or sha(inventory)!=inv['sha256'] or not nodes or any(x['docId']!=cfg['document_id'] for x in nodes):raise ValueError('Unqualified document/inventory')
 title=BeautifulSoup(document,'html.parser').title.get_text(' ',strip=True)
 if cfg['identity_term'].lower() not in title.lower():raise ValueError('Unmatched source identity')
 qualified=HERE/'readiness-qualified-configs.json';data=json.loads(qualified.read_text());prefix='qualified-configs/'+a.publication;archive=HERE/'readiness-source-evidence.zip'
 with zipfile.ZipFile(archive) as z:members={n:z.read(n) for n in z.namelist()}
 for name,raw in {'config.json':(ROOT/a.config).read_bytes(),'document.html':document,'inventory.json':inventory,'document-receipt.json':json.dumps(doc,sort_keys=True).encode(),'receipt.json':json.dumps(inv,sort_keys=True).encode()}.items():members[prefix+'/'+name]=raw
 base=json.loads((HERE/'publications.json').read_text())['publications'];original=next((x['source_url'] for x in base if x['id']==a.publication),cfg['source_url'])
 data['publications'][a.publication]={'runnable':True,'unsupported_reason':None,'publisher':'gridics','source_family':'gridics','source_url':cfg['source_url'],'original_source_url':original,'title':title,'observed_title':title,'adapter_config_path':a.config,'scope_kind':'publication','qualification_evidence':{'kind':'gridics-native-inventory','prefix':prefix,'bundle':archive.name,'evidence_path':a.evidence_path,'expected_native_document_id':cfg['document_id'],'observed_root_count':len(nodes),'observed_heading_count':coverage['records'],'scope_note':'Acquisition/configuration qualified only. Exact native/DOM comparisons, unexplained empty bodies and required references remain explicit completeness gaps.','source_error_count':len(coverage['source_errors']),'unexplained_empty_count':len(coverage['unexplained_empty_source_ids']),'publication_complete':False}}
 with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
  for name,raw in sorted(members.items()):info=zipfile.ZipInfo(name,date_time=(2026,10,17,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,raw)
 (HERE/'readiness-source-evidence-manifest.json').write_text(json.dumps({'schema_version':1,'archive_sha256':sha(archive.read_bytes()),'files':[{'member':n,'bytes':len(b),'sha256':sha(b)} for n,b in sorted(members.items())]},indent=2)+'\n');qualified.write_text(json.dumps(data,indent=2)+'\n')
 print(json.dumps({'publication_id':a.publication,'runnable_config':True,'full_live_verified':False,'whole_publication_complete':False,'source_comparison_errors':len(coverage['source_errors'])}))
if __name__=='__main__':main()
