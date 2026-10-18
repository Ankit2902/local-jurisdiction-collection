from pathlib import Path
from collections import Counter,defaultdict
import hashlib,json,sys,socket,base64
from urllib.parse import urlsplit
from unittest.mock import patch
from bs4 import BeautifulSoup,Tag,NavigableString,Comment,Declaration,Doctype,ProcessingInstruction
c=Path(sys.argv[1]);o=Path(sys.argv[2]);source=c/'collection/source';norm=c/'collection/normalized'
sha=lambda x:hashlib.sha256(x).hexdigest()
load=lambda p:json.loads(p.read_text())
rs=[json.loads(l)for l in(norm/'records.jsonl').read_text().splitlines()];assert sha((norm/'records.jsonl').read_bytes())=='1344484a99e9dce522f72d2254b713e9b725d552bb28d174c3fb66884a7fae5b'
state=load(source/'checkpoint.json');artifacts=[a for a in state['artifacts']if a['role']=='content'];byurl={a['source_url']:a for a in artifacts};assert len(byurl)==len(artifacts)==361
bydoc=defaultdict(list)
for r in rs:bydoc[r['source_url'].split('#')[0]].append(r)
assert set(bydoc)==set(byurl)and len(rs)==2661
BLOCKS={'p','h1','h2','h3','h4','h5','h6','table','ul','ol','pre','blockquote','svg','img','picture','object','iframe','hr'}
def blocks(root):
 for n in root.children:
  if isinstance(n,(Comment,Declaration,Doctype,ProcessingInstruction)):continue
  if isinstance(n,NavigableString):
   if str(n).strip():w=BeautifulSoup('<p></p>','html.parser').p;w.string=str(n);yield w
  elif isinstance(n,Tag):
   if n.name in {'script','style','head'}:continue
   if n.name=='a'and str(n.get('href','')).startswith('#wwfootnote_inline_'):yield n;continue
   if n.name in BLOCKS:yield n
   else:yield from blocks(n)
raws={};units={};totalblocks=0
for u,a in byurl.items():
 raw=(source/a['path']).read_bytes();assert sha(raw)==a['sha256'];raws[u]=raw
 assert all(r['source_sha256']==sha(raw)for r in bydoc[u])
 root=BeautifulSoup(raw,'html.parser').select_one('#mainContent');assert root is not None;units[u]=list(blocks(root));owned=[i for r in bydoc[u]for i in r['block_indices']];assert Counter(owned)==Counter(range(len(units[u])));totalblocks+=len(owned)
assert totalblocks==24237
cfg=load(c/'source/configs.json')['targets']['original-flagstaff-az'];rule=cfg['source_navigation_resolutions'][0];url=rule['source_url'];assert sha(raws[url])==rule['source_sha256'];root=BeautifulSoup(raws[url],'html.parser').select_one('#mainContent');fragment=rule['href_fragment']
assert not root.find(id=fragment)and not root.find(attrs={'name':fragment})
exact=[n for n in root.find_all(True)if n.get('id')==fragment+'\t'or n.get('name')==fragment+'\t'];assert len(exact)==2
records_by_id={r['record_id']:r for r in rs};target=records_by_id[rule['target_record_id']];assert target['heading']==rule['target_heading']and target['source_heading_ids']==rule['target_source_heading_ids']and target['block_indices']==rule['target_block_indices']
assert sha(target['full_text'].encode())==rule['target_full_text_sha256']and sha(target['semantic_html'].encode())==rule['target_semantic_html_sha256'];assert sha(''.join(str(units[url][i])for i in rule['target_block_indices']).encode())==rule['target_source_body_sha256']
source_refs=[]
for ref in rule['source_refs']:
 r=records_by_id[ref['owner_record_id']];assert r['source_url'].split('#')[0]==url and ref['source_block_index']in r['block_indices'];link=r['links'][ref['link_index']]
 assert link['url']==url+'#'+fragment and link['attributes']['href']==ref['source_raw_href']and link['text']==ref['source_text']
 unit=units[url][ref['source_block_index']];anchors=([unit]if unit.name=='a'else[])+list(unit.find_all('a',href=True));hits=[a for a in anchors if a.get('href')==ref['source_raw_href']and sha(str(a).encode())==ref['source_anchor_sha256']];assert len(hits)==1
 source_refs.append({'owner_record_id':r['record_id'],'link_index':ref['link_index'],'block_index':ref['source_block_index'],'source_anchor_sha256':sha(str(hits[0]).encode()),'literal_href_unchanged':True})
