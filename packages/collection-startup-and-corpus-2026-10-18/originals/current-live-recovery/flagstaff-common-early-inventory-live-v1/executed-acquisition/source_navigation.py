"""Finite source-bound retained-target coverage, separate from literal browser fragment validity.
No acquisition, source rewriting, ID trimming or inferred missing legal sections.
"""
import collections,re
from urllib.parse import urljoin,urlsplit,unquote
from bs4 import BeautifulSoup
from source_common import sha,clean,decode,key
from model import dom_text,sanitize_images,table_data,normalized_links,source_notes,source_assets,image_asset

def assess(records,raw_documents,inventory,audits,dependencies,currency,rules,reference_rules,separate_prefixes,blocks):
 errors=[];asset_reference_complete=True;contexts={};owners={};primary_references=[];diagnostics=[];resolutions=[];unresolved=[];body_stats=[]
 bydoc=collections.defaultdict(list)
 for row in records:bydoc[key(row['source_url'])].append(row)
 if set(bydoc)!=set(raw_documents):errors.append('Primary document/record ownership inventory differs')
 if {key(e['source_url']) for e in inventory}!=set(raw_documents):errors.append('Primary native inventory/document acquisition differs')
 for url,raw in raw_documents.items():
  root=BeautifulSoup(decode(raw)[0],'html.parser').select_one('#mainContent')
  if root is None:errors.append('Primary legal source container absent '+url);continue
  units=list(blocks(root));rows=bydoc[url];indices=[i for row in rows for i in row['block_indices']]
  if sorted(indices)!=list(range(len(units))):errors.append('Primary source block missing/duplicate '+url)
  sourceids=collections.Counter((field,str(node[field])) for node in root.find_all(True) for field in ['id','name'] if node.get(field));normids=collections.Counter();idowners={'id':collections.defaultdict(set),'name':collections.defaultdict(set)}
  for row in rows:
   if row.get('source_sha256')!=sha(raw):errors.append('Primary record source hash differs '+row['record_id'])
   if any(i<0 or i>=len(units) for i in row['block_indices']):errors.append('Primary record source index outside document');continue
   expectedtext=clean(' '.join(dom_text(sanitize_images(units[i])) for i in row['block_indices']))
   if row['full_text']!=expectedtext:errors.append('Primary source text conservation differs '+row['record_id'])
   semantic=BeautifulSoup(row['semantic_html'],'html.parser')
   if dom_text(semantic)!=row['full_text']:errors.append('Primary rendered HTML/text conservation differs '+row['record_id'])
   expectedtables=[];expectedlinks=[];expectednotes=[];expectedassets=[];expectedimages=0
   for i in row['block_indices']:
    unit=units[i];projected=sanitize_images(unit);expectedtables.extend(table_data(projected));expectedlinks.extend(normalized_links(unit,url));expectednotes.extend(source_notes(unit));expectedassets.extend(source_assets(unit,url));expectedimages+=projected.get_text().count('[IMAGE]')
   if row['tables']!=expectedtables or row['links']!=expectedlinks or row['notes']!=expectednotes or row['image_placeholder_count']!=expectedimages:errors.append('Primary table/link/note/image source projection differs '+row['record_id'])
   if len(row['assets'])!=len(expectedassets):errors.append('Primary source asset-reference inventory differs '+row['record_id']);asset_reference_complete=False
   else:
    for actual,expected in zip(row['assets'],expectedassets):
     if any(actual.get(k)!=v for k,v in expected.items() if k not in ['required','status','classification','reason']):errors.append('Primary source asset-reference fields differ '+row['record_id']);asset_reference_complete=False
   for node in semantic.find_all(True):
    for field in ['id','name']:
     if node.get(field):normids[(field,str(node[field]))]+=1;idowners[field][str(node[field])].add(row['record_id'])
   for link_index,link in enumerate(row['links']):primary_references.append((row,link_index,link))
  if sourceids!=normids:errors.append('Primary source ID/name occurrence conservation differs '+url)
  contexts[url]={'raw':raw,'root':root,'units':units,'records':rows};owners[url]=idowners;body_stats.append({'source_url':url,'source_sha256':sha(raw),'source_blocks':len(units),'owned_blocks':len(indices),'source_id_name_occurrences':sum(sourceids.values()),'normalized_id_name_occurrences':sum(normids.values())})
 for audit in audits:
  if audit['source_blocks']!=audit['owned_blocks'] or audit['source_blocks']!=audit['unique_owned_blocks'] or audit['source_tables']!=audit['owned_tables'] or audit['source_toc_edges']!=audit['matched_toc_edges'] or any(audit[k] for k in ['missing_toc_edges','extra_body_headings','heading_only_unresolved']):errors.append('Primary native inventory/body/table audit incomplete '+audit['url'])
 ownership_errors=list(errors)
 expecteddeps=[dict(asset,owner_record_id=row['record_id']) for row in records for asset in row['assets']]
 if len(expecteddeps)!=len(dependencies):errors.append('Required dependency ledger inventory differs')
 else:
  for original,dep in zip(expecteddeps,dependencies):
   if any(dep.get(k)!=v for k,v in original.items() if k not in ['required','status','classification','reason']):errors.append('Dependency/source reference binding differs')
   if image_asset(dep):valid=dep.get('required') is False and dep.get('status')=='policy_omitted_image'
   elif key(dep['url']) in raw_documents:valid=dep.get('required') is False and dep.get('status')=='retained_primary_document'
   else:
    matches=[r for r in reference_rules if re.fullmatch(r['url_regex'],dep['url']) and re.search(r['context_regex'],dep.get('context',''),re.I)]
    valid=len(matches)==1 and dep.get('required') is False and dep.get('status')=='independent_legal_layer_reference'
   if not valid:errors.append('Required nonimage dependency remains unqualified '+dep.get('url',''))
 dependency_errors=[e for e in errors if e not in ownership_errors]
 validpins={}
 for rule in rules:
  context=contexts.get(rule['source_url']);active=context and sha(context['raw'])==rule['source_sha256']
  # Changed source receives no finite disposition. Unknown literal defects still fail below.
  if not active:continue
  reasons=[]
  if currency!=rule['publication_currency']:reasons.append('edition marker differs')
  numeric=[r for r in context['records'] if r['heading'].split(' ',1)[0]==rule['printed_numeric_locator']]
  if len(numeric)!=1:reasons.append('numeric locator missing/ambiguous')
  target=numeric[0] if len(numeric)==1 else None
  if target:
   for field,expected in [('record_id',rule['target_record_id']),('heading',rule['target_heading']),('source_heading_ids',rule['target_source_heading_ids']),('block_indices',rule['target_block_indices'])]:
    if target.get(field)!=expected:reasons.append('target '+field+' differs')
   if target.get('body_qualification')!='source_body' or sha(target['full_text'].encode())!=rule['target_full_text_sha256'] or sha(target['semantic_html'].encode())!=rule['target_semantic_html_sha256']:reasons.append('retained target body differs/unqualified')
   if all(0<=i<len(context['units']) for i in rule['target_block_indices']):
    sourcebody=''.join(str(context['units'][i]) for i in rule['target_block_indices'])
    if sha(sourcebody.encode())!=rule['target_source_body_sha256']:reasons.append('source target block witness differs')
   else:reasons.append('source target block index missing')
  edges=[e for e in inventory if e['edge_id']==rule['source_toc_edge_id'] and e['label']==rule['target_heading'] and e['source_url']==rule['source_url']+'#'+rule['href_fragment']]
  maps=[m for audit in audits for m in audit['mapping'] if m['edge_id']==rule['source_toc_edge_id'] and m['record_id']==rule['target_record_id']]
  if len(edges)!=1 or len(maps)!=1:reasons.append('native inventory target mapping missing/ambiguous')
  for ref in rule['source_refs']:
   rs=[r for r in context['records'] if r['record_id']==ref['owner_record_id']];row=rs[0] if len(rs)==1 else None;index=ref['link_index'];link=row['links'][index] if row and index<len(row['links']) else None
   if not row or ref['source_block_index'] not in row['block_indices'] or not link or link.get('url')!=rule['source_url']+'#'+rule['href_fragment'] or link.get('attributes',{}).get('href')!=ref['source_raw_href'] or link.get('text')!=ref['source_text']:reasons.append('owner/reference changed or missing');continue
   unit=context['units'][ref['source_block_index']];anchors=([unit] if unit.name=='a' else [])+list(unit.find_all('a',href=True));matching=[n for n in anchors if n.get('href')==ref['source_raw_href'] and sha(str(n).encode())==ref['source_anchor_sha256']]
   if len(matching)!=1:reasons.append('raw source reference witness missing/ambiguous')
  if reasons:errors.append('Finite source navigation witness rejected '+rule['rule_id']+': '+', '.join(sorted(set(reasons))));continue
  for ref in rule['source_refs']:validpins[(ref['owner_record_id'],ref['link_index'])]={'rule_id':rule['rule_id'],'source_url':rule['source_url'],'source_sha256':rule['source_sha256'],'publication_currency':currency,'target_record_id':rule['target_record_id'],'target_heading':rule['target_heading'],'target_source_heading_ids':rule['target_source_heading_ids'],'target_full_text_sha256':rule['target_full_text_sha256'],'original_href':ref['source_raw_href'],'literal_browser_fragment_valid':False,'publisher_source_rewritten':False}
 for row,index,link in primary_references:
  destination=key(link['url']);fragment=unquote(urlsplit(link['url']).fragment)
  if any(destination.startswith(prefix) for prefix in separate_prefixes):continue
  if destination.startswith('https://www.codepublishing.com/AZ/Flagstaff/html/') and destination not in raw_documents:unresolved.append({'owner_record_id':row['record_id'],'url':link['url'],'reason':'Unacquired same-primary publication document'});continue
  if destination not in raw_documents or not fragment:continue
  targetowners=owners.get(destination,{});found=targetowners.get('id',{}).get(fragment,set()) or targetowners.get('name',{}).get(fragment,set())
  if len(found)==1:continue
  defect={'owner_record_id':row['record_id'],'url':link['url'],'source_issue':'publisher_missing_anchor' if not found else 'source_ambiguous_target_owner','correction_applied':False,'link_index':index};diagnostics.append(defect)
  pin=validpins.get((row['record_id'],index))
  if pin and destination==pin['source_url']:resolutions.append(dict(defect,**pin))
  else:unresolved.append(dict(defect,reason='No unique exact-source retained target witness'))
 return {'schema':'source-navigation-target-coverage-1','source_target_coverage_complete':not errors and not unresolved,'literal_browser_fragment_complete':not diagnostics,'source_broken_link_occurrences':len(diagnostics),'diagnostics':diagnostics,'resolutions':resolutions,'unresolved':unresolved,'full_primary_source_ownership_complete':not ownership_errors,'source_text_ownership_complete':not ownership_errors,'dependency_coverage_complete':not dependency_errors and asset_reference_complete,'source_asset_reference_inventory_complete':asset_reference_complete,'primary_documents':len(raw_documents),'primary_records':len(records),'primary_source_evidence':body_stats,'dependency_references_checked':len(dependencies),'errors':sorted(set(errors)),'scope':'Primary source fidelity and exact retained-target coverage; literal publisher browser navigation remains separately reported. No publisher bytes or href/id/name values are repaired.'}
