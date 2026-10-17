#!/usr/bin/env python3
"""Deterministic parsers. --offline reads/compares only; --write creates normalized artifacts."""
import argparse,csv,hashlib,io,json,re,sys
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from alp_normalize import normalize_html
from encode_parse import decode,parse_section
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(t):return re.sub(r'\s+([,.;:)\]”’\"])',r'\1',re.sub(r'\s+',' ',t).strip()).casefold()
def stable(x):return json.dumps(x,ensure_ascii=False,indent=2)+'\n'
def put(p,s,write):
 if write:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
 else:assert p.read_bytes()==s.encode('utf-8'),'Replay differs: '+str(p)
def records_output(out,records,write):
 put(out/'sections.jsonl',''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records),write)
 fields=['jurisdiction','source_family','source_url','document_id','citation','heading','text','table_count'];stream=io.StringIO(newline='');w=csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(records);put(out/'sections.csv',stream.getvalue(),write)
def alp(row,target,write):
 d=ROOT/'raw'/target['slug'];rec=json.loads((d/'receipt.json').read_text());out=ROOT/'parsed'/target['slug'];checks=[]
 for p in rec['pages']:assert sha(d/(p['name']+'.html'))==p['html_sha256'],'Source hash mismatch'
 source=(d/'sample-expanded.html').read_text();rr=normalize_html(source,row,rec['sample_url'],'headed-browser-rendered-source')
 soup=BeautifulSoup(source,'html.parser');identity=any(urljoin(rec['sample_url'],a.get('href','')).rstrip('/')==target['overview_url'].rstrip('/') and row['selection_name'].casefold() in a.get_text(' ',strip=True).casefold() for a in soup.select('a.toc-link'))
 expected=target.get('publication_prefix') or rec['publication_prefix'];publication_ok=rec['sample_url'].startswith(expected) and re.search(target['publication_pattern'],rec['publication_title'],re.I) is not None
 pub=rec.get('publisher_export',{});pr=[]
 if pub.get('file'):
  p=ROOT/pub['file'];assert sha(p)==pub['sha256'];pr=normalize_html(p.read_text(),row,rec['sample_url'],'publisher-native-selected-section-HTML')
 matches=[any(r['document_id']==p['document_id'] and norm(r['text'])==norm(p['text']) for r in rr) for p in pr]
 binding=bool(pr) and all(norm(p['heading'])==norm(pub.get('requested_heading','')) and any(r['document_id']==p['document_id'] for r in rr) for p in pr)
 checks=[{'check':'source_hashes','passed':True},{'check':'current_dom_jurisdiction_identity','passed':identity},{'check':'expected_publication_binding','passed':publication_ok,'expected_prefix':expected},{'check':'multiple_substantive_sections','passed':len(rr)>=2,'count':len(rr)},{'check':'citations_headings_text','passed':bool(rr) and all(r['heading'] and r['citation'] and len(r['text'])>len(r['heading'])+10 for r in rr)},{'check':'unique_document_ids','passed':len({r['document_id'] for r in rr})==len(rr)},{'check':'all_native_bodies_match_source','passed':bool(matches) and all(matches),'matched':sum(matches),'total':len(matches)},{'check':'native_requested_heading_and_id_binding','passed':binding}]
 records_output(out,rr,write);records_output(out/'publisher',pr,write)
 overview=BeautifulSoup((d/'overview.html').read_text(),'html.parser');ver=overview.select_one('.codenav__versions');currentness={'publisher_overview':target['overview_url'],'version_label':ver.get_text(' ',strip=True) if ver else None,'native_job_version':json.loads((d/'native-job.json').read_text()).get('version') if (d/'native-job.json').exists() else None,'basis':'Current overview metadata + native selected section exact body matching; full-publication edition equivalence untested'}
 summary={'record_unit':'complete rendered operative section within bounded sample','record_count':len(rr),'native_record_count':len(pr),'table_count':sum(r['table_count'] for r in rr),'cross_reference_count':sum(len(r['cross_references']) for r in rr),'checks':checks,'currentness':currentness,'complete_corpus':False};put(out/'validation.json',stable(summary),write);return summary

