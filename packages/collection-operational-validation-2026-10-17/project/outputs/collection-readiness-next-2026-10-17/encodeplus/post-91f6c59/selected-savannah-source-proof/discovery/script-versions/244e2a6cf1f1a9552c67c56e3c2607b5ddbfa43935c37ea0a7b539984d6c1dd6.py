from pathlib import Path
import sys,json,hashlib,shutil,datetime
here=Path(__file__).resolve().parent;project=here.parents[3];repo=project/'github/local-jurisdiction-collection';sys.path.insert(0,str(repo));from collectors.encodeplus.transport import fetch
out=here/'savannah-alternative-discovery';url='https://online.encodeplus.com/regs/savannah-ga/doclibrary.aspx?id=5b9f83a2-11c8-45c7-b8de-e4f23038d768'
proof={'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'discovery_method':'web search returned exact publisher URL; no UUID suffix construction or malformed-URL retry','queries':['site.savannahga.gov "2018" "8-3370" ordinance','site.savannahga.gov "April 12, 2018" "Conservation" ordinance','site.agenda.savannahga.gov "17-007079" "ordinance"'],'result_title':'Ordinance of 04-12-2018 (3)','result_url':url,'result_extract':'ADOPTED AND APPROVED: APRIL 12, 2018; Map 2: Ardmore Conservation District (CD-2)','prior_malformed_url':'https://online.encodeplus.com/regs/savannah-ga/doclibrary.aspx?id=5b9f83a2-11c8-45c7-b8','prior_failure_preserved':True};(out/'enacted-native-search-provenance.json').write_text(json.dumps(proof,indent=2)+'\n')
for p in [Path(__file__),repo/'collectors/encodeplus/transport.py',repo/'collectors/encodeplus/util.py']:
 h=hashlib.sha256(p.read_bytes()).hexdigest();shutil.copy2(p,out/'script-versions'/(h+'.py'))
data,meta=fetch(url,out/'observed-enacted-2018-04-12-3.pdf');print(json.dumps({'http_status':meta['http_status'],'sha256':meta['sha256'],'bytes':len(data)},indent=2))
