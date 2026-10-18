"""Concrete source-evidenced MRSC successor binding proposal; never auto-promotes incorporation."""
import argparse,json,re,sys
from pathlib import Path
from urllib.parse import urljoin
from source_common import *
URL='https://mrsc.org/explore-topics/public-records/pra/public-records-act-basics'
INDEX='https://mrsc.org/publications'
def run(successor,out):
 src=Path(successor).resolve();base=load(src/'checkpoint.json');out=Path(out).resolve()
 if out.exists() and any(out.iterdir()):raise ValueError('Fresh binding output required')
 out.mkdir(parents=True,exist_ok=True);state={'artifacts':[],'errors':[],'complete':False,'adoption_binding_complete':False,'source_url':URL,'code_fingerprint':source_snapshot(out,['king_mrsc_binding_candidate.py','source_common.py','shared_transport.py']),'successor_provenance':{'checkpoint_sha256':sha((src/'checkpoint.json').read_bytes()),'native_sha256':base['source_pdf_sha256'],'native_url':base['native_url'],'publisher_edition':'December 2025','pdf_pages':base['pdf_pages']}};save(out/'checkpoint.json',state)
 for a in base['artifacts']:
  if sha((src/a['path']).read_bytes())!=a['sha256']:raise ValueError('Corrupt retained MRSC source')
 try:
  raw,a=acquire(out,state,'publisher-scope-description',URL);s=BeautifulSoup(decode(raw)[0],'html.parser');statements=[]
  for p in s.select('p'):
   text=clean(p.get_text(' ',strip=True))
   if 'Appendix C' in text and ('exemption' in text.lower() or 'adopt' in text.lower()):statements.append(text)
  state['publisher_appendix_scope_statements']=statements
  raw,a=acquire(out,state,'publisher-index-closing',INDEX);s=BeautifulSoup(decode(raw)[0],'html.parser');state['current_native_route_still_listed']=any(urljoin(INDEX,x['href'])==base['native_url'] for x in s.select('a[href]'))
  state['proposal']={'original_incorporated_url':'http://www.mrsc.org/Publications/pra06.pdf','original_route_outcome':'404 after publisher redirects; retained separately','source_code_language':'most-recent list posted on MRSC website, Appendix C, incorporated by reference','candidate_current_native_url':base['native_url'],'edition':'December 2025','suggested_scope':'Appendix C only','source_identity_evidence':'Current official publisher list and current publisher explanatory page explicitly connect PRA publication/Appendix C with exemptions and adoption by reference','remaining_review':'Old County wording describes other statutes generally; current MRSC page calls Appendix C selected federal exemptions. Preserve scope-change distinction and qualify attachment text/tables with existing strict PDF importer before resolving incorporation automatically.','automatic_substitution':False}
 except Exception as e:state['errors'].append({'type':type(e).__name__,'message':str(e)})
 save(out/'checkpoint.json',state);return state
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--successor',required=True);p.add_argument('--out',required=True);a=p.parse_args();r=run(a.successor,a.out);print(json.dumps(r,indent=2));sys.exit(2)
