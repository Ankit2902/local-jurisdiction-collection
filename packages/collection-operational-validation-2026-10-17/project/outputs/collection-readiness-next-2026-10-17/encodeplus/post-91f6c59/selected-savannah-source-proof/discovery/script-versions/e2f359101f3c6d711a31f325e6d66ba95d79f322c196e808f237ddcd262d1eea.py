from pathlib import Path
import sys,json,hashlib,datetime,shutil
here=Path(__file__).resolve().parent;project=here.parents[3];repo=project/'github/local-jurisdiction-collection';sys.path.insert(0,str(repo));from collectors.encodeplus.transport import fetch
from collectors.encodeplus.collect import runtime_info
out=here/'savannah-alternative-discovery';out.mkdir(exist_ok=True);scripts=out/'script-versions';scripts.mkdir(exist_ok=True)
for p in [Path(__file__),repo/'collectors/encodeplus/transport.py',repo/'collectors/encodeplus/util.py']:
 h=hashlib.sha256(p.read_bytes()).hexdigest();shutil.copy2(p,scripts/(h+'.py'))
url='https://agenda.savannahga.gov/publishing/april-12-2018-city-council-regular-meeting/agenda.html'
(out/'discovery.json').write_text(json.dumps({'scope':'Exactofficial April12,2018 councilagenda route observedinwebsearch; no guessedUUID or badURLretry','url':url,'original_required_url':'https://online.encodeplus.com/regs/savannah-ga/doclibrary.aspx?id=5b9f83a2-11c8-45c7-b8','source_owner_id':'6459','source_owner_heading':'CODE COMPARATIVE TABLE - ORDINANCES','source_owner_body_sha256':'24009f90de284ccb9f1d8a0c0d3a0942074235fd955ff489b596a56622380277','source_table_label':'4-12-2018(3),1Added,8-3370–8-3379','recorded_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runtime':runtime_info()},indent=2)+'\n')
data,meta=fetch(url,out/'agenda.html');print({'status':meta['http_status'],'bytes':len(data),'sha256':meta['sha256']})
