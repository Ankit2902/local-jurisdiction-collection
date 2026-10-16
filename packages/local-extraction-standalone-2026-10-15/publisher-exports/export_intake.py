#!/usr/bin/env python3
"""Verify an operator-supplied publisher export without executing HTML or inferring legal completeness."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import platform
import re
import shutil
from pathlib import Path
from urllib.parse import urlsplit

MAX_BYTES=30*1024*1024
KINDS=('publisher-export','publisher-print-preview','browser-print','unknown')

class Rejected(ValueError): pass

def sha256(data): return hashlib.sha256(data).hexdigest()

def source_url(value):
 p=urlsplit(value)
 if p.scheme!='https' or not p.hostname or p.username or p.password:
  raise Rejected('source_url must be an HTTPS public URL without embedded credentials')
 return value

def sniff(data):
 head=data[:4096].lstrip()
 if head.startswith(b'%PDF-'): return 'pdf'
 if head.startswith(b'{\\rtf'): return 'rtf'
 if head.startswith(b'PK\x03\x04'): raise Rejected('ZIP/DOCX is not supported; preserve original and use a reviewed converter')
 try: text=data.decode('utf-8-sig')
 except UnicodeDecodeError: raise Rejected('unsupported binary or non-UTF-8 text; no guessed decoding')
 if '\x00' in text: raise Rejected('NUL bytes in text')
 if re.search(r'<(?:!doctype\s+html|html|body|head|title|div|section|p|h[1-6]|table)\b',text[:4096],re.I): return 'html'
 return 'txt'

def validate_provenance(prov):
 required=('source_url','jurisdiction','publication','selection_scope','retrieved_at','artifact_kind','acquisition_mode','edition_evidence')
 for k in required:
  if not isinstance(prov.get(k),str) or not prov[k].strip(): raise Rejected('missing nonempty provenance '+k)
 source_url(prov['source_url'])
 if prov['artifact_kind'] not in KINDS: raise Rejected('invalid artifact_kind')
 if prov['acquisition_mode'] not in ('unattended-standalone','operator-browser-download','retained-replay'): raise Rejected('invalid acquisition_mode')
 try:
  when=dt.datetime.fromisoformat(prov['retrieved_at'].replace('Z','+00:00'))
  if when.utcoffset() is None: raise ValueError('timezone missing')
 except ValueError: raise Rejected('retrieved_at must be ISO8601 with timezone')
 return prov

def parse_sample(data,kind,pages=None):
 import bs4
 report={'format':kind,'tables':[],'text':'','text_extraction_status':'PASS','review_gates':[]}
 if kind=='html':
  soup=bs4.BeautifulSoup(data.decode('utf-8-sig'),'html.parser')
  title=soup.title.get_text(' ',strip=True) if soup.title else ''
  report['title']=title
  for tag in soup(['script','style','noscript']):tag.decompose()
  report['text']=soup.get_text('\n',strip=True)
  # Cell spans and source HTML are retained. Flattened row strings are only a convenience.
  for i,table in enumerate(soup.find_all('table')):
   report['tables'].append({'ordinal':i+1,'html':str(table),'rows':[[{'text':cell.get_text(' ',strip=True),'rowspan':cell.get('rowspan','1'),'colspan':cell.get('colspan','1')} for cell in row.find_all(['th','td'],recursive=False)] for row in table.find_all('tr')]})
  visible=report['text'].lower()
  # Structural challenge/auth evidence, not blanket legal-word filtering.
  if any(x in title.lower() for x in ('access denied','just a moment','attention required','forbidden','sign in','log in')) or soup.select('form input[type=password],#challenge-form,[id^=cf-chl]'):
   raise Rejected('HTML authentication/challenge/error page, not verified code export')
  if len(visible)<80: raise Rejected('HTML too short to qualify as substantive content')
  report['review_gates']+=['Confirm selection boundaries, headings, history/footnotes and external attachments against publisher page.','HTML tables preserved with spans; complex table meaning still requires source comparison.']
 elif kind=='pdf':
  import io,pdfplumber
  with pdfplumber.open(io.BytesIO(data)) as pdf:
   count=len(pdf.pages)
   if count<1:raise Rejected('PDF has no pages')
   selected=sorted(set(pages or [1,count]))
   if len(selected)>20:raise Rejected('bounded verification permits at most20 selected pages')
   if any(x<1 or x>count for x in selected):raise Rejected('selected PDF page outside document')
   report.update(page_count=count,sampled_pages=selected,pages=[])
   for number in selected:
    page=pdf.pages[number-1];text=page.extract_text(layout=True) or '';tables=page.extract_tables()
    report['pages'].append({'page':number,'width':page.width,'height':page.height,'text':text,'word_count':len(page.extract_words()),'image_count':len(page.images),'tables':tables})
    report['text']+=f'\n[PAGE {number}]\n'+text
    for i,table in enumerate(tables):report['tables'].append({'page':number,'ordinal':i+1,'rows':table})
    if not text.strip() or len(page.extract_words())<10:
     report['text_extraction_status']='REVIEW_REQUIRED'
     report['review_gates'].append(f'Page {number}: sparse/no text; image/OCR review required.')
    elif page.images:report['review_gates'].append(f'Page {number}: mixed image/text; inspect visual content before use.')
  report['review_gates']+=['Render selected PDF pages and compare legal text, tables, footnotes, headers and page continuations.','Only selected PDF pages were parsed; full document and legal completeness remain unverified.']
 elif kind=='rtf':
  report['review_gates']+=['RTF identified by signature but no semantic parser supplied; use a reviewed RTF converter and compare tables/footnotes.']
 else:
  report['text']=data.decode('utf-8-sig')
  if len(report['text'].strip())<80:raise Rejected('text too short to qualify as substantive content')
  report['review_gates']+=['Plain text cannot prove table geometry or retained images; compare with HTML/PDF publisher source.']
 return report

def inspect(path,prov,expected_format=None,expected_sha=None,pages=None,expect=()):
 validate_provenance(prov)
 if path.stat().st_size>MAX_BYTES:raise Rejected('input exceeds30MiB bounded sample limit')
 data=path.read_bytes()
 if not data:raise Rejected('empty input')
 digest=sha256(data)
 if expected_sha and digest!=expected_sha.lower():raise Rejected('input SHA256 mismatch')
 kind=sniff(data)
 if expected_format and kind!=expected_format:raise Rejected(f'format mismatch: expected {expected_format}, detected {kind}')
 try: sample=parse_sample(data,kind,pages)
 except Rejected: raise
 except Exception as e: raise Rejected(f'{kind} parsing failed: {type(e).__name__}: {e}') from e
 missing=[s for s in expect if s not in sample['text']]
 if missing:raise Rejected('expected source sample absent: '+repr(missing))
 return {'schema_version':1,'verified_at':dt.datetime.now(dt.timezone.utc).isoformat(),'runtime':{'python':platform.python_version()},'input':{'filename':path.name,'sha256':digest,'bytes':len(data)},'provenance_claim':prov,'integrity_status':'PASS','sample_text_expectations':list(expect),'sample_status':'REVIEW_REQUIRED' if kind=='rtf' or sample['text_extraction_status']=='REVIEW_REQUIRED' or not expect else 'PASS','text_expectation_status':'MATCHED' if expect else 'UNSPECIFIED','method_e2e_status':'NOT_QUALIFIED_BY_FILE_INTAKE_ALONE','legal_semantic_status':'MANUAL_REVIEW_REQUIRED','scope_completeness_status':'NOT_PROVEN','source_authenticity_status':'OPERATOR_PROVENANCE_REQUIRES_EXTERNAL_RECEIPT','browser_print_is_publisher_export':False,'sample':sample}

def write_result(path,prov,out,**kwargs):
 if out.exists() and any(out.iterdir()): raise Rejected('output directory must be new or empty; existing evidence never overwritten')
 result=inspect(path,prov,**kwargs)
 out.mkdir(parents=True,exist_ok=True)
 rawname=result['input']['sha256']+'.'+result['sample']['format'];shutil.copyfile(path,out/rawname)
 (out/'sample.txt').write_text(result['sample']['text'],encoding='utf-8')
 (out/'verification.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 return result

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--file',required=True,type=Path);p.add_argument('--provenance',required=True,type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--format',choices=('pdf','html','rtf','txt'));p.add_argument('--sha256');p.add_argument('--pages',help='1-based comma-separated PDF page sample, maximum20');p.add_argument('--expect',action='append',default=[])
 args=p.parse_args()
 try:
  r=write_result(args.file,json.loads(args.provenance.read_text()),args.out,expected_format=args.format,expected_sha=args.sha256,pages=[int(x) for x in args.pages.split(',')] if args.pages else None,expect=args.expect)
  print(json.dumps({k:r[k] for k in ('integrity_status','sample_status','legal_semantic_status','scope_completeness_status')}));return 0 if r['sample_status']=='PASS' else 2
 except (Rejected,OSError,ValueError) as e: print(json.dumps({'status':'REJECTED','error':str(e)}));return 1
if __name__=='__main__':raise SystemExit(main())
