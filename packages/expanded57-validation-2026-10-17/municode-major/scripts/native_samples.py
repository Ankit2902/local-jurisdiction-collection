"""Standalone native publisher export download and bounded, conservative normalization."""
import argparse,csv,hashlib,json,re,platform,subprocess,time
from pathlib import Path
from datetime import datetime,timezone
from municode_shared import fetch
from lxml import html,etree
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
SOURCES={
 'new-orleans-czo':{'url':'https://czo.nola.gov/print-all/','format':'html','jurisdiction':'New Orleans','state':'LA','family':'Comprehensive Zoning Ordinance'},
 'tulsa-zoning':{'url':'https://tulsaplanning.org/plans/TulsaZoningCode.pdf','format':'pdf','jurisdiction':'Tulsa','state':'OK','family':'Zoning Code'},
 'tulsa-subdivision':{'url':'https://tulsaplanning.org/plans/Tulsa-subregs.pdf','format':'pdf','jurisdiction':'Tulsa','state':'OK','family':'Metropolitan Area Subdivision and Development Regulations'},
}
def parse_html(p,cfg):
 doc=html.fromstring(p.read_bytes());body=doc.find('body');body=doc if body is None else body
 for e in body.xpath('.//script|.//style|.//nav'):e.drop_tree()
 records=[];cur=None
 for event,e in etree.iterwalk(body,events=('start','end')):
  if event=='start':
   if e.tag in ('h1','h2','h3','h4','h5','h6'):
    title=' '.join(e.text_content().split())
    if cur:records.append(cur)
    cur={'heading':title,'text_parts':[],'tables':[]}
   if cur and e.tag=='table':cur['tables'].append(etree.tostring(e,encoding='unicode',method='html'))
   if cur and e.text:cur['text_parts'].append(e.text)
  elif cur and e.tail:cur['text_parts'].append(e.tail)
 if cur:records.append(cur)
 out=[]
 for r in records:
  m=re.match(r'^(\d+\.\d+(?:\.[A-Z0-9]+)?)\s+(.+)',r['heading'])
  if m:out.append({'identifier':m[1],'heading':r['heading'],'text':' '.join(' '.join(r['text_parts']).split()),'tables_html':r['tables'],'record_type':'section'})
 numeric_count=len(out)
 out=[r for r in out if len(r['text'])>len(r['heading'])+20]
 sample=out[:12]
 table_record=next((r for r in out if r['tables_html']),None)
 if table_record and table_record not in sample:sample.append(table_record)
 return sample,{'source_numeric_headings':numeric_count,'substantive_numbered_heading_records':len(out),'table_structure_preserved':True,'source_tables':len(body.xpath('.//table')),'sample_tables':sum(len(r['tables_html']) for r in sample),'selection':'first 12 numbered sections plus first table-bearing section','full_html_retained':True}
def parse_pdf(p,cfg):
 reader=PdfReader(p);records=[];table_candidates=[]
 for i,page in enumerate(reader.pages[:32]):
  text=page.extract_text() or ''
  if (re.search(r'Section\s+\d|\d+\.\d{2,3}|\d+-\d{3}',text) and len(text)>300 and len(re.findall(r'\.{4,}',text))<4):
   title=next((x.strip() for x in text.splitlines() if re.search(r'Section\s+\d|\d+\.\d{2,3}',x)),text.splitlines()[0])
   records.append({'identifier':f'pdf-page-{i+1}','heading':title,'text':text,'record_type':'pdf_page','page':i+1,'tables_html':[]})
   if re.search('Table 5-|Table 4-',text):table_candidates.append(i)
 sample=records[:8]
 if table_candidates:
  r=next((r for r in records if r['page']==table_candidates[0]+1),None)
  if r and r not in sample:sample.append(r)
 tables=[]
 if table_candidates:
  import pdfplumber
  with pdfplumber.open(p) as pdf:
   page_idx=table_candidates[0];tables=pdf.pages[page_idx].extract_tables()
  (p.parent/'table-sample.json').write_text(json.dumps({'page':page_idx+1,'tables':tables},indent=2))
 return sample,{'source_pages':len(reader.pages),'parsed_page_limit':min(32,len(reader.pages)),'sample_tables':len(tables),'table_measure':'detected fragments on sampled page; not distinct complete legal tables','table_structure_preserved':False,'table_quality_limitation':'Merged headers split into fragments; some row labels absent. Original PDF and source page image retained.','table_extraction_method':'pdfplumber extract_tables on first table-labelled page' if table_candidates else None,'selection':'first eight substantive matching pages plus first table-labelled page; records are pages, not inferred legal sections','full_pdf_retained':True}
def run(name,offline=False):
 cfg=SOURCES[name];d=ROOT/'native'/name;d.mkdir(parents=True,exist_ok=True);p=d/('source.'+cfg['format'])
 if not offline:
  try:fetch(cfg['url'],p,timeout=90)
  except Exception as ex:
   (d/'failure.json').write_text(json.dumps({'error':str(ex)}))
   if 'CERTIFICATE_VERIFY_FAILED' not in str(ex):print(name,'blocked',ex,flush=True);return
   # macOS curl uses system trust; preserve original urllib TLS failure. No insecure flags.
   failure=p.with_name(p.name+'.urllib-failure');p.replace(failure)
   p.with_name(p.name+'.receipt.json').replace(failure.with_name(failure.name+'.receipt.json'))
   started=datetime.now(timezone.utc).isoformat()
   cp=subprocess.run(['curl','--fail','--location','--silent','--show-error','--max-time','120','--dump-header',str(d/'curl-headers.txt'),'--output',str(p),'--write-out','%{http_code}',cfg['url']],text=True,capture_output=True)
   if cp.returncode:print(name,'curl blocked',cp.stderr);return
   receipt={'url':cfg['url'],'final_url':cfg['url'],'started_at':started,'finished_at':datetime.now(timezone.utc).isoformat(),'http_status':int(cp.stdout),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'method':'curl GET with normal system certificate verification','runtime':subprocess.check_output(['curl','--version'],text=True).splitlines()[0]}
   p.with_name(p.name+'.receipt.json').write_text(json.dumps(receipt,indent=2))
 receipt=json.loads(p.with_name(p.name+'.receipt.json').read_text())
 if receipt['http_status']!=200:print(name,'retained HTTP failure');return
 assert hashlib.sha256(p.read_bytes()).hexdigest()==receipt['sha256']
 records,checks=(parse_html(p,cfg) if cfg['format']=='html' else parse_pdf(p,cfg))
 for r in records:r.update(jurisdiction=cfg['jurisdiction'],state=cfg['state'],publication=cfg['family'],source_url=cfg['url'],source_sha256=receipt['sha256'])
 (d/'normalized.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records))
 with (d/'normalized.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['jurisdiction','state','publication','identifier','heading','text','record_type','source_url','source_sha256']);w.writeheader();w.writerows({k:r.get(k,'') for k in w.fieldnames} for r in records)
 report={'name':name,'record_count':len(records),'unique_identifiers':len({r['identifier'] for r in records})==len(records),'all_text_nonempty':all(len(r['text'])>20 for r in records),'cross_reference_records':sum(bool(re.search(r'Section|Article|Chapter|§',r['text'])) for r in records),'source_sha256_verified':True,'complete_corpus':False,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'runtime':platform.python_version(),**checks}
 (d/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--offline',action='store_true');ap.add_argument('--target',choices=list(SOURCES));a=ap.parse_args()
 for n in ([a.target] if a.target else SOURCES):run(n,a.offline)
