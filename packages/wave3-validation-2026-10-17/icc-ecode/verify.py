#!/usr/bin/env python3
"""Read-only deterministic retained-source replay, source table geometry and native export matching."""
import json,re,tempfile,sys,csv,copy,contextlib,io
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from pypdf import PdfReader
import collect
R=Path(__file__).resolve().parent

def geometry(table):
 s=BeautifulSoup(str(table),'html.parser')
 for im in s.select('img'):im.replace_with('[IMAGE]'+(' '+im.get('alt') if im.get('alt') else ''))
 return [[{'tag':c.name,'text_ignoring_whitespace':re.sub(r'\s+','',c.get_text()),'rowspan':c.get('rowspan'),'colspan':c.get('colspan'),'scope':c.get('scope'),'headers':c.get('headers')} for c in tr.find_all(['td','th'],recursive=False)] for tr in s.select('tr')]
def main():
 jobs=json.loads((R/'jobs.json').read_text());samples=json.loads((R/'samples.json').read_text());report=[]
 for slug,folder in samples.items():
  d=R/folder;job=jobs[slug];meta=json.loads((d/'acquisition.json').read_text());raw=(d/'source.html').read_bytes();assert collect.sha(raw)==meta['sha256'];checks=json.loads((d/'checks.json').read_text());details=json.loads((d/'parse-details.json').read_text());sp=BeautifulSoup(raw,'html.parser')
  with tempfile.TemporaryDirectory() as tmp:
   o=Path(tmp)
   for f in ['source.html','acquisition.json']:(o/f).write_bytes((d/f).read_bytes())
   with contextlib.redirect_stdout(io.StringIO()):collect.parse(job,o)
   for f in ['records.jsonl','records.csv']:assert (o/f).read_bytes()==(d/f).read_bytes(),(slug,f)
  table_checks=[];cross_reference_targets_checked=0
  for rec in details.get('source_records',[]):
   if job['family']=='eCode360':source=sp.find(id=rec['node_id']+'_content');semantic=BeautifulSoup(rec['semantic_html'],'html.parser')
   else:
    source=BeautifulSoup(rec.get('content_html',''),'html.parser');semantic=source
   source_targets=[urljoin(meta['url'],a['href']) for a in source.select('a[href]')];semantic_targets=[a['href'] for a in semantic.select('a[href]')]
   if job['family']=='eCode360':
    assert source_targets==semantic_targets,(slug,rec['node_id'],'cross_reference_targets');cross_reference_targets_checked+=len(source_targets)
   a=source.select('table');b=semantic.select('table');assert [geometry(t) for t in a]==[geometry(t) for t in b],(slug,rec['node_id'])
   if a:table_checks.append({'node_id':rec['node_id'],'tables':len(a),'rows':sum(len(t.select('tr')) for t in a),'cells':sum(len(t.select('td,th')) for t in a),'spanned_cells':sum(len(t.select('[rowspan],[colspan]')) for t in a),'text_and_geometry_equal':True})
  export=json.loads((d/'publisher-export.json').read_text());export_checks=[]
  for x in export.get('downloads',[]):
   p=d/x['path'];assert collect.sha(p.read_bytes())==x['sha256'];item={'file':str(p.relative_to(R)),'hash_verified':True}
   if p.suffix.lower()=='.pdf':
    pdf=PdfReader(p);text='\n'.join(page.extract_text() or '' for page in pdf.pages);assert len(text)>50
    selected=next(v for v in details['source_records'] if v['node_id']==export['selected_id']);srcwords=set(re.findall('[a-z]{4,}',BeautifulSoup(selected['full_text'],'html.parser').get_text(' ',strip=True).lower()));pdfwords=set(re.findall('[a-z]{4,}',text.lower()));coverage=len(srcwords&pdfwords)/max(1,len(srcwords));assert coverage>.9,(slug,coverage)
    item.update(native_format='PDF',selected_id=export['selected_id'],citation=selected['citation'],pages=len(pdf.pages),selected_body_word_coverage=coverage)
   elif p.suffix.lower()=='.html':
    rec,notes=collect.mc.parse_page(p.read_text(),meta['url'],job['base']);live=details['source_records'];assert [(v['citation'],v['full_text']) for v in rec]==[(v['citation'],v['full_text']) for v in live];item.update(native_format='HTML',record_count=len(rec),citations_bodies_equal=True)
   export_checks.append(item)
  report.append({'job':slug,'records':checks['record_count'],'raw_hash_verified':True,'deterministic_jsonl_csv':True,'table_checks':table_checks,'cross_reference_targets_checked':cross_reference_targets_checked,'native_exports':export_checks,'complete_corpus':False})
 # Meaningful negative checks: modified raw bytes fail before parsing; wrong publication/customer cannot pass.
 with tempfile.TemporaryDirectory() as tmp:
  d=Path(tmp);slug=next(iter(samples));src=R/samples[slug]
  for f in ['source.html','acquisition.json']:(d/f).write_bytes((src/f).read_bytes())
  (d/'source.html').write_bytes((d/'source.html').read_bytes()+b' tamper')
  try:collect.parse(jobs[slug],d)
  except AssertionError:pass
  else:raise AssertionError('tampered source accepted')
 ecode_slug=next(k for k in samples if jobs[k]['family']=='eCode360');wrong=copy.deepcopy(jobs[ecode_slug]);wrong['expected_identity']['code_id']='INVALID-EDITION'
 with tempfile.TemporaryDirectory() as tmp:
  d=Path(tmp);src=R/samples[ecode_slug]
  for f in ['source.html','acquisition.json']:(d/f).write_bytes((src/f).read_bytes())
  try:collect.parse(wrong,d)
  except collect.ec.ValidationError:pass
  else:raise AssertionError('wrong edition accepted')
 print(json.dumps({'results':report,'tampered_raw_rejected':True,'wrong_edition_rejected':True},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
