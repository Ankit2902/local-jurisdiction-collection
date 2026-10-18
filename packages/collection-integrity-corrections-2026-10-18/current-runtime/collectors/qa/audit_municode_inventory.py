#!/usr/bin/env python3
"""Independent raw TOC/Docs/record identity reconciliation; no collector model imports."""
import argparse,collections,hashlib,json
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
def sha(raw):return hashlib.sha256(raw).hexdigest()
def audit(root):
 root=Path(root);cp=json.loads((root/'checkpoint.json').read_text());errors=[];reports=[];sources=[]
 def unit(name,pid=None,job=None):
  entry=cp['units'][name];receipt=json.loads((root/entry['receipt']).read_text());raw=(root/receipt['body_file']).read_bytes()
  if receipt['status']!=200 or receipt.get('access_stop') or sha(raw)!=receipt['sha256'] or sha(raw)!=entry['sha256']:raise ValueError('Raw receipt/hash/access binding '+name)
  if receipt.get('request',{}).get('url',entry['request']['url'])!=entry['request']['url']:raise ValueError('Receipt/request crosswire '+name)
  query=parse_qs(urlsplit(entry['request']['url']).query)
  for key,value in [('productId',pid),('jobId',job)]:
   if value is not None and query.get(key)!=[str(value)]:raise ValueError('Exact product/job query '+name)
  sources.append({'unit':name,'receipt':entry['receipt'],'sha256':sha(raw),'request_url':entry['request']['url']});return json.loads(raw)
 for pid,pub in cp['publications'].items():
  toc=unit(pub['toc_unit'],pid,pub['job_id']);nodes={};paths={}
  def walk(node,parent=None,path=()):
   ident=str(node['Id'])
   if ident in nodes:raise ValueError('Duplicate raw TOC ID '+ident)
   nodes[ident]=node;paths[ident]=list(path)+( [node['Heading']] if node.get('Heading') else [] )
   if node.get('ParentId')!=parent:errors.append({'id':ident,'kind':'source-parent-disagreement'})
   for child in node.get('Children',[]):walk(child,ident,paths[ident])
  walk(toc)
  docs={}
  for name in pub['content_units']:
   data=unit(name,pid,pub['job_id']);data=data if isinstance(data,list) else data['Docs']
   for doc in data:
    if str(doc['Id']) in docs:raise ValueError('Duplicate raw Doc '+str(doc['Id']))
    docs[str(doc['Id'])]=doc
  path=root/'publications'/pid/'sections.jsonl';raw=path.read_bytes();records=[json.loads(line) for line in raw.decode().splitlines() if line.strip()];counts=collections.Counter(str(r['node_id']) for r in records);by={str(r['node_id']):r for r in records};exclusions=[]
  missing=set(nodes)-set(docs)
  if missing=={pid} and pub.get('root_landing_unit'):
   landing=unit(pub['root_landing_unit'],pid,pub['job_id']);landing=landing['Docs'];d=landing[0] if len(landing)==1 else {}
   if str(d.get('Id'))==pid and d.get('DocType')==4 and not any(d.get(k) for k in ('Content','Title','Notes','Footnotes')) and toc['Data']['DocType']==0:exclusions=[pid];missing=set()
  if missing or set(docs)-set(nodes):errors.append({'product_id':pid,'kind':'raw-inventory-document-set','missing':sorted(missing),'extra':sorted(set(docs)-set(nodes))})
  if set(by)!=set(docs) or any(n!=1 for n in counts.values()):errors.append({'product_id':pid,'kind':'source-document-record-set','missing':sorted(set(docs)-set(by)),'extra':sorted(set(by)-set(docs)),'duplicates':[i for i,n in counts.items() if n!=1]})
  for ident,doc in docs.items():
   record=by.get(ident)
   if not record:continue
   expected={'product_id':int(pid),'job_id':pub['job_id'],'parent_id':nodes[ident]['ParentId'],'path':paths[ident],'toc_heading':nodes[ident]['Heading'],'body_sha256':sha((doc.get('Content') or '').encode()),'doc_type':doc['DocType']}
   for key,value in expected.items():
    if record.get(key)!=value:errors.append({'product_id':pid,'id':ident,'field':key,'kind':'raw-record-binding'})
  ends=pub['end_units'];end_toc=unit(ends['toc'],pid,pub['job_id'])
  closing_toc_equal=toc==end_toc
  if not closing_toc_equal:errors.append({'product_id':pid,'kind':'opening-closing-TOC-drift'})
  reports.append({'product_id':pid,'job_id':pub['job_id'],'raw_toc_nodes':len(nodes),'raw_source_docs':len(docs),'normalized_records':len(records),'explicit_empty_root_exclusions':exclusions,'closing_TOC_equal':closing_toc_equal,'records_sha256':sha(raw)})
 return {'schema_version':1,'kind':'independent-raw-TOC-Docs-record-identity-and-ownership','network_requests_sent':0,'read_only':True,'checkpoint_sha256':sha((root/'checkpoint.json').read_bytes()),'publications':reports,'sources':sources,'passed':not errors,'errors':errors,'scope_note':'Exact source-ID/body-hash/TOC parent/path and opening-closing TOC bindings only. Does not prove legal text/list/table reading-order equivalence or every required external publication.'}
def main():
 p=argparse.ArgumentParser();p.add_argument('run',type=Path);a=p.parse_args();r=audit(a.run);print(json.dumps(r,indent=2));return 0 if r['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
