"""Replay five current reader paths, including newly corrected Albany/Cleveland derivatives."""
import sys
sys.dont_write_bytecode=True
import argparse,hashlib,json,socket
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--flagstaff-proof',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();repo=a.repo.resolve();a.out.parent.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(repo/'collectors/corpus_package'))
import common,package
calls=[]
def no(*args,**kwargs):calls.append('network');raise AssertionError('No network in reader composition')
socket.socket.connect=no;socket.socket.connect_ex=no;socket.create_connection=no
old=repo/'packages/collection-startup-and-corpus-2026-10-18/corpus';new=repo/'packages/collection-source-recovery-2026-10-18'
cases=[('Flagstaff','originals-flagstaff-html-v1',old/'flagstaff-current-live-export/package',2661,True),('Henderson','municode-html-publication-v1',old/'municode-encodeplus-final/fixtures/packages/henderson',2122,False),('Lincoln Charter','encodeplus-html-publication-v1',old/'municode-encodeplus-final/fixtures/packages/charter',188,False),('Albany','ecode-html-retained-incomplete-v1',new/'ecode/corrected-corpus-v3',3006,False),('Cleveland','american-legal-native-html-publication-v1',new/'cleveland/candidate/package',6141,False)]
source_before=package.code();results=[]
for label,mode,baseline,count,selected in cases:
 root=baseline/'evidence/input';pp=a.flagstaff_proof if label=='Flagstaff' else baseline/'evidence/proofs/read-only-proof.json';pb=pp.read_bytes();fb=(pp.parent/'family-verification.json').read_bytes();before=common.files(root)
 binding,proof,family,projection=package.binding(root,pb,fb,mode);outputs=common.artifacts(projection)
 assert len(projection.rows)==count
 different=[name for name,data in outputs.items() if name!='validation-report.json' and (baseline/name).read_bytes()!=data];assert not different,(label,different)
 report=json.loads(outputs['validation-report.json']);previous=json.loads((baseline/'validation-report.json').read_text());trim=lambda x:{k:v for k,v in x.items() if k not in ['selected_publication_ready','selected_publication_readiness']}
 assert trim(report)==trim(previous),(label,'strict report changed')
 assert report['selected_publication_ready'] is selected and report['complete'] is False and report['downstream_ready'] is False
 assert common.files(root)==before
 results.append({'publication':label,'reader':mode,'rows':count,'fields_per_row':16,'source_nodes':len(projection.nodes),'source_files':len(before),'identical_data_artifacts':len(outputs)-1,'IMAGE_positions':sum(row['full_text'].count('[IMAGE]') for row in projection.rows),'selected_publication_ready':selected,'strict_complete':False,'original_strict_report_unchanged':True,'source_input_unchanged':True,'proof_sha256':common.sha(pb),'family_report_sha256':common.sha(fb),'generated_artifact_sha256':{n:common.sha(b) for n,b in outputs.items()}})
assert source_before==package.code() and not calls
result={'passed':True,'source_code_before':source_before,'source_code_after':package.code(),'source_code_unchanged':True,'network_calls':calls,'site_packages_disabled':bool(sys.flags.no_site),'runtime':sys.version,'results':results,'total_rows':sum(x['rows'] for x in results),'scope':'Actual whole retained input projection/serialization equality against selected baselines. Albany uses corrected raw-source V3 and Cleveland includes the source-specific whole attachment; raw-source independent peer reports qualify their changed content. Other three baselines are historical source proofs; no current common-source acceptance rebind, new acquisition or stronger inherited completeness.'}
a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':True,'rows':result['total_rows'],'publications':len(results),'all_data_artifacts_unchanged':True}))
