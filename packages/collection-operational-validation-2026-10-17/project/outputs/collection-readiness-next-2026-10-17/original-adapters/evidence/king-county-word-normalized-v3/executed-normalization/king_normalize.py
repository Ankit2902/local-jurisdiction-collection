"""Offline source-complete Word-HTML ownership and edition/dependency audit, no network."""
import argparse,collections,csv,re,sys,copy
from pathlib import Path
from urllib.parse import urlsplit,urljoin,unquote
from bs4 import BeautifulSoup,Tag,NavigableString
from source_common import *
from king_acquire import inventory,URL
from model import semantics,image_asset,redact_image_metadata
SECTION=re.compile(r'^(\d+[A-Z]?(?:\.\d+[A-Z]?){2,})\s+(.+)$',re.I)
CHARTER=re.compile(r'^(?:Section\s+)?(\d{3}(?:\.\d+)*[A-Z]?)\.?\s+(.+)$',re.I)
BLOCKS={'p','h1','h2','h3','h4','h5','h6','table','ul','ol','pre','blockquote','svg','img','picture','object','iframe','hr'}
def blocks(root):
 for n in root.children:
  if isinstance(n,NavigableString):
   if clean(n):
    wrap=BeautifulSoup('<p></p>','html.parser').p;wrap.string=str(n);yield wrap
  elif isinstance(n,Tag):
   if n.name in {'script','style','head'}:continue
   if n.name in BLOCKS:yield n
   else:yield from blocks(n)
def datevalue(text):
 from datetime import datetime
 text=re.sub(r'^UPDATED\s*:?\s*','',text,flags=re.I).strip().rstrip('.')
 for fmt in ['%B %d, %Y','%b %d, %Y','%m/%d/%Y']:
  try:return datetime.strptime(text,fmt).date().isoformat()
  except ValueError:pass
 return None

