"""Independent retained-source/config/receipt/TOC reconciliation. No family imports/network."""
import copy,hashlib,json,re,sys,datetime
from pathlib import Path
from urllib.parse import urljoin,urlparse,parse_qs
from bs4 import BeautifulSoup
from pypdf import PdfReader
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def clean(v):return ' '.join(str(v).split())
repo,run,out=map(Path,sys.argv[1:]);cp=json.loads((run/'checkpoint.json').read_text());records=[json.loads(x) for x in (run/'records.jsonl').read_text().split('\n') if x];recordmap={r['id']:r for r in records};inv=json.loads((run/'inventory.json').read_text());errors=[];checks=0
def check(ok,kind,**data):
 global checks
 checks+=1
 if not ok:errors.append({'check':kind,**data})
start_manifest={str(p.relative_to(run)):sha(p) for p in run.rglob('*') if p.is_file()}
(out/'run-input-manifest.json').write_text(json.dumps(start_manifest,indent=2)+'\n')
jobpath=run.parent/'.collection-jobs/2ee31989281c6166/job.json';job=json.loads(jobpath.read_text());binding=job['binding'];attempt=job['attempts'][-1];cfg=cp['config'];snapshot=run.parent/'execution-source-fresh-overland-v1'
check(binding['target_id']=='82' and binding['publication_id']=='82-primary','selected_publication_identity')
check(binding['publication']['dispatch_config']==cfg,'selected_dispatch_equals_actual_config')
check(canonical(cfg)==cp['config_sha256'],'actual_configuration_hash')
check(json.loads((repo/'collectors/encodeplus/targets.json').read_text())['overland']==cfg,'named_config_actual_bytes')
check(attempt['collector_sources_before']==attempt['collector_sources_after']==binding['collector_sources'],'job_before_after_source_identity')
check(not attempt['source_changed_during_run'] and not attempt['runtime_changed_during_run'],'job_source_runtime_drift_flags')
source_comparisons=[]
for rel,digest in binding['collector_sources'].items():
 current=repo/rel;captured=snapshot/rel
 check(current.is_file() and sha(current)==digest,'current_shared_source',path=rel)
 check(captured.is_file() and sha(captured)==digest,'captured_shared_source',path=rel)
 source_comparisons.append({'path':rel,'sha256':digest})
family_comparisons=[]
for name,digest in cp['code_hashes'].items():
 current=repo/'collectors/encodeplus'/name;captured=snapshot/'collectors/encodeplus'/name
 check(sha(current)==digest and sha(captured)==digest,'current_and_executed_family_source',path=name)
 check(any(p.name.startswith(digest+'.') and sha(p)==digest for p in (run/'script-versions').iterdir()),'retained_executed_script',path=name)
 family_comparisons.append({'path':name,'sha256':digest})
check('collectors/encodeplus/targets.json' not in binding['collector_sources'],'documented_named_config_wrapper_omission_still_present')
check(binding.get('native_export') is not False,'native_request_not_removed')
# Parse original publisher TOC independently, without normalized record IDs as expectations.
tocraw=run/cp['inventory_raw']['path'];soup=BeautifulSoup(tocraw.read_bytes(),'html.parser');identity=clean(soup.select_one('#toc-pagehead').get_text());toc=[]
check(identity==cfg['identity'],'raw_publication_title')
for li in soup.select('#toc-list li.tocLink'):
 match=re.fullmatch(r'secid-x(\d+)',li.get('id',''));check(bool(match),'raw_TOC_ID_shape')
 if not match:continue
 ident=match.group(1);link=li.select_one('a[href]');url=urljoin(cfg['base'],link['href']);label=li.select_one('.toc-item');heading=clean(label.get_text())
 check(parse_qs(urlparse(url).query).get('secid')==[ident],'raw_TOC_link_binding',id=ident)
 toc.append({'id':ident,'heading':heading,'viewer_url':url})
check(len({n['id'] for n in toc})==len(toc),'independent_TOC_unique')
observed=[{k:n[k] for k in ['id','heading','viewer_url']} for n in inv['nodes']]
check(toc==observed,'independent_TOC_order_labels_links_equal_inventory')
check(set(n['id'] for n in toc)<=recordmap.keys(),'every_raw_TOC_ID_has_record')
check(len(recordmap)==len(records),'unique_normalized_IDs')
inventory_receipts=[];body_receipts=[];outside_controls=[];closing=[];source_ids=[];native_pins=[]
def receipt(relative,expected_url,expected_sha):
 p=run/relative;rp=Path(str(p)+'.receipt.json');r=json.loads(rp.read_text())
 check(sha(p)==expected_sha==r['sha256'],'raw_and_receipt_SHA',path=relative)
 check(r['url']==expected_url and r.get('final_url',r['url'])==expected_url,'exact_request_final_URL',path=relative)
 check(r['http_status']==200 and not r['challenge'] and not r.get('error'),'successful_retained_response',path=relative)
 return {'path':relative,'sha256':sha(p),'receipt_sha256':sha(rp),'url':expected_url,'started_at':r['started_at'],'finished_at':r['finished_at']}
