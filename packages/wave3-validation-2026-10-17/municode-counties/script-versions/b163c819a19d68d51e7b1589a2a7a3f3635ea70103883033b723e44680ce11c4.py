"""Native official-government PDF acquisition + bounded page normalization, no publisher calls."""
import argparse,json,csv,hashlib,platform,re,time,urllib.request,urllib.error,urllib.parse
from datetime import datetime,timezone
from pathlib import Path
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sources():
 routes=json.loads((ROOT/'official-route-inventory.json').read_text());result={}
 for r in routes:
  if r['name']=='clark-title30':
   link=next(l for l in r['links'] if l['text']=='Title 30' and '.pdf' in l['url'].lower())
   result['clark-title30']={'sequence':96,'jurisdiction':'Clark County','state':'NV','entity_type':'County','publication':'Title30 Unified Development Code','url':link['url'],'route_evidence':r['evidence_path'],'scope_note':'County development code; preserve explicit unincorporated-area qualifiers. Does not establish applicability of all county enactments or incorporated-city codes.'}
  if r['name']=='baton-rouge-udc':
   for name,prefix in [('baton-rouge-udc-general','Chapter 1 -'),('baton-rouge-udc-uses','Chapter 9 -')]:
    link=next(l for l in r['links'] if l['text'].startswith(prefix))
    result[name]={'sequence':95,'jurisdiction':'Baton Rouge / East Baton Rouge Parish','state':'LA','entity_type':'Combined city/parish government','publication':link['text'],'url':link['url'],'route_evidence':r['evidence_path'],'scope_note':'Combined city/parish target. Applicability to city, parish, unincorporated area or other municipalities must be determined provision by provision; no city-only population assigned.'}
 return result
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*a,**kw):return None

def download(cfg,d):
 d=Path(d);d.mkdir(parents=True,exist_ok=True);p=d/'source.pdf';rp=d/'source.pdf.receipt.json'
 if p.exists():raise ValueError('Fresh output required; original evidence is immutable')
 url=cfg['url'];started=datetime.now(timezone.utc).isoformat();redirects=[]
 for _ in range(5):
  if not urllib.parse.urlparse(url).hostname.endswith('.gov'):raise ValueError('Government hosts only; no publisher redirect followed')
  time.sleep(3.5);body=b'';status=None;headers={};error=None
  try:
   resp=urllib.request.build_opener(NoRedirect()).open(urllib.request.Request(url,headers={'User-Agent':'CompliSolv bounded official-government PDF validation/1.0'}),timeout=90);body=resp.read();status=resp.status;headers=dict(resp.headers)
  except urllib.error.HTTPError as ex:body=ex.read();status=ex.code;headers=dict(ex.headers);error=str(ex)
  except Exception as ex:error=repr(ex)
  if status in [301,302,303,307,308] and headers.get('Location'):
   redirects.append({'url':url,'status':status,'location':headers['Location']});url=urllib.parse.urljoin(url,headers['Location']);continue
  p.write_bytes(body);receipt={'url':cfg['url'],'final_url':url,'started_at':started,'finished_at':datetime.now(timezone.utc).isoformat(),'http_status':status,'headers':headers,'bytes':len(body),'sha256':sha(p),'redirects':redirects,'error':error,'script_sha256':sha(Path(__file__)),'runtime':platform.python_version(),'publisher_requests_sent':0,'method':'native official-government PDF GET; no retries/challenge interaction'};rp.write_text(json.dumps(receipt,indent=2))
  if status!=200 or not body.startswith(b'%PDF-'):raise ValueError('Government PDF unavailable or not PDF; '+str(status)+' '+str(error))
  return
 raise ValueError('Redirect limit')

