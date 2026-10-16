#!/usr/bin/env python3
"""Bounded OCR-to-contract pilot for the official Santa Clara Charter first page.
This is not a municipal-code or whole-charter parser. Preserve OCR and page image.
"""
import argparse,csv,json,re,hashlib
from pathlib import Path
import ecode360 as e

def process(pdf,ocr_path,source_url,out):
 pdf=Path(pdf);ocr_path=Path(ocr_path);out=Path(out)
 if out.exists() and any(out.iterdir()):raise e.ValidationError('use a fresh empty output directory')
 if not source_url.startswith('https://santaclara.legistar.com/View.ashx?'):raise e.ValidationError('this pilot requires reviewed official Santa Clara attachment URL')
 ocr=e.load(ocr_path);page=int(ocr['processed_page_number']);rows=ocr['rows'];docsha=e.digest(pdf.read_bytes());ocrsha=e.digest(ocr_path.read_bytes());nodes=[];current=None;article=''
 for row in rows:
  line=row['text'];a=re.match(r'^Article ([IVXLCDM]+)\. (.+)',line)
  if a:article='Article '+a.group(1)+'. '+a.group(2);continue
  section=re.match(r'^§\s*(\d+)\.\s*(.*)',line)
  if section:
   current={'number':section.group(1),'heading':section.group(2),'article':article,'header_line':row['source_line_id'],'lines':[],'header_confidence':row['confidence']};nodes.append(current)
  elif current:current['lines'].append(row)
 records=[];dispositions=[];provenance=[]
 for n in nodes:
  identity='santa-clara-ca:city-charter:pdf-'+docsha+':page-'+str(page)+':'+n['header_line'];rid=e.digest(identity.encode())
  if not n['lines']:
   dispositions.append({'source_node_key':identity,'printed_number':n['number'],'disposition':'unresolved_at_page_boundary','reason':'heading visible but body not present in this one-page pilot'});continue
  if min([n['header_confidence']]+[r['confidence'] for r in n['lines']])<0.95:
   dispositions.append({'source_node_key':identity,'printed_number':n['number'],'disposition':'unresolved_low_ocr_confidence'});continue
  record={k:'' for k in e.FIELDS};record.update(jurisdiction='Santa Clara',code_name='City Charter (official attachment; bounded OCR pilot)',article=n['article'],section_number=n['number'],section_name=n['heading'],citation='§ '+n['number']+'. '+n['heading'],full_text=' '.join(r['text'] for r in n['lines']),source_url=source_url+'#page='+str(page),scrape_date=e.now()[:10]);records.append(record)
  provenance.append({'record_id':rid,'source_node_key':identity,'publication_id':'city-charter','pdf_sha256':docsha,'ocr_sha256':ocrsha,'page':page,'header_line_id':n['header_line'],'body_line_ids':[r['source_line_id'] for r in n['lines']],'body_bboxes':[r['bbox'] for r in n['lines']],'method':'macOS Vision OCR followed by bounded printed-header segmentation','human_visual_review_required':True,'full_document_complete':False})
  dispositions.append({'source_node_key':identity,'printed_number':n['number'],'disposition':'included_bounded_ocr_review_sample','record_ids':[rid]})
 out.mkdir(parents=True);e.dump(out/'fulltext.json',{'metadata':{'status':'bounded_ocr_review_sample','publication':'City Charter only','not_municipal_code':True,'full_collection_verified':False},'provisions':records})
 with (out/'fulltext.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=e.FIELDS);w.writeheader();w.writerows(records)
 with (out/'fulltext.csv').open(encoding='utf-8-sig',newline='') as f:
  if list(csv.DictReader(f))!=records:raise e.ValidationError('OCR CSV/JSON parity failed')
 e.jsonl(out/'provenance.jsonl',provenance);e.jsonl(out/'node-dispositions.jsonl',dispositions)
 report={'status':'partial_official_charter_ocr_review_output','source_url':source_url,'pdf_sha256':docsha,'ocr_sha256':ocrsha,'pages_processed':[page],'total_pdf_pages':ocr['pdf_page_count'],'detected_section_headers':len(nodes),'output_records':len(records),'unresolved_boundary_nodes':sum(x['disposition']=='unresolved_at_page_boundary' for x in dispositions),'source_acquisition_outside_codex':True,'ocr_outside_codex':True,'municipal_code_gap_closed':False,'whole_charter_parsed':False,'human_visual_review_required':True,'full_collection_verified':False,'output_sha256':{p.name:e.digest(p.read_bytes()) for p in out.iterdir() if p.is_file()}}
 e.dump(out/'report.json',report);return report

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pdf',required=True);p.add_argument('--ocr',required=True);p.add_argument('--source-url',required=True);p.add_argument('--out',required=True);a=p.parse_args();print(json.dumps(process(a.pdf,a.ocr,a.source_url,a.out),indent=2))
if __name__=='__main__':main()
