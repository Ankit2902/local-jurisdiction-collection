#!/usr/bin/env python3
"""Offline native-PDF edition and bounded operative-body corroboration, never corpus segmentation."""
import hashlib,json,re,pathlib
import pypdfium2

def native_check(base,seq,folder,records,out):
 raw=base/'raw'/folder;receipt=json.loads((raw/'receipt.json').read_text());pdf=raw/'publisher-export.pdf';b=pdf.read_bytes();native=receipt['publisher_download']
 assert b.startswith(b'%PDF-') and hashlib.sha256(b).hexdigest()==native['sha256']
 doc=pypdfium2.PdfDocument(pdf);cover=doc[0].get_textpage().get_text_range();c=re.sub(r'\s+',' ',cover).upper()
 if seq==71: tokens=['SUPPLEMENT NO. 11','JUNE 2026','SAINT LOUIS','72042'];groups=[([171],records)]
 else:tokens=['SUPPLEMENT NO. 40','SEPTEMBER 2026','CHATTANOOGA','TENNESSEE','14374'];groups=[([157],records[:2]),(list(range(163,169)),records[2:3]),([319,320,321],records[3:])]
 for t in tokens:assert t in c,(seq,t)
 matches=[]
 for pages,rs in groups:
  text=' '.join(doc[i-1].get_textpage().get_text_range() for i in pages);terms=set(re.findall(r'[a-z]{4,}',text.lower()))
  for r in rs:
   body=set(re.findall(r'[a-z]{4,}',r['text'].lower()));coverage=len(body&terms)/len(body);assert coverage>=.90,(seq,r['id'],coverage)
   matches.append({'id':r['id'],'physical_pages':pages,'distinct_body_words_4plus_coverage':coverage,'minimum_required':.90,'word_count':len(body)})
 report={'native_pdf':str(pdf.relative_to(base)),'sha256':hashlib.sha256(b).hexdigest(),'page_count':len(doc),'cover_tokens_verified':tokens,'cover_text':cover,'api_publication_product_id':receipt['product']['ProductID'],'api_job_id':receipt['job']['Id'],'api_supplement':receipt['job']['Name'],'edition_match':'Printed supplement/date, ordinance number and jurisdiction match selected publisher job/banner; not only transport success. St. Louis / Saint Louis is an explicit name alias; state binding independently comes from client metadata.','operative_body_checks':matches,'record_count_from_pdf':0,'limitations':['Native PDF is retained whole; only bounded API excerpts corroborated against operative pages.','Word coverage permits PDF hyphenation and extraction differences; it is not an exact reconstruction test.','PDF TOC pages do not count as bodies.','Page images, diagrams and full-document tables are not reconstructed or checked. HTML table checks are separate; PDF table reconstruction was not tested.']}
 out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');doc.close();return report
