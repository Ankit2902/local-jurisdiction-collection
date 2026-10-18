"""Required data enters normal code/snapshot binding; no transport instantiated."""
from pathlib import Path
import sys,json,hashlib,socket
from unittest.mock import patch
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H/'candidate-final'))
with patch.object(socket,'socket',side_effect=AssertionError('No publisher work')):
 from collectors.encodeplus.collect import code_hashes
 actual=code_hashes();name='infrastructure-multiline-native-geometry.json';p=H/'candidate-final/collectors/encodeplus'/name;assert actual[name]==hashlib.sha256(p.read_bytes()).hexdigest()
x={'passed':True,'required_geometry_snapshot_name':name,'required_geometry_sha256':actual[name],'code_hash_inventory_includes_required_data':True,'source_file_count':len(actual),'new_transport_requests':0,'production_modified':False,'scope':'Calls existing normal code_hashes; fresh/resume/script-version code consumes this dictionary. Does not claim a fresh acquisition or old-checkpoint upgrade occurred.'};print(json.dumps(x,indent=2))
