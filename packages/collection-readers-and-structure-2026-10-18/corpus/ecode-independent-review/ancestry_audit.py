"""All retained parent/hierarchy chains independently rebuilt from input IR."""
import hashlib,json
from pathlib import Path
S=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00/outputs/collection-readiness-poste026685-2026-10-17/ecode-corpus-reader-v1/package');R=S/'evidence/input';H=Path(__file__).resolve().parent
load=lambda p:json.loads(p.read_bytes());lines=lambda p:[json.loads(x)for x in p.read_text().split('\n')if x]
inv={n['id']:n for n in load(R/'inventory.json')};ir={r['id']:r for r in lines(R/'records.jsonl')};nodes=lines(S/'source-nodes.jsonl');pr=lines(S/'record-provenance.jsonl');cp=load(R/'checkpoint.json');arts={a['path']:a for a in cp['artifacts']}
for n in nodes:
 i=n['node_id'].split(':',1)[1];parent=(ir.get(i)or{}).get('parent_id')or inv[i].get('parent_id');assert n['parent_node_id']==('source:'+parent if parent else None)
for p in pr:
 i=p['record_id'].split(':',1)[1];chain=[];seen=set();current=i
 while current:
  assert current in inv and current not in seen;seen.add(current);chain.append(inv[current]);current=(ir.get(current)or{}).get('parent_id')or inv[current].get('parent_id')
 chain.reverse();assert p['hierarchy_chain']==chain;assert ir[i]['path']==[n['heading']for n in chain];w=p['source_order_witness'];a=arts[w['raw_artifact_path'].removeprefix('evidence/input/')];assert a['sha256']==w['raw_sha256'];assert w['selector']=='#toc .contentTitle[data-guid="'+i+'"][data-position="'+w['literal_data_position']+'"]'
result={'passed':True,'inventory_parent_links_checked':len(nodes),'exact_retained_path_and_provenance_chains':len(pr),'source_selector_and_hash_witnesses':len(pr),'source_request_normalizer_image_native_calls':0};(H/'ancestry-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
