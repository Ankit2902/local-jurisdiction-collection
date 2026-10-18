"""Two observed official sources only; serial shared host gate, no retries/images."""
import hashlib,io,json,pathlib,sys,urllib.parse
from bs4 import BeautifulSoup
from pypdf import PdfReader
import official_transport as transport
BASE=pathlib.Path(__file__).resolve().parents[1]
URL='https://www.jocogov.org/department/environment/solid-waste/solid-waste-management-plan'
def save(name,data,receipt):
 assert not (BASE/'raw'/name).exists(),'Never overwrite source evidence'
 (BASE/'raw'/name).write_bytes(data);(BASE/'raw'/(name+'.receipt.json')).write_text(json.dumps(receipt,indent=2)+'\n')
def main():
 assert not (BASE/'county-acquisition.json').exists() and not (BASE/'raw/county-landing.html').exists(),'Existing capture: refuse before any request'
 before={}
 for host in ['www.jocogov.org','jocogov.org','www.opkansas.org','opkansas.org']:
  path=transport.ROOT/hashlib.sha256(host.encode()).hexdigest()[:20]/'state.json';before[host]={'path':str(path),'exists':path.exists(),'state':json.loads(path.read_text()) if path.exists() else None}
 assert all(not (row['state'] or {}).get('stop') for row in before.values()),'Observed existing stop; do not request'
 (BASE/'host-state-before.json').write_text(json.dumps(before,indent=2)+'\n')
 body,receipt=transport.fetch(URL,max_bytes=5_000_000);save('county-landing.html',body,receipt)
 if receipt.get('access_stop') or receipt['status']!=200:return {'status':'stopped','receipt':receipt}
 soup=BeautifulSoup(body,'html.parser');matches=[a for a in soup.find_all('a',href=True) if 'Johnson County Code of Regulations for Solid Waste Management' in a.get_text(' ',strip=True)]
 assert matches,'Official named regulation link absent'
 urls=list(dict.fromkeys(urllib.parse.urljoin(receipt['final_url'],a['href']) for a in matches));assert len(urls)==1
 url=urls[0];assert urllib.parse.urlparse(url).hostname=='www.jocogov.org' and urllib.parse.urlparse(url).scheme=='https' and urllib.parse.urlparse(url).path.lower().endswith('.pdf')
 evidence={'landing_sha256':receipt['sha256'],'landing_url':URL,'observed_anchor_html':[str(a) for a in matches],'observed_url':url};(BASE/'official-link-binding.json').write_text(json.dumps(evidence,indent=2)+'\n')
 data,receipt=transport.fetch(url,max_bytes=20_000_000);save('county-code.pdf',data,receipt)
 if receipt.get('access_stop') or receipt['status']!=200:return {'status':'stopped','receipt':receipt}
 assert data.startswith(b'%PDF-')
 reader=PdfReader(io.BytesIO(data),strict=True);text=reader.pages[0].extract_text()
 assert '2010 Edition' in text and '074-14' in text and '068-10' in text and len(reader.pages)==43
 result={'status':'native-candidate-acquired','source_sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'pages':len(reader.pages),'url':url,'front_page_text':text,'front_page_sha256':hashlib.sha256(text.encode()).hexdigest(),'native_title_edition':'2010 Edition amended by Resolution074-14','initial_adoption_resolution':'068-10','issuing_authority':'Johnson County, Kansas; Board of County Commissioners; Johnson County Environmental Department','source_scope':'Official landing linked43page county code; amended2014, not proven unamended2010 version or2011equivalent','all_semantic_text_tables_reading_order_qualified':False,'edition_equivalence_to_2011_sixpage_source':False,'currentness_beyond_official_live_link':False,'image_policy':'literal [IMAGE]; no separate image fetch/decode/extract/render/OCR','new_publisher_requests':False,'official_government_requests':2,'transport_source_sha256':hashlib.sha256((BASE/'source/official_transport.py').read_bytes()).hexdigest(),'collector_source_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()}
 return result
if __name__=='__main__':
 result=main();(BASE/'county-acquisition.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));sys.exit(0 if result['status']=='native-candidate-acquired' else 2)
