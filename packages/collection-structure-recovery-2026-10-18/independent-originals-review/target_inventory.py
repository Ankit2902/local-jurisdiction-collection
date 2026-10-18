"""Independent original legal-container target IDs/names to normalized ownership.
No collector/model imports, image processing, browser attachment or network.
"""
import json,hashlib,collections,sys
from pathlib import Path
from urllib.parse import urlsplit,unquote
from bs4 import BeautifulSoup
base,out=map(Path,sys.argv[1:]);run=base/'note-resume-candidate-v6/collection';state=json.loads((run/'source/checkpoint.json').read_text());records=[json.loads(x) for x in (run/'normalized/records.jsonl').read_text().split('\n') if x];bydoc=collections.defaultdict(list)
def key(u):return urlsplit(u)._replace(fragment='').geturl()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for r in records:bydoc[key(r['source_url'])].append(r)
docs=[];errors=[];source_values={};normalized_values={};source_owners={};all_groups=[]
for artifact in state['artifacts']:
 if artifact['role']!='content':continue
 path=run/'source'/artifact['path'];assert sha(path)==artifact['sha256'];url=artifact['source_url'];s=BeautifulSoup(path.read_bytes(),'html.parser');root=s.select_one('#mainContent');expected=collections.Counter();actual=collections.Counter();norm_owners=collections.defaultdict(set)
 for el in root.find_all(True):
  for field in ['id','name']:
   if el.get(field):expected[(field,str(el[field]))]+=1
 for r in bydoc[url]:
  tree=BeautifulSoup(r['semantic_html'],'html.parser')
  for el in tree.find_all(True):
   for field in ['id','name']:
    if el.get(field):actual[(field,str(el[field]))]+=1;norm_owners[str(el[field])].add(r['record_id'])
 missing=expected-actual;extra=actual-expected
 if missing or extra:errors.append({'source_url':url,'missing':[{'attribute':a,'value':v,'count':count} for (a,v),count in missing.items()],'extra':[{'attribute':a,'value':v,'count':count} for (a,v),count in extra.items()]})
 source_values[url]={v for (_,v) in expected};normalized_values[url]={v for (_,v) in actual};source_owners[url]=norm_owners
 groups=root.select('div.Bulleted_outer,div.P2_outer');nested=[]
 for group in groups:
  parents=[p for p in group.parents if getattr(p,'name',None)=='div' and set(p.get('class',[]))&{'Bulleted_outer','P2_outer'}]
  if parents:nested.append({'classes':group.get('class',[]),'id':group.get('id'),'ancestor_classes':[p.get('class',[]) for p in parents]})
 all_groups.extend([{'source_url':url,'classes':g.get('class',[]),'id':g.get('id')} for g in groups]);docs.append({'source_url':url,'raw_sha256':artifact['sha256'],'source_targets':sum(expected.values()),'normalized_targets':sum(actual.values()),'exact_attribute_value_occurrence_match':not missing and not extra,'source_list_groups':len(groups),'nested_source_groups':nested})
linked=[]
for r in records:
 for link in r['links']:
  u=link['url'];target=key(u);fragment=unquote(urlsplit(u).fragment)
  if target not in source_values or not fragment:continue
  linked.append({'owner_record_id':r['record_id'],'url':u,'in_original_legal_container':fragment in source_values[target],'in_normalized_legal_records':fragment in normalized_values[target],'normalized_owner_ids':sorted(source_owners[target].get(fragment,set()))})
report={'schema_version':1,'kind':'independent-all-actual-legal-target-ID-name-retention-and-owner-inventory','passed':not errors,'source_documents':len(docs),'records':len(records),'records_sha256':sha(run/'normalized/records.jsonl'),'source_checkpoint_sha256':sha(run/'source/checkpoint.json'),'source_target_occurrences':sum(d['source_targets'] for d in docs),'normalized_target_occurrences':sum(d['normalized_targets'] for d in docs),'errors':errors,'document_results':docs,'actual_source_list_groups':all_groups,'actual_nested_list_group_count':sum(len(d['nested_source_groups']) for d in docs),'referenced_fragment_occurrences':len(linked),'original_legal_target_missing_links':[x for x in linked if not x['in_original_legal_container']],'source_present_but_normalized_missing_links':[x for x in linked if x['in_original_legal_container'] and not x['in_normalized_legal_records']],'ambiguous_normalized_target_links':[x for x in linked if len(x['normalized_owner_ids'])>1],'network_requests':0,'no_image_download_decode_render_extract_OCR':True,'auditor_sha256':sha(Path(__file__))}
(out/'target-ID-retention.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['document_results','actual_source_list_groups','original_legal_target_missing_links','ambiguous_normalized_target_links']}));sys.exit(0 if report['passed'] else 2)
