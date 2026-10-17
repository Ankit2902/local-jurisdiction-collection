#!/usr/bin/env python3
"""Offline source-bound bounded normalization; never counts inventories/TOCs as legal records."""
import argparse,csv,hashlib,importlib.util,json,pathlib,re,sys
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import pdfplumber
BASE=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/'scripts/encodeplus'))
import parse as ep

def sha(b):return hashlib.sha256(b).hexdigest()
def clean(t):return re.sub(r'\s+',' ',t).strip()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def generic_tables(node):
 return [[[{'text':clean(c.get_text(' ',strip=True)),'rowspan':int(c.get('rowspan',1)),'colspan':int(c.get('colspan',1)),'tag':c.name} for c in tr.find_all(['td','th'],recursive=False)] for tr in table.find_all('tr')] for table in node.find_all('table')]
def base_record(row,ident,heading,text,url,raw,publication):
 assert len(text)>20,(ident,'Empty legal body')
 return {'jurisdiction':row['jurisdiction'],'state':row['state'],'id':ident,'heading':heading,'citation':publication+' '+ident,'publication':publication,'text':text,'source_url':url,'raw_ref':str(raw.relative_to(BASE)),'raw_sha256':sha(raw.read_bytes()),'record_unit':'legal_section','tables':[],'links':[],'complete_corpus':False}
def spokane(row,raw):
 records=[]
 for ending in ['010','020','030','950']:
  f=raw/f'78-section{ending}.html';s=BeautifulSoup(f.read_bytes(),'html.parser');node=s.select_one('#hideRepealed');ident='01.02.'+ending;a=node.find('a',href='/smc/?Section='+ident);assert a,'Exact section link absent';title=clean(str(a.next_sibling));parts=[]
  for sib in a.next_siblings:parts.append(str(sib))
  b=BeautifulSoup(''.join(parts),'html.parser');full=clean(b.get_text(' ',strip=True));assert full.startswith(title)
  text=full[len(title):].strip();r=base_record(row,ident,title,text,'https://my.spokanecity.org/smc/?Section='+ident,f,'Spokane Municipal Code');r.update(body_html=str(b),tables=generic_tables(b),links=[{'text':clean(x.get_text(' ',strip=True)),'url':urljoin(r['source_url'],x['href'])} for x in b.select('a[href]')]);records.append(r)
 # Native publisher print endpoint must contain identical operative source body, not merely headings.
 native=BeautifulSoup((raw/'78-print-section010.html').read_bytes(),'html.parser');target=native.select_one('#hideRepealed') or native
 assert 'Gender, number, and tense are interchangeable.' in target.get_text(' ',strip=True)
 assert records[0]['text'] in clean(target.get_text(' ',strip=True))
 toc=BeautifulSoup((raw/'78-print102.html').read_bytes(),'html.parser');assert 'Gender, number, and tense are interchangeable.' not in toc.get_text(' ',strip=True)
 return records

def pdf_segments(row,file,pages,start_marker,pattern,publication,url,expected,footer_pattern=None):
 lines=[]
 with pdfplumber.open(file) as pdf:
  for i in pages:
   for line in (pdf.pages[i].extract_text() or '').splitlines():
    if footer_pattern and re.fullmatch(footer_pattern,line.strip()):continue
    lines.append((i+1,line))
 # TOC headings are excluded by beginning at the final occurrence of the first section heading on its opening page.
 starts=[i for i,(page,line) in enumerate(lines) if re.match(start_marker,line)];assert starts,'First operative heading absent';start=starts[-1] if len(starts)>1 and lines[starts[0]][0]==lines[starts[-1]][0] else starts[0]
 out=[];current=None
 for page,line in lines[start:]:
  m=re.match(pattern,line)
  if m:
   current={'jurisdiction':row['jurisdiction'],'state':row['state'],'id':m[1],'heading':clean(m[2]),'citation':publication+' '+m[1],'publication':publication,'text':'','source_url':url+'#page='+str(page),'raw_ref':str(file.relative_to(BASE)),'raw_sha256':sha(file.read_bytes()),'record_unit':'legal_section','tables':[],'links':[],'complete_corpus':False,'pdf_page_start':page,'pdf_page_end':page}
   out.append(current)
  elif current:
   # One county section heading wraps at a visible source line break.
   if current['id']=='1-6' and line.strip() in ['That Permissible.','Permissible.']:current['heading']+=' '+line.strip();continue
   current['text']+=(line+'\n');current['pdf_page_end']=page
 assert [r['id'] for r in out]==expected,([r['id'] for r in out],expected)
 for r in out:r['text']=r['text'].strip();assert len(r['text'])>20,(r['id'],'TOC-only/empty PDF section')
 return out

