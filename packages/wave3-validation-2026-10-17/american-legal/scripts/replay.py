#!/usr/bin/env python3
"""Deterministic parsers. --offline reads/compares only; --write creates normalized artifacts."""
import argparse,csv,hashlib,io,json,re,sys
sys.dont_write_bytecode=True
from pathlib import Path
from urllib.parse import urljoin,urlparse,parse_qs
from bs4 import BeautifulSoup
from alp_normalize import normalize_html
from encode_parse import decode,parse_section
from pypdf import PdfReader
from normalize import LegalHTML
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
 assert sha(ROOT/'scripts/executed'/(rec['script_sha256']+'.mjs'))==rec['script_sha256']
 for p in rec['pages']:assert sha(d/(p['name']+'.html'))==p['html_sha256'],'Source hash mismatch'
 source=(d/'sample-expanded.html').read_text();rr=normalize_html(source,row,rec['sample_url'],'headed-browser-rendered-source')
 soup=BeautifulSoup(source,'html.parser');identity=any(urljoin(rec['sample_url'],a.get('href','')).rstrip('/')==target['overview_url'].rstrip('/') and row['selection_name'].casefold() in a.get_text(' ',strip=True).casefold() for a in soup.select('a.toc-link'))
 expected=target.get('publication_prefix') or rec['publication_prefix'];publication_ok=rec['sample_url'].startswith(expected) and re.search(target['publication_pattern'],rec['publication_title'],re.I) is not None
 pub=rec.get('publisher_export',{});pr=[]
 if pub.get('script_sha256'):assert sha(ROOT/'scripts/executed'/(pub['script_sha256']+'.mjs'))==pub['script_sha256']
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
  p=d/'publisher-section.pdf';assert sha(p)==pub['sha256'];pdf=PdfReader(p);text='\n'.join(pg.extract_text() or '' for pg in pdf.pages);compact=lambda v:re.sub(r'\W','',v).casefold();native_cell_matches=[compact(c['text']) in compact(text) for c in cells];assert all(native_cell_matches);pdfcheck={'check':'native_pdf_valid_and_identified','passed':'2100' in text and 'Zoning Districts' in text,'pages':len(pdf.pages),'all_source_table_cells_present':all(native_cell_matches),'matched_source_table_cells':len(native_cell_matches),'scope':'Selected zoning §2100; primary general county code remains a separate publication'}
 s={'record_count':len(rr),'record_unit':'requested operative zoning provision','table_count':sum(len(r['tables']) for r in rr),'table_cell_count':len(cells),'spanned_cell_count':sum(int(c['rowspan'])>1 or int(c['colspan'])>1 for c in cells),'checks':cc+[pdfcheck],'complete_corpus':False,'primary_county_code_scope':False};put(ROOT/'parsed/fairfax-zoning-validation.json',stable(s),write);return s

