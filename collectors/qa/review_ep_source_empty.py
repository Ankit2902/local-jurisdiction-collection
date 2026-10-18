"""Actual six-source/native empty-node review and fail-closed boundary faults."""
import argparse,copy,hashlib,importlib,io,json,re,shutil,socket,sys,tempfile,types
from pathlib import Path
from unittest.mock import patch
from bs4 import BeautifulSoup
from pypdf import PdfReader
from pypdf.generic import EncodedStreamObject

def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--family',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 if a.out.exists():raise ValueError('Fresh report required')
 pkg=types.ModuleType('qa_ep_empty');pkg.__path__=[str(a.family)];sys.modules[pkg.__name__]=pkg;m=importlib.import_module('qa_ep_empty.source_empty_qualifications');fixture_raw=(a.family/'fixtures/overland-source-empty-records.json').read_bytes();fixture=json.loads(fixture_raw);records=fixture['records'];config=fixture['config'];checks=[];native=[]
 def check(name,passed):checks.append({'name':name,'passed':bool(passed)})
 def deny(*a,**k):raise AssertionError('No network/image decode allowed')
 old=EncodedStreamObject.get_data
 def safe(stream,*args,**kwargs):
  if stream.get('/Subtype')=='/Image':raise AssertionError('No image stream decode')
  return old(stream,*args,**kwargs)
 with patch.object(socket.socket,'connect',deny),patch.object(socket,'create_connection',deny),patch.object(EncodedStreamObject,'get_data',safe):
  baseline=m.qualify(copy.deepcopy(records),config);check('exact_six_classify',sum(r['kind']=='confirmed_source_empty' for r in baseline.values())==6);check('parent7941_entire_record_unchanged',baseline['7941']==records['7941'])
  for ident,q in m.QUALIFICATIONS.items():
   r=records[ident];rawhtml=BeautifulSoup(r['body_html'],'html.parser');visible=' '.join(rawhtml.get_text(' ',strip=True).split());check(ident+'_actual_html_only_heading_or_empty',visible in ['',r['heading']]);check(ident+'_no_source_assets_or_images',not r['assets'] and not r['image_refs'])
   data=(a.family/q['selected_native_path']).read_bytes();receipt=json.loads((a.family/(q['selected_native_path']+'.receipt.json')).read_text());pdf=PdfReader(io.BytesIO(data),strict=True);text='\n'.join(p.extract_text() or '' for p in pdf.pages);check(ident+'_actual_native_sha_page_text',sha(data)==q['selected_native_sha256'] and len(pdf.pages)==1 and sha(m.normalize(text).encode())==q['selected_native_text_sha256']);check(ident+'_actual_source_receipt',receipt['sha256']==sha(data) and receipt['http_status']==200 and receipt['url']==q['selected_native_source_url'] and receipt['final_url']==receipt['url'])
   remaining=m.normalize(re.sub(r'Page\s+\d+','',text,flags=re.I));allowed=q['allowed_observed_heading_path']+(records['7941']['text'].splitlines() if ident=='7942' else [])
   for value in sorted(allowed,key=lambda value:len(m.normalize(value)),reverse=True):remaining=remaining.replace(m.normalize(value),'')
   check(ident+'_all_native_characters_accounted_for',not remaining);native.append({'id':ident,'native_sha256':sha(data),'native_url':receipt['url'],'native_text':text,'pages':len(pdf.pages),'raw_sha256':r['raw_sha256'],'body_sha256':r['body_sha256'],'classification_scope':q['source_surface_disposition']})
   keys=['text','raw_sha256','body_sha256','source_url','heading','parent_id','canonical_body_key','path']
   for key in keys:
    changed=copy.deepcopy(records);changed[ident][key]=[] if key=='path' else 'WRONG_SOURCE_OR_OPERATIVE_BODY';got=m.qualify(changed,config);check(ident+'_wrong_'+key+'_refused',got[ident]['kind']!='confirmed_source_empty')
   check(ident+'_record_body_tables_html_preserved',all(baseline[ident].get(k)==r.get(k) for k in r if k not in ('kind','disposition')))
  changed_config=copy.deepcopy(config);changed_config['identity']='Another jurisdiction';check('wrong_config_refused',all(r['kind']!='confirmed_source_empty' for r in m.qualify(copy.deepcopy(records),changed_config).values()))
  changed=copy.deepcopy(records);changed.pop('7941');check('missing_parent_refused',m.qualify(changed,config)['7942']['kind']!='confirmed_source_empty');changed=copy.deepcopy(records);changed['7941']['text']+=' changed clause';check('changed_parent_refused',m.qualify(changed,config)['7942']['kind']!='confirmed_source_empty')
  with tempfile.TemporaryDirectory() as td:
   clone=Path(td);shutil.copytree(a.family/'fixtures/overland-source-empty',clone/'fixtures/overland-source-empty');original_here=m.HERE;m.HERE=clone
   try:
    for ident,q in m.QUALIFICATIONS.items():
     p=clone/q['selected_native_path'];data=p.read_bytes();p.write_bytes(data[:-32]);check(ident+'_truncated_native_refused',m.qualify(copy.deepcopy(records),config)[ident]['kind']!='confirmed_source_empty');p.write_bytes(data)
     witness=clone/q['fixture_witnesses'][0]['path'];data=witness.read_bytes();witness.unlink();check(ident+'_missing_bound_source_witness_refused',m.qualify(copy.deepcopy(records),config)[ident]['kind']!='confirmed_source_empty');witness.write_bytes(data)
   finally:m.HERE=original_here
 report={'passed':all(x['passed'] for x in checks),'checks':checks,'check_count':len(checks),'actual_native_evidence':native,'source_module_sha256':sha(Path(m.__file__).read_bytes()),'source_fixture_sha256':sha(fixture_raw),'source_config_canonical_sha256':m.hash_json(config),'no_separate_image_download':True,'no_image_decode_render_extraction_or_OCR':True,'network_requests_sent':0,'scope':'Only six exact config/source/hierarchy/parent/native editions. Empty bodies remain empty; parent7941 owns its exact substantive paragraphs. No generic empty-heading/repeal exclusion, no invented legal body, no whole-jurisdiction or native-book edition pass.'};a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'checks':len(checks),'failures':[x['name'] for x in checks if not x['passed']]}));return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
