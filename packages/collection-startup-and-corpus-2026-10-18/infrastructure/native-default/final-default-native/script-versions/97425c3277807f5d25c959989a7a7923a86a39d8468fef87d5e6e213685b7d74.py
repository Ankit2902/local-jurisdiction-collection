"""Exact adopted Savannah ordinance alternative for one retained malformed reference.
No generated URL, source text substitution, network or image operations.
"""
import copy,io
from .util import hash_json,digest
CONFIG_SHA='7dab177a40615c08f092c2d6a2fa009b36c1dc80a5006abb6b3ae68564db7ace'
ALTERNATIVE={'owner': {'id': '6459', 'heading': 'CODE COMPARATIVE TABLE - ORDINANCES', 'body_sha256': '24009f90de284ccb9f1d8a0c0d3a0942074235fd955ff489b596a56622380277', 'raw_sha256': '4f531d2bb5f91e69deb0f802252f87f1c46469d47093ca5e51d3407188358449', 'source_url': 'https://online.encodeplus.com/regs/savannah-ga/doc-view.aspx?secid=6459&ajax=0', 'path': [{'heading': 'CODE OF ORDINANCES SAVANNAH, GEORGIA', 'id': '1'}, {'heading': 'DIVISION II', 'id': '6486'}], 'canonical_body_key': '_001-004-013'}, 'original_url': 'https://online.encodeplus.com/regs/savannah-ga/doclibrary.aspx?id=5b9f83a2-11c8-45c7-b8', 'original_literal_href': 'doclibrary.aspx?id=5b9f83a2-11c8-45c7-b8', 'source_label': '4-12-2018(3)', 'source_table_section': '1 Added', 'source_table_codified_range': '8-3370—8-3379', 'source_owner_raw_path': 'raw/node-6486.html', 'url': 'https://online.encodeplus.com/regs/savannah-ga/doclibrary.aspx?id=5b9f83a2-11c8-45c7-b8de-e4f23038d768', 'expected_sha256': '49637afca507126704ead37155e4a8a839423cc17273c4a36a7914649a587d9d', 'expected_pages': 4, 'page_text_sha256': ['ec2ae40ff49d3a1d109db9774146aa43f2aec7cdc28ca7a48fda01a40f983413', 'c0f5e1610a868a44b51d20e3a58ac309ac6e02064cf05c278bc9b8cfd7a31c2b', 'd6f6f9863ddf65caf645936913c09adccc09ceaea489fb89e28938e3298cce88', 'a253171ab18519a9c131c090f225a4ba380a24cc6f96b782e0aafab85ee3091f'], 'identity': 'City of Savannah Georgia; Ordinance of04-12-2018(3); ArticleQ ConservationOverlayDistrict; §§8-3370—8-3379; ADOPTED AND APPROVED APRIL12,2018', 'discovery': 'Exact complete publisher URL from observed search result, not malformed URL retry or constructed UUID', 'search_provenance_sha256': '65f534ee1177914c74963c1e106abcbd79b6e98630f4bf7f8cbbd98848f9b6a3', 'native_receipt_sha256': '5f07330697727c0a0a1e971638130249d82a3844016a3a4dd8757d6d2ca1f1b0', 'original_failure': {'raw_path': 'assets/85d8d12db5a4feb84785369ebbc9d066582653dce8b2466569c8603064caeac2.bin', 'reason': 'HTTP failure 404 https://online.encodeplus.com/regs/savannah-ga/errors/doclib404.aspx'}, 'original_failed_receipt_sha256': 'f39af3c55d6f225b986755a57c5afe2a991e516c528521862a48df8011618d26', 'proposal_excluded': 'Official meeting draft has blank adoption date; not accepted as alternative. Actual publisher file contains completed Apr12,2018 adoption date.'}

def reconcile(records,cfg):
 if hash_json(cfg)!=CONFIG_SHA:return records
 q=ALTERNATIVE;owner=records.get(q['owner']['id'])
 if not owner or {k:owner.get(k) for k in q['owner']}!=q['owner']:return records
 if not any(link.get('attributes',{}).get('href')==q['original_literal_href'] and link.get('text')==q['source_label'] for link in owner.get('links',[])):return records
 for asset in owner.get('assets',[]):
  if asset.get('url')!=q['original_url']:continue
  asset['original_source_url']=q['original_url'];asset['url']=q['url'];asset['source_qualified_alternative']=copy.deepcopy(q)
  owner.setdefault('qualified_reference_dispositions',[]).append({'type':'qualified_exact_adopted_savannah_ordinance_document_alternative','original_failed_url':q['original_url'],'qualified_source_url':q['url'],'source_binding':copy.deepcopy(q),'required_document':True,'reason':'Exact retained comparative-table owner, literal href/label/body/raw hash and codified range; actual observed complete publisher URL, four-page native hash, all-page text pins and completed Apr12,2018 adoption. Original truncated404 and separate blank-date draft retained. Not a new edition or a repaired URL request.'})
 return records

def qualify(data,binding):
 if binding!=ALTERNATIVE:raise ValueError('Unqualified Savannah alternative source binding')
 q=ALTERNATIVE
 if digest(data)!=q['expected_sha256']:raise ValueError('Savannah alternative adopted native SHA mismatch')
 from pypdf import PdfReader
 reader=PdfReader(io.BytesIO(data),strict=True)
 if len(reader.pages)!=q['expected_pages']:raise ValueError('Savannah alternative physical page count mismatch')
 for page,expected in zip(reader.pages,q['page_text_sha256']):
  normalized=''.join(c.casefold() for c in (page.extract_text() or '') if c.isalnum())
  if digest(normalized.encode())!=expected:raise ValueError('Savannah adopted text/version witness mismatch')
 return copy.deepcopy(q)