for entry in [cp['inventory_raw'],cp['end_inventory']]:inventory_receipts.append(receipt(entry['path'],cfg['base']+'doc-view.aspx',entry['sha256']))
check(inventory_receipts[0]['sha256']==inventory_receipts[1]['sha256'],'raw_start_end_inventory_byte_identity')
ends={b['requested']:b for b in cp['end_blocks']}
for b in cp['blocks']:
 check(b['requested'] in {n['id'] for n in toc},'requested_block_is_raw_TOC_ID',id=b['requested'])
 expected=cfg['base']+'doc-view.aspx?secid='+b['requested']+'&ajax=0';body_receipts.append(receipt(b['path'],expected,b['sha256']));end=ends[b['requested']];closing.append(receipt(end['path'],expected,end['sha256']));check(b['sha256']==end['sha256'],'opening_closing_complete_raw_byte_identity',id=b['requested'])
 page=BeautifulSoup((run/b['path']).read_bytes(),'html.parser').select_one('#thePage');check(page.get('secid')==b['requested'],'requested_page_source_identity')
 sections=page.select('section[data-secid]');keys=lambda el:max((c for c in el.get('class',[]) if re.fullmatch(r'_\d+(?:-\d+)*',c)),key=len,default='')
 selected=next(s for s in sections if s['data-secid']==b['requested']);sk=keys(selected);expectedids=[]
 for section in sections:
  ident=section['data-secid'];key=keys(section);belongs=section is selected or bool(sk and key.startswith(sk+'-')) or selected in section.parents
  if belongs:
   source_ids.append(ident);expectedids.append(ident);r=recordmap.get(ident);check(r is not None and r['raw_path']==b['path'] and r['raw_sha256']==b['sha256'],'raw_body_owner_binding',id=ident)
  else:check(bool(key and sk.startswith(key+'-')),'only_proven_ancestor_context_outside_selected_scope',id=ident)
 check(set(expectedids)==set(b['record_ids']),'block_acquired_IDs_independently_reconciled',path=b['path'])
 outside=copy.deepcopy(page)
 for sec in list(outside.select('section[data-secid]')):
  if sec.parent is not None and not sec.find_parent('section',attrs={'data-secid':True}):sec.decompose()
 controls=[]
 for el in list(outside.select('#sectionBanner,script,style')):
  controls.append({'tag':el.name,'id':el.get('id')});el.decompose()
 check(not clean(outside.get_text()),'no_unowned_source_text',path=b['path'])
 check(not outside.select('img,picture,svg,object,embed,iframe,source,[background],[poster]'),'no_unowned_source_visual_or_embedded_document',path=b['path'])
 outside_controls.append({'raw_path':b['path'],'excluded_source_controls':controls})
check(len(set(source_ids))==len(source_ids)==len(records),'full_source_body_ID_union_once')
check(set(source_ids)==recordmap.keys(),'full_source_body_union_exact_output')
def instant(s):return datetime.datetime.fromisoformat(s)
check(max(instant(x['finished_at']) for x in body_receipts)<min(instant(x['started_at']) for x in closing),'all_opening_body_responses_before_closing')
check(max(instant(x['finished_at']) for x in closing)<instant(inventory_receipts[1]['started_at']),'closing_inventory_after_body_checks')
# Required document capture only. Page structure counts do not qualify semantics.
assets=[]
for url,a in cp['assets'].items():
 rec=receipt(a['path'],url,a['sha256']);owners=[r['id'] for r in records if any(x.get('url')==url and x.get('required') for x in r['assets'])];check(bool(owners),'asset_has_required_record_owners',url=url)
 reader=PdfReader(run/a['path'],strict=True);pages=len(reader.pages);check(pages==a['document_integrity']['pages']>0,'independent_required_PDF_page_tree',url=url)
 assets.append({**rec,'owner_ids':owners,'bytes':(run/a['path']).stat().st_size,'format':'PDF','independent_page_tree_count':pages,'text_table_reading_order_qualified':False})
for r in records:
 if r['kind']=='confirmed_source_empty':
  q=r['source_empty_qualification']['source_native_binding'];pins=[]
  for w in q['fixture_witnesses']:
   p=repo/'collectors/encodeplus'/w['path'];check(p.is_file() and sha(p)==w['sha256'],'exact_source_empty_witness_current',id=r['id'],path=w['path']);pins.append(w)
  native_pins.append({'id':r['id'],'witnesses':pins,'source_sha256':r['raw_sha256'],'selected_native_sha256':q['selected_native_sha256'],'scope':r['source_empty_qualification']['scope']})
report={'schema_version':1,'kind':'independent-fresh-primary-config-source-inventory-body-receipt-closing-binding','passed':not errors,'checks':checks,'errors':errors,'run':str(run),'target_id':'82','publication_id':'82-primary','config':cfg,'config_sha256':canonical(cfg),'checkpoint_sha256':sha(run/'checkpoint.json'),'records_sha256':sha(run/'records.jsonl'),'inventory_sha256':sha(run/'inventory.json'),'coverage_sha256':sha(run/'coverage.json'),'job_sha256':sha(jobpath),'auditor_sha256':sha(__file__),'raw_TOC_nodes':len(toc),'raw_owned_body_IDs':len(source_ids),'embedded_body_IDs':len(set(source_ids)-{x['id'] for x in toc}),'source_comparisons':source_comparisons,'family_comparisons':family_comparisons,'inventory_receipts':inventory_receipts,'opening_receipts':body_receipts,'closing_receipts':closing,'outside_controls':outside_controls,'required_document_capture':assets,'confirmed_source_empty_witnesses':native_pins,'known_operational_gap':'Shared wrapper collector_sources omits named targets.json. Exact actual config and targets.json hash are nevertheless independently bound here and retained by family checkpoint. No general operational acceptance inferred.','native_export':cp['native_export'],'network_requests_sent':0,'image_APIs_used':False,'PDF_semantics_accepted':False,'edition_accepted':False,'jurisdiction_accepted':False}
(out/'source-binding.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k in ['passed','checks','errors','raw_TOC_nodes','raw_owned_body_IDs','embedded_body_IDs']}));sys.exit(0 if report['passed'] else 2)
