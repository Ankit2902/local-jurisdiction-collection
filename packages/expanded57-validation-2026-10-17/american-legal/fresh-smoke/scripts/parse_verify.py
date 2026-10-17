#!/usr/bin/env python3
"""Offline replay of retained publisher and public rendered HTML; no network or Codex."""
import argparse,csv,hashlib,json,re,sys,zipfile
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
BASE=Path(__file__).resolve().parents[1]
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def clean(n):
 for e in n.select('script,style,button,.code-options,.annotation-drawer,.clearfix'):e.decompose()
 return n

def cells(node):
 return [{'table_index':ti,'row_index':ri,'cell_index':ci,'tag':c.name,'text':c.get_text(' ',strip=True),'rowspan':int(c.get('rowspan',1)),'colspan':int(c.get('colspan',1))} for ti,t in enumerate(node.find_all('table')) for ri,tr in enumerate(t.find_all('tr')) for ci,c in enumerate(tr.find_all(['td','th'],recursive=False))]

def normalize_html(html,row,url,kind):
 soup=BeautifulSoup(html,'html.parser'); scope=soup.select_one('.codenav__section-body') or soup
 chunks=scope.select('[id^="section-"]'); records=[]
 if chunks:
  for ch in chunks:
   head=ch.select_one('.toc-destination')
   if not head:continue
   title=head.get_text(' ',strip=True)
   if not re.match(r'^(?:SEC\.|§|\d)',title,re.I):continue
   docid=(head.get('id') or '').removeprefix('rid-');clean(ch)
   text=ch.get_text('\n',strip=True)
   if len(text)<=len(title)+10:continue
   citation=re.match(r'(?:SEC\.\s*|§\s*)?([\d]+[\w.\-]*[\d\w])',title,re.I)
   tables=[[[c.get_text(' ',strip=True) for c in tr.find_all(['td','th'],recursive=False)] for tr in t.find_all('tr')] for t in ch.find_all('table')]
   records.append({'jurisdiction':row['jurisdiction'],'state':row['state'],'source_family':'American Legal','source_url':url.rsplit('/',1)[0]+'/'+docid if re.fullmatch(r'0-0-0-\d+',docid) else url,'document_id':docid,'citation':citation.group(1) if citation else title,'heading':title,'text':text,'table_count':len(tables),'tables':tables,'table_cells':cells(ch),'cross_references':[{'label':a.get_text(' ',strip=True),'href':a.get('href')} for a in ch.find_all('a',href=True)],'acquisition_kind':kind,'complete_section':True})
 else:
  # Publisher exports contain source heading .Section/.Heading rather than React chunks.
  clean(scope)
  heads=scope.select('.Section,.Heading,.toc-destination')
  heads=[h for h in heads if not any(p in heads for p in h.parents)]
  for h in heads:
   title=h.get_text(' ',strip=True)
   if not re.match(r'^(?:SEC\.|§|\d+[.\-])',title,re.I):continue
   parts=[str(h)]
   for sibling in h.next_siblings:
    if getattr(sibling,'name',None) and sibling in heads:break
    parts.append(str(sibling))
   fragment=BeautifulSoup(''.join(parts),'html.parser');text=fragment.get_text('\n',strip=True)
   if len(text)<len(title)+10:continue
   citation=re.match(r'(?:SEC\.\s*|§\s*)?([\d]+[\w.\-]*[\d\w])',title,re.I)
   tables=[[[c.get_text(' ',strip=True) for c in tr.find_all(['td','th'],recursive=False)] for tr in t.find_all('tr')] for t in fragment.find_all('table')]
   docid=(h.get('id') or h.get('name') or '').removeprefix('rid-')
   records.append({'jurisdiction':row['jurisdiction'],'state':row['state'],'source_family':'American Legal','source_url':url.rsplit('/',1)[0]+'/'+docid if re.fullmatch(r'0-0-0-\d+',docid) else url,'document_id':docid,'citation':citation.group(1) if citation else title,'heading':title,'text':text,'table_count':len(tables),'tables':tables,'table_cells':cells(fragment),'cross_references':[{'label':a.get_text(' ',strip=True),'href':a.get('href')} for a in fragment.find_all('a',href=True)],'acquisition_kind':kind,'complete_section':True})
 return records

