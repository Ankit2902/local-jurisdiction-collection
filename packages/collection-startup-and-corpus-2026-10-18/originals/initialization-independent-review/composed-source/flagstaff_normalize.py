"""Offline full native Flagstaff HTML export + independent expanded TOC reconciliation."""
import argparse,collections,csv,re,sys
from pathlib import Path
from urllib.parse import urljoin,urlsplit,unquote
from bs4 import BeautifulSoup,Tag
from source_common import *
from king_normalize import blocks
from model import semantics,redact_image_metadata,image_asset,dom_text
URL='https://www.codepublishing.com/AZ/Flagstaff/'
def labelkey(t):return re.sub(r'[^\w]','',re.sub(r'^Section\s+','',clean(t),flags=re.I)).casefold()
def load_frames(source,name):
 frames=load(source/(name+'-frames.json'))
 for f in frames:
  if sha((source/f['path']).read_bytes())!=f['sha256']:raise ValueError('Corrupt retained frame '+f['path'])
 return frames

def toc_inventory(source):
 frames=load_frames(source,'selected');toc=next(f for f in frames if 'FlagstaffTOC.pl' in f['url']);s=BeautifulSoup((source/toc['path']).read_bytes(),'html.parser');root=s.select_one('#divmuni')
 if root is None:raise ValueError('Primary City Code source selector missing')
 roots=[{'value':p.select_one('input[name="code"]')['value'],'label':clean(p.select_one('a').get_text(' ',strip=True))} for p in root.find_all('p',recursive=False) if p.select_one('input[name="code"]')]
 entries=[]
 for p in root.select('p'):
  a=p.find('a',href=True);control=p.select_one('input[name="code"]')
  if not a or control is None:continue
  u=urljoin(toc['url'],a['href'])
  if not u.startswith(URL+'html/'):raise ValueError('Foreign primary TOC route')
  entries.append({'source_url':u,'label':clean(a.get_text(' ',strip=True)),'value':control['value'],'source_id':a.get('id'),'ancestor_classes':control.get('class',[])})
 if len(roots)<10 or len(entries)<=len(roots):raise ValueError('Expanded whole-publication TOC missing/truncated')
 urls=[e['source_url'] for e in entries]
 if len(urls)!=len(set(urls)):raise ValueError('Duplicate source TOC identities')
 return roots,entries

def currency(source,stem):
 frames=load_frames(source,stem);claims=[]
 for f in frames:
  t=BeautifulSoup((source/f['path']).read_bytes(),'html.parser').get_text(' ',strip=True)
  claims.extend(clean(x) for x in re.findall(r'The Flagstaff City Charter and City Code are current through[^.]*\.',t,re.I))
 if not claims:raise ValueError('Source edition/currency marker absent')
 return sorted(set(claims))

