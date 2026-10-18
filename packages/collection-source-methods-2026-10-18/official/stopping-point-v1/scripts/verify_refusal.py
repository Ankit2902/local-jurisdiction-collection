"""Read-only refusal witness check, never source/publication completeness."""
import hashlib,json,pathlib,sys
sys.dont_write_bytecode=True
def verify(folder):
 p=pathlib.Path(folder);s=json.loads((p/'source-status.json').read_text());r=json.loads((p/'retained/receipt.json').read_text());b=(p/'retained/response.html').read_bytes()
 assert hashlib.sha256(b).hexdigest()==s['retained_response_sha256']==r['sha256']
 assert hashlib.sha256((p/'retained/receipt.json').read_bytes()).hexdigest()==s['retained_receipt_sha256']
 assert r['url']==s['source_url']and r.get('status',r.get('http_status'))==s['observed_status']==403
 assert not s['runnable']and not s['full_publication_verified']and not s['native_inventory_established']and not s['publication_body_identity_established']
 assert s['new_publisher_requests']==s['alternate_transport_or_route_requests']==s['source_records']==0
 assert not s['gate_reset']and s['status']=='retained_exact_source_refusal_no_retry'
 return {'refusal_witness_verified':True,'source_url':s['source_url'],'historical_status':403,'publication_inventory_or_text_qualified':False,'new_network_calls':0}
if __name__=='__main__':print(json.dumps(verify(sys.argv[1]),indent=2))
