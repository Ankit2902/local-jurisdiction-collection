#!/usr/bin/env python3
"""Network-free Savannah selected native-PDF verification; default writes nothing."""
import argparse,pathlib,json,re,hashlib
from bs4 import BeautifulSoup
from pypdf import PdfReader
from parse import decode,sha,clean
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--render',type=pathlib.Path,help='Optional new directory for all4page PNGs; never overwrites');a=p.parse_args();receipts=0;snapshots=0
 for path in ROOT.rglob('*.receipt.json'):
  if '.venv' in path.parts:continue
  m=json.loads(path.read_text());raw=path.with_name(path.name[:-len('.receipt.json')]);assert sha(raw.read_bytes())==m['sha256'];receipts+=1
 for path in ROOT.rglob('script-versions/*'):
  if path.is_file():assert path.stem==sha(path.read_bytes());snapshots+=1
 source=ROOT/'source/87-impact-fee7137.html';m=json.loads(source.with_name(source.name+'.receipt.json').read_text());soup=BeautifulSoup(decode(source.read_bytes(),m['headers']),'html.parser');section=soup.select_one('section[data-secid="7137"]');assert section;control=soup.find('a',title='Export PDF');assert control and 'OpenPDF("001.004.008.017.013",false)' in control['onclick'];js=(ROOT/'raw/observed-doc-view.js').read_text();assert 'var mURL = "export2doc.aspx?pdf=1&tocid=" + id' in js
 reader=PdfReader(ROOT/'native/publisher.pdf');assert len(reader.pages)==4;assert reader.metadata.title=='Savannah, Georgia City of Savannah Code of Ordinances';assert 'Aspose.Words' in reader.metadata.producer
 text='\n'.join(page.extract_text() for page in reader.pages);assert text==(ROOT/'native/publisher-text.txt').read_text();flat=clean(text);heading=clean(section.find(re.compile('^h[1-6]$')).get_text(' ',strip=True));assert heading in flat
 table=section.find('table');rows=table.find_all('tr');cells=[clean(c.get_text(' ',strip=True)) for c in table.find_all(['td','th'])];assert len(rows)==79 and len(cells)==555
 unmatched=[c for c in cells if c and c not in flat];assert not unmatched,unmatched;fee_row=[clean(c.get_text(' ',strip=True)) for c in rows[3].find_all(['td','th'])];assert len(fee_row)==8 and fee_row[0]=='Single-Family Detached Housing' and fee_row[6]=='$3,930.8511';assert clean(' '.join(fee_row)) in flat,'Single-family8cell row not contiguous/ordered in nativePDFtext'
 assert 'Effective on: 7/1/2023' in flat
 report=json.loads((ROOT/'native/export.json').read_text());assert report['status']=='passed' and report['pdf_sha256']==sha((ROOT/'native/publisher.pdf').read_bytes())
 if (ROOT/'MANIFEST.sha256').exists():
  for line in (ROOT/'MANIFEST.sha256').read_text().splitlines():
   digest,relative=line.split('  ',1);assert sha((ROOT/relative).read_bytes())==digest,relative
 if a.render:
  assert not a.render.exists(),'New render directory required';a.render.mkdir(parents=True)
  import pypdfium2
  doc=pypdfium2.PdfDocument(ROOT/'native/publisher.pdf')
  for i in range(len(doc)):doc[i].render(scale=1.25).to_pil().save(a.render/('page-'+str(i+1)+'.png'))
 print(json.dumps({'status':'passed','network_used':False,'read_only':not bool(a.render),'raw_receipts_verified':receipts,'script_snapshots_verified':snapshots,'publication_identity':reader.metadata.title,'heading':heading,'section_id':'7137','native_pdf_pages':len(reader.pages),'native_pdf_bytes':(ROOT/'native/publisher.pdf').stat().st_size,'native_pdf_sha256':report['pdf_sha256'],'source_table_rows':len(rows),'source_table_cells':len(cells),'all_cell_texts_present_in_pdf':True,'single_family_eight_cell_row_ordered_match':fee_row,'effective_date_matches':'7/1/2023','scope':'Only Attachment A. Impact Fee Schedule; not full Savannah code','limitations':['Cell-text presence does not establish every PDF row/column layout relationship','No additional unique legal records counted beyond official-sources existing section7137','No whole-code current-through or corpus completeness claim']},indent=2))
if __name__=='__main__':main()
