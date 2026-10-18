#!/usr/bin/env python3
"""Current candidate against exact retained legal bodies; no network/decode/pixels."""
import argparse,base64,collections,hashlib,json,pathlib,sys,time
from unittest.mock import patch
p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path,required=True);p.add_argument('--run',type=pathlib.Path,action='append',required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();sys.path.insert(0,str(a.candidate));import collect,model
if a.out.exists():raise ValueError('Fresh output required')
reports=[]
with patch.object(base64,'b64decode',side_effect=AssertionError('Forbidden inline decoder'))as decoder:
 for run in a.run:
  state=collect.load(run/'checkpoint.json');c=collect.load(run/'config.json');counts=collections.Counter();changed=[];witnesses=[];mismatches=[]
  for i in state['items']:
   if i['kind']!='html':continue
   raw=(run/i['raw_ref']).read_bytes();old=collect.load(run/'items'/(model.sha(i['id'].encode())[:24]+'.json'));new,dispositions=collect.parse_item(raw,i,c);witnesses.append({'id':i['id'],'source_sha256':model.sha(raw),'prior_item_sha256':model.sha((run/'items'/(model.sha(i['id'].encode())[:24]+'.json')).read_bytes())});counts['documents']+=1;counts['records']+=len(new)
   if len(old['records'])!=len(new):mismatches.append({'id':i['id'],'kind':'record_count'});continue
   for before,after in zip(old['records'],new):
    delta=[k for k in sorted(set(before)|set(after))if before.get(k)!=after.get(k)]
    for k in delta:counts['changed_'+k]+=1
    if delta:changed.append({'record_id':after['id'],'changed_fields':delta})
    unknown=set(delta)-{'assets','document_assets','links'}
    if unknown:mismatches.append({'id':after['id'],'unexpected_fields':sorted(unknown)})
   if old['dispositions']!=dispositions:mismatches.append({'id':i['id'],'kind':'dispositions'})
  reports.append({'publication_id':c['id'],'executed_prior_model_sha256':state['scripts']['model.py'],'counts':dict(counts),'changed_records':changed,'unexpected_changes':mismatches,'source_witnesses':witnesses})
 decoder.assert_not_called()
report={'schema':1,'kind':'candidate_retained_source_applicability','candidate_model_sha256':model.sha((a.candidate/'model.py').read_bytes()),'candidate_collect_sha256':model.sha((a.candidate/'collect.py').read_bytes()),'network_requests':0,'inline_decoder_calls':0,'pixel_operations':0,'runs':reports,'pass':not any(r['unexpected_changes']for r in reports),'scope':'Exact complete retained initial legal body set compared against the72-test producer. Only asset/link reference metadata expected to differ; not fresh source acquisition or new PDF replay.'};a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'pass':report['pass'],'runs':[{'id':r['publication_id'],'counts':r['counts'],'unexpected':len(r['unexpected_changes'])}for r in reports]},indent=2))
