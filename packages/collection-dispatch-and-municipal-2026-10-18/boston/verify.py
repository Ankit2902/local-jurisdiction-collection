#!/usr/bin/env python3
"""Read-only portable source/receipt/routing/advisory replay, stdlib only; no requests."""
import pathlib,json,hashlib,sys,socket
from unittest.mock import patch
sys.dont_write_bytecode=True
P=pathlib.Path(__file__).resolve().parent
h=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();r=lambda q:json.loads(q.read_text())
def main():
 manifest=r(P/'MANIFEST.json');actual={x.relative_to(P).as_posix()for x in P.rglob('*')if x.is_file()and x.name!='MANIFEST.json'};assert actual==set(manifest)
 for n,v in manifest.items():
  rel=pathlib.Path(n);assert not rel.is_absolute()and'..'not in rel.parts;assert h(P/rel)==v,n
 receipt=r(P/'raw/zoning-code-index.receipt.json');assert h(P/'raw/zoning-code-index.bin')==receipt['sha256']=='f56323855559d20ce9cf503a646c6bd6ae1d59860659f8ea28bebeab29eedb2c';assert receipt['script_sha256']==h(P/'fetch_one.py')and receipt['executed_transport_sha256']==h(P/'runtime/transport.py')==r(P/'preflight.json')['transport_sha256']
 calls=[]
 def deny(*a,**k):calls.append('network');raise AssertionError('Offline verification forbids network')
 with patch.object(socket,'socket',deny),patch.object(socket,'create_connection',deny):
  import derive
  result=derive.derive();assert result==r(P/'SUMMARY.json')
 assert not calls
 gate=r(P/'official-host-gate-after.json');assert not gate['state'].get('stop')and len(gate['requests'])==1 and gate['requests'][0]['url']==receipt['url']
 mc=r(P/'access-state/municode-browser-stop.json');assert mc['operator_release_required']is True
 for f in r(P/'access-state/snapshot-provenance.json')['files']:assert h(P/f['retained_ref'])==f['sha256']
 proposal=r(P/'registry-correction-proposal.json');assert proposal['keep_runnable_false']and proposal['not_a_qualified_collection_config']and proposal['alternative_active_route_change_for_registry_owner_review_only']['runnable']is False
 assert result['operative_records_acquired']==0 and not result['full_publication_inventory_complete']and result['whole_publication_inventory_count']is None and result['requests_performed']['municode']==0
 for n,v in manifest.items():assert h(P/n)==v
 print(json.dumps({'passed':True,'packet_entries':len(manifest),'official_HTML_requests_captured':1,'publisher_requests':0,'separate_images_requested':0,'operative_legal_records':0,'full_publication_inventory_established':False,'native_export_size_runtime_established':False,'persistent_access_stop_preserved':True,'runnable_promoted':False,'verification_network_calls':calls,'mode':'Read-only retained source/routing/advisory verification; no nativePDF/image/browser APIs'}))
if __name__=='__main__':main()
