#!/usr/bin/env python3
"""Source-only inline URI/context inventory; no data decoding, network or pixels."""
import argparse,hashlib,json,pathlib,re,collections
from bs4 import BeautifulSoup

def scan(run):
 run=pathlib.Path(run);state=json.loads((run/'checkpoint.json').read_text());c=json.loads((run/'config.json').read_text());sources=[];entries=[];outside=0
 for item in state['items']:
  if item['kind']!='html':continue
  refs=[('initial',item['raw_ref'])]+[('closing',x['raw_ref'])for x in state.get('item_consistency',[])if x['kind']=='item'and x['id']==item['id']]
  for phase,ref in refs:
   raw=(run/ref).read_bytes();soup=BeautifulSoup(raw,'html.parser');node=soup.select_one(c['content_selector'])
   if node is None:raise ValueError('Exact selected legal container absent during source applicability scan')
   source={'phase':phase,'item_id':item['id'],'raw_ref':ref,'raw_sha256':hashlib.sha256(raw).hexdigest(),'selected_container':c['content_selector']};sources.append(source)
   for el in [node]+node.find_all(True):
    values=[(k,' '.join(v)if isinstance(v,list)else str(v))for k,v in el.attrs.items()]
    if el.name=='style':values.append(('style-text',el.get_text()))
    for attribute,value in values:
     for match in re.finditer('data:',value,re.I):
      fragment=value[match.start()+5:];header,sep,_=fragment.partition(',');declared=header.split(';',1)[0].strip().lower();declared=declared if re.fullmatch(r'[a-z0-9.+_-]+/[a-z0-9.+_-]+',declared)else'unrecognized/absent'
      image=el.name in ['img','picture','svg','image','use']or el.find_parent('picture')is not None or attribute in ['poster','background','srcset','style','style-text']or str(el.get('type','')).lower().startswith('image/')or el.name=='input'and str(el.get('type','')).lower()=='image'
      entries.append({**source,'tag':el.name,'attribute':attribute,'attribute_value_sha256':hashlib.sha256(value.encode()).hexdigest(),'declared_data_media_type':declared,'source_context_image':image,'comma_present':bool(sep),'characters':len(value)})
 return {'publication_id':c['id'],'run_path_provenance':str(run),'selected_legal_source_documents':len(sources),'html_item_count':sum(i['kind']=='html'for i in state['items']),'pdf_item_count':sum(i['kind']=='pdf'for i in state['items']),'counts':dict(collections.Counter((e['phase']+'|'+e['tag']+'|'+e['attribute']+'|'+e['declared_data_media_type'])for e in entries)),'entries':entries,'source_witnesses':sources,'source_code_snapshot_model_sha256':state['scripts']['model.py'],'scope':'All initial/closing selected HTML containers. PDF source_assets path is not used; PDF annotation normalization is a separate module. No inferred zero exposure.'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run',action='append',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args()
 if a.out.exists():raise ValueError('Fresh scan output required')
 report={'schema':1,'decoder_calls':0,'network_requests':0,'pixel_operations':0,'runs':[scan(run)for run in a.run]};a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps([{'id':r['publication_id'],'sources':r['selected_legal_source_documents'],'inline_occurrences':len(r['entries']),'counts':r['counts']}for r in report['runs']],indent=2))
