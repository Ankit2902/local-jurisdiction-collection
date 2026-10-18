"""Pure retained HTML/canonical source inventory analysis; no network or images."""
from pathlib import Path
import json,hashlib,sys
from bs4 import BeautifulSoup
P=Path(__file__).resolve().parent;s=BeautifulSoup((P/'clark-county-code.html').read_bytes(),'html.parser');container=s.select('main .table.bordered.bid');assert len(container)==1
rows=container[0].find_all('div',recursive=False);documents=[]
for order,row in enumerate(rows):
 cols=row.find_all('div',recursive=False)
 if not cols:continue
 a=cols[0].find('a',href=True)
 if not a:continue
 assert len(cols)==4
 documents.append({'source_order':len(documents),'ordinance':a.get_text(' ',strip=True),'url':a['href'],'title':cols[1].get_text(' ',strip=True),'adopted_literal':cols[2].get_text(' ',strip=True),'effective_literal':cols[3].get_text(' ',strip=True),'source_row_html':str(row),'source_row_sha256':hashlib.sha256(str(row).encode()).hexdigest(),'owner_source_url':json.loads((P/'clark-county-code.receipt.json').read_text())['url'],'owner_source_sha256':hashlib.sha256((P/'clark-county-code.html').read_bytes()).hexdigest()})
assert len(documents)==22 and [r['ordinance']for r in documents]==list(map(str,range(5388,5410)))
links=[{'label':a.get_text(' ',strip=True),'url':a['href']}for a in s.select('main a[href]')if 'library.municode.com' in a['href']];assert links==[{'label':'Clark County Code','url':'https://library.municode.com/nv/clark_county/codes/code_of_ordinances'}]
output={'schema':1,'source_url':documents[0]['owner_source_url'],'source_sha256':documents[0]['owner_source_sha256'],'inventory_container_selector':'main .table.bordered.bid','inventory_anchor_selector':'main .table.bordered.bid > div > div:first-child a[href]','published_codification_statement':s.select_one('main .rightsection').get_text(' ',strip=True).split('The following table')[0],'codified_publication_reference':{'alias_of':'96-primary','source_link':links[0],'disposition':'Existing required county-code primary; publisher stop preserved; not acquired or erased by this independent ordinance inventory.'},'uncodified_ordinances':documents,'scope':'Exactly22PDFslisted bycountyClerkasnotyet codified. Source list may lagothercode publications; do not infer allcurrentcounty ordinances or mergeintoTitle30. Nativeimagesintrinsic originals allowed; no separatelygrabbedimages orpixels.'}
(P/'clark-uncodified-inventory.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'current_uncodified_anchors':len(documents),'document_hosts':sorted({r['url'].split('/')[2]for r in documents}),'codified_primary_alias':links,'clark_scope_is_alias_only':False},indent=2))