def parse(raw,doc):
 text,encoding=decode(raw);s=BeautifulSoup(text,'html.parser');body=s.body
 if body is None:raise ValueError('Source body absent')
 visible=clean(body.get_text(' ',strip=True))
 if doc['kind']=='title':
  number=re.match(r'Title\s+(\d+[A-Z]?)',doc['heading'],re.I).group(1)
  if not re.search(r'\bTitle\s+'+re.escape(number)+r'(?![A-Z0-9])',visible[:2000],re.I):raise ValueError('Wrong source document title identity '+doc['url'])
 elif doc['kind']=='charter' and not re.search(r'\bCHARTER\b',visible[:1000],re.I):raise ValueError('Wrong source Charter identity')
 units=list(blocks(body));pattern=CHARTER if doc['kind']=='charter' else SECTION if doc['kind']=='title' else re.compile(r'(?!)')
 owners=[];records=[];section_toc=[];anchors={};seen_heading=collections.Counter();current=None
 def new(i,label,kind,num=''):
  rid=sha((doc['url']+'::block-'+str(i)).encode());r={'record_id':rid,'source_url':doc['url'],'source_document_id':doc['id'],'source_sha256':sha(raw),'source_ordinal':len(records),'jurisdiction':'King County, WA','publication':'Charter' if doc['kind']=='charter' else 'King County Code','document_heading':doc['heading'],'kind':kind,'number':num,'heading':label,'block_indices':[],'semantic_html':'','full_text':'','tables':[],'assets':[],'links':[],'notes':[],'image_placeholder_count':0};records.append(r);return r
 for i,b in enumerate(units):
  label=clean(b.get_text(' ',strip=True));bolds=[clean(x.get_text(' ',strip=True)) for x in b.find_all(['b','strong']) if clean(x.get_text(' ',strip=True))];leading=bolds[0] if bolds else ''
  if re.fullmatch(r'(?:Section\s+)?\d+[A-Z]?(?:\.\d+[A-Z]?)*\.?',leading,re.I) and len(bolds)>1:leading+=' '+bolds[1]
  match=pattern.match(leading);is_heading=bool(match and label.startswith(leading))
  if is_heading:
   num,name=match.groups();current=new(i,name,'section',num);current['source_heading_literal']=leading;seen_heading[num]+=1
  elif b.name in {'h1','h2','h3','h4','h5','h6'}:current=new(i,label,'container')
  elif current is None:current=new(i,doc['heading']+' — source introduction','source_editorial')
  # Every source block, including operative container history and blank/visual units, has one owner.
  m=semantics(b,doc['url']);current['block_indices'].append(i);current['semantic_html']+=m['html'];current['full_text']=clean(current['full_text']+' '+m['text']);current['tables'].extend(m['tables']);current['assets'].extend(m['assets']);current['links'].extend(m['links']);current['notes'].extend(m['notes']);current['image_placeholder_count']+=m['image_placeholder_count'];owners.append(current['record_id'])
  for el in [b]+b.find_all(True):
   for anchor in set(filter(None,[el.get('id'),el.get('name')])):anchors.setdefault(anchor,[]).append({'record_id':current['record_id'],'block_index':i})
  if not bolds:
   t=pattern.match(label)
   if t:section_toc.append({'number':t.group(1),'heading':t.group(2),'block_index':i})
 # A source-heading citation can repeat (editorial quotations); never deduplicate by citation.
 local=[];missing=[]
 for a in body.select('a[href]'):
  u=urljoin(doc['url'],a['href']);p=urlsplit(u)
  if p.fragment and key(u)==doc['url']:
   target=unquote(p.fragment);entry={'fragment':target,'label':clean(a.get_text(' ',strip=True)),'owners':anchors.get(target,[])};local.append(entry)
   if not entry['owners']:missing.append(entry)
 updates=[clean(p.get_text(' ',strip=True)) for p in body.select('p') if clean(p.get_text(' ',strip=True)).upper().startswith('UPDATED')]
 update_dates=[datevalue(v) for v in updates];expected=datevalue(doc['updated']);conflict=bool(expected and update_dates and expected not in update_dates)
 heading_only=[]
 for r in records:
  if r['kind']=='section':
   own_body=r['full_text'][len(r.get('source_heading_literal','')):].strip() if r['full_text'].startswith(r.get('source_heading_literal','')) else r['full_text']
   r['body_qualification']='substantive_source_body' if own_body else 'explicit_reserved_or_repealed' if re.search(r'\b(reserved|repealed|omitted)\b',r['heading'],re.I) else 'unresolved_heading_only'
   if r['body_qualification']=='unresolved_heading_only':heading_only.append(r['record_id'])
 actual_tables=len(body.find_all('table'));owned_tables=sum(len(r['tables']) for r in records)
 toc_missing=[t for t in section_toc if not seen_heading[t['number']]]
 return records,{'document_id':doc['id'],'url':doc['url'],'heading':doc['heading'],'encoding':encoding,'source_blocks':len(units),'owned_blocks':len(owners),'unique_owned_block_indices':len({i for r in records for i in r['block_indices']}),'records':len(records),'heading_only_unresolved':heading_only,'section_records':sum(r['kind']=='section' for r in records),'source_tables':actual_tables,'owned_tables':owned_tables,'local_toc_links':len(local),'missing_local_targets':missing,'independent_plain_section_entries':len(section_toc),'plain_section_entries_without_body_heading':toc_missing,'repeated_citations':{k:v for k,v in seen_heading.items() if v>1},'index_updated':doc['updated'],'body_updated_markers':updates,'index_body_date_conflict':conflict,'local_target_inventory':local}

