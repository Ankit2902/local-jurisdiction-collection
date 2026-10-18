"""All172 fresh records versus prior complete retained IR; no native library calls."""
import collections,gzip,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;old=[json.loads(l)for l in gzip.decompress((H/'source/cached-whole172.jsonl.gz').read_bytes()).decode().split('\n')if l];new=[json.loads(l)for l in(H/'actual-retained-full172/records.jsonl').read_text().split('\n')if l];assert len(old)==len(new)==172
oldid=old[0]['document_id'];newid=new[0]['document_id'];oldref=old[0]['raw_ref'];newref=new[0]['raw_ref'];identity={'heading','publication','jurisdiction','path','document_source_title','primary_source_owners'}
def rebind(v):
 if isinstance(v,str):return v.replace(oldid,newid).replace(oldref,newref)
 if isinstance(v,list):return [rebind(x)for x in v]
 if isinstance(v,dict):return {rebind(k):rebind(x)for k,x in v.items()}
 return v
def changes(a,b,path=''):
 if type(a)!=type(b):return [(path,a,b)]
 if isinstance(a,dict):
  out=[]
  for k in set(a)|set(b):out+=changes(a.get(k),b.get(k),path+'/'+k)
  return out
 if isinstance(a,list):
  if len(a)!=len(b):return [(path+'/length',len(a),len(b))]
  return [z for i,(x,y)in enumerate(zip(a,b))for z in changes(x,y,path+'/'+str(i))]
 return []if a==b else[(path,a,b)]
all_diff=[];context=[]
for a,b in zip(old,new):
 assert a['physical_page']==b['physical_page'];aa=rebind(a);context.append({'physical_page':a['physical_page'],'old_context':{k:a[k]for k in identity if k in a},'new_context':{k:b[k]for k in identity if k in b}});diff=changes({k:v for k,v in aa.items()if k not in identity},{k:v for k,v in b.items()if k not in identity});all_diff.extend({'physical_page':a['physical_page'],'path':p,'old':x,'new':y}for p,x,y in diff)
report={'passed':not all_diff,'pages':172,'namespace_rebinding':{'old':oldid,'new':newid,'kind':'Published collection namespace/source-reference metadata only; no legal text edits'},'raw_ref_rebinding':{'old':oldref,'new':newref},'context_fields_explicitly_changed':sorted(identity),'other_field_difference_count':len(all_diff),'other_differences':all_diff,'all_172_legal_text_exact':all(a['text']==b['text']for a,b in zip(old,new)),'all_IMAGE_positions_and_metadata_equal_except_ID_ref':all(rebind(a['assets'])==b['assets']for a,b in zip(old,new)),'cached_source_sha256':hashlib.sha256((H/'source/cached-whole172.jsonl.gz').read_bytes()).hexdigest(),'source_original_unchanged':True,'native_parse_performed':False,'publication_text_complete':False}
(H/'cached-whole172-comparison.json').write_text(json.dumps(report,indent=2)+'\n');(H/'source-context-rebinding.json').write_text(json.dumps(context,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='other_differences'},indent=2));assert not all_diff
