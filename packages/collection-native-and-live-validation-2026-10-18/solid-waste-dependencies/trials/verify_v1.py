"""Offline source/dependency proof recomputation. No producer imports or network."""
import hashlib,json,pathlib,re
from bs4 import BeautifulSoup
from pypdf import PdfReader
BASE=pathlib.Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
 b=BASE/'retained-chapter-binding';proof=json.loads((b/'proof.json').read_text());records=[json.loads(x) for x in (b/'chapter-records.jsonl').read_text().splitlines()];assert len(records)==40 and len({r['id'] for r in records})==40
 raw=b/'raw/title7-start.html';end=b/'raw/title7-end.html';assert sha(raw)==sha(end)==proof['raw_title7_start_sha256']==proof['raw_title7_end_sha256']
 source=BeautifulSoup(raw.read_bytes(),'html.parser');sections=[s for s in source.find_all('section',attrs={'data-secid':True}) if '_007-010' in s.get('class',[])];assert [s['data-secid'] for s in sections]==[r['id'] for r in records]==proof['source_dom_order'];assert records[0]['id']=='1578'
 for s,r in zip(sections,records):
  assert r['raw_sha256']==sha(raw) and r['body_sha256']==hashlib.sha256(r['html'].encode()).hexdigest();assert s['data-secid']==r['id'];assert r['parent_id']==('1296' if r['id']=='1578' else '1578')
 assert len(sections)==proof['owned_units']==40 and proof['operative_units']==39
 by={r['id']:r for r in records};county=by['1593'];assert 'Johnson County, Kansas' in county['text'] and '2010 Edition' in county['text'] and '(as may be amended from time to time)' in county['text'] and 'Ord. SW-2927 §7, 2011' in county['text']
 native=BASE/'raw/overland-sixpage-source.pdf';assert sha(native)==proof['same_native_sha256']=='1af70bb8170cf2701cfb9e7ede2b274bf848309ca6fcaa3b7a7eeba9cd426c39'
 for sid in ['1586','1612']:assert any('doclibrary.aspx?id=68642c1d-ce7d-4ab0-a9e3-cf56d6def79a' in a['url'] for a in by[sid]['links'])
 post=json.loads((b/'post2011-amendment-evidence.json').read_text());assert len(post)==7 and all(any(y>2011 for y in r['years']) for r in post) and not proof['reusable_as_2011_edition_equivalent'] and proof['new_publisher_requests']==0
 land=BASE/'raw/county-landing.html';pdf=BASE/'raw/county-code.pdf';lr=json.loads((land.with_name(land.name+'.receipt.json')).read_text());pr=json.loads((pdf.with_name(pdf.name+'.receipt.json')).read_text())
 for file,receipt in [(land,lr),(pdf,pr)]:assert sha(file)==receipt['sha256'] and file.stat().st_size==receipt['bytes'] and receipt['status']==200 and not receipt.get('access_stop') and not receipt.get('policy_omitted_image')
 bs=BeautifulSoup(land.read_bytes(),'html.parser');matches=[a for a in bs.find_all('a',href=True) if 'Johnson County Code of Regulations for Solid Waste Management' in a.get_text(' ',strip=True)];assert len(matches)==1
 binding=json.loads((BASE/'official-link-binding.json').read_text());assert binding['observed_url']==pr['url'] and matches[0]['href']==pr['url'] and binding['landing_sha256']==sha(land)
 reader=PdfReader(pdf,strict=True);assert len(reader.pages)==43;front=reader.pages[0].extract_text();assert '2010 Edition' in front and '068-10' in front and '074-14' in front
 acquisition=json.loads((BASE/'county-acquisition.json').read_text());assert acquisition['source_sha256']==sha(pdf)=='17a96ce506109a96f8a2c432fe97f9b7c78443bc15a433861da9456b73000193' and acquisition['front_page_text']==front and acquisition['edition_equivalence_to_2011_sixpage_source']==acquisition['all_semantic_text_tables_reading_order_qualified']==False
 return {'passed':True,'retained_chapter_owned_units':40,'source_start_end_equal':True,'reciprocal_sixpage_native_identity_equal':True,'county_identity_source_owner':'1593','county_official_pdf_pages':43,'county_official_pdf_sha256':sha(pdf),'official_direct_HTTP200_count':2,'new_publisher_requests':0,'historical_2011_edition_binding':False,'county_full_semantic_text_tables_reading_order':False,'image_fetch_decode_extract_render_OCR':False}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