def run(source,out):
 source=Path(source).resolve();out=Path(out).resolve()
 if out.exists() and any(out.iterdir()):raise ValueError('Fresh normalized output required')
 out.mkdir(parents=True,exist_ok=True);state=load(source/'checkpoint.json');errors=[];arts=state['artifacts']
 if state.get('source_url')!=URL:raise ValueError('Wrong publication source identity')
 for a in arts:
  if a.get('final_url',a['source_url'])!=a['source_url']:raise ValueError('Unexpected retained source redirect identity')
 for a in arts:
  raw=(source/a['path']).read_bytes()
  if sha(raw)!=a['sha256']:raise ValueError('Corrupt retained source '+a['path'])
 opening=next(a for a in arts if a['role']=='index-start');closing=next((a for a in arts if a['role']=='index-end'),None)
 start=inventory((source/opening['path']).read_bytes());end=inventory((source/closing['path']).read_bytes()) if closing else []
 if start!=state['inventory'] or start!=end:errors.append('Opening/closing/source-inventory mismatch')
 records=[];reports=[];dependencies=[];doc_urls={d['url'] for d in start}
 for d in start:
  matches=[a for a in arts if a['role']=='content' and a['source_url']==d['url'] and a['status']==200]
  if len(matches)!=1:errors.append('Missing/duplicate source document '+d['url']);continue
  rr,report=parse((source/matches[0]['path']).read_bytes(),d);records.extend(rr);reports.append(report)
  if report['heading_only_unresolved']:errors.append('Unresolved heading-only source sections '+d['url'])
  if report['source_tables']!=report['owned_tables']:errors.append('Table ownership mismatch '+d['url'])
  if report['source_blocks']!=report['unique_owned_block_indices']:errors.append('Source block ownership mismatch '+d['url'])
  if report['missing_local_targets']:errors.append('Unresolved local source links '+d['url'])
  if report['index_body_date_conflict']:errors.append('Index/document updated-date conflict '+d['url'])
  # Plain section entries are a supplementary independent source ledger, not all are operative (e.g. disposition tables).
  for r in rr:
   for a in r['assets']:
    asset=dict(a,owner_record_id=r['record_id'])
    if image_asset(asset):asset.update(required=False,status='policy_omitted_image')
    elif key(asset['url']) in doc_urls:asset.update(required=False,status='retained_primary_document')
    elif asset.get('status') not in ['retained_inline','retained_inline_reference']:asset.update(required=True,status='unresolved_nonimage_attachment');errors.append('Unresolved nonimage attachment '+asset['url'])
    dependencies.append(asset)
  # Hyperlinks to other legal layers are retained as references; every potential file attachment is above.
 ids=[r['record_id'] for r in records]
 if len(ids)!=len(set(ids)):errors.append('Duplicate ownership record IDs')
 for r in records:
  if re.search(r'data:image/|<(?:img|svg|picture)\b|background\s*=',r['semantic_html'],re.I):errors.append('Active normalized image markup '+r['record_id'])
 transport.atomic(out/'records.jsonl',b''.join(canon(redact_image_metadata(r))+b'\n' for r in records))
 with (out/'records.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['record_id','source_url','publication','document_heading','kind','number','heading','full_text']);w.writeheader();w.writerows({k:r[k] for k in w.fieldnames} for r in records)
 save(out/'document-audits.json',reports);save(out/'dependencies.json',dependencies)
 code={n:sha((Path(__file__).parent/n).read_bytes()) for n in ['king_normalize.py','king_acquire.py','source_common.py','shared_transport.py','model.py','legacy_html.py']};save(out/'executed-normalization.json',code)
 summary={'schema':'original-official-normalization-1','source':str(source),'normalized_at':stamp(),'complete':not errors and not state['errors'],'whole_jurisdiction_complete':False,'scope':'All 35 HTML documents listed by official County Code index, including Charter and editorial materials; independent Board of Health publication excluded and unresolved','opening_closing_inventory_equal':start==end,'inventory_documents':len(start),'acquired_documents':len(reports),'records':len(records),'sections':sum(r['kind']=='section' for r in records),'source_blocks':sum(r['source_blocks'] for r in reports),'owned_blocks':sum(r['owned_blocks'] for r in reports),'source_tables':sum(r['source_tables'] for r in reports),'owned_tables':sum(r['owned_tables'] for r in reports),'images_downloaded':False,'image_placeholders':sum(r['image_placeholder_count'] for r in records),'unresolved_nonimage_dependencies':sum(d.get('status')=='unresolved_nonimage_attachment' for d in dependencies),'errors':sorted(set(errors)),'code_fingerprint':code};save(out/'summary.json',summary);return summary
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args();r=run(a.source,a.out);print(json.dumps(r,indent=2));sys.exit(0 if r['complete'] else 2)
