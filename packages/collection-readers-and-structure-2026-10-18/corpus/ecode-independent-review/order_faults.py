"""Source-position fault checks against the actual whole acquired reader."""
import json,socket,sys
from pathlib import Path
from unittest.mock import patch
S=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00/outputs/collection-readiness-poste026685-2026-10-17/ecode-corpus-reader-v1');H=Path(__file__).resolve().parent;sys.path.insert(0,str(S/'source'))
import ecode_html as ec
root=S/'package/evidence/input';proof=ec.load(S/'actual-standard-proof/read-only-proof.json');family=ec.load(S/'actual-standard-proof/family-verification.json');original=ec.toc_positions
nodes=ec.lines(S/'package/source-nodes.jsonl');nonroots=[n for n in nodes if not n['source_order_witness'].get('root_wrapper')];target=nonroots[1]['node_id'].split(':',1)[1];first=nonroots[0]['source_order_witness']['literal_data_position'];results=[]
def missing(data):return [(i,p)for i,p in original(data)if i!=target]
def duplicate(data):return [(i,first if i==target else p)for i,p in original(data)]
def reverse(data):
 values=original(data);return list(reversed(values))if len(values)>1 else values
with patch.object(socket,'socket',side_effect=AssertionError('Offline')):
 for name,f in [('missing_global_position',missing),('duplicate_global_position',duplicate),('reversed_source_DOM_order',reverse)]:
  with patch.object(ec,'toc_positions',side_effect=f):
   try:ec.read_projection(root,proof,family)
   except ValueError as e:results.append({'fault':name,'refused':True,'message':str(e)})
   else:raise AssertionError('Position fault accepted: '+name)
(H/'order-faults.json').write_text(json.dumps({'passed':True,'actual_source_position_faults':results,'source_modified':False,'native_image_normalizer_network_calls':0},indent=2)+'\n');print(json.dumps(results,indent=2))
