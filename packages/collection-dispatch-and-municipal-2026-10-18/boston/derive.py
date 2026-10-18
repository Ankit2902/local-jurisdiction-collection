#!/usr/bin/env python3
"""Offline source-routing extraction only; no legal records, browser, PDF or image APIs."""
import pathlib,json,hashlib,sys
from html.parser import HTMLParser
P=pathlib.Path(__file__).resolve().parent
class Route(HTMLParser):
 def __init__(self):super().__init__();self.head=None;self.htext=[];self.section=None;self.sections=[];self.anchor=None;self.full=[]
 def handle_starttag(self,t,a):
  if t=='h2':self.head=True;self.htext=[];self.section=None
  if t=='a'and self.section is not None:self.anchor={'href':dict(a).get('href'),'text':''}
 def handle_endtag(self,t):
  if t=='h2'and self.head:self.head=False;self.section={'heading':' '.join(''.join(self.htext).split()),'text':[],'links':[]};self.sections.append(self.section)
  if t=='a'and self.anchor is not None:
   if self.section is not None:self.section['links'].append(self.anchor)
   self.anchor=None
 def handle_data(self,d):
  self.full.append(d)
  if self.head:self.htext.append(d)
  if self.section is not None:self.section['text'].append(d)
  if self.anchor is not None:self.anchor['text']+=d

def derive():
 raw=(P/'raw/zoning-code-index.bin').read_bytes();receipt=json.loads((P/'raw/zoning-code-index.receipt.json').read_text());sha=hashlib.sha256(raw).hexdigest();assert sha==receipt['sha256']and receipt['status']==200 and receipt['final_url']==receipt['url']=='https://www.bostonplans.org/planning-zoning/zoning-code'and not receipt.get('access_stop')and not receipt.get('policy_omitted_image')
 x=Route();x.feed(raw.decode('utf-8'));sections={s['heading']:s for s in x.sections};assert set(sections)=={'Boston Zoning Code','Boston Zoning Maps','Boston Zoning Viewer'}
 section=sections['Boston Zoning Code'];text=' '.join(' '.join(section['text']).split());assert 'Access the whole document on Municode' in text
 urls=list(dict.fromkeys(a['href']for a in section['links']if a['href']));assert urls==['https://library.municode.com/ma/boston/codes/redevelopment_authority']
 maps=list(dict.fromkeys(a['href']for a in sections['Boston Zoning Maps']['links']if a['href']));assert maps==['https://www.bostonplans.org/3d-data-maps/gis-maps/zoning-maps']
 assert 'An official website of the City of Boston'in' '.join(' '.join(x.full).split())
 advisories=json.loads((P/'access-state/registry-access-advisories.json').read_text());mc=next(a for a in advisories['advisories']if a['family']=='municode');assert mc['operator_review_required']and mc['automatic_retry']is False
 observed=json.loads((P/'access-state/observed-access-stops.json').read_text());assert observed['stops']['municode:publisher']['source']['state']['stop']is True
 return {'schema_version':1,'status':'official_route_observed_municode_body_collection_stopped','publication_id':'15-4cb58ccd8b21','government':'Boston city','expected_state':'MA','state_route_evidence':'Observed publisher route /ma/boston; no publisher API identity acquired','official_source_url':receipt['url'],'source_sha256':sha,'source_identity_banner':'An official website of the City of Boston','source_section_heading':section['heading'],'source_section_text':text,'whole_document_publisher_route':urls[0],'body_publisher_family':'municode','duplicate_whole_document_controls':len(section['links']),'official_native_export_links_in_code_section':[],'whole_publication_inventory_count':None,'native_export_availability':None,'source_publication_edition':None,'estimated_full_run_bytes':None,'estimated_full_run_seconds':None,'estimate_reason':'Whole publication not inventoried or requested; active publisher-family stop applies. The government page is routing evidence, not the legal publication.','separate_map_component':{'source_heading':'Boston Zoning Maps','observed_url':maps[0],'acquired':False,'full_inventory_known':False,'substitutes_for_code':False},'operative_records_acquired':0,'complete':False,'full_publication_inventory_complete':False,'legal_semantic_coverage_complete':False,'jurisdiction_complete':False,'runnable_config_qualified':False,'requests_performed':{'official_source_HTML_GET':1,'municode':0,'maps_or_other_resources':0,'separate_images':0},'request_guard_scope':'Copied standard HTTP transport enforces persisted host gate and image-MIME body omission; no browser/PDF/image APIs imported by this discovery. No instrumented image API tripwire claim.','access_stop':{'family':'municode','preserved':True,'operator_release_required':True,'authority':'Retained registry advisory + durable observedstop + shared gate snapshots. This does not assert all legitimate Municode routes are unreachable.','new_Boston_Municode_availability_tested':False},'next_offline_action':'Supply a genuine complete exact-publication source bundle/export with publisher identity/edition/TOC/native hashes and closure evidence for offline qualification; then implement/test the source-bound import if needed. No generic MC import command exists in this release.','no_retry_reset_or_alternate_transport':True,'production_or_catalog_mutations':False}
if __name__=='__main__':
 out=derive();path=pathlib.Path(sys.argv[1]);assert not path.exists(),'Fresh offline output required';path.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':out['status'],'publisher_route':out['whole_document_publisher_route'],'operative_records':0,'publisher_requests':0,'full_inventory':False}))
