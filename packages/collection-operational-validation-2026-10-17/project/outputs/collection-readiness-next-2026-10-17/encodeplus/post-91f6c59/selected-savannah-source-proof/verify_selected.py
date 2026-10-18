"""Read-only selected native/source checks. Omitted whole corpus is never read or claimed."""
from pathlib import Path
import json,hashlib,io
from unittest.mock import patch,PropertyMock
from pypdf import PdfReader,PageObject
from bs4 import BeautifulSoup
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
 count=0
 for line in (HERE/'MANIFEST.sha256').read_text().splitlines():
  h,name=line.split('  ',1);p=(HERE/name).resolve();assert p.is_relative_to(HERE.resolve());assert sha(p)==h,name;count+=1
 scope=json.loads((HERE/'SCOPE.json').read_text());assert scope['whole_body_records']==5674 and scope['whole_required_documents_integrity_verified']==707;assert not scope['native_export_complete'] and not scope['edition_complete'] and not scope['jurisdiction_complete'];assert sha(HERE/'LOCAL-WHOLE-PROOF.sha256')==scope['local_wholeproof_hashmanifest_sha256']
 raw=HERE/'raw/full-primary-node6486.html';m=json.loads(raw.with_name(raw.name+'.receipt.json').read_text());assert sha(raw)==m['sha256']=='4f531d2bb5f91e69deb0f802252f87f1c46469d47093ca5e51d3407188358449';assert m['http_status']==200
 soup=BeautifulSoup(raw.read_text(encoding='utf-8'),'html.parser');node=soup.find('section',attrs={'data-secid':'6459'});assert node is not None;anchor=node.find('a',href='doclibrary.aspx?id=5b9f83a2-11c8-45c7-b8');assert anchor.get_text(strip=True)=='4-12-2018(3)';cells=[x.get_text(' ',strip=True) for x in anchor.find_parent('tr').find_all(['td','th'],recursive=False)];assert cells[-2:]==['1 Added','8-3370—8-3379']
 empty=soup.find('section',attrs={'data-secid':'6451'});assert empty is not None and empty.find(['h1','h2','h3','h4','h5','h6']).get_text(strip=True)=='8.9.11';clone=BeautifulSoup(str(empty),'html.parser')
 for h in clone.find_all(['h1','h2','h3','h4','h5','h6']):h.decompose()
 ledger=json.loads((HERE/'records/6451.json').read_text())['omitted_null_metadata'];assert ledger==['Effective on: 1/1/1901']
 for notice in clone.select('p.archiveNotice.nullValue'):
  assert ' '.join(notice.get_text(' ',strip=True).split())=='Effective on: 1/1/1901';notice.decompose()
 assert not clone.get_text(strip=True)
 adopted=HERE/'discovery/observed-enacted-2018-04-12-3.pdf';q=json.loads((HERE/'bindings/adopted-reference.json').read_text());assert sha(adopted)==q['expected_sha256'];reader=PdfReader(adopted,strict=True);assert len(reader.pages)==4;norm=lambda t:''.join(c.casefold() for c in t if c.isalnum());texts=[page.extract_text() or '' for page in reader.pages];assert [hashlib.sha256(norm(t).encode()).hexdigest() for t in texts]==q['page_text_sha256'];full=norm('\n'.join(texts));assert 'cityofsavannah' in full and 'adoptedandapprovedapril122018' in full;assert all('8337'+str(n) in full for n in range(10))
 record=json.loads((HERE/'records/6451.json').read_text());assert record['kind']=='confirmed_source_empty' and record['text']=='';binding=record['source_empty_qualification']['source_native_binding'];native=HERE/'selected-empty6451/native/attempt-0/publication.pdf';assert sha(native)==binding['selected_native_sha256']=='f310c987a7242ab7928571ee14f2ecab922d0854ffd5d50a74deb1e3e4f0bd5a';nr=PdfReader(native,strict=True);assert len(nr.pages)==2;assert [hashlib.sha256((p.extract_text() or '').encode()).hexdigest() for p in nr.pages]==binding['selected_native_page_text_sha256'];assert sha(HERE/'selected-empty6451/source-before.html')==sha(HERE/'selected-empty6451/source-after.html')
 failed=json.loads((HERE/'raw/original-malformed-404.bin.receipt.json').read_text());assert failed['http_status']==404;assert sha(HERE/'raw/original-malformed-404.bin')==failed['sha256'];draft=PdfReader(HERE/'discovery/proposed-article-q.pdf',strict=True);assert len(draft.pages)==5;assert 'adoptedandapprovedapril122018' not in norm('\n'.join(p.extract_text() or '' for p in draft.pages));stub=PdfReader(HERE/'native-whole-root-stub/publication.pdf',strict=True);assert len(stub.pages)==3
 return {'passed':True,'scope':'Selected source6459 adopted ordinance/6451source-empty qualification witnesses only','selected_manifest_files_checked':count,'adopted_native_pages':4,'adopted_sections_checked':10,'selected_empty_native_pages':2,'original404_and_excluded_draft_and_incomplete_stub_preserved':True,'whole_savannah_replay_self_contained':False,'whole_707_document_set_included':False,'local_hashmanifest_is_provenance_not_restoration_promise':True,'network_requests':0,'image_decode_extract_render_OCR_calls':0}
if __name__=='__main__':
 def forbidden(*a,**k):raise AssertionError('No network/image extraction')
 with patch('socket.socket',side_effect=forbidden),patch.object(PageObject,'images',new_callable=PropertyMock,side_effect=forbidden):result=verify()
 print(json.dumps(result,indent=2))
