"""Narrow independent candidate binding/image/public-reader audit; no acquisition."""
import argparse,hashlib,importlib,importlib.util,json,socket,sys,types
from pathlib import Path
from unittest.mock import patch,PropertyMock
from bs4 import BeautifulSoup

def main():
 ap=argparse.ArgumentParser();ap.add_argument('candidate',type=Path);ap.add_argument('--raw',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 if a.out.exists():raise ValueError('Fresh report required')
 folder=a.candidate/'collectors/encodeplus';pkg=types.ModuleType('independent_ep_candidate');pkg.__path__=[str(folder)];sys.modules[pkg.__name__]=pkg
 rel=importlib.import_module(pkg.__name__+'.reference_qualifications');docs=importlib.import_module(pkg.__name__+'.documents');model=importlib.import_module(pkg.__name__+'.model')
 sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.glob('*.py')};raw=a.raw.read_bytes();soup=BeautifulSoup(raw,'html.parser');checks=[]
 def check(name,value):checks.append({'name':name,'passed':bool(value)});assert value,name
 check('context_witness_raw_binding',all(v['raw_sha256']==hashlib.sha256(raw).hexdigest() for v in rel.CONTEXTS.values()))
 matched={};negatives=0
 for el in soup.find_all('a',href=True):
  result=rel.authority_reference(el,rel.BASE)
  if not result:continue
  matched[result['source_context_sha256']]=True
  for base in [rel.BASE+'other/','https://example.invalid/regs/fairfaxcounty-va-pfm/']:
   check('wrong_publication_does_not_dispose',rel.authority_reference(el,base) is None);negatives+=1
  clone=BeautifulSoup(str(el.find_parent(['p','li','td']) or el.parent),'html.parser');anchor=clone.find('a',href=el['href'])
  anchor['href']=el['href']+'wrong';check('changed_target_remains_required',rel.authority_reference(anchor,rel.BASE) is None);negatives+=1
  anchor['href']=el['href'];(anchor.find_parent(['p','li','td']) or anchor.parent).append(' CHANGED LEGAL CONTEXT');check('changed_context_remains_required',rel.authority_reference(anchor,rel.BASE) is None);negatives+=1
 check('all_exact17_contexts_found_in_actual_raw',set(matched)==set(rel.CONTEXTS))
 cfg={'base':rel.BASE,'identity':'Fixture Code','jurisdiction':'Fairfax County VA','scope':'image regression'}
 body='<h2>Image provision</h2><table><tr><td background="outer.png">Outer<table><tr><td><img src="DATA:IMAGE/PNG;base64,PIXELS"></td></tr></table></td></tr></table><object type="IMAGE/PNG" data="opaque"></object>'
 rows=model.parse_document('<div id="thePage" secid="1"><section data-secid="1">'+body+'</section></div>','1',cfg,{'1':{'heading':'Image provision','has_children':False}})
 record=rows[0];check('normalized_no_inline_payload','PIXELS' not in json.dumps(record));check('nested_cells_image_markers',all('[IMAGE]' in e.get_text() for e in BeautifulSoup(record['body_html'],'html.parser').select('td')));check('image_only_refs_not_required',not any(x.get('required') for x in record['assets']));check('active_image_html_absent',not BeautifulSoup(record['body_html'],'html.parser').select('img,picture,svg,[background]'))
 from pypdf._page import PageObject
 import pypdfium2 as pdfium
 def denied(*args,**kwargs):raise AssertionError('IMAGE_OR_NETWORK_API_FORBIDDEN')
 native=folder/'fixtures/public-open-pfm-sheet.pdf';data=native.read_bytes()
 with patch.object(socket.socket,'connect',denied),patch.object(PageObject,'images',new_callable=PropertyMock,side_effect=denied),patch.object(pdfium.PdfPage,'render',denied),patch.object(pdfium.PdfPage,'get_objects',denied),patch.object(pdfium.PdfImage,'extract',denied),patch.object(pdfium.PdfImage,'get_bitmap',denied):
  result=docs.qualify_document(data,'https://example.invalid/original.pdf','application/pdf');check('actual_native_public_open_without_credentials',result['pages']>0 and result['public_open_encryption']['credentials_supplied'] is False)
  for value in [b'',b'%PDF-1.7\n%%EOF',data[:100]]:
   try:docs.qualify_document(value,'https://example.invalid/original.pdf','application/pdf');valid=True
   except ValueError:valid=False
   check('empty_or_truncated_rejected',not valid)
 check('candidate_runtime_unchanged',sources=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.glob('*.py')})
 report={'passed':True,'candidate_sources':sources,'raw_sha256':hashlib.sha256(raw).hexdigest(),'native_sha256':hashlib.sha256(data).hexdigest(),'native_result':result,'exact_contexts':len(matched),'adverse_context_checks':negatives,'checks':checks,'network_requests_sent':0,'scope':'Candidate only: exact authority cross-reference scope and ordinary public-reader byte integrity, not publication semantics or production promotion.'};a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'checks':len(checks),'contexts':len(matched),'pages':result['pages']}))
if __name__=='__main__':main()
