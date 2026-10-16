#!/usr/bin/env python3
"""Offline CodeHUB parser/package CLI. Network acquisition lives in acquire.py."""
from __future__ import annotations
import argparse, csv, hashlib, json, re, os
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit
from bs4 import BeautifulSoup, Tag, NavigableString, Comment
VERSION='gridics-validation-1.0'
BASE='https://codehub.gridics.com/us/ca/cupertino'
UUID=r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
PATH=re.compile(r'/(?:'+UUID+r')(?:/'+UUID+r')*$',re.I)
FIELDS='jurisdiction code_name division title subtitle chapter subchapter article part subpart section_number section_name citation full_text source_url scrape_date'.split()

def digest(v):return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()
def canonical(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def save(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8');os.replace(tmp,p)
def jsonl(p,rows):Path(p).write_text(''.join(canonical(x)+'\n' for x in rows),encoding='utf8')
def clean(v):return ' '.join(v.split())
def valid_route(url):
 u=urlsplit(url)
 return u.scheme=='https' and u.netloc=='codehub.gridics.com' and u.path.rstrip('/')=='/us/ca/cupertino' and not u.query and bool(PATH.fullmatch(u.fragment))
def route(path):
 if not PATH.fullmatch(path):raise ValueError('Not an observed UUID path: '+path)
 return BASE+'#'+path

def own_heading(node):
 return next((h for h in node.select('h1,h2,h3,h4,h5,h6') if h.find_parent(class_='section') is node),None)

def semantic(node):
 """One recursion per node, no independent descendant selections. Retain HTML too."""
 if isinstance(node,Comment):return ''
 if isinstance(node,NavigableString):return str(node)
 if not isinstance(node,Tag):return ''
 n=node.name
 if n in {'script','style','button','noscript'} or set(node.get('class',[])) & {'share-print','section','fake-div-border'}:return ''
 if n=='img':return '[IMAGE]'
 if n=='br':return '\n'
 body=''.join(semantic(c) for c in node.children)
 if n in {'sup','sub'}:return '<'+n+'>'+body+'</'+n+'>'
 if n=='a':return body
 # HTML tables preserve header/cell identity and spans in corpus-compatible text.
 if n in {'table','thead','tbody','tfoot','tr','td','th','caption'}:
  attrs=''.join(' '+a+'="'+str(node[a])+'"' for a in ['rowspan','colspan','scope'] if a in node.attrs)
  return '<'+n+attrs+'>'+body+'</'+n+'>'+ ('\n' if n in {'tr','table'} else '')
 if n in {'ol','ul'}:
  attrs=''.join(' '+a+'="'+str(node[a])+'"' for a in ['type','start','reversed'] if a in node.attrs)
  if 'type' not in node.attrs and n=='ol':
   style=re.search(r'list-style-type:\s*([a-z-]+)',node.get('style',''))
   value={'upper-alpha':'A','lower-alpha':'a','upper-roman':'I','lower-roman':'i','decimal':'1'}.get(style.group(1)) if style else None
   if value:attrs+=' type="'+value+'"'
  return '\n<'+n+attrs+'>'+body+'</'+n+'>\n'
 if n=='li':
  attrs=' value="'+str(node['value'])+'"' if 'value' in node.attrs else ''
  return '<li'+attrs+'>'+body.strip()+'</li>\n'
 if n in {'p','div','blockquote','dl','dt','dd','pre','figure','figcaption','aside','h1','h2','h3','h4','h5','h6'}:return '\n'+body+'\n'
 return body

def own_body(node):
 copy=BeautifulSoup(str(node),'html.parser').select_one('.section')
 for sub in list(copy.select('.section')):sub.decompose()
 for ui in list(copy.select('.share-print,script,style,button')):ui.decompose()
 heading=own_heading(copy)
 if heading:heading.decompose()
 text=''.join(semantic(x) for x in copy.children)
 lines=[re.sub(r'[\t\r\f\v ]+',' ',x).strip() for x in text.split('\n')]
 text=re.sub(r'\n{3,}','\n\n','\n'.join(lines)).strip()
 return text, str(copy)

def inventory_html(html):
 s=BeautifulSoup(html,'html.parser');rows=[]
 tree=s.select_one('ul.doc-tree[role="tree"]')
 if not tree:raise ValueError('Observed CodeHUB navigation tree missing')
 for order,li in enumerate(tree.select('li[role="treeitem"]')):
  ids=[c[3:] for c in li.get('class',[]) if re.fullmatch('id-'+UUID,c,re.I)]
  title=li.select_one(':scope > .doc-tree-node-content-wrapper > .doc-tree-title')
  label=clean(title.get_text(' ',strip=True)) if title else ''
  if not ids:
   if label=='TABLE OF CONTENTS':continue
   raise ValueError('Unidentified navigation item: '+label)
  ancestors=[]
  for par in reversed(list(li.parents)):
   if isinstance(par,Tag) and par.name=='li':
    ancestors.extend(c[3:] for c in par.get('class',[]) if re.fullmatch('id-'+UUID,c,re.I))
  path='/'+ '/'.join(ancestors+ids)
  children=li.select_one(':scope > ul[role="group"]')
  expandable='has-children' in li.get('class',[])
  rows.append({'node_id':ids[0],'parent_node_id':ancestors[-1] if ancestors else None,'path':path,'display_heading':label,'source_order':order,'source_url':route(path),'node_kind':'section' if re.match(r'^\d+(?:\.\d+)+\s',label) else 'container','has_children':expandable,'children_enumerated':bool(children and children.select('li')) if expandable else True})
 return rows

def parse_html(html,url):
 if not valid_route(url):raise ValueError('Out of publication route')
 if '[Truncated]' in html:raise ValueError('Truncated browser export; reacquire complete DOM in bounded chunks')
 s=BeautifulSoup(html,'html.parser');nodes=[];records=[];dispositions=[]
 bypath={}
 for n in s.select('div.section[data-path]'):
  p=n.get('data-path','');h=own_heading(n)
  if not PATH.fullmatch(p) or n.get('id')!='section-'+p.rsplit('/',1)[-1] or h is None:raise ValueError('Missing/conflicting publisher node identity')
  if p in bypath:raise ValueError('Duplicate rendered source node')
  bypath[p]=n
 if not bypath:raise ValueError('No UUID-backed legal containers; shell or error page')
 requested=urlsplit(url).fragment
 if requested not in bypath:raise ValueError('Requested UUID route absent from legal containers')
 for order,(p,n) in enumerate(bypath.items()):
  h=own_heading(n);label=clean(h.get_text(' ',strip=True));text,structured=own_body(n);nodeid=p.rsplit('/',1)[-1]
  parents=p.strip('/').split('/')[:-1];pathparts=p.strip('/').split('/')
  hierarchy={}
  for k in range(1,len(pathparts)+1):
   par=bypath.get('/'+'/'.join(pathparts[:k]));ph=own_heading(par) if par else None
   if ph:
    pl=clean(ph.get_text(' ',strip=True))
    if re.match('^TITLE\\b',pl,re.I):hierarchy['title']=pl
    if re.match('^CHAPTER\\b',pl,re.I):hierarchy['chapter']=pl
  item={'node_id':nodeid,'parent_node_id':parents[-1] if parents else None,'source_order':order,'path':p,'source_url':route(p),'display_heading':label,'locator':{'kind':'html-id','value':n['id']},'node_kind':'section' if h.name in {'h4','h5','h6'} else 'container','structured_html':structured,'semantic_body_sha256':digest(canonical({'text':text,'images':[(x.get('src'),x.get('alt')) for x in BeautifulSoup(structured,'html.parser').select('img')]}))}
  nodes.append(item)
  status='reserved_or_repealed' if re.search(r'\b(reserved|repealed)\b',label,re.I) and not text else ('included' if text else 'structural')
  ids=[]
  if text:
   row={x:'' for x in FIELDS};m=re.match(r'^(\d+(?:\.\d+)+)\s+(.+)$',label)
   row.update(jurisdiction='Cupertino',code_name='Municipal Code',citation=label,section_number=m.group(1) if m else '',section_name=m.group(2) if m else label,full_text=text,source_url=route(p),**hierarchy)
   rid='cupertino-ca:municipal-code:'+nodeid
   records.append({'record_id':rid,'node_id':nodeid,'row':row});ids=[rid]
  dispositions.append({'node_id':nodeid,'disposition':status,'record_ids':ids,'evidence':'Own body excludes all nested publisher containers; status classification from own heading.'})
 return nodes,records,dispositions

def source_path(root,relative):
 p=(root/relative).resolve()
 if not p.is_relative_to(root.resolve()):raise ValueError('Artifact escapes snapshot bundle')
 return p

def replay(manifest_path,out,stop_after=None):
 manifest_path=Path(manifest_path);root=manifest_path.parent;m=json.loads(manifest_path.read_text());out=Path(out);out.mkdir(parents=True,exist_ok=True)
 if not m.get('snapshot_id') or not m.get('source_version'):raise ValueError('Explicit snapshot and version binding required')
 binding={'jurisdiction':'cupertino-ca','publication':'municipal-code','snapshot_id':m['snapshot_id'],'source_version':m['source_version'],'manifest_sha256':digest(manifest_path.read_bytes()),'parser_sha256':digest(Path(__file__).read_bytes()),'config_sha256':digest(canonical({'version':VERSION,'fields':FIELDS,'base':BASE}))}
 cp=out/'checkpoint.json';state={'binding':binding,'processed':[]}
 if cp.exists():
  state=json.loads(cp.read_text())
  if state['binding']!=binding:raise ValueError('Checkpoint binding mismatch; use a separate output directory')
 # Recompute parsed records from immutable sources on each resume; checkpoint is progress only.
 allnodes={};allrecords={};alldisp={};prov={};exceptions=[]
 for ix,a in enumerate(m['artifacts']):
  raw=source_path(root,a['path']).read_bytes()
  if digest(raw)!=a['sha256']:raise ValueError('Raw artifact hash mismatch: '+a['path'])
  retained=source_path(out,a['path']);retained.parent.mkdir(parents=True,exist_ok=True)
  if retained.exists() and retained.read_bytes()!=raw:raise ValueError('Immutable output raw artifact conflict')
  retained.write_bytes(raw)
  ns,rs,ds=parse_html(raw.decode('utf8'),a['url'])
  for n in ns:
   key=n['node_id'];prev=allnodes.get(key)
   if prev and (prev['path']!=n['path'] or prev['semantic_body_sha256']!=n['semantic_body_sha256']):raise ValueError('Conflicting same-node body/version: '+key)
   allnodes.setdefault(key,{**n,'raw_artifact_path':a['path'],'raw_sha256':a['sha256'],'source_version':m['source_version'],'publication_id':'municipal-code','jurisdiction_slug':'cupertino-ca'})
  for r in rs:
   r['row']['scrape_date']=a.get('retrieved_at','')[:10]
   prev=allrecords.get(r['record_id'])
   if prev and prev['row']!=r['row']:raise ValueError('Conflicting duplicate record')
   allrecords.setdefault(r['record_id'],r)
   prov.setdefault(r['record_id'],{'record_id':r['record_id'],'node_id':r['node_id'],'publication_id':'municipal-code','raw_artifact_path':a['path'],'raw_sha256':a['sha256'],'locator':{'kind':'html-id','value':'section-'+r['node_id']},'extraction_version':VERSION,'source_version':m['source_version']})
  for d in ds:alldisp[d['node_id']]=d
  state['processed']=list(range(ix+1));save(cp,state)
  if stop_after is not None and ix+1>=stop_after:return {'status':'interrupted','processed_artifacts':ix+1}
 inv=[]
 if m.get('inventory'):
  ia=m['inventory'];ib=source_path(root,ia['path']).read_bytes()
  if digest(ib)!=ia['sha256']:raise ValueError('Inventory hash mismatch')
  retained=source_path(out,ia['path']);retained.parent.mkdir(parents=True,exist_ok=True);retained.write_bytes(ib)
  inv=json.loads(ib)
 for n in inv:
  if n['node_id'] not in allnodes:
   allnodes[n['node_id']]={**n,'source_version':m['source_version'],'publication_id':'municipal-code','jurisdiction_slug':'cupertino-ca'}
   alldisp[n['node_id']]={'node_id':n['node_id'],'disposition':'unresolved','record_ids':[],'evidence':'Navigation node not acquired in bounded sample.'}
 for n in allnodes.values():
  if n['node_id'] not in {x['node_id'] for x in inv}:exceptions.append({'node_id':n['node_id'],'issue':'Not independently enumerated in retained navigation; sample inventory incomplete'})
 rows=[r['row'] for r in allrecords.values()];pub=out/'publications/municipal-code';pub.mkdir(parents=True,exist_ok=True)
 metadata={'jurisdiction':'Cupertino','publication_id':'municipal-code','source_version':m['source_version'],'snapshot_id':m['snapshot_id'],'total_provisions':len(rows),'completion_status':'bounded_sample_only'}
 for stem,data in [('fulltext',rows),('toc',[dict(r,full_text='') for r in rows])]:
  envelope={'metadata':metadata,'provisions':data};save(pub/(stem+'.json'),envelope);save(out/('aggregate-'+stem+'.json'),envelope)
  for p in [pub/(stem+'.csv'),out/('aggregate-'+stem+'.csv')]:
   with p.open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(data)
 jsonl(out/'source-nodes.jsonl',allnodes.values());jsonl(out/'node-dispositions.jsonl',alldisp.values());jsonl(out/'record-provenance.jsonl',prov.values());jsonl(out/'exceptions.jsonl',exceptions)
 save(out/'source-snapshot-manifest.json',m)
 save(out/'publications.json',[{'publication_id':'municipal-code','official_title':'Cupertino Municipal Code','root':BASE,'scope_decision':'bounded validation sample','source_version':m['source_version'],'currency_raw':m.get('currency_raw'),'currency_status':'unverified' if not m.get('currency_raw') else 'retained_raw_text_only'}])
 report={'status':'bounded_sample_only','record_count':len(rows),'rendered_source_nodes':sum(1 for n in allnodes.values() if 'raw_sha256' in n),'inventory_nodes':len(inv),'disposition_counts':{k:sum(x['disposition']==k for x in alldisp.values()) for k in ['included','structural','reserved_or_repealed','unresolved']},'independent_inventory_complete':False,'full_collection_validated':False,'exceptions':len(exceptions)}
 save(out/'validation-report.json',report)
 files={str(p.relative_to(out)):digest(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file() and p.name not in {'run-manifest.json','checkpoint.json'}}
 save(out/'run-manifest.json',{'binding':binding,'source_manifest':m,'status':'bounded_sample_only','artifact_hashes':files,'counts':report})
 return report

def main():
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='cmd',required=True)
 q=sub.add_parser('replay');q.add_argument('--manifest',required=True);q.add_argument('--out',required=True);q.add_argument('--stop-after',type=int)
 q=sub.add_parser('inventory');q.add_argument('--html',required=True);q.add_argument('--out',required=True)
 a=p.parse_args()
 if a.cmd=='replay':print(json.dumps(replay(a.manifest,a.out,a.stop_after),indent=2))
 else:
  rows=inventory_html(Path(a.html).read_text());save(a.out,rows);print(json.dumps({'nodes':len(rows),'closed_branches':sum(not n['children_enumerated'] for n in rows),'complete':False}))
if __name__=='__main__':main()
