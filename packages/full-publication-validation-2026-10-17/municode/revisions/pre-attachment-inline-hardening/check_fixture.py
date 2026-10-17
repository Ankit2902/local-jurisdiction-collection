"""Read-only retained operative-table fixture check; source backed but not whole-publication proof."""
import sys
sys.dont_write_bytecode=True
import json
from pathlib import Path
from normalize import LegalHTML
p=Path(__file__).parent/'fixtures/retained-fee-table.json';j=json.loads(p.read_text());h=LegalHTML();h.feed(j['doc']['Content']);text=h.parsed();actual={'table_count':len(h.tables),'row_count':sum(len(t) for t in h.tables),'cell_count':sum(len(r) for t in h.tables for r in t),'internal_link_count':sum(bool(l.get('target_node_id')) for l in h.links)};assert actual==j['expected'];assert text;print(json.dumps({'passed':True,'evidence_kind':j['evidence_kind'],'network_requests':0,'node_id':j['doc']['Id'],**actual},indent=2))
