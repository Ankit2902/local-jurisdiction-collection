#!/usr/bin/env python3
"""Bounded original official PDF transport and page-preserving text extraction. Not a section parser."""
import argparse, csv, datetime, hashlib, json, pathlib, platform, re, urllib.request, urllib.error, time
from pypdf import PdfReader
ROOT=pathlib.Path(__file__).resolve().parents[1]
SOURCES={
'providence-ri':{'url':'https://www.providenceri.gov/wp-content/uploads/2026/10/26.07.22-Official-Zoning-Ordinance.pdf','publication':'Zoning Ordinance (current official PDF linked by city zoning route)'},
'jackson-ms':{'url':'https://jacksonms.gov/wp-content/uploads/2026/06/COJ-Zoning-Ordinance-Amended-December-2024.pdf','publication':'Zoning Ordinance (official current route; amended December2024 in filename)'},
'huntsville-al':{'url':'https://www.huntsvilleal.gov/wp-content/uploads/2026/04/ZonOrd_as_of_01April2026.pdf','publication':'Zoning Ordinance (official city PDF)'},
'cheyenne-wy':{'url':'https://www.cheyennecity.org/files/sharedassets/public/departments/planningdevelopment/udc/udc-2022.pdf','publication':'Unified Development Code (official city PDF; amended through April 1, 2022 per route)'},
'charleston-wv':{'url':'https://www.charlestonwv.gov/sites/default/files/documents/2024-10/Zoning%20Ordinance.pdf','publication':'Zoning Ordinance (official city PDF; file path 2024-10, current-through date not qualified)'}}
def sha(b):return hashlib.sha256(b).hexdigest()
def run(slug,offline=False):
 conf=SOURCES[slug];out=ROOT/'official-pdf'/slug;out.mkdir(parents=True,exist_ok=True);pdf=out/'source.pdf';rp=out/'source.pdf.receipt.json'
 if not offline:
  meta={'url':conf['url'],'acquired_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runtime':platform.python_version(),'script_sha256':sha(pathlib.Path(__file__).read_bytes())}
  try:
   with urllib.request.urlopen(urllib.request.Request(conf['url'],headers={'User-Agent':'Mozilla/5.0 (compatible; bounded code validation)'}),timeout=60) as r:b=r.read();meta.update(status=r.status,final_url=r.url,headers=dict(r.headers))
  except urllib.error.HTTPError as e:b=e.read();meta.update(status=e.code,headers=dict(e.headers),error=str(e))
  except Exception as e:b=b'';meta.update(status=None,error=str(e))
  pdf.write_bytes(b);meta.update(bytes=len(b),sha256=sha(b));rp.write_text(json.dumps(meta,indent=2));time.sleep(3)
 meta=json.loads(rp.read_text());assert sha(pdf.read_bytes())==meta['sha256']
 if meta['status']!=200 or not pdf.read_bytes().startswith(b'%PDF-'):return {'slug':slug,'passed':False,'receipt':meta}
 reader=PdfReader(pdf);rows=[]
 # Retain pages 1..15 verbatim in page records; section identities are observed snippets only.
 page_indices=([19,20,21]+list(range(23,35))) if slug=='huntsville-al' else list(range(min(15,len(reader.pages))))
 for i in page_indices:
  p=reader.pages[i]
  text=p.extract_text(extraction_mode='layout') or '';headings=re.findall(r'(?mi)^\s*(?:Sec(?:tion)?\.?\s*)?\d+(?:[.\-]\d+)+(?:\s+|\s*[-–—]\s*)[^\n]{2,110}',text)
  rows.append({'jurisdiction':slug,'publication':conf['publication'],'record_kind':'pdf_page','page_number':i+1,'source_url':conf['url']+'#page='+str(i+1),'source_pdf_sha256':meta['sha256'],'observed_heading_candidates':headings,'full_text':text})
 (out/'normalized.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
 with (out/'normalized.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows({**r,'observed_heading_candidates':json.dumps(r['observed_heading_candidates'])} for r in rows)
 checks=[{'name':'original_PDF_signature','passed':True},{'name':'retained_source_hash','passed':True},{'name':'nonempty_page_records','passed':all(r['full_text'].strip() for r in rows)},{'name':'observed_heading_candidates','count':sum(len(r['observed_heading_candidates']) for r in rows)}]
 report={'slug':slug,'passed':all(c.get('passed',True) for c in checks),'scope':'physical PDF pages '+','.join(str(i+1) for i in page_indices)+'; page records; no section-boundary or table reconstruction claim','pdf_pages':len(reader.pages),'record_count':len(rows),'checks':checks,'source':meta}
 (out/'report.json').write_text(json.dumps(report,indent=2));return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('slug',choices=list(SOURCES)+['all']);p.add_argument('--offline',action='store_true');a=p.parse_args()
 for slug in SOURCES if a.slug=='all' else [a.slug]:print(json.dumps(run(slug,a.offline)))