def inventories(raw,out):
 for seq,name in [(58,'58-browser-index'),(71,'71-index'),(78,'78-index'),(80,'80-index'),(85,'85-index'),(99,'99-browser-index')]:
  f=raw/(name+'.html');s=BeautifulSoup(f.read_bytes(),'html.parser');links=[{'title':clean(a.get_text(' ',strip=True)),'url':urljoin(json.loads((raw/(name+'.meta.json')).read_text())['url'],a['href'])} for a in s.select('a[href]')];dump(out/f'{seq}-official-inventory.json',{'source':str(f.relative_to(BASE)),'links':links,'complete_corpus':False,'note':'Official route/publication inventory only; not legal records.'})
 portal=BeautifulSoup((raw/'99-search-browser.html').read_bytes(),'html.parser');docs=[{'title':clean(a.get_text(' ',strip=True)),'detail_url':urljoin('https://document-search.arlingtonva.us',a['href']),'listing':clean(a.parent.get_text(' ',strip=True))} for a in portal.select('a[href*="/details/county-code/"]')];assert len(docs)==80;dump(out/'99-current-portal-inventory.json',{'source':'raw/99-search-browser.html','documents':docs,'document_count':len(docs),'warning':'Official portal states not all code chapters are current; true copies from County Board Clerk. Separate zoning ordinance is outside county-code collection.'})
 zi=BeautifulSoup((raw/'80-zoning-index.html').read_bytes(),'html.parser');dump(out/'80-zoning-inventory.json',{'links':[{'title':clean(a.get_text(' ',strip=True)),'url':urljoin('https://www.worcesterma.gov',a['href'])} for a in zi.select('main a[href]')],'note':'Zoning and maps are separate; none of these PDFs normalized in this bounded test.'})

def verify_raw(raw):
 checked=[]
 for f in sorted(raw.glob('*.meta.json')):
  m=json.loads(f.read_text())
  if m.get('path') and m.get('sha256'):
   p=raw/m['path'];assert sha(p.read_bytes())==m['sha256'];checked.append(str(p.relative_to(BASE)))
  if m.get('native'):
   n=m['native'];p=raw/n['path'];assert sha(p.read_bytes())==n['sha256'] and p.read_bytes().startswith(b'%PDF-');checked.append(str(p.relative_to(BASE)))
 for f in sorted(raw.glob('*.receipt.json')):
  m=json.loads(f.read_text())
  if 'raw_file' not in m:continue
  p=raw/m['raw_file'];assert sha(p.read_bytes())==m['sha256'];checked.append(str(p.relative_to(BASE)))
 if (raw/'receipt.json').exists():
  receipt=json.loads((raw/'receipt.json').read_text());assert receipt['status']=='acquired' and not receipt.get('access_stop')
  for r in receipt['responses']:
   p=raw/r['file'];assert sha(p.read_bytes())==r['sha256'];checked.append(str(p.relative_to(BASE)))
  if receipt.get('publisher_download',{}).get('status')=='passed':
   p=raw/'publisher-export.pdf';assert sha(p.read_bytes())==receipt['publisher_download']['sha256'] and p.read_bytes().startswith(b'%PDF-');checked.append(str(p.relative_to(BASE)))
 return checked

