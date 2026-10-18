"""Full raw Flagstaff HTML replay: every source document/block and TOC edge reconciled."""
import argparse,csv,json,re,sys,collections
from pathlib import Path
from urllib.parse import urlsplit,urljoin
from bs4 import BeautifulSoup
from source_common import *
from publication_source_verify import validate as validate_source
from king_normalize import blocks
from flagstaff_html import inventory,currency,URL
from flagstaff_root import root_inventory,ROOT_TOC_URL
from flagstaff_normalize import labelkey
from model import semantics,image_asset,redact_image_metadata,dom_text,sanitize_images

def independent_reference(a,rules):
 return [rule for rule in rules if a['kind']=='a' and a['source_attribute']=='href' and re.fullmatch(rule['url_regex'],a['url']) and re.search(rule['context_regex'],a.get('context',''),re.I)]

def parse(raw,url,expected):
 text,encoding=decode(raw);s=BeautifulSoup(text,'html.parser');root=s.select_one('#mainContent')
 if root is None:raise ValueError('Unprofiled legal HTML source container '+url)
 units=list(blocks(root));records=[];heads=[];current=None;html_parts={}
 for i,b in enumerate(units):
  label=dom_text(b);classes=b.get('class',[]);is_division=b.name=='p' and 'Division' in classes;ishead=is_division or b.name in ['h1','h2','h3','h4','h5','h6']
  if ishead and not label and classes==['Caption'] and not b.find(['img','svg','picture','object','table']) and not b.get('id') and not b.find(attrs={'name':True}):ishead=False
  if ishead or current is None:
   current={'record_id':sha((url+'::block-'+str(i)).encode()),'jurisdiction':'Flagstaff, AZ','publication':'City Code including Charter','source_url':url,'source_sha256':sha(raw),'source_heading_classes':classes,'kind':'section' if ishead and b.name in ['h3','h4','h5','h6'] and 'Caption' not in classes else 'container' if ishead else 'source_introduction','heading':label if ishead else 'Source introduction','source_heading_level':b.name if ishead else None,'source_heading_ids':[x.get('id') or x.get('name') for x in [b]+b.select('[id],[name]') if x.get('id') or x.get('name')],'block_indices':[],'semantic_html':'','full_text':'','tables':[],'notes':[],'assets':[],'links':[],'image_placeholder_count':0};records.append(current)
   if ishead:heads.append(current)
  m=semantics(b,url);html_parts[i]=m['html'];current['block_indices'].append(i);current['semantic_html']+=m['html'];current['full_text']=clean(current['full_text']+' '+m['text']);current['tables'].extend(m['tables']);current['notes'].extend(m['notes']);current['assets'].extend(m['assets']);current['links'].extend(m['links']);current['image_placeholder_count']+=m['image_placeholder_count']
 # Source explicitly groups bullet marker and legal text in these list containers.
 # Keep every existing leaf ownership index and its text/table metadata, adding the
 # original sanitized wrapper only to HTML rendering; never duplicate child HTML.
 overrides={};suppressed=set();prior_groups=[]
 for ordinal,group in enumerate(root.select('div.Bulleted_outer,div.P2_outer')):
  indices=[i for i,unit in enumerate(units) if any(ancestor is group for ancestor in unit.parents)]
  owners=[record for record in records if any(i in record['block_indices'] for i in indices)]
  if not indices or indices!=list(range(indices[0],indices[-1]+1)) or len(owners)!=1:raise ValueError('Unqualified source list group ownership shape')
  expected_group_text=clean(' '.join(dom_text(units[i]) for i in indices))
  if dom_text(group)!=expected_group_text:raise ValueError('Source list group contains unowned legal content')
  parent=None
  for prior in prior_groups:
   if set(indices).intersection(prior['indices']):
    if not set(indices).issubset(prior['indices']) or not any(ancestor is prior['node'] for ancestor in group.parents) or owners[0] is not prior['owner']:raise ValueError('Unqualified crossing or ambiguous source list group ownership; preserve raw source and require review')
    parent=prior
  metadata={'source_group_id':sha((url+'::list-group-'+str(ordinal)).encode()),'source_tag':group.name,'source_classes':group.get('class',[]),'child_block_indices':indices,'source_group_sha256':sha(str(group).encode())}
  if parent is not None:metadata['parent_source_group_id']=parent['metadata']['source_group_id']
  else:
   overrides[indices[0]]=str(sanitize_images(group));suppressed.update(indices[1:])
  owners[0].setdefault('source_list_groups',[]).append(metadata)
  prior_groups.append({'node':group,'indices':set(indices),'owner':owners[0],'metadata':metadata})
 for record in records:record['semantic_html']=''.join(overrides.get(i,html_parts[i]) for i in record['block_indices'] if i not in suppressed)
 available=list(heads);mapping=[];missing=[]
 # DOM order disambiguates genuine repeated Charter IDs within separate articles.
 # Every edge retains its own composite root/order identity; bodies are acquired once/document.
 last=-1
 for edge in expected:
  matches=[h for h in available if labelkey(h['heading'])==labelkey(edge['label'])]
  if not matches:
   fragment=urlsplit(edge['source_url']).fragment
   matches=[h for h in available if fragment and fragment in h['source_heading_ids']]
  if matches:
   h=matches[0];available.remove(h);h.setdefault('source_toc_edges',[]).append(edge['edge_id']);h['source_url']=edge['source_url'];mapping.append({'edge_id':edge['edge_id'],'record_id':h['record_id'],'source_heading':edge['label'],'body_heading':h['heading'],'resolution':'source_heading_label_and_document_order' if labelkey(h['heading'])==labelkey(edge['label']) else 'source_fragment_and_document_order'})
  else:missing.append(edge)
 heading_only=[]
 for pos,r in enumerate(records):
  r['source_child_section_ids']=[]
  for child in records[pos+1:]:
   parent_ids=[x for x in r['source_heading_ids'] if re.fullmatch(r'\d+(?:\.\d+)+',x)]
   if not parent_ids or not any(cid.startswith(pid+'.') for pid in parent_ids for cid in child['source_heading_ids']):break
   r['source_child_section_ids'].append(child['record_id'])
 for r in records:
  if r['kind']=='section':
   rest=r['full_text'][len(r['heading']):].strip() if r['full_text'].startswith(r['heading']) else r['full_text']
   r['body_qualification']='source_body' if rest else 'explicit_reserved_or_repealed' if re.search(r'\b(reserved|repealed|omitted)\b',r['heading'],re.I) else 'unresolved_heading_only'
   if r['body_qualification']=='unresolved_heading_only' and r['source_child_section_ids']:r['body_qualification']='source_structural_parent_with_published_children'
   if r['body_qualification']=='unresolved_heading_only':heading_only.append(r['record_id'])
 return records,{'url':url,'encoding':encoding,'source_blocks':len(units),'owned_blocks':sum(len(r['block_indices']) for r in records),'unique_owned_blocks':len({i for r in records for i in r['block_indices']}),'source_tables':len(root.find_all('table')),'owned_tables':sum(len(r['tables']) for r in records),'source_toc_edges':len(expected),'matched_toc_edges':len(mapping),'mapping':mapping,'missing_toc_edges':missing,'extra_body_headings':[{'record_id':r['record_id'],'heading':r['heading']} for r in available if r['kind']=='section'],'source_body_only_containers':[{'record_id':r['record_id'],'heading':r['heading'],'source_classes':r['source_heading_classes']} for r in available if r['kind']!='section'],'source_structural_parents':sum(r.get('body_qualification')=='source_structural_parent_with_published_children' for r in records),'heading_only_unresolved':heading_only,'image_placeholders':sum(r['image_placeholder_count'] for r in records)}