def run(source,out):
 source=Path(source).resolve();out=Path(out).resolve()
 if out.exists() and any(out.iterdir()):raise ValueError('Fresh normalized output required')
 out.mkdir(parents=True,exist_ok=True);meta=load(source/'receipt.json');errors=[]
 if meta.get('blocked') or meta.get('error'):errors.append('Acquisition did not finish cleanly')
 roots,toc=toc_inventory(source)
 if set(meta.get('checked_values',[]))!=set(e['value'] for e in toc):errors.append('Submitted source root scope mismatch')
 if set(meta.get('preview_hidden_selections',[]))!=set(e['value'] for e in toc):errors.append('Native preview source root scope mismatch')
 beginning=currency(source,'opening')
 try:ending=currency(source,'closing')
 except Exception as e:ending=[];errors.append(str(e))
 if beginning!=ending:errors.append('Opening/closing edition mismatch')
 downloads=[]
 for receipt in source.glob('download-*.receipt.json'):
  a=load(receipt);raw=(source/a['path']).read_bytes()
  if sha(raw)!=a['sha256']:raise ValueError('Corrupt native download '+a['path'])
  downloads.append((raw,a))
 unique={sha(raw):(raw,a) for raw,a in downloads}
 if len(unique)!=1:raise ValueError('Expected one genuine full native export byte identity')
 raw,native=next(iter(unique.values()));text,encoding=decode(raw);s=BeautifulSoup(text,'html.parser');body=s.select_one('#mainContent') or s.body
 if body is None:raise ValueError('Native export legal body absent')
 for x in body.select('#printpreview'):x.decompose()
 units=list(blocks(body));records=[];heads=[];current=None;owned=[]
 for i,b in enumerate(units):
  heading=b.name in ['h1','h2','h3','h4','h5','h6'];label=dom_text(b)
  if heading or current is None:
   ids=[x.get('id') or x.get('name') for x in [b]+b.select('[id],[name]') if x.get('id') or x.get('name')]
   current={'record_id':sha((sha(raw)+'::block-'+str(i)).encode()),'source_url':URL,'source_native_sha256':sha(raw),'source_heading_ids':ids,'heading':label if heading else 'Source introduction','kind':'section' if heading and b.name in ['h3','h4','h5','h6'] else 'container' if heading else 'source_editorial','heading_level':b.name if heading else None,'block_indices':[],'semantic_html':'','full_text':'','tables':[],'assets':[],'links':[],'notes':[],'image_placeholder_count':0};records.append(current)
   if heading:heads.append(current)
  m=semantics(b,URL+'html/');current['block_indices'].append(i);current['semantic_html']+=m['html'];current['full_text']=clean(current['full_text']+' '+m['text']);current['tables'].extend(m['tables']);current['assets'].extend(m['assets']);current['links'].extend(m['links']);current['notes'].extend(m['notes']);current['image_placeholder_count']+=m['image_placeholder_count'];owned.append(current['record_id'])
 available=list(heads);mapping=[];missing=[]
 for e in toc:
  matches=[h for h in available if labelkey(h['heading'])==labelkey(e['label'])]
  if len(matches)!=1:
   fragment=unquote(urlsplit(e['source_url']).fragment);candidate='a'+re.sub(r'[-.]','x',fragment)
   matches=[h for h in available if fragment and candidate in h['source_heading_ids']]
   if len(matches)>1:matches=[h for h in matches if labelkey(e['label']) in labelkey(h['heading']) or labelkey(h['heading']) in labelkey(e['label'])]
  if len(matches)==1:
   h=matches[0];available.remove(h);h['source_url']=e['source_url'];h['source_toc_id']=e['source_id'];mapping.append({'source_url':e['source_url'],'record_id':h['record_id'],'source_heading':e['label'],'native_heading':h['heading']})
  else:missing.append(dict(e,candidate_records=[h['record_id'] for h in matches]))
 if missing:errors.append('Missing/ambiguous source TOC-to-native headings')
 extra=[{'record_id':h['record_id'],'heading':h['heading']} for h in available]
 if extra:errors.append('Native headings absent from source TOC (requires source-backed disposition)')
 source_tables=len(body.find_all('table'));owned_tables=sum(len(r['tables']) for r in records)
 if source_tables!=owned_tables:errors.append('Table ownership mismatch')
 if len(units)!=len({i for r in records for i in r['block_indices']}):errors.append('Block ownership mismatch')
 dependencies=[];primary_documents={key(e['source_url']) for e in toc}
 for r in records:
  for a in r['assets']:
   a=dict(a,owner_record_id=r['record_id'])
   if image_asset(a):a.update(status='policy_omitted_image',required=False)
   elif key(a['url']) in primary_documents:a.update(status='retained_primary_document',required=False)
   elif a.get('status') not in ['retained_inline','retained_inline_reference']:a.update(status='unresolved_nonimage_attachment',required=True)
   dependencies.append(a)
  if re.search(r'data:image/|<(?:img|svg|picture)\b|background\s*=',r['semantic_html'],re.I):errors.append('Active normalized image markup')
 unresolved=[a for a in dependencies if a.get('required') and a.get('status')=='unresolved_nonimage_attachment']
 if unresolved:errors.append('Unresolved nonimage attachment')
 transport.atomic(out/'records.jsonl',b''.join(canon(redact_image_metadata(r))+b'\n' for r in records))
 with (out/'records.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['record_id','source_url','kind','heading','full_text']);w.writeheader();w.writerows({k:r[k] for k in w.fieldnames} for r in records)
 save(out/'source-toc.json',toc);save(out/'toc-mapping.json',mapping);save(out/'missing-toc.json',missing);save(out/'extra-headings.json',extra);save(out/'dependencies.json',dependencies)
 summary={'schema':'flagstaff-native-normalization-1','source':str(source),'complete':not errors,'whole_jurisdiction_complete':False,'scope':'Publisher City Code roots including Charter, Titles1–15, statutory references and Title20; separate Employee Handbook excluded','source_primary_roots':len(roots),'source_toc_entries':len(toc),'native_headings':len(heads),'matched_toc':len(mapping),'missing_toc':len(missing),'extra_headings':len(extra),'records':len(records),'source_blocks':len(units),'owned_blocks':len(owned),'source_tables':source_tables,'owned_tables':owned_tables,'native_download':native,'native_encoding':encoding,'opening_currency':beginning,'closing_currency':ending,'images_downloaded':False,'image_placeholders':sum(r['image_placeholder_count'] for r in records),'unresolved_nonimage_dependencies':len(unresolved),'errors':errors,'code_fingerprint':{n:sha((Path(__file__).parent/n).read_bytes()) for n in ['flagstaff_normalize.py','king_normalize.py','model.py','legacy_html.py','source_common.py']}};save(out/'summary.json',summary);return summary
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args();r=run(a.source,a.out);print(json.dumps(r,indent=2));sys.exit(0 if r['complete'] else 2)