def cincinnati_excerpt(write):
 p=ROOT/'raw/official/cincinnati-ch319-excerpt.pdf';receipt=json.loads(p.with_suffix('.pdf.receipt.json').read_text());assert sha(p)==receipt['sha256'];pdf=PdfReader(p);text='\n'.join(pg.extract_text() or '' for pg in pdf.pages[:2]);assert 'Cincinnati Municipal Code' in text and 'CHAPTER 317' in text
 headings=list(re.finditer(r'^Sec\.\s+(\d[\w-]*)\.\s+([^\n]+)',text,re.M));rr=[]
 for a,b in zip(headings,headings[1:]):
  title=a.group(0).strip();body=text[a.start():b.start()].strip();rr.append({'jurisdiction':'Cincinnati','source_family':'Official municipal departmental PDF excerpt; currency unqualified','source_url':receipt['url'],'document_id':'appendix-e-'+a.group(1),'citation':a.group(1),'heading':title,'text':body,'table_count':0,'tables':[],'source_pdf_pages_inspected':[1,2],'complete_corpus':False})
  if len(rr)==3:break
 assert len(rr)==3 and all(len(r['text'])>len(r['heading'])+20 for r in rr);out=ROOT/'parsed/cincinnati-official-excerpt';records_output(out,rr,write);s={'record_count':len(rr),'record_unit':'fully delimited operative section excerpt from first PDF page','pdf_page_count':len(pdf.pages),'pages_text_sampled':[1,2],'source_hash':sha(p),'edition':'No current-through date established; visible source histories include 2002/2003. Not substituted for current Municode corpus.','checks':[{'check':'pdf_magic_and_parse','passed':p.read_bytes().startswith(b'%PDF-')},{'check':'jurisdiction_and_chapter_identity','passed':True},{'check':'bounded_sections_complete_between_source_headings','passed':True}],'complete_corpus':False};put(out/'validation.json',stable(s),write);return s

def fairfax_zoning(write):
 d=ROOT/'runs/fairfax-zoning-live';rec=json.loads((d/'receipt.json').read_text());rr=[];cc=[]
 for n in rec['selected_nodes']:
  p=d/('section-'+n['section_id']+'.html');receipt=json.loads(p.with_suffix('.html.receipt.json').read_text());assert sha(p)==receipt['sha256'];record,check,_=parse_section(decode(p.read_bytes(),receipt['headers']),{'section_id':n['section_id'],'heading':n['heading'],'path':['Fairfax County Zoning Ordinance']},n['source_url'],'Fairfax County',sha(p));rr.append(record);cc.append(check)
 # Compare engine outputs without write_outputs side effects.
 expected=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rr);assert (d/'parsed/sections.jsonl').read_text()==expected
 table=next(r for r in rr if r['section_id']=='2230');cells=[c for t in table['tables'] for row in t for c in row];assert cells and any(int(c['colspan'])>1 for c in cells);assert 'unincorporated' in table['full_text'].lower()
 pub=rec.get('publisher_download',{});pdfcheck={'check':'native_pdf_valid_and_identified','passed':False}
 if pub.get('status')=='passed':
  p=d/'publisher-section.pdf';assert sha(p)==pub['sha256'];pdf=PdfReader(p);text='\n'.join(pg.extract_text() or '' for pg in pdf.pages);pdfcheck={'check':'native_pdf_valid_and_identified','passed':'2100' in text and 'Zoning Districts' in text,'pages':len(pdf.pages),'scope':'Selected zoning §2100; primary general county code remains a separate publication'}
 s={'record_count':len(rr),'record_unit':'requested operative zoning provision','table_count':sum(len(r['tables']) for r in rr),'table_cell_count':len(cells),'spanned_cell_count':sum(int(c['rowspan'])>1 or int(c['colspan'])>1 for c in cells),'checks':cc+[pdfcheck],'complete_corpus':False,'primary_county_code_scope':False};put(ROOT/'parsed/fairfax-zoning-validation.json',stable(s),write);return s

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');ap.add_argument('--offline',action='store_true');ap.add_argument('--sequence',type=int);a=ap.parse_args();rows=json.loads((ROOT/'assignment.json').read_text());targets=json.loads((ROOT/'targets.json').read_text());failed=False
 for target in targets:
  if a.sequence and a.sequence!=target['sequence']:continue
  row=next(r for r in rows if r['sequence']==target['sequence'])
  if not (ROOT/'raw'/target['slug']/'receipt.json').exists():continue
  summary=alp(row,target,a.write);print(row['jurisdiction'],summary['record_count'],'source',summary['native_record_count'],'native',all(c['passed'] for c in summary['checks']));failed|=not all(c['passed'] for c in summary['checks'])
 if not a.sequence or a.sequence==63:print('Cincinnati official alternative',cincinnati_excerpt(a.write)['record_count'])
 if (not a.sequence or a.sequence==100) and (ROOT/'runs/fairfax-zoning-live/receipt.json').exists():print('Fairfax zoning alternative',fairfax_zoning(a.write)['record_count'])
 sys.exit(int(failed))
if __name__=='__main__':main()
