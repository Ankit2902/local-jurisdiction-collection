#!/usr/bin/env python3
"""Read-only, independent full-body comparison of native HTML against publisher renderer raw responses."""
import argparse,json,re,sys
sys.dont_write_bytecode=True
from urllib.parse import quote
from pathlib import Path
from model import *
from verify import Files,verify

def norm(v):return re.sub(r'\s+','',v).casefold()
def comparisons(native,reference):
 left={r['document_id']:r for r in native};right={r['document_id']:r for r in reference};assert len(left)==len(native) and len(right)==len(reference)
 rows=[]
 for did in sorted(set(left)|set(right)):
  a=left.get(did);b=right.get(did);checks={'both_present':bool(a and b)}
  if a and b:
   checks.update(full_body_equal=norm(a['text'])==norm(b['text']),source_block_ids_equal=a['body_block_ids']==b['body_block_ids'],table_cells_and_spans_equal=[[[(norm(c['text']),c['rowspan'],c['colspan']) for c in row] for row in t] for t in a['tables']]==[[[(norm(c['text']),c['rowspan'],c['colspan']) for c in row] for row in t] for t in b['tables']])
  rows.append({'document_id':did,'checks':checks,'passed':all(checks.values())})
 return rows

def compare(native_path,render_path):
 report=verify(native_path);nf=Files(native_path);rf=Files(render_path);nm=nf.json('run.json');rm=rf.json('run.json');requests=rf.json('requests.json');assert rm['status']=='acquired' and rm['max_items'] is None and rm['strategy']=='traverse','Reference must be a full unbounded renderer capture'
 def data(key):
  e=requests[key];b=rf.read(e['file']);assert digest(b)==e['sha256'];return b
 raw=data('overview-start');identity,code,_=select(raw,rm['source_url'],rm['expected_jurisdiction'],rm['expected_state'],rm.get('publication_selector'),rm.get('identity_aliases',[]));assert identity==nm['identity'],'Reference edition/publication differs'
 def toc(url):
  internal=url.rstrip('/').split('/')[-1];entries=[(k,e) for k,e in requests.items() if k.startswith('start:toc:') and e['requested_url']==url];assert len(entries)==1,'Independent reference branch missing/duplicate';return data(entries[0][0])
 inv=inventory_from_sources(identity,code,toc);reference=[]
 for item in inv['nodes']:
  if item.get('passthru_doc_id'):
   e=requests['start:toc:'+item['document_id']];reference.append(passthrough_record(item,inv,identity,{'url':e['requested_url'],'sha256':e['sha256']}));continue
  url=f"https://codelibrary.amlegal.com/api/render-section/{identity['client_slug']}/{identity['version_uuid']}/{identity['code_slug']}/{quote(item['orig_doc_id'],safe='')}/{item['orig_doc_idx']}/";key='fetch:'+url;payload=data(key);reference.append(html_record(json.loads(payload),item,identity,url,requests[key]['sha256']))
 native=[json.loads(v) for v in nf.read('sections.jsonl').splitlines()];rows=comparisons(native,reference)
 return {'schema_version':1,'comparison':'Complete normalized bodies and raw source block IDs/table cells/spans; all independently inventoried nodes','source_identity':identity,'independent_inventory_count':len(inv['nodes']),'native_record_count':len(native),'matched_records':sum(r['passed'] for r in rows),'checks':rows,'passed':bool(rows) and all(r['passed'] for r in rows),'reference_mode':'Retained raw renderer responses recomputed; old normalized outputs/success flags not trusted','image_policy':IMAGE_POLICY}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('native_run',type=Path);p.add_argument('renderer_reference',type=Path);a=p.parse_args()
 try:r=compare(a.native_run,a.renderer_reference);print(json.dumps(r,indent=2));sys.exit(0 if r['passed'] else 2)
 except Exception as e:print(json.dumps({'passed':False,'error':str(e)}));sys.exit(1)
