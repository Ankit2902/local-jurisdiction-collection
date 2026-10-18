import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib,re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
B=Path(__file__).resolve().parent;R=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00/github/local-jurisdiction-collection');S=R/'packages/collection-source-recovery-2026-10-18/ecode/corrected-corpus-v3/evidence/input';report=json.loads((B/'source-anchor-and-four-PDF-audit.json').read_text());out=[]
for entry in report['required_PDFs']:
 refs=[]
 for owner in entry['source_references']:
  for witness in owner['raw_witnesses']:
   raw=(S/witness['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==witness['sha256'];doc=BeautifulSoup(raw,'html.parser');roots=doc.find_all(id=owner['owner_id']+'_content');assert len(roots)==1
   for a in roots[0].find_all('a',href=True):
    nearest=next((p for p in a.parents if p.get('id') and re.fullmatch(r'[0-9]+_content',p['id'])),None)
    if nearest is roots[0] and urljoin('https://ecode360.com/'+owner['owner_id'],a['href'])==entry['url']:
     refs.append({'owner_id':owner['owner_id'],'owner_heading':owner['heading'],'source_raw_path':witness['path'],'source_raw_sha256':witness['sha256'],'raw_anchor_html_sha256':hashlib.sha256(str(a).encode()).hexdigest(),'literal_href':a['href'],'literal_label':a.get_text(' ',strip=True),'classes':a.get('class',[]),'data_title':a.get('data-title'),'inline_icon_references':len(a.find_all(['img','svg','picture'])),'source_statref_class_present':'statref' in a.get('class',[])})
 assert refs;out.append({'url':entry['url'],'raw_source_owners':refs,'required':True,'status':entry['status'],'image_policy':'Original raw anchor may reference an icon; no icon/image or PDF body acquired here'})
(B/'four-PDF-raw-source-owner-bindings.json').write_text(json.dumps({'passed':True,'documents':out,'PDF_body_parse_or_acquisition':False,'normalization_note':'source-anchor-and-four-PDF-audit.source_references.source_anchor is already-normalized body HTML (icon=[IMAGE]); this supplementary audit binds the original raw anchor separately without projecting its image markup.'},indent=2)+'\n');print(json.dumps({'documents':len(out),'owner_bindings':sum(len(e['raw_source_owners']) for e in out),'acquisition':False}))
