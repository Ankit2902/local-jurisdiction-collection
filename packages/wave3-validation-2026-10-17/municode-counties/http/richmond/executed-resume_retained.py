"""Offline continuation after a coordinated family stop; no content synthesized/no network."""
import json,hashlib,platform,shutil
from pathlib import Path
from normalize import normalize
ROOT=Path(__file__).resolve().parents[1]
def run(name):
 d=ROOT/'http'/name;product=json.loads((d/'product-response.json').read_text())['Model'];job=json.loads((d/'job.json').read_text());samples=json.loads((d/'samples.json').read_text());cc=json.loads((d/'client-content.json').read_text());responses=[]
 for p in sorted(d.glob('*.receipt.json')):
  r=json.loads(p.read_text());body=d/r['raw_file'];assert hashlib.sha256(body.read_bytes()).hexdigest()==r['sha256'];responses.append({'url':r['url'],'status':r['http_status'],'file':body.name,'sha256':r['sha256'],'retrieved_at':r['finished_at']})
 r={'url':'https://library.municode.com/va/richmond/codes/code_of_ordinances','status':'sample_acquired_driver_stopped','method':'standalone-public-http-acquisition-with-offline-retained-continuation','product':product,'job':job,'responses':responses,'publications':cc.get('codes',[]),'selected_nodes':[{'id':s['node']['Id'],'heading':s['node']['Heading']} for s in samples],'publisher_download':{'status':'not_tested','reason':'PDF URL resolution succeeded, but binary request was not started before coordinator stopped publisher family for challenges observed in other groups.'},'complete_corpus':False,'runtime':platform.platform(),'executed_collector_sha256':hashlib.sha256((d/'executed-collect_http.py').read_bytes()).hexdigest(),'offline_continuation_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'stop_context':'Core/root requested coordinated publisher pause after denied Cincinnati/Fairfax routes. This Richmond sample had only200responses; no retry or parallel browser probe was made.'}
 toc=json.loads((d/'toc-full.json').read_text());r['families_top_level']=[{'id':n['Id'],'heading':n.get('Heading')} for n in toc.get('Children',[])]
 (d/'receipt.json').write_text(json.dumps(r,indent=2));report=normalize(d);(d/'continuation-validation.json').write_text(json.dumps(report,indent=2));shutil.copyfile(__file__,d/'executed-resume_retained.py');print(json.dumps(report,indent=2))
if __name__=='__main__':run('richmond')