def run(row):
 slug=row['source_lead_url'].split('/')[4];d=BASE/'raw'/slug;out=BASE/'parsed'/slug;out.mkdir(parents=True,exist_ok=True)
 receipt=json.loads((d/'receipt.json').read_text());records=[];checks=[];publisher_records=[]
 for pg in receipt.get('pages',[]):
  p=d/(pg['name']+'.html');assert digest(p)==pg['html_sha256'],f'hash mismatch {p}'
 sample=d/('sample-expanded.html' if any(p['name']=='sample-expanded' for p in receipt.get('pages',[])) else 'sample.html')
 if sample.exists() and receipt.get('sample_url'): records=normalize_html(sample.read_text(),row,receipt['sample_url'],'standalone_browser_rendered_html')
 table_records=normalize_html((d/'table-sample.html').read_text(),row,receipt['table_sample']['url'],'supplemental_operative_table_html') if receipt.get('table_sample') else []
 export=receipt.get('publisher_export',{});pubfile=export.get('file')
 if pubfile:
  p=BASE/pubfile;assert digest(p)==export['sha256']
  if zipfile.is_zipfile(p):
   with zipfile.ZipFile(p) as z:
    for n in z.namelist():
     if n.lower().endswith(('.html','.htm')):publisher_records+=normalize_html(z.read(n).decode('utf-8',errors='replace'),row,receipt['sample_url'],'publisher_native_html_export')
  elif p.suffix.lower() in ('.html','.htm'):publisher_records=normalize_html(p.read_text(errors='replace'),row,receipt['sample_url'],'publisher_native_html_export')
 sample_name='sample-expanded' if sample.name=='sample-expanded.html' else 'sample'
 sample_meta=next((p for p in reversed(receipt.get('pages',[])) if p['name']==sample_name),{})
 identity_soup=BeautifulSoup(sample.read_text(),'html.parser') if sample.exists() else BeautifulSoup('','html.parser')
 identity_ok=any(urljoin(receipt.get('sample_url',row['source_lead_url']),a.get('href','')).rstrip('/')==row['source_lead_url'].rstrip('/') and row['selection_name'].casefold() in a.get_text(' ',strip=True).casefold() for a in identity_soup.select('a.toc-link'))
 expected_route=next(r for r in json.loads((BASE/'routes.json').read_text()) if r['sequence']==row['sequence'])['sample_url']
 expected_prefix=expected_route.rsplit('/',1)[0]+'/'
 publication_ok=receipt.get('sample_url','').startswith(expected_prefix) and sample_meta.get('url','').startswith(expected_prefix)
 native_titles=[r['heading'] for r in publisher_records]
 exported_scope={'actual_headings':native_titles,'actual_citations':[r['citation'] for r in publisher_records],'record_count':len(publisher_records)}
 (out/'publisher-scope.json').write_text(json.dumps(exported_scope,ensure_ascii=False,indent=2)+'\n')
 norm=lambda t:re.sub(r'\s+([,.;:)\]])',r'\1',re.sub(r'\s+',' ',t).strip()).casefold()
 matches=[any(norm(p['text'])==norm(r['text']) for r in records) for p in publisher_records]
 binding=bool(publisher_records) and bool(export.get('requested_heading')) and all(norm(p['heading'])==norm(export['requested_heading']) and any(r['document_id']==p['document_id'] for r in records) for p in publisher_records)
 checks=[{'check':'raw_html_hashes','passed':True},{'check':'substantive_multiple_records','passed':len(records)>=2,'count':len(records)},{'check':'source_identity','passed':identity_ok and bool(records)},{'check':'publication_prefix_binding','passed':publication_ok,'expected_prefix':expected_prefix,'observed_url':receipt.get('sample_url')},{'check':'headings_citations_text','passed':bool(records) and all(r['heading'] and r['citation'] and len(r['text'])>len(r['heading'])+10 for r in records)},{'check':'unique_document_ids','passed':len({r['document_id'] for r in records})==len(records)},{'check':'native_export_parsed','passed':bool(publisher_records),'count':len(publisher_records)},{'check':'native_text_matches_rendered','passed':bool(matches) and all(matches),'matched_records':sum(matches),'native_records':len(matches)},{'check':'native_export_selection_binding','passed':binding,'requested_heading':export.get('requested_heading')}]
 for name,rr in [('records',records),('publisher-records',publisher_records),('table-records',table_records)]:
  (out/(name+'.jsonl')).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rr))
  with (out/(name+'.csv')).open('w',newline='') as f:
   fields=['jurisdiction','state','source_family','source_url','document_id','citation','heading','text','table_count','acquisition_kind','complete_section'];w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rr)
 (out/'verification.json').write_text(json.dumps({'checks':checks,'record_count':len(records),'publisher_record_count':len(publisher_records),'table_count':sum(r['table_count'] for r in records+table_records),'supplemental_table_record_count':len(table_records),'supplemental_table_cell_count':sum(len(r['table_cells']) for r in table_records),'supplemental_spanned_cell_count':sum(c['rowspan']>1 or c['colspan']>1 for r in table_records for c in r['table_cells']),'cross_reference_count':sum(len(r['cross_references']) for r in records)},indent=2)+'\n')
 return records,publisher_records,checks

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--offline',action='store_true');ap.add_argument('--sequence',type=int);ns=ap.parse_args();rows=json.loads((BASE/'assignment.json').read_text());failed=False
 for row in rows:
  if ns.sequence and row['sequence']!=ns.sequence:continue
  try:
   rr,pr,ch=run(row);print(row['jurisdiction'],len(rr),'rendered records;',len(pr),'publisher export records');failed|=not all(x['passed'] for x in ch if x['check'] not in ('native_export_parsed','native_text_matches_rendered','native_export_selection_binding'))
  except FileNotFoundError as e:print(row['jurisdiction'],'missing acquisition',e);failed=True
 sys.exit(int(failed))
if __name__=='__main__':main()
