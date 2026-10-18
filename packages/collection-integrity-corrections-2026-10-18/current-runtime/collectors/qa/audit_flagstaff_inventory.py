"""Reconstruct all Flagstaff source TOC controls and retained closing independently."""
import argparse,collections,hashlib,json,re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin,urldefrag
from lxml import html
BASE='https://www.codepublishing.com/AZ/Flagstaff/'
def sha(v):return hashlib.sha256(v).hexdigest()
def clean(v):return ' '.join(v.split())
def text(node):return clean(''.join(node.itertext()))
def decode(raw):
 try:return raw.decode('utf-8-sig')
 except UnicodeDecodeError:return raw.decode('cp1252')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--normalized',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 if a.out.exists():raise ValueError('Fresh report required')
 cpraw=(a.source/'checkpoint.json').read_bytes();cp=json.loads(cpraw);rr=(a.normalized/'records.jsonl').read_bytes();records=[json.loads(x) for x in rr.split(b'\n') if x.strip()];errors=[];artifacts=[]
 for r in cp['artifacts']:
  raw=(a.source/r['path']).read_bytes()
  if sha(raw)!=r['sha256'] or r['status']!=200 or r['source_url']!=r['final_url']:raise ValueError('Unbound source artifact '+r['path'])
  artifacts.append({k:r.get(k) for k in ['role','source_url','path','sha256','started_at','finished_at']})
 def source(role,url=None):
  rows=[r for r in cp['artifacts'] if r['role']==role and (url is None or r['source_url']==url)]
  if len(rows)!=1:raise ValueError('Missing/duplicate source witness '+role+' '+str(url))
  r=rows[0];return html.fromstring(decode((a.source/r['path']).read_bytes()).encode('utf-8'),parser=html.HTMLParser(encoding='utf-8')),r
 roots=[]
 for role in ['root-toc-start','root-toc-end']:
  doc,_=source(role);rows=[]
  for p in doc.xpath('//*[@id="divmuni"]/p'):
   control=p.xpath('.//input[@name="code"]');anchor=p.xpath('.//a[@href]')
   if anchor:rows.append({'source_url':urljoin(BASE+'cgi/FlagstaffTOC.pl',anchor[0].get('href')),'value':control[0].get('value') if control else anchor[0].get('href'),'label':text(anchor[0]),'source_id':anchor[0].get('id')})
  roots.append(rows)
 if roots[0]!=roots[1] or roots[0]!=[r['root'] for r in cp['observed_readers']]:errors.append('Root source inventory mismatch')
 phases=[]
 for role in ['toc-start','toc-end']:
  entries=[]
  for ri,reader in enumerate(cp['observed_readers']):
   entries.append(dict(roots[0][ri],root_index=ri,source_order=len(entries)))
   doc,_=source(role,reader['url'])
   for p in doc.xpath('//p[.//input[@name="code"] and .//a[@href]]'):
    control=p.xpath('.//input[@name="code"]')[0];anchor=p.xpath('.//a[@href]')[0];url=urljoin(BASE+'cgi/FlagstaffTOC.pl',anchor.get('href'))
    if not url.startswith(BASE+'html/') or not urldefrag(url)[0].endswith('.html'):raise ValueError('Foreign or unprofiled source control route')
    entries.append({'root_index':ri,'source_order':len(entries),'source_url':url,'value':control.get('value'),'label':text(anchor),'source_id':anchor.get('id'),'ancestor_classes':control.get('class','').split()})
  phases.append(entries)
 projection=[{k:v for k,v in e.items() if k!='edge_id'} for e in cp['inventory']]
 if phases[0]!=phases[1] or phases[0]!=projection:errors.append('Independent opening/closing TOC projection mismatch')
 original_docs={urldefrag(e['source_url'])[0] for e in phases[0]};content=[r for r in cp['artifacts'] if r['role']=='content']
 if original_docs!={r['source_url'] for r in content} or len(content)!=len(original_docs):errors.append('Content document inventory missing/duplicate/extra')
 mapped=collections.Counter(edge for r in records for edge in r.get('source_toc_edges',[]));expected=collections.Counter(e['edge_id'] for e in cp['inventory'])
 if mapped!=expected:errors.append('Output TOC edge ownership mismatch')
 for r in records:
  if urldefrag(r['source_url'])[0] not in original_docs:errors.append('Output record foreign source URL')
 currencies=[]
 for role in ['currency-start','currency-end']:
  doc,_=source(role);matches=[text(p) for p in doc.xpath('//p') if 'current through' in text(p).lower()];currencies.append(matches)
 if not currencies[0] or currencies[0]!=currencies[1]:errors.append('Independent source currency text mismatch')
 opening=[r for r in cp['artifacts'] if r['role']=='toc-start'];closing=[r for r in cp['artifacts'] if r['role']=='toc-end']
 parse=lambda value:datetime.fromisoformat(value)
 if max(parse(r['finished_at']) for r in opening)>min(parse(r['started_at']) for r in content):errors.append('Opening readers after substantive source acquisition')
 if min(parse(r['started_at']) for r in closing)<max(parse(r['finished_at']) for r in content):errors.append('Closing readers before substantive source acquisition completed')
 assert cpraw==(a.source/'checkpoint.json').read_bytes() and rr==(a.normalized/'records.jsonl').read_bytes()
 report={'passed':not errors,'script_sha256':sha(Path(__file__).read_bytes()),'source_checkpoint_sha256':sha(cpraw),'records_sha256':sha(rr),'source_roots':len(roots[0]),'source_edges_per_phase':len(phases[0]),'source_documents':len(original_docs),'normalized_records':len(records),'mapped_edges':sum(mapped.values()),'opening_closing_native_projection_equal':phases[0]==phases[1],'source_currency_paragraphs':currencies,'source_raw_receipts':artifacts,'errors':errors,'network_requests_sent':0,'scope':'Independent raw native controls/root/route/chronology and complete source-document set. Every TOC edge has exactlyone output owner. Closing verifies native inventory and currency, not a second download of every legal body; legal effective-date interpretation and separate Employee Handbook are outside this receipt.'};a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['passed','source_roots','source_edges_per_phase','source_documents','normalized_records','errors']}));return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
