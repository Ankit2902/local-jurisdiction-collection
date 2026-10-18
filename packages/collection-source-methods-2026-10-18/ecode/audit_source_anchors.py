import sys
sys.dont_write_bytecode=True
import json,hashlib,types,importlib,re,collections
from pathlib import Path
from bs4 import BeautifulSoup
B=Path(__file__).resolve().parent;R=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00/github/local-jurisdiction-collection');SRC=R/'packages/collection-source-recovery-2026-10-18/ecode/corrected-corpus-v3/evidence/input';records=[json.loads(x) for x in (SRC/'records.jsonl').read_text().splitlines()];cp=json.loads((SRC/'checkpoint.json').read_text());arts={a['path']:a for a in cp['artifacts']};ledger=json.loads((B/'original-review-ledger.json').read_text())['records'];pkg=types.ModuleType('_raw_audit');pkg.__path__=[str(B/'candidate')];sys.modules['_raw_audit']=pkg;A=importlib.import_module('_raw_audit.adapters');E=importlib.import_module('_raw_audit.engine');out=[]
# This census walks all original responses independently of the producer's strip logic.
raws={};headers=0
for a in cp['artifacts']:
 data=(SRC/a['path']).read_bytes();assert hashlib.sha256(data).hexdigest()==a['sha256']
 if a.get('status')==200 and b'<html' in data.lower():raws[a['path']]=BeautifulSoup(data,'html.parser');headers+=1
for i,row in enumerate(ledger):
 art=arts[row['raw_path']];assert art['sha256']==row['raw_sha256'];s=raws[row['raw_path']];root=s.find(id=row['owner_id']+'_content');assert root is not None
 matches=[]
 for a in root.find_all('a',href=True):
  nearest=next((p for p in a.parents if p.get('id') and re.fullmatch(r'[0-9]+_content',p['id'])),None)
  if nearest is root and a['href']==row['url'] and a.get_text(' ',strip=True)==row['label'] and 'statref' in a.get('class',[]):matches.append(a)
 assert matches
 # Repeated identical source occurrences remain distinct in the final 21-link census.
 a=matches[0];context=a.find_parent(['p','li','dd','td','div']) or a.parent;source=A.link_refs(str(a if False else root),'https://ecode360.com/'+row['owner_id'],row['owner_id']);hits=[l for l in source if l['url']==row['url'] and l['label']==row['label']];assert hits and all(E.statutory_reference(l['url'],cp['publication_url'],'ecode360',l) for l in hits)
 out.append({**row,'source_statref_explicit':True,'raw_owner_unique':len(s.find_all(id=row['owner_id']+'_content'))==1,'exact_source_context':context.get_text(' ',strip=True),'source_context_sha256':hashlib.sha256(str(context).encode()).hexdigest(),'candidate_classification':'external_statutory_reference','external_law_acquired':False,'candidate_evidence':hits[0]['source_statutory_evidence']})
# Independently census all still-required PDF source references and every acquisition attempt.
cov=json.loads((SRC/'coverage.json').read_text());required=[]
for url in cov['missing_assets']:
 refs=[]
 for r in records:
  for a in BeautifulSoup(r['content_html'],'html.parser').find_all('a',href=True):
   if A.urljoin(r['source_url'],a['href'])==url:refs.append({'owner_id':r['id'],'heading':r['heading'],'source_anchor':str(a),'raw_witnesses':[{'path':p,'sha256':arts[p]['sha256']} for p in r['raw_witnesses']]})
 assert refs;attempts=[a for a in cp['artifacts'] if a.get('requested_url')==url];required.append({'url':url,'source_references':refs,'attempts':attempts,'document_bytes_retained':any(a['role']=='asset' and a.get('status')==200 for a in attempts),'status':'HTTP403 stop; no document body' if any(a.get('status')==403 for a in attempts) else 'Not requested after persistent access stop'})
report={'all_original_raw_hashes_checked':len(cp['artifacts']),'successful_raw_HTML':headers,'occurrences':len(out),'distinct_urls':len({r['url'] for r in out}),'classifications':out,'required_PDFs':required,'closing_artifacts':[a for a in cp['artifacts'] if a['role'] in ['root-end','contents-end']],'opening_identity':cp['identity'],'errors':cov['errors'],'unchanged_falsegates':{k:cov[k] for k in ['publication_text_complete','attachments_complete','edition_complete','start_end_inventory_consistent','complete','resumable']},'new_requests':0,'nativePDFparse_performed':False};(B/'source-anchor-and-four-PDF-audit.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'raws':len(cp['artifacts']),'HTML':headers,'occurrences':len(out),'unique':len({r['url'] for r in out}),'four_PDFs':len(required),'closing':len(report['closing_artifacts'])}))
