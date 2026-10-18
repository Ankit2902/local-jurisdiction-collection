"""Source-owned selected native PDF attachment outputs; no acquisition or pixels."""
import csv,hashlib,json,pathlib
from urllib.parse import urldefrag
import model,native_labels

def source_inputs(out,c,state):
 out=pathlib.Path(out);rules={r['url']:r for r in c.get('native_label_attachment_rules',[])}
 if len(rules)!=len(c.get('native_label_attachment_rules',[])):raise ValueError('Duplicate native attachment selection rules')
 owners={url:[]for url in rules};downloads={}
 for item in state['items']:
  path=out/'items'/(model.sha(item['id'].encode())[:24]+'.json')
  if not path.exists():continue
  document=json.loads(path.read_text())
  if document['item']!=item or model.sha((out/item['raw_ref']).read_bytes())!=document['raw_sha256']:raise ValueError('Native attachment owner document/raw identity mismatch')
  for asset in document.get('asset_downloads',[]):
   if asset.get('status')!='acquired':continue
   url=urldefrag(asset['url'])[0]
   if url not in rules:continue
   previous=downloads.get(url)
   if previous and previous['sha256']!=asset['sha256']:raise ValueError('Same native attachment URL has conflicting acquired source bytes')
   downloads[url]=asset
  for record in document['records']:
   for asset in record.get('assets',[])+record.get('document_assets',[]):
    url=urldefrag(asset['url'])[0]
    if url not in rules or not asset.get('required') or model.image_asset(asset):continue
    if record.get('document_id')!=item['id'] or record.get('raw_sha256')!=document['raw_sha256']:raise ValueError('Native attachment owner record/source binding mismatch')
    owner={'owner_record_id':record['id'],'owner_document_id':record['document_id'],'owner_source_sha256':record['raw_sha256'],'reference_url':asset['url']}
    for key in ['source_id','source_attribute']:
     if key in asset:owner[key]=asset[key]
    if owner not in owners[url]:owners[url].append(owner)
 return rules,owners,downloads

def expected(out,c,state):
 out=pathlib.Path(out);rules,owners,downloads=source_inputs(out,c,state);artifacts=[]
 for url,rule in rules.items():
  summary={'source_url':url,'source_rule':rule,'required_by':owners[url]}
  if not owners[url] or url not in downloads:
   artifacts.append({'summary':dict(summary,status='missing_source_owned_reference'if not owners[url]else'missing_native_source_acquisition'),'records':[]});continue
  asset=downloads[url];ref='raw/'+model.sha(('asset:'+asset['url']).encode())[:20]+'.bin'
  if ref!=asset['raw_ref']:raise ValueError('Native attachment acquired raw reference crosswire')
  data=(out/ref).read_bytes();receipt=json.loads((out/ref).with_suffix('.receipt.json').read_text())
  if model.sha(data)!=asset['sha256']or receipt['sha256']!=asset['sha256']or receipt['url']!=asset['url']or receipt.get('request_name')!='asset:'+asset['url']or not receipt.get('success',receipt.get('status')==200)or receipt.get('access_stop'):raise ValueError('Native attachment receipt/raw URL/hash mismatch')
  item={'id':'attachment:'+url,'url':url,'heading':rule.get('title',url),'kind':'pdf','raw_ref':ref}
  rows,q=native_labels.project(data,item,c,required_by=owners[url]);artifact='native-attachments/'+model.sha(url.encode())[:24]+'.json'
  artifacts.append({'summary':dict(summary,status='normalized',artifact=artifact,raw_ref=ref,source_sha256=asset['sha256'],qualification=q),'records':rows})
 return artifacts

def jsonl(records):return b''.join(model.encoded(r)+b'\n'for r in records)
def write(out,c,state):
 if not c.get('native_label_attachment_rules'):return
 import transport
 out=pathlib.Path(out);artifacts=expected(out,c,state)if state.get('completed')else[];records=[]
 for artifact in artifacts:
  records+=artifact['records']
  if artifact['summary'].get('artifact'):transport.atomic(out/artifact['summary']['artifact'],model.encoded(artifact)+b'\n')
 transport.atomic(out/'attachment-pages.jsonl',jsonl(records))
 with(out/'attachment-pages.csv').open('w',newline='')as f:
  writer=csv.DictWriter(f,fieldnames=['id','document_id','heading','source_url','physical_page','page_count','text','raw_ref','raw_sha256'],extrasaction='ignore');writer.writeheader();writer.writerows(records)

def validate(out,c,state):
 if not c.get('native_label_attachment_rules')or not state.get('completed'):return
 out=pathlib.Path(out);records=[]
 for artifact in expected(out,c,state):
  records+=artifact['records'];ref=artifact['summary'].get('artifact')
  if ref and(out/ref).read_bytes()!=model.encoded(artifact)+b'\n':raise ValueError('Native attachment normalized records/qualification differ from actual source')
 if(out/'attachment-pages.jsonl').read_bytes()!=jsonl(records):raise ValueError('Native attachment page output missing/duplicated/corrupt')
 with(out/'attachment-pages.csv').open(newline='')as f:
  csv.field_size_limit(32_000_000);rows=list(csv.DictReader(f))
 if len(rows)!=len(records)or any(a['id']!=b['id']or a['text']!=b['text']for a,b in zip(rows,records)):raise ValueError('Native attachment CSV/JSONL mismatch')

def summaries(out,c,state):
 if not c.get('native_label_attachment_rules'):return []
 out=pathlib.Path(out);rules,owners,downloads=source_inputs(out,c,state);summaries=[]
 for url,rule in rules.items():
  ref='native-attachments/'+model.sha(url.encode())[:24]+'.json';path=out/ref
  if path.exists():summaries.append(json.loads(path.read_text())['summary'])
  else:summaries.append({'source_url':url,'source_rule':rule,'required_by':owners[url],'status':'missing_normalized_output'})
 return summaries