def write_rows(out,seq,rows):
 assert len({r['id'] for r in rows})==len(rows);p=out/str(seq);p.mkdir(parents=True,exist_ok=True)
 (p/'records.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
 fields=['jurisdiction','state','publication','id','heading','citation','text','source_url','record_unit','raw_ref','raw_sha256']
 with (p/'records.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
 with (p/'records.csv').open(newline='') as f:csvrows=list(csv.DictReader(f))
 assert len(csvrows)==len(rows) and all(a['text']==b['text'] and a['id']==b['id'] for a,b in zip(csvrows,rows))
 return {'record_count':len(rows),'record_unit':'legal_section' if all(r['record_unit']=='legal_section' for r in rows) else 'operative provisions/fee attachment','table_count':sum(len(r['tables']) for r in rows),'complete_corpus':False}

def chattanooga_code(mn,raw,base_rows,supplement=None,source=None,current_path=None):
 p=supplement or raw/'85-code';batch=json.loads((p/'batch-receipt.json').read_text());source=source or raw/'85-browser'
 assert sha((source/'receipt.json').read_bytes())==batch['source_receipt_sha256']
 assert sha((source/'toc-full.json').read_bytes())==batch['source_toc_sha256']
 current=json.loads(((current_path or raw/'85-final')/'receipt.json').read_text());assert batch['product_id']==current['product']['ProductID'] and batch['job_id']==current['job']['Id']
 result=[]
 for index,node in enumerate(batch['nodes'],1):
  folder=p/str(index);receipt=json.loads((folder/'acquisition-receipt.json').read_text());f=folder/'content.json'
  assert receipt['status']=='acquired' and not receipt.get('access_stop') and sha(f.read_bytes())==receipt['response']['sha256']
  from urllib.parse import urlparse,parse_qs
  query=parse_qs(urlparse(receipt['api_url']).query);assert query['nodeId']==[node['Id']] and query['productId']==[str(batch['product_id'])] and query['jobId']==[str(batch['job_id'])]
  docs=json.loads(f.read_text())['Docs'];matches=[d for d in docs if d['Id']==node['Id']];assert len(matches)==1
  d=matches[0];parser=mn.LegalHTML();parser.feed(d['Content']);text=parser.parsed();title=mn.LegalHTML();title.feed(d.get('TitleHtml') or d['Title']);heading=title.parsed()
  assert clean(heading)==clean(node['Heading']) and len(text)>100
  r=base_record(base_rows,node['Id'],heading,text,current['url'].split('?')[0]+'?nodeId='+node['Id'],f,'Chattanooga Part II City Code');r.update(html=d['Content'],tables=parser.tables,links=parser.links,product_id=batch['product_id'],job_id=batch['job_id'],publication_family='primary_city_code',path=['PART II CITY CODE','Chapter 1 GENERAL PROVISIONS',node['Heading']]);result.append(r)
 return result

def run(out,allow_missing=False):
 raw=BASE/'raw';out.mkdir(parents=True,exist_ok=True);rows={r['sequence']:r for r in json.loads((BASE/'assignment.json').read_text())};verified=verify_raw(raw);inventories(raw,out);summary={}
 tx=pdf_segments(rows[58],raw/'58-alarm-export-native.pdf',range(9,12),r'^Section 2\.01\s',r'^Section\s+(2\.\d+)\s+(.+)$','Arlington Texas Alarm Systems ArticleII','https://www.arlingtontx.gov/files/assets/city/v/2/city-secretary/documents/city-code-of-ordinances/alarm-systems-chapter.pdf',[f'2.0{i}' for i in range(1,8)],r'ALARM SYSTEMS|2\.\d+|ARTICLE II - \d+');summary[58]=write_rows(out,58,tx)
 county=pdf_segments(rows[99],raw/'99-code-native-native.pdf',range(3),r'^§ 1-1\.\s',r'^§\s+(1-\d+(?:\.\d+)?)\.\s+(.+)$','Arlington County Virginia Code Chapter1','https://www.arlingtonva.us/files/sharedassets/public/v/5/county-board/documents/code/ch.-1-general-provisions.pdf',['1-1','1-2','1-3','1-4','1-5','1-6','1-7','1-7.1','1-8','1-9'],r'ARLINGTON COUNTY CODE(?: GENERAL PROVISIONS)?|1-\d+|Code Updated September 2011');summary[99]=write_rows(out,99,county);assert county[5]['heading'].endswith('That Permissible.') and all('ARLINGTON COUNTY CODE' not in r['text'] for r in county)
 worcester=pdf_segments(rows[80],raw/'80-part1.pdf',range(2,6),r'^§ 1\. Citation$',r'^§\s+(\d+)\.\s+(.+)$','Worcester Revised Ordinances PartI Chapter1','https://www.worcesterma.gov/city-clerk/document-center/revised-ordinances-2008-1.pdf',[str(i) for i in range(1,9)],r'\d+');summary[80]=write_rows(out,80,worcester)
 with pdfplumber.open(raw/'80-part1.pdf') as pdf:assert len(pdf.pages)==659 and 'September 8, 2026' in pdf.pages[0].extract_text()
 with pdfplumber.open(raw/'58-alarm-export-native.pdf') as pdf:assert len(pdf.pages)==59 and 'May 27, 2014' in pdf.pages[0].extract_text()
 with pdfplumber.open(raw/'99-code-native-native.pdf') as pdf:assert len(pdf.pages)==3 and all('Code Updated September 2011' in page.extract_text() for page in pdf.pages)
 dump(out/'official-pdf-editions.json',{'58':{'pages':59,'printed_chapter_edition':'May 27, 2014','current_enactments_reconciled':False},'80':{'pages':659,'printed_edition':'September 8, 2026'},'99':{'pages':3,'printed_edition':'September 2011','current_portal_corrobates_posted_edition':True,'current_enactments_reconciled':False}})
 summary[78]=write_rows(out,78,spokane(rows[78],raw))
 html=(raw/'87-encodeplus-toc.html').read_text();inventory=ep.inventory(html,'https://online.encodeplus.com/regs/savannah-ga/','Savannah');dump(out/'87-publisher-inventory.json',inventory);sav=[];checks=[]
 for ident,file in [('499','87-section499.html'),('500','87-section500.html'),('501','87-section501.html'),('7137','87-impact-fee7137.html')]:
  node=next(n for n in inventory['nodes'] if n['section_id']==ident);p=raw/file;url=json.loads((raw/(file+'.receipt.json')).read_text())['final_url'];r,ch,_=ep.parse_section(p.read_text(),node,url,'Savannah',sha(p.read_bytes()));r.update(state='GA',id=ident,text=r['full_text'],source_family='enCodePlus',publication='Savannah Code of Ordinances',record_unit='fee_attachment' if ident=='7137' else 'legal_section',raw_ref=str(p.relative_to(BASE)));sav.append(r);checks.append(ch)
 table=sav[-1]['tables'][0];assert table[0][0]['colspan']=='8';known=next(row for row in table if row[0]['text']=='Single-Family Detached Housing');assert [c['text'] for c in known]==['Single-Family Detached Housing','$1,769.8490','$76.6431','$1,055.1640','$850.2371','$178.9578','$3,930.8511','dwelling'];summary[87]=write_rows(out,87,sav);dump(out/'87-parser-checks.json',checks)
 # Reuse source-bound exact-node Municode normalizer; its own output units stay separate.
 spec=importlib.util.spec_from_file_location('municode_normalize_owned',BASE/'scripts/municode/normalize.py');mn=importlib.util.module_from_spec(spec);spec.loader.exec_module(mn)
 for seq,folder in [(71,'71-browser'),(85,'85-final')]:
  p=raw/folder
  if not (p/'receipt.json').exists():
   if allow_missing:continue
   raise AssertionError('Required Municode acquisition missing '+str(seq))
  receipt=json.loads((p/'receipt.json').read_text());assert receipt.get('status')=='acquired',receipt.get('error')
  report=mn.normalize(p,out/str(seq));summary[seq]={k:report[k] for k in ['record_count','table_count','complete_corpus']};summary[seq]['record_unit']='exact requested legal provisions'
  enriched=[]
  for record in [json.loads(line) for line in (out/str(seq)/'sections.jsonl').read_text().splitlines()]:
   record.update(jurisdiction=rows[seq]['jurisdiction'],state=rows[seq]['state'],id=record['node_id'],citation=record['heading'],publication=receipt['product'].get('ProductName','Code of Ordinances'),record_unit='legal_section',raw_ref=str((p/'samples.json').relative_to(BASE)),raw_sha256=sha((p/'samples.json').read_bytes()));enriched.append(record)
  if seq==85:
   for r in enriched:r.update(publication='Chattanooga Part I Charter Compilation',publication_family='charter',path=['PART I CHARTER COMPILATION']+r.get('path',[]))
   enriched+=chattanooga_code(mn,raw,rows[85])
  summary[seq]=write_rows(out,seq,enriched)
  if seq==85:summary[seq].update(charter_record_count=3,primary_code_record_count=3)
  if seq==85:
   table_record=next(r for r in enriched if r['tables']);source=BeautifulSoup(table_record['html'],'html.parser')
   actual=generic_tables(source);expected=table_record['tables']
   normalize=lambda tables:[[[{'text':c['text'],'rowspan':str(c['rowspan']),'colspan':str(c['colspan']),'tag':c['tag']} for c in row] for row in table] for table in tables]
   assert normalize(actual)==normalize(expected)
   assert len(expected)==1 and len(expected[0])==97 and len([c for row in expected[0] for c in row])==291
   assert any([c['text'] for c in row]==['','11011','5/9/000'] for row in expected[0])
   dump(out/'85-table-checks.json',{'record_id':table_record['id'],'table_scope':'Publisher-appended Charter editor note/Home Rule amendments table; dates preserved verbatim including source 5/9/000.','table_count':1,'rows':97,'cells':291,'all_cell_text_spans_independently_source_compared':True,'pdf_table_reconstruction_tested':False})
  from native_pdf_qa import native_check
  native_check(BASE,seq,folder,enriched,out/f'{seq}-native-pdf-checks.json')
  for resp in receipt['responses']:
   assert sha((p/resp['file']).read_bytes())==resp['sha256']
  dump(out/f'{seq}-publisher-inventory.json',{'product':receipt['product'],'job':receipt['job'],'publications':receipt.get('publications'),'families_top_level':receipt.get('families_top_level'),'publisher_download':receipt.get('publisher_download'),'complete_corpus':False})
 dump(out/'verification.json',{'raw_bodies_verified':len(verified),'verified_raw_paths':verified,'jurisdictions':summary,'checks':['Source hashes before normalization','PDF operative bodies after TOCs; exact expected section IDs/counts','PDF page boundaries and source citations retained','Spokane native one-section print body matches operative source; chapter TOC-only print excluded','Savannah requested container/TOC/body IDs and headings match','Savannah fee table every cell text/span independently source-compared; known8-cell residential fee row retained','JSONL/CSV text and identifiers round-trip','Municode exact requested document/current product/publication identity from source-bound sample'],'complete_corpus':False});return summary
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--offline',action='store_true');p.add_argument('--out',type=pathlib.Path,default=BASE/'parsed');p.add_argument('--allow-missing',action='store_true');a=p.parse_args();print(json.dumps(run(a.out,a.allow_missing),indent=2))
