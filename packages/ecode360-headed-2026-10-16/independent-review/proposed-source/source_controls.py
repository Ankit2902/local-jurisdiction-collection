"""Receipt controls shared by the current DOM importers; no network operations."""
import json,re
from pathlib import Path
import ecode360 as e

def verify_route_binding(receipt,jurisdiction,publication_id):
 registry=e.load(Path(__file__).with_name('route-registry.json'))
 entries=registry if isinstance(registry,list) else registry['routes']
 row=next((x for x in entries if x['slug']==receipt['job']['slug']),None)
 if row is None or row['jurisdiction']!=jurisdiction:raise e.ValidationError('receipt slug/jurisdiction absent from independent route registry')
 identity=receipt['browser_state']['identity']
 expected_customer=str(row['customer_id']);allowed_codes={str(x) for x in row.get('allowed_code_ids',[row['code_id']])}
 if identity['customer_id']!=expected_customer or str(identity['code_id']) not in allowed_codes:raise e.ValidationError('customer/code does not match independent jurisdiction registry; document any new edition before updating registry')
 urls=row.get('allowed_source_urls',[row['discovery_url']])
 if e.fetch_url(receipt['job']['url']) not in {e.fetch_url(x) for x in urls}:raise e.ValidationError('capture URL outside reviewed jurisdiction acquisition routes')
 if row.get('publication_id','municipal-code')!=publication_id:raise e.ValidationError('publication family differs from route registry')
 # Currency is checked start/end and against raw identity, never pinned to an old
 # calendar date: a legitimate new publisher edition needs documented registry update.
 return row

def acquisition_transport(receipt,standalone=False):
 label=receipt.get('transport') or 'supported CUA documented browser capture'
 if standalone:
  if receipt.get('acquisition_mode') not in {'fully_standalone_headed','fully_standalone_headless'} or receipt.get('operator_assisted') is not False:raise e.ValidationError('receipt does not establish fully standalone acquisition mode')
  runtime=receipt.get('runtime',{})
  if runtime.get('fresh_context') is not True or runtime.get('storage_state_imported') is not False:raise e.ValidationError('standalone receipt lacks fresh-context/no-imported-state evidence')
  if receipt.get('rate_limit') or any(x.get('status')==429 for x in receipt.get('response_chronology',[])):raise e.ValidationError('rate-limited acquisition cannot be imported as accepted standalone source')
  if receipt.get('final_document_http_status')!=200:raise e.ValidationError('standalone legal source requires final document HTTP200')
 return label

def comparison_text(value):
 # Preserve Unicode word boundaries and punctuation, while ignoring rendering
 # whitespace introduced by block/list wrappers. "the rapist" != "therapist".
 return json.dumps(re.findall(r'\w+|[^\w\s]',value,re.UNICODE),ensure_ascii=False,separators=(',',':'))