assert len(source_refs)==3and len(set(r['owner_record_id']for r in source_refs))==2
inv=load(norm/'source-inventory.json');audits=load(norm/'document-audits.json');assert len(inv)==2658 and len(audits)==361
edge=[e for e in inv if e['edge_id']==rule['source_toc_edge_id']];assert len(edge)==1and edge[0]['label']==target['heading']and edge[0]['source_url']==url+'#'+fragment
maps=[m for a in audits for m in a['mapping']if m['edge_id']==rule['source_toc_edge_id']];assert len(maps)==1and maps[0]['record_id']==target['record_id']
deps=load(norm/'dependencies.json');expected=[dict(a,owner_record_id=r['record_id'])for r in rs for a in r['assets']];assert len(deps)==len(expected)==993
for a,d in zip(expected,deps):
 for k,v in a.items():
  if k not in ['required','status','classification','reason']:assert d.get(k)==v
assert all(d['required']is False for d in deps);statuses=Counter(d['status']for d in deps);assert statuses==Counter({'policy_omitted_image':882,'retained_primary_document':93,'independent_legal_layer_reference':18})
nav=load(norm/'source-target-coverage.json');assert nav['source_target_coverage_complete']is True and nav['literal_browser_fragment_complete']is False and nav['dependency_coverage_complete']is True and nav['source_asset_reference_inventory_complete']is True and len(nav['diagnostics'])==len(nav['resolutions'])==3and not nav['unresolved']and not nav['errors']
assert all(r['literal_browser_fragment_valid']is False and r['publisher_source_rewritten']is False for r in nav['resolutions'])
# Reproduce the V8 omission lesson using the exact frozen V9 function, under network/pixel tripwires.
sys.path.insert(0,str(c));import test_source_navigation as t
calls=[]
def forbid(*a,**kw):calls.append('forbidden');raise AssertionError('Network/image/browser operation forbidden')
from PIL import Image
with patch.object(socket.socket,'connect',forbid),patch.object(socket,'create_connection',forbid),patch.object(base64,'b64decode',forbid),patch.object(Image,'open',forbid):
 x=t.fixture(attachment=True)
 for row in x['records']:row['assets']=[]
 x['dependencies']=[];fault=t.assess(**x);assert not fault['source_target_coverage_complete']and not fault['dependency_coverage_complete']and not fault['source_asset_reference_inventory_complete']
 x=t.fixture();wrong=t.assess(**dict(x,currency='Wrong edition'));assert not wrong['source_target_coverage_complete']
 assert not calls
result={'passed':True,'independent_raw_HTML_anchor_and_block_audit':True,'no_browser_or_render':True,'raw_documents':361,'records':2661,'owned_source_blocks':totalblocks,'native_TOC_edges':2658,'dependencies':993,'dependency_statuses':dict(statuses),'three_source_reference_witnesses':source_refs,'target_source_trailing_TAB_ID_name_occurrences':2,'literal_browser_fragment_valid':False,'finite_source_target_coverage_complete':True,'V8_omission_of_asset_and_ledger_refused_in_V9':True,'wrong_edition_refused':True,'all_records_hash_exact_preexisting_audit_stream':True,'required_nonimage_attachments_qualified_by_synthetic_fix':False,'whole_jurisdiction_accepted':False,'forbidden_network_image_calls':calls,'full361_normalizer_replay_repeated':False,'record_sha256':sha((norm/'records.jsonl').read_bytes()),'auditor_sha256':sha(Path(__file__).read_bytes())}
(o/'independent-source-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
