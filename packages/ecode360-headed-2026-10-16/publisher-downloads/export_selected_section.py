#!/usr/bin/env python3
"""Narrow PDF-native export for the observed one-page selected-section eCode PDFs. Offline only."""
from __future__ import annotations
import argparse,csv,datetime as dt,hashlib,json,re,unicodedata
from pathlib import Path
from bs4 import BeautifulSoup,NavigableString,Tag
import pdfplumber
from export_intake import Rejected
from qualify_download import qualify,digest
BLOCKS={'div','p','li','ul','ol','section','article','tr','h1','h2','h3','h4','h5','h6'}
def source_text(node):
 if isinstance(node,NavigableString):return str(node)
 if not isinstance(node,Tag) or node.name in ('script','style'):return ''
 if node.name=='br':return '\n'
 text=''.join(source_text(c) for c in node.children)
 return '\n'+text+'\n' if node.name in BLOCKS else text

def normalize(text):return re.sub(r'\s+',' ',unicodedata.normalize('NFC',text)).strip()
def parse_lines(text,jurisdiction):
 lines=[s.strip() for s in text.splitlines() if s.strip()]
 if len(lines)<4 or jurisdiction.casefold() not in lines[0].casefold():raise Rejected('PDF first line must independently identify expected jurisdiction')
 heading=re.fullmatch(r'(?:§\s*)?(\d[\dA-Za-z.-]*?)\.\s+(.+)',lines[1])
 if not heading:raise Rejected('unobserved citation/title layout; manual review required')
 footer=re.fullmatch(r'Downloaded from (https://ecode360\.com/[A-Za-z0-9]+) on (\d{4}-\d{2}-\d{2})',lines[-1])
 if not footer:raise Rejected('publisher backlink/date footer absent or unobserved layout')
 return {'pdf_jurisdiction_header':lines[0],'citation':heading.group(1),'section_title':heading.group(2),'body_text':'\n'.join(lines[2:-1]),'pdf_customer_backlink':footer.group(1),'publisher_download_date':footer.group(2)}

def export_section(file,receipt_path,source_path,out):
 if out.exists() and any(out.iterdir()):raise Rejected('section output must be new or empty')
 receipt=json.loads(receipt_path.read_text());upstream_path=(receipt_path.parent/receipt['upstream_receipt_path']).resolve();upstream=json.loads(upstream_path.read_text())
 if digest(source_path)!=upstream.get('sha256'):raise Rejected('source DOM SHA256 must match actual acquisition receipt')
 guid=receipt.get('selected_guid')
 if not guid:raise Rejected('canonical receipt selected_guid required')
 out.mkdir(parents=True,exist_ok=True);intake=qualify(file,receipt_path,out/'intake')
 if intake['sample_status']!='PASS':raise Rejected('PDF sample needs review before narrow text export')
 soup=BeautifulSoup(source_path.read_bytes(),'html.parser');body=soup.find(id=str(guid)+'_content');title=soup.select_one('.titleTitle[data-guid="'+str(guid)+'"]')
 if body is None or title is None:raise Rejected('selected source body/title missing')
 with pdfplumber.open(file) as pdf:
  if len(pdf.pages)!=1:raise Rejected('only observed one-page selected-section layout supported; multipage manual review')
  page=pdf.pages[0];native=page.extract_text() or '';record=parse_lines(native,receipt['jurisdiction']);tables=page.extract_tables();images=[{k:v for k,v in image.items() if k in ('x0','top','x1','bottom','width','height','srcsize','bits','imagemask','name')} for image in page.images]
 if record['citation'] not in receipt['selected_citations']:raise Rejected('PDF-derived citation disagrees with selected citation receipt')
 source_body=source_text(body);expected_title=title.get_text('',strip=False)
 comparisons={'full_body_equal_after_NFC_whitespace_normalization':normalize(source_body)==normalize(record['body_text']),'section_title_equal_after_NFC_whitespace_normalization':normalize(expected_title)==normalize(record['section_title']),'normalization':'NFC Unicode normalization and whitespace collapse only; no punctuation, history, footnote or legal-word removal.','expected_body_from_source':source_body,'actual_body_from_pdf':record['body_text'],'source_body_sha256':hashlib.sha256(normalize(source_body).encode()).hexdigest(),'pdf_body_sha256':hashlib.sha256(normalize(record['body_text']).encode()).hexdigest()}
 if not all(comparisons[k] for k in ('full_body_equal_after_NFC_whitespace_normalization','section_title_equal_after_NFC_whitespace_normalization')):semantic='REVIEW_REQUIRED_TEXT_MISMATCH'
 elif images or tables:semantic='REVIEW_REQUIRED_NON_TEXT_OR_TABLE_LAYOUT'
 else:semantic='PASS_BOUNDED_SELECTED_SECTION_TEXT'
 record.update(schema_version=1,source_pdf_sha256=digest(file),source_pdf_filename=file.name,source_url=receipt['source_url'],observed_download_url=receipt.get('observed_download_url'),selected_source_guid=guid,page=1,page_count=1,source_dom_sha256=digest(source_path),source_provenance='Body/citation/title parsed from PDF bytes; DOM is used solely for independent expected-text comparison.',publisher_edition_in_pdf=False,publisher_edition_context_from_receipt=receipt.get('currentness_check',{}),semantic_status=semantic,whole_publication_complete=False,nontext_regions=images,detected_tables=tables)
 (out/'section.json').write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n');(out/'source-comparison.json').write_text(json.dumps(comparisons,indent=2,ensure_ascii=False)+'\n');(out/'native-pdf-text.txt').write_text(native,encoding='utf-8')
 fields=['citation','section_title','body_text','pdf_jurisdiction_header','semantic_status','source_pdf_sha256','selected_source_guid','page','source_url','publisher_download_date','pdf_customer_backlink']
 with (out/'section.csv').open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerow(record)
 return record

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--file',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--source-html',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 try:r=export_section(a.file,a.receipt,a.source_html,a.out);print(json.dumps({'citation':r['citation'],'semantic_status':r['semantic_status'],'pdf_sha256':r['source_pdf_sha256'],'images':len(r['nontext_regions'])}));return 0 if r['semantic_status']=='PASS_BOUNDED_SELECTED_SECTION_TEXT' else 2
 except (Rejected,OSError,ValueError,KeyError) as e:print(json.dumps({'status':'REJECTED','error':str(e)}));return 1
if __name__=='__main__':raise SystemExit(main())