def parse(cfg,d,out=None):
 d=Path(d);out=Path(out) if out else d/'normalized';out.mkdir(parents=True,exist_ok=True);p=d/'source.pdf';receipt=json.loads((d/'source.pdf.receipt.json').read_text());assert sha(p)==receipt['sha256'];assert p.read_bytes()[:5]==b'%PDF-'
 reader=PdfReader(p);all_candidates=[];table_candidates=[]
 for i,page in enumerate(reader.pages[:60]):
  text=page.extract_text() or ''
  if len(text)<250 or len(re.findall(r'\.{4,}',text))>=4:continue
  if not re.search(r'\b(?:30\.\d|1\.\d|9\.\d|Section|Applicability|Purpose)',text,re.I):continue
  heading=next((l.strip() for l in text.splitlines() if l.strip()),'PDF page '+str(i+1))
  rec={'jurisdiction':cfg['jurisdiction'],'state':cfg['state'],'entity_type':cfg['entity_type'],'publication':cfg['publication'],'identifier':'pdf-page-'+str(i+1),'heading':heading,'citation':cfg['publication']+', PDF page '+str(i+1),'record_type':'pdf_page','record_unit':'source PDF page; not inferred legal section','page':i+1,'text':text,'source_url':cfg['url']+'#page='+str(i+1),'source_sha256':receipt['sha256'],'territorial_scope_note':cfg['scope_note'],'applicability_terms_present':sorted(set(re.findall(r'\b(?:unincorporated|incorporated|parish|county|city)\b',text,re.I))),'complete_corpus':False}
  all_candidates.append(rec)
  if re.search(r'Table\s+(?:30\.|9[.\-]|9\b)',text,re.I):table_candidates.append(i)
 sample=all_candidates[:8]
 if table_candidates:
  extra=next(r for r in all_candidates if r['page']==table_candidates[0]+1)
  if extra not in sample:sample.append(extra)
 tables=[]
 if table_candidates:
  import pdfplumber
  with pdfplumber.open(p) as doc:tables=doc.pages[table_candidates[0]].extract_tables()
  (out/'table-sample.json').write_text(json.dumps({'page':table_candidates[0]+1,'detected_regions':tables,'quality_limit':'PDF grid regions may split merged headers or omit labels; original PDF/text retained. No full table fidelity certification.'},indent=2))
 assert len(sample)>=3,'Too few substantive page records'
 (out/'pages.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in sample))
 with (out/'pages.csv').open('w',newline='') as f:
  fields=['jurisdiction','state','publication','identifier','heading','citation','record_type','page','text','source_url','source_sha256','territorial_scope_note'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:r[k] for k in fields} for r in sample)
 report={'record_count':len(sample),'record_unit':'PDF page','source_pdf_pages':len(reader.pages),'page_scan_limit':min(60,len(reader.pages)),'first_page_text_excerpt':reader.pages[0].extract_text()[:3000],'pdf_table_regions_detected':len(tables),'sample_table_page':table_candidates[0]+1 if table_candidates else None,'cross_reference_pages':sum(bool(re.search(r'Section|§|30\.\d',r['text'])) for r in sample),'nonempty_bodies':True,'unique_identifiers':len({r['identifier'] for r in sample})==len(sample),'source_sha256_verified':True,'complete_corpus':False,'parser_sha256':sha(Path(__file__)),'outputs_sha256':{p.name:sha(p) for p in [out/'pages.jsonl',out/'pages.csv']}}
 (out/'verification.json').write_text(json.dumps(report,indent=2));return report
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--target');ap.add_argument('--out',type=Path);ap.add_argument('--offline',action='store_true');a=ap.parse_args();cfgs=sources()
 for name,cfg in cfgs.items():
  if a.target and name!=a.target:continue
  d=(a.out if a.target else a.out/name) if a.out else ROOT/'native'/name
  try:
   if not a.offline:download(cfg,d);(d/'source-config.json').write_text(json.dumps(cfg,indent=2))
   report=parse(cfg,d);print(name,json.dumps(report),flush=True)
  except Exception as ex:print(name,'FAILED',repr(ex),flush=True)
