"""Real official HTML parser: preserve bounded prose; refuse ambiguous pixel/prose."""
import argparse,hashlib,importlib.util,json,socket,sys
from pathlib import Path
from unittest.mock import patch

def main():
 ap=argparse.ArgumentParser();ap.add_argument('candidate',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 if a.out.exists():raise ValueError('Fresh output required')
 sys.path.insert(0,str(a.candidate));spec=importlib.util.spec_from_file_location('qa_official_boundaries',a.candidate/'model.py');model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model);before=hashlib.sha256((a.candidate/'model.py').read_bytes()).hexdigest();tail='UElYRUxTX0NPTlRJTlVBVElPTl9NVVNUX05PVF9TVVJWSVZF';uri='DATA:IMAGE/PNG;base64,QUJD';prefix='Every application shall apply the following requirement. Before legal text ';suffix=' after legal caption remains mandatory.';rows=[]
 cfg={'schema':1,'mode':'html_single','id':'fixture','jurisdiction':'Fixture','state':'NV','publication':'Fixture Code','content_selector':'main','legal_marker_regex':'shall apply'};item={'id':'fixture','heading':'Section1','url':'https://example.invalid/book/','raw_ref':'raw/fixture.html'}
 values=[('quoted',prefix+'"'+uri+'\n'+tail+'"'+suffix),('two-quoted',prefix+'"'+uri+'\n'+tail+'" between "'+uri+'\t'+tail+'"'+suffix)]+[('bare-'+name,prefix+uri+space+tail+suffix) for name,space in [('LF','\n'),('TAB','\t'),('SPACE',' ')]]
 def denied(*args,**kwargs):raise AssertionError('BOUNDARY_PROBE_NETWORK_FORBIDDEN')
 with patch.object(socket.socket,'connect',denied),patch.object(socket,'create_connection',denied):
  for name,text in values:
   try:
    records,_=model.html_records(('<html><main><h2>Section1</h2><p>'+text+'</p></main></html>').encode(),item,cfg);serial=json.dumps(records);body=records[0]['text'];error=None
   except ValueError as exc:records=None;serial='';body='';error=str(exc)
   bounded=name in ['quoted','two-quoted'];passed=(error is None and tail not in serial and 'data:image/' not in serial.lower() and 'Before legal text' in body and suffix.strip() in body) if bounded else error is not None
   rows.append({'case':name,'passed':passed,'normalized_text':body,'qualification_error':error,'continuation_leaked':tail in serial,'legal_suffix_retained':suffix.strip() in body})
 after=hashlib.sha256((a.candidate/'model.py').read_bytes()).hexdigest();report={'passed':all(x['passed'] for x in rows) and before==after,'model_sha256':before,'model_source_unchanged':before==after,'rows':rows,'network_requests_sent':0,'scope':'Synthetic legal-text path through realhtml_records. Bounded quoted URI replacement preserves actual prose; unbounded ambiguity must explicitly refuse qualification.'};a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
