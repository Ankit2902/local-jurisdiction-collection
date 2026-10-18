from pathlib import Path
import json,hashlib,collections,re
B=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00');O=Path(__file__).resolve().parent;old=json.loads((O/'census.json').read_text());roots=[B/r['root']for r in old['runs']];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
seen={};refs=[];samples=[];inline=[];tot=collections.Counter();witness={};sources={}
for root in roots:
 for receipt in sorted((root/'raw').glob('*.json')):
  try:r=json.loads(receipt.read_text())
  except (ValueError,UnicodeError):continue
  if 'body_file' not in r:continue
  headers={k.lower():v for k,v in r.get('headers',{}).items()};mime=headers.get('content-type','').lower()
  if 'json' not in mime:tot['non_json_receipts_skipped_without_reading_body']+=1;continue
  body=root/r['body_file'];bh=sha(body);assert bh==r['sha256'];witness[str(receipt.relative_to(B))]=sha(receipt);witness[str(body.relative_to(B))]=bh
  refs.append({'receipt':str(receipt.relative_to(B)),'body':str(body.relative_to(B)),'sha256':bh,'status':r.get('status'),'mime':mime});sources.setdefault(bh,refs[-1])
  if bh not in seen:
   try:seen[bh]=json.loads(body.read_bytes())
   except (ValueError,UnicodeError):tot['mislabelled_json']+=1;continue
for bh,value in seen.items():
 def walk(value,path):
  if isinstance(value,dict):
   if 'DocType' in value and 'Id' in value:
    tot['unique_response_doc_occurrences']+=1
    for k,v in value.items():
     if k.lower() in {'notes','footnotes'}:
      tot[k+'_schema_'+type(v).__name__]+=1
      if v:samples.append({'source':sources[bh],'locator':path,'doc_id':str(value['Id']),'doc_type':value['DocType'],'field':k,'value':v})
    content=value.get('Content')or''
    if isinstance(content,str) and len(inline)<12:
     pattern=re.compile(r"(?:Editor's|Editor’s|Codifier's|Codifier’s)\s+note|class=[\"'][^\"']*footnote|id=[\"'][^\"']*(?:footnote|foot--)",re.I)
     m=pattern.search(content)
     if m:inline.append({'source':sources[bh],'locator':path,'doc_id':str(value['Id']),'title':value.get('Title'),'field':'Content','source_content_sha256':hashlib.sha256(content.encode()).hexdigest(),'literal_match':m.group(),'source_character_range':[max(0,m.start()-120),min(len(content),m.end()+350)],'snippet':content[max(0,m.start()-120):m.end()+350]})
   for k,v in value.items():walk(v,path+'.'+k)
  elif isinstance(value,list):
   for i,v in enumerate(value):walk(v,path+'['+str(i)+']')
 walk(value,'$')
assert all(sha(B/n)==h for n,h in witness.items())
r={'source_files_unchanged':True,'publisher_requests':0,'image_api_calls':0,'scope':'All retained JSON-MIME response bodies (including noncommitted/landing responses) in the 18 actual run raw directories. Non-JSON body bytes are not opened. No source HTML parser or normalizer invoked.','run_roots':old['runs'],'response_references':refs,'unique_json_responses':len(seen),'totals':dict(tot),'populated_note_fields':samples,'inline_note_samples':inline,'source_manifest':witness};(O/'raw-response-census.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'unique_json_responses':len(seen),'response_receipts':len(refs),'totals':dict(tot),'populated_note_fields':len(samples),'inline_samples':len(inline)},indent=2))
