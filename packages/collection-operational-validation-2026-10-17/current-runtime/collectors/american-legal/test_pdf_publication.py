"""Network-free complete PDF publication collection, verifier and real page-cache resume."""
import base64,contextlib,copy,io,json,tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import collect,pdf_tags
from model import digest
from test_pdf_tags import fixture
from transport import save
from verify import verify
def sources():
 code={'uuid':'pdf-code','slug':'fixture_pdf','title':'Independent PDF Book','is_pdf':True,'sections':[{'id':1,'doc_id':'PDF-ROOT','title':'Independent PDF Book','has_children':False}]};version={'uuid':'pdf-edition','name':'PDF edition','currency_info':'Synthetic only','client_slug':'pdfcity','toc':[code]};state={'codes':{'currClient':{'slug':'pdfcity','name':'PDF City','region':{'slug':'oh'}},'selectedVersion':version}};overview=('<script>window._redux_state = JSON.parse('+json.dumps(json.dumps(state))+')</script>').encode();url='https://files.amlegal.com/source.pdf'
 return {'https://codelibrary.amlegal.com/codes/pdfcity/latest/overview':overview,'https://codelibrary.amlegal.com/api/sec-info/pdfcity/pdf-edition/fixture_pdf/PDF-ROOT/':json.dumps({'doc_id':'PDF-ROOT','version_uuid':'pdf-edition','code_uuid':'pdf-code','pdf_path':url}).encode(),url:fixture()}
class Browser:
 raw=sources();calls=[]
 def __init__(self):type(self).calls=[]
 def call(self,op,url=None,**kwargs):
  type(self).calls.append((op,url));body=self.raw[url];return {'body':base64.b64encode(b'' if op=='head' else body).decode(),'url':url,'status':200,'headers':{'content-type':'application/pdf' if url.endswith('.pdf') else 'text/html'},'browser':'synthetic-no-network','runtime':'synthetic'}
 def close(self):pass
def args(out,resume=False):return SimpleNamespace(out=out,url='https://codelibrary.amlegal.com/codes/pdfcity/latest/fixture_pdf',jurisdiction='PDF City',state='OH',publication='fixture_pdf',identity_alias=[],resume=resume,strategy='traverse',assets='download',max_items=None)
def run(a):
 with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):return collect.run(a)
def tests():
 results=[]
 with tempfile.TemporaryDirectory() as t,patch.object(collect,'Browser',Browser):
  root=Path(t);baseline=root/'baseline';assert run(args(baseline))==0;coverage=verify(baseline);assert coverage['publication_complete'] and coverage['publication_text_complete'] and coverage['pdf_semantic_text_completeness_qualified'] and coverage['pdf_table_completeness_qualified'] and not coverage['pdf_legal_provision_segmentation_qualified'];assert coverage['pdf_tagged_source_table_count']==1 and coverage['pdf_tagged_source_cell_count']==3;results.append({'name':'full_synthetic_tagged_publication_all_source_pages_tables_and_inventory_qualified_separate_from_inferred_legal_segmentation','passed':True})
  original=pdf_tags.parse;invoked=[]
  def interrupt(data,cache_dir=None,interrupt_after=None):
   invoked.append(True);return original(data,cache_dir,interrupt_after=1)
  interrupted=root/'interrupted'
  with patch.object(pdf_tags,'parse',interrupt):assert run(args(interrupted))==2
  assert invoked and len(list((interrupted/'pdf-tag-cache').glob('*/page-0001.json')))==1
  try:verify(interrupted);raise RuntimeError('Interrupted run accepted')
  except AssertionError:pass
  resumed_code=run(args(interrupted,True));assert resumed_code==0,json.loads((interrupted/'run.json').read_text());assert verify(interrupted)['publication_complete'];assert not any(op=='binary' for op,url in Browser.calls),'Resume unexpectedly fetched retained native PDF bytes'
  for name in ['sections.jsonl','pdf-pages.jsonl','inventory.json']:assert (interrupted/name).read_bytes()==(baseline/name).read_bytes()
  results.append({'name':'production_PDF_first_page_interruption_resume_reuses_native_bytes_and_matches_uninterrupted_whole_book','passed':True})
  for name,mutate in [('omitted_middle_owned_MCID',lambda p:p[0]['tagged_page']['blocks'].pop(1)),('changed_source_cell_span',lambda p:p[0]['tagged_document']['tables'][0]['rows'][0][0].update(colspan=9)),('continuation_page_missing',lambda p:p.pop()),('duplicated_page_body',lambda p:p.append(copy.deepcopy(p[0]))),('source_ActualText_omitted',lambda p:p[0]['tagged_page']['inline_actual_text'].clear())]:
   path=baseline/'pdf-pages.jsonl';original_bytes=path.read_bytes();pages=[json.loads(v) for v in original_bytes.splitlines()];mutate(pages);path.write_bytes(b''.join(json.dumps(p,ensure_ascii=False).encode()+b'\n' for p in pages))
   try:verify(baseline);raise RuntimeError('Fault accepted '+name)
   except AssertionError:results.append({'name':name,'passed':True})
   finally:path.write_bytes(original_bytes)
 return {'schema_version':1,'kind':'Synthetic production PDF publication/cache/resume/verifier integration, not live law proof','passed':True,'count':len(results),'tests':results}
if __name__=='__main__':
 result=tests();Path(__file__).with_name('pdf-publication-tests.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
