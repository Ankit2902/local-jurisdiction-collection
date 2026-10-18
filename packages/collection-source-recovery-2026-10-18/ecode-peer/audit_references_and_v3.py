"""Bounded independent source reference identity + residue guard controls."""
import sys
sys.dont_write_bytecode=True
import hashlib,importlib,json,socket,base64,types
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from unittest.mock import patch
from bs4 import BeautifulSoup
ROOT=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00');B=ROOT/'outputs/collection-readiness-post716cfcb-2026-10-17/ecode-recovery-audit-v1';S=ROOT/'outputs/collection-readiness-post-91f6c59-2026-10-17/ecode/albany-image-context-replay-v2';T=B/'albany-derived-v3';OUT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();records=[json.loads(x) for x in (T/'records.jsonl').read_text().split('\n') if x];cp=json.loads((S/'checkpoint.json').read_text());original_files={p.relative_to(S).as_posix():sha(p) for p in S.rglob('*') if p.is_file()};refs=[];calls=[]
for r in records:
 for asset in r['assets']:
  if asset.get('kind')!='owned_definition_self_anchor':continue
  proof=asset['source_target'];raw=S/r['raw_witnesses'][0];soup=BeautifulSoup(raw.read_bytes(),'html.parser');body=soup.find(id=r['id']+'_content');target=proof['definition_id'];hits=body.find_all(id=target);assert len(hits)==1;definition=hits[0];assert definition.name=='section' and 'definition' in definition.get('class',[]);term=definition.find('dfn',class_='term');anchor=term.find('a',class_='termLink');assert anchor and anchor.get('onclick','').strip()=='return false;';url=urlsplit(urljoin(r['source_url'],anchor['href']));assert url.scheme=='https' and url.netloc=='ecode360.com' and url.path=='/'+target and url.fragment==target and not url.query
  nearest=definition.find_parent(lambda x:x.get('id','').endswith('_content') and x.get('id','')[:-8].isdigit() and 'content' in x.get('class',[]));assert nearest is body;assert definition.find(class_='deftext').get_text(strip=True);assert proof['owner_id']==r['id'] and proof['body_root_id']==body['id'] and asset['required'] is False and asset['image'] is False
  refs.append({'source_owner_id':r['id'],'source_target_id':target,'raw_path':r['raw_witnesses'][0],'raw_sha256':sha(raw),'literal_href':anchor['href'],'label':anchor.get_text(),'source_inert_term_anchor':True,'target_unique_and_already_in_same_body':True,'candidate_classification':asset['kind']})
assert {(x['source_owner_id'],x['source_target_id']) for x in refs}=={('33432619','33432651'),('33432619','33433083'),('33430088','38049117')}
# This imports only frozen candidate parser modules under guards, never transport.
name='_independent_ecode_v3';package=types.ModuleType(name);package.__path__=[str(B/'candidate-v3')];sys.modules[name]=package
artifact=next(x for x in cp['artifacts'] if x['role']=='content' and x['status']==200);raw=(S/artifact['path']).read_bytes();expect=cp['identity'];tests=[]
def no(*a,**k):calls.append('forbidden_network_or_decode');raise AssertionError(calls[-1])
with patch.object(socket.socket,'connect',no),patch.object(base64,'b64decode',no):
 adapter=importlib.import_module(name+'.adapters')
 for empty in [False,True]:
  soup=BeautifulSoup(raw,'html.parser');n=soup.new_tag('div',attrs={'class':'content contentTitle'});n.string='' if empty else 'INDEPENDENT UNOWNED LEGAL BODY';soup.find(id='codeContent').append(n)
  try:adapter.parse_ecode(str(soup).encode(),artifact['url'],expect);raise AssertionError('Combined class unknown body was suppressed')
  except adapter.QualificationError as e:assert 'Unowned legal content container' in str(e);tests.append({'case':'empty unknown content+contentTitle' if empty else 'operative unknown content+contentTitle','refused':True,'reason':str(e)})
 soup=BeautifulSoup(raw,'html.parser');body=next(e for e in soup.find_all(True) if e.get('id','').endswith('_content') and e.get('id','')[:-8].isdigit() and 'content' in e.get('class',[]));n=soup.new_tag('div',attrs={'class':'content contentTitle'});n.string='INDEPENDENT OWNED LEGAL BODY';body.append(n);got=adapter.parse_ecode(str(soup).encode(),artifact['url'],expect);assert any('INDEPENDENT OWNED LEGAL BODY' in x['semantic_html'] for x in got['records']);tests.append({'case':'same combined classes inside exact own GUID body','retained':True})
assert not calls and original_files=={p.relative_to(S).as_posix():sha(p) for p in S.rglob('*') if p.is_file()}
coverage=json.loads((T/'coverage.json').read_text());assert len(coverage['missing_assets'])==4 and all('/attachment/336787/' in x and x.endswith('.pdf') for x in coverage['missing_assets']);assert coverage['complete'] is False
report={'passed':True,'three_source_explicit_definition_references':refs,'required_nonimage_PDFs_still_missing':coverage['missing_assets'],'complete':False,'additional_unresolved_link_fields':{k:v for k,v in coverage.items() if 'link' in k and 'unresolved' in k},'independent_v3_guard_controls':tests,'forbidden_calls':calls,'all_original_458_files_unchanged':len(original_files)==458,'candidate_adapters_sha256':sha(B/'candidate-v3/adapters.py'),'candidate_engine_sha256':sha(B/'candidate-v3/engine.py'),'auditor_sha256':sha(Path(__file__)),'full_original_source_normalization_acquisition_native_parse_calls':0,'bounded_in_memory_modified_source_guard_parser_calls':len(tests)};(OUT/'reference-and-v3-guard-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