CODEFILES=['flagstaff_html_normalize.py', 'flagstaff_html.py', 'flagstaff_inventory.py', 'flagstaff_root.py', 'flagstaff_root_guard.py', 'flagstaff_normalize.py', 'king_normalize.py', 'source_common.py', 'shared_transport.py', 'model.py', 'legacy_html.py', 'browser_safety.py', 'configs.json', 'king_acquire.py', 'source_dispositions.json','publication_source_verify.py','character_recovery.py','source_character_dispositions.json']

def run(source,out):
 validate_source('flagstaff-html',source)
 src=Path(source).resolve();out=Path(out).resolve();reference_rules=load(Path(__file__).parent/'configs.json')['targets']['original-flagstaff-az']['independent_reference_rules']
 if out.exists() and any(out.iterdir()):raise ValueError('Fresh output required')
 out.mkdir(parents=True,exist_ok=True);code=normalization_snapshot(out,CODEFILES);state=load(src/'checkpoint.json');errors=[]
 if state.get('source_url')!=URL:raise ValueError('Wrong source publication identity')
 for a in state['artifacts']:
  if sha((src/a['path']).read_bytes())!=a['sha256']:raise ValueError('Corrupt retained source '+a['path'])
  if a['status']!=200 or a['source_url']!=a['final_url']:raise ValueError('Unqualified response source identity')
 def readers(role):
  found=[]
  for r in state['observed_readers']:
   aa=[a for a in state['artifacts'] if a['role']==role and a['source_url']==r['url']]
   if len(aa)!=1:raise ValueError('Missing/duplicate opening/closing native TOC '+r['url'])
   found.append(dict(r,raw=decode((src/aa[0]['path']).read_bytes())[0]))
  return found
 opening=inventory(readers('toc-start'));closing=inventory(readers('toc-end'))
 expected_roots=[r['root'] for r in state['observed_readers']];root_sets=[]
 for role in ['root-toc-start','root-toc-end']:
  aa=[a for a in state['artifacts'] if a['role']==role and a['source_url']==ROOT_TOC_URL]
  if len(aa)!=1:errors.append('Missing/duplicate whole-publication root inventory '+role);root_sets.append(None)
  else:root_sets.append(root_inventory((src/aa[0]['path']).read_bytes()))
 if root_sets!=[expected_roots,expected_roots]:errors.append('Whole-publication primary roots drift/mismatch')
 if state.get('root_finalization'):
  phase=state['root_finalization'];proof_path=src/phase['receipt_path']
  if sha(proof_path.read_bytes())!=phase['receipt_sha256'] or sha((src/'checkpoint-before-root-finalization.json').read_bytes())!=phase['source_checkpoint_before_sha256']:raise ValueError('Corrupt explicit finalization provenance')
  old=load(src/'checkpoint-before-root-finalization.json')
  if state['artifacts'][:len(old['artifacts'])]!=old['artifacts']:raise ValueError('Original body/reader source ledger changed during finalization')
  proof=load(proof_path)
  if proof['source_checkpoint_before_sha256']!=phase['source_checkpoint_before_sha256'] or proof['blocked'] or proof['errors']:errors.append('Finalization proof incomplete/unbound')
  aa=[a for a in state['artifacts'] if a['role']=='currency-root-guard-end']
  if len(aa)!=1 or currency((src/aa[0]['path']).read_bytes())!=state['opening_currency']:errors.append('Finalization currency mismatch')

 if opening!=closing or opening!=state['inventory']:errors.append('Opening/closing/source graph drift')
 currencies=[]
 for role in ['currency-start','currency-end']:
  aa=[a for a in state['artifacts'] if a['role']==role]
  if len(aa)!=1:errors.append('Missing/duplicate source currency '+role);currencies.append(None)
  else:currencies.append(currency((src/aa[0]['path']).read_bytes()))
 if currencies[0]!=currencies[1]:errors.append('Opening/closing currency drift')
 docs=list(dict.fromkeys(key(e['source_url']) for e in opening));records=[];audits=[];dependencies=[]
 for u in docs:
  aa=[a for a in state['artifacts'] if a['role']=='content' and a['source_url']==u]
  if len(aa)!=1:errors.append('Missing/duplicate source document '+u);continue
  rr,audit=parse((src/aa[0]['path']).read_bytes(),u,[e for e in opening if key(e['source_url'])==u]);records.extend(rr);audits.append(audit)
  for name in ['missing_toc_edges','extra_body_headings','heading_only_unresolved']:
   if audit[name]:errors.append(name+' '+u)
  if audit['source_tables']!=audit['owned_tables'] or audit['source_blocks']!=audit['unique_owned_blocks']:errors.append('Table/block ownership mismatch '+u)
  for r in rr:
   for a in r['assets']:
    a=dict(a,owner_record_id=r['record_id'])
    if image_asset(a):a.update(required=False,status='policy_omitted_image')
    elif key(a['url']) in docs:a.update(required=False,status='retained_primary_document')
    elif a.get('status') not in ['retained_inline','retained_inline_reference']:
     rules=independent_reference(a,reference_rules)
     if len(rules)==1:a.update(required=False,status='independent_legal_layer_reference',boundary_reason=rules[0]['reason'])
     else:a.update(required=True,status='unresolved_nonimage_attachment')
    dependencies.append(a)
   if re.search(r'data:image/|<(?:img|svg|picture)\b|background\s*=',r['semantic_html'],re.I):errors.append('Active normalized image markup')
 source_targets={}
 for document in docs:
  artifact=next(a for a in state['artifacts'] if a['role']=='content' and a['source_url']==document)
  body=BeautifulSoup(decode((src/artifact['path']).read_bytes())[0],'html.parser')
  source_targets[document]={str(node[field]) for node in body.find_all(True) for field in ['id','name'] if node.get(field)}
 source_link_defects=[]
 from urllib.parse import unquote
 for record in records:
  for link in record['links']:
   destination=key(link['url']);fragment=unquote(urlsplit(link['url']).fragment)
   if destination in source_targets and fragment and fragment not in source_targets[destination]:source_link_defects.append({'owner_record_id':record['record_id'],'url':link['url'],'source_issue':'publisher_missing_anchor','correction_applied':False})
 if source_link_defects:errors.append('Publisher source contains absent primary cross-reference targets')
 save(out/'source-link-defects.json',source_link_defects)
 unresolved=[a for a in dependencies if a.get('required') and a.get('status')=='unresolved_nonimage_attachment']
 if unresolved:errors.append('Unresolved required nonimage dependencies')
 verify_normalization_revision(code)
 transport.atomic(out/'records.jsonl',b''.join(canon(redact_image_metadata(r))+b'\n' for r in records))
 with (out/'records.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['record_id','source_url','kind','heading','full_text']);w.writeheader();w.writerows({k:r[k] for k in w.fieldnames} for r in records)
 save(out/'document-audits.json',audits);save(out/'dependencies.json',dependencies);save(out/'source-inventory.json',opening)
 summary={'schema':'flagstaff-full-html-normalized-1','source':str(src),'complete':not errors and not state['errors'] and not state['blocked'],'whole_jurisdiction_complete':False,'publication':'City Code including Charter; Employee Handbook separate and excluded','source_graph_edges':len(opening),'source_documents':len(docs),'acquired_parsed_documents':len(audits),'records':len(records),'source_blocks':sum(a['source_blocks'] for a in audits),'owned_blocks':sum(a['owned_blocks'] for a in audits),'source_tables':sum(a['source_tables'] for a in audits),'owned_tables':sum(a['owned_tables'] for a in audits),'matched_toc_edges':sum(a['matched_toc_edges'] for a in audits),'missing_toc_edges':sum(len(a['missing_toc_edges']) for a in audits),'extra_body_headings':sum(len(a['extra_body_headings']) for a in audits),'heading_only_unresolved':sum(len(a['heading_only_unresolved']) for a in audits),'image_placeholders':sum(a['image_placeholders'] for a in audits),'images_downloaded':False,'opening_closing_inventory_equal':opening==closing,'opening_closing_roots_equal':root_sets==[expected_roots,expected_roots],'opening_currency':currencies[0],'closing_currency':currencies[1],'independent_legal_layer_references':sum(a.get('status')=='independent_legal_layer_reference' for a in dependencies),'source_body_only_containers':sum(len(a['source_body_only_containers']) for a in audits),'source_structural_parents':sum(a['source_structural_parents'] for a in audits),'source_navigation_complete':not source_link_defects,'source_broken_link_occurrences':len(source_link_defects),'source_list_groups':sum(len(record.get('source_list_groups',[])) for record in records),'unresolved_nonimage_dependencies':len(unresolved),'errors':sorted(set(errors)),'code_fingerprint':code};save(out/'summary.json',summary);return summary
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args();r=run(a.source,a.out);print(json.dumps(r,indent=2));sys.exit(0 if r['complete'] else 2)
