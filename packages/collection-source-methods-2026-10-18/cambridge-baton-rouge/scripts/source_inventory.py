"""Pure source-bound inventory; does not request any link."""
import sys
sys.dont_write_bytecode=True
import hashlib,json
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from bs4 import BeautifulSoup
URL='https://www.brla.gov/706/Unified-Development-Code'
SHA='250b6cb5676687c8be23036fa4b677e6bb2f359330e5266fc4d7834df6eccf5d'
SELECTOR='main .relatedDocumentsSection:has(> h3:-soup-contains("Chapters")) a.fileType.pdf[href], main .relatedDocumentsSection:has(> h3:-soup-contains("Appendices")) a.fileType.pdf[href]'
def inventory(raw):
 assert hashlib.sha256(raw).hexdigest()==SHA,'Source bytes/version differ; requalification required'
 s=BeautifulSoup(raw,'html.parser')
 out=[];hidden=[]
 for group,count in [('Chapters',19),('Appendices',11),('Draft Ordinances (none)',0)]:
  boxes=[b for b in s.select('main .relatedDocumentsSection')if b.find('h3',recursive=False)and b.find('h3',recursive=False).get_text(' ',strip=True)==group]
  assert len(boxes)==1,'Source group missing/duplicated'
  box=boxes[0];anchors=box.select('a.fileType.pdf[href]');assert len(anchors)==count
  actual=[]
  for a in anchors:
   url=urljoin(URL,a['href']);u=urlsplit(url);label=a.get_text(' ',strip=True);ident=a.parent.get('data-documentid')
   assert u.scheme=='https'and u.hostname=='www.brla.gov'and u.path.startswith('/DocumentCenter/View/'+ident+'/')
   actual.append(ident);out.append({'ordinal':len(out),'group':group,'source_document_id':ident,'label':label,'url':url})
  configured=[x for x in box.get('data-documentids','').split(',')if x]
  sorted_ids=[x for x in box.get('data-sorteddocumentids','').split(',')if x]
  hidden.extend({'group':group,'source_document_id':x,'in_documentids':x in configured,'in_sorteddocumentids':x in sorted_ids,'disposition':'unlinked_widget_metadata_unqualified_no_URL_invented'}for x in dict.fromkeys(configured+sorted_ids) if x not in actual)
 assert len(s.select(SELECTOR))==30 and len({r['url']for r in out})==30
 assert [r['label'].split(' - ')[0]for r in out[:19]]==['Chapter '+str(i)for i in range(1,20)]
 assert [r['label'].split(' - ')[0]for r in out[19:]]==['Appendix '+c for c in 'ABCDEFGHIJK']
 return {'source_url':URL,'source_sha256':SHA,'selected_visible_documents':out,'document_count':30,'chapter_count':19,'appendix_count':11,'unlinked_widget_metadata':hidden,'full_publication_qualification':False}
def main():
 root=Path(__file__).resolve().parents[1];d=inventory((root/'source/95-152a3da8bd28.html').read_bytes())
 (root/'brla-udc-inventory.json').write_text(json.dumps(d,indent=2)+'\n')
 cfg={'schema':1,'id':'95-baton-rouge-udc-official-chapters-appendices','jurisdiction':'Baton Rouge, East Baton Rouge Parish','state':'LA','publication':'Unified Development Code - nineteen Chapters and eleven Appendices on official index','source_url':URL,'mode':'pdf_set','transport':'http','document_transport':'http','inventory_selector':SELECTOR,'include_url_regex':r'^https://www[.]brla[.]gov/DocumentCenter/View/[0-9]+/[^?#]+$','source_currency_selector':'main h1','source_identity_tokens':['Unified Development Code','Chapter 1 - General Provisions','Appendix K - Stormwater BMPs','Draft Ordinances (none)'],'coverage_level':'file_pages','pdf_normalization':'coordinate-v1','scope_warning':'Exactly thirty visible source-owned chapter/appendix PDFs. Seven unlinked widget metadata IDs remain unqualified; no URLs inferred. No county-wide, enacted-amendment, edition or full legal-semantic acceptance from file_pages capture. Reserved appendices retained. Native originals may intrinsically contain images; no separate image requests/decode/render/OCR; exact[IMAGE].'}
 (root/'configs/brla-udc-current-visible-documents.json').write_text(json.dumps(cfg,indent=2)+'\n')
 print(json.dumps({'visible_documents':30,'unlinked_widget_metadata':d['unlinked_widget_metadata']}))
if __name__=='__main__':main()