def municode(name,expected_name,state,write):
 d=Path(name) if Path(name).is_absolute() else ROOT/'runs'/name;rec=json.loads((d/'receipt.json').read_text());assert rec['status']=='acquired',rec.get('error');product=json.loads((d/'product.json').read_text());job=json.loads((d/'job.json').read_text());cc=json.loads((d/'client-content.json').read_text());samples=json.loads((d/'samples.json').read_text());checks=[]
 assert product==rec['product'] and job==rec['job'] and job['ProductId']==product['ProductID'];assert product['Client']['ClientName']==expected_name and product['Client']['State']['StateAbbreviation']==state;assert any(p['productId']==product['ProductID'] and not p.get('hideInLibrary') for p in cc['codes']);assert sha(d/'executed-collect_browser.cjs')==rec['script_sha256'];assert sha(d/'executed-gate_cli.py')==rec['gate_script_sha256']
 for response in rec['responses']:assert sha(d/response['file'])==response['sha256']
 toc=json.loads((d/'toc-full.json').read_text());toc_nodes={}
 def walk_toc(node):
  if node.get('Id'):toc_nodes[node['Id']]=node
  for child in node.get('Children',[]):walk_toc(child)
 walk_toc(toc)
 records=[]
 for sample in samples:
  node=sample['node'];assert node['Id'] in toc_nodes and toc_nodes[node['Id']]['Heading']==node['Heading'];api_matches=[r for r in rec['responses'] if '/CodesContent?' in r['url'] and parse_qs(urlparse(r['url']).query).get('nodeId')==[node['Id']] and parse_qs(urlparse(r['url']).query).get('jobId')==[str(job['Id'])] and parse_qs(urlparse(r['url']).query).get('productId')==[str(product['ProductID'])]];assert api_matches and any(json.loads((d/r['file']).read_text())==sample['content'] for r in api_matches);docs=[v for v in sample['content']['Docs'] if v.get('Id')==node['Id']];assert len(docs)==1;doc=docs[0];html=doc.get('Content') or '';parser=LegalHTML();parser.feed(html);text=parser.parsed();title=LegalHTML();title.feed(doc.get('Title') or doc.get('TitleHtml') or node.get('Heading') or '');assert text and title.parsed()
  records.append({'node_id':node['Id'],'heading':title.parsed(),'toc_heading':node['Heading'],'path':node.get('path',[]),'text':text,'html':html,'tables':parser.tables,'links':parser.links,'list_count':parser.lists,'footnotes':doc.get('Footnotes'),'notes':doc.get('Notes'),'doc_order_id':doc.get('DocOrderId'),'product_id':product['ProductID'],'job_id':job['Id'],'source_url':rec['url'].split('?')[0]+'?nodeId='+node['Id'],'body_sha256':hashlib.sha256(html.encode()).hexdigest(),'complete_corpus':False})
 assert len(records)>=2 and len({r['node_id'] for r in records})==len(records)
 out=d/'normalized';put(out/'sections.jsonl',''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records),write);fields=['node_id','heading','text','product_id','job_id','source_url','body_sha256'];buf=io.StringIO(newline='');writer=csv.DictWriter(buf,fieldnames=fields);writer.writeheader();writer.writerows({k:r[k] for k in fields} for r in records);put(out/'sections.csv',buf.getvalue(),write)
 checks=[{'check':'retained_raw_response_and_executed_script_hashes','passed':True},{'check':'exact_jurisdiction_state_and_visible_publication_identity','passed':True},{'check':'pinned_job_requested_doc_body_and_heading','passed':True},{'check':'unique_multiple_substantive_nodes','passed':True}]
 pub=rec.get('publisher_download',{});native={'status':pub.get('status'),'reason':pub.get('reason'),'parsed_pages':0,'matched_nodes':[]}
 if (d/'publisher-export.pdf').exists():
  p=d/'publisher-export.pdf';pr=json.loads((d/'publisher-export.receipt.json').read_text());assert sha(p)==pr['sha256']==pub['sha256'];assert p.read_bytes().startswith(b'%PDF-');pdf=PdfReader(p);page_numbers=list(range(min(35,len(pdf.pages))))
  if expected_name=='Cincinnati':
   def outlines(items):
    for item in items:
     if isinstance(item,list):yield from outlines(item)
     else:yield item
   for item in outlines(pdf.outline):
    if norm(item.get('/Title',''))=='administrative code':
     start=pdf.get_destination_page_number(item);page_numbers+=list(range(start,min(start+12,len(pdf.pages))))
  page_numbers=sorted(set(page_numbers));page_texts=[pdf.pages[n].extract_text() or '' for n in page_numbers];flat=norm(' '.join(page_texts));matches=[]
  for r in records:
   sentences=[norm(v) for v in r['text'].split('\n') if len(norm(v))>60];probe=next((v[:160] for v in sentences if len(v)>80),norm(r['text'])[:100]);matches.append({'node_id':r['node_id'],'heading':r['heading'],'probe':probe,'body_probe_in_native_pdf':probe in flat})
  native={'status':'passed' if all(m['body_probe_in_native_pdf'] for m in matches) else 'partial','pdf_page_count':len(pdf.pages),'parsed_pages':len(page_texts),'page_numbers':[n+1 for n in page_numbers],'matched_nodes':matches,'edition_front_matter':page_texts[:2],'scope':'Whole publication downloaded; first35 front-matter pages plus12 pages at observed Administrative Code bookmark extracted for bounded sample matching. Full PDF normalization and edition equivalence are untested.'}
  if expected_name=='Cincinnati' and 'SUPPLEMENT NO. 47' in page_texts[0] and '48' in job['Name']:
   native['status']='partial';native['edition_comparison']={'matches_live_latest':False,'native':'Supplement47,March2026; throughOrd0010-2026 effectiveJanuary14,2026','live':job['BannerText'],'reason':'Native publisher PDF lags current API edition'}
  put(out/'publisher-sample-pages.jsonl',''.join(json.dumps({'page':i+1,'text':t},ensure_ascii=False)+'\n' for i,t in zip(page_numbers,page_texts)),write)
  checks.append({'check':'native_pdf_valid_and_bounded_parsing','passed':True,'matched_body_probes':sum(m['body_probe_in_native_pdf'] for m in matches),'total_sample_nodes':len(matches)})
 summary={'record_count':len(records),'record_unit':'exact requested leaf provision bound to live product/job IDs','table_count':sum(len(r['tables']) for r in records),'checks':checks,'publisher_download_validation':native,'complete_corpus':False,'currentness':{'job':job,'product_name':product.get('ProductName'),'basis':'Pinned live Jobs/latest identity; whole-publication edition equivalence untested'}};put(out/'validation.json',stable(summary),write);return summary

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');ap.add_argument('--offline',action='store_true');ap.add_argument('--sequence',type=int);a=ap.parse_args();rows=json.loads((ROOT/'assignment.json').read_text());targets=json.loads((ROOT/'targets.json').read_text());failed=False
 for target in targets:
  if a.sequence and a.sequence!=target['sequence']:continue
  row=next(r for r in rows if r['sequence']==target['sequence'])
  if not (ROOT/'raw'/target['slug']/'receipt.json').exists():continue
  summary=alp(row,target,a.write);print(row['jurisdiction'],summary['record_count'],'source',summary['native_record_count'],'native',all(c['passed'] for c in summary['checks']));failed|=not all(c['passed'] for c in summary['checks'])
 if (ROOT/'raw/official/cincinnati-ch319-excerpt.pdf').exists() and (not a.sequence or a.sequence==63):print('Cincinnati official alternative',cincinnati_excerpt(a.write)['record_count'])
 for seq,name,expected,state in [(63,'cincinnati-browser','Cincinnati','OH'),(100,'fairfax-county-browser','Fairfax County','VA')]:
  if (not a.sequence or a.sequence==seq) and (ROOT/'runs'/name/'receipt.json').exists():print(expected,'Municode browser',municode(name,expected,state,a.write)['record_count'])
 if (not a.sequence or a.sequence==100) and (ROOT/'runs/fairfax-zoning-live/receipt.json').exists():print('Fairfax zoning alternative',fairfax_zoning(a.write)['record_count'])
 if (not a.sequence or a.sequence==100) and (ROOT/'runs/fairfax-current-smoke/receipt.json').exists():
  print('Fairfax final collector fresh smoke',municode('fairfax-current-smoke','Fairfax County','VA',a.write)['record_count'])
 if not a.write and (ROOT/'manifest.json').exists():
  manifest=json.loads((ROOT/'manifest.json').read_text())
  for rel,expected in manifest['files'].items():assert sha(ROOT/rel)==expected,'Manifest mismatch: '+rel
  print('Manifest hashes',len(manifest['files']))
 sys.exit(int(failed))
if __name__=='__main__':main()
