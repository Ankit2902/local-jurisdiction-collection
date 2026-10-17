"""Read-only resolution of normalized internal reference targets against same-job retained TOC."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('primary',type=Path);p.add_argument('supplemental',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();r=json.loads((a.supplemental/'normalized/sections.jsonl').read_text().splitlines()[0]);ids=set()
def walk(n):
 ids.add(n.get('Id'))
 for c in n.get('Children',[]):walk(c)
walk(json.loads((a.primary/'toc-full.json').read_text()));refs=[x for x in r['links'] if x.get('target_node_id')];attrs=lambda x:x.get('attributes',{});qa={'scope':'Preservation and same-job TOC resolution of internal data-nodeid/data-chunk-id targets in one operative legal table; no referenced body collection. Independent raw anchor-attribute comparison is in table DOM QA.','source_node_id':r['node_id'],'link_count':len(r['links']),'internal_target_count':len(refs),'targets_in_same_toc':sum(x['target_node_id'] in ids for x in refs),'unresolved_targets':[x for x in refs if x['target_node_id'] not in ids],'source_attributes_preserved':all((attrs(x).get('data-nodeid') or attrs(x).get('data-node-id') or attrs(x).get('data-chunk-id'))==x['target_node_id'] for x in refs),'same_product_attributes':all(not attrs(x).get('data-product-id') or attrs(x)['data-product-id']==str(r['product_id']) for x in refs)}
if a.out:a.out.write_text(json.dumps(qa,indent=2))
print(json.dumps(qa,indent=2))
