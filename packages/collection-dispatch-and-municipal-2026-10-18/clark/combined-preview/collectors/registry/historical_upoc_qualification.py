"""Finite historical UPOC method qualification from exact portable original witnesses.

No acquisition, native parser, pixel operations or extraction. This qualifies the
whole source method/config, never current legal text/edition or jurisdiction.
"""
import csv,gzip,hashlib,io,json,zipfile
IDENT='82-8fbdce15716d'
KIND='historical-observed-native-receipt-full172-retained-current-parser'
URL='https://codes.opkansas.org/municipal-code/doclibrary.aspx?id=29e4fde6-8eab-4f2c-a715-8914aa24cfe0'
ALIAS='https://online.encodeplus.com/regs/overlandpark-ks/doclibrary.aspx?id=29e4fde6-8eab-4f2c-a715-8914aa24cfe0'
CONFIG_SHA='0167a3a39a6728834f0e226f4177843fbdc5027a4a7c23b9129a284a5d1bae2f'
NATIVE_SHA='877c6e874d4de7873d22dd51443fd5c42169445ad2955db3836841a105a57102'
RECORDS_SHA='dc3ee35dd02b4eed5199dcc6fa13d59184633ce3c40087134080496a428bc656'
COVERAGE_SHA='c77ea0b3815cdb4a2f4ebf02e8316940d82359bfcc701b584bdd78c9d894719d'
CHECKPOINT_SHA='961f2ef2f5eca639dcc1cb80bdc2a583bebff9b60aeff18643e4cc9b86f40012'
ARCHIVE_SHA='37483819dbc4e7d98ac761c6e76f20d9794c15bc373ecca379950c19abcd2afa'
CONFIG_PATH='collectors/encodeplus/configs/native-82-8fbdce15716d.json'
sha=lambda b:hashlib.sha256(b).hexdigest()
canon=lambda v:json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def need(condition,reason):
 if not condition:raise ValueError(reason)
def audit(here,catalog):
 try:
  rows=[p for p in catalog['publications']if p['id']==IDENT];need(len(rows)==1,'Historical UPOC exact publication ID missing/duplicated');p=rows[0];q=p.get('qualification_evidence',{})
  need(q.get('kind')==KIND,'Historical UPOC proof kind mismatch');need(p.get('runnable')and p.get('adapter_mode')=='native_document'and p.get('adapter_config_path')==CONFIG_PATH,'Historical UPOC exact runnable native method');need(not p.get('full_live_verified')and p.get('validation_level')=='mapped_only','Historical source method is not fresh live/legal verification')
  need(p.get('catalog_source_url')==ALIAS,'Original catalog alias provenance must remain explicit');need(p.get('source_url')==URL and q.get('native_sha256')==NATIVE_SHA and q.get('physical_pages')==172 and q.get('config_sha256')==CONFIG_SHA,'Historical source URL/config/whole-book pins')
  archive=here/'historical-upoc-source-evidence.zip';m=json.loads((here/'historical-upoc-source-evidence-manifest.json').read_text());need(m.get('kind')==KIND and m.get('archive_sha256')==ARCHIVE_SHA==sha(archive.read_bytes()),'Historical UPOC source archive binding')
  expected={'config.json','source.pdf','receipt.json','checkpoint.json','coverage.json','records.jsonl.gz','records.csv','cached-whole172-comparison.json'}
  with zipfile.ZipFile(archive)as z:
   need(set(z.namelist())==expected and len(z.namelist())==len(expected),'Historical UPOC exact archive member inventory');need({r['member']for r in m['files']}==expected and len(m['files'])==len(expected),'Historical UPOC manifest inventory')
   data={name:z.read(name)for name in expected}
   for r in m['files']:need(sha(data[r['member']])==r['sha256']and len(data[r['member']])==r['bytes'],'Historical witness corrupt '+r['member'])
  cfg=json.loads(data['config.json']);actual=(here.parents[1]/CONFIG_PATH).resolve();need(actual.is_relative_to(here.parents[1].resolve())and actual.is_file()and actual.read_bytes()==data['config.json']and sha(data['config.json'])==CONFIG_SHA,'Historical native config differs from exact witness')
  need((cfg['id'],cfg['mode'],cfg['url'],cfg['expected_sha256'],cfg['expected_pages'])==(IDENT,'native_document',URL,NATIVE_SHA,172),'Historical config identity/source scope');need(cfg['qualification']['catalog_source_url']==ALIAS and cfg['qualification']['catalog_alias_acquisition_verified']is False,'Unproven catalog URL alias must remain distinct')
  source=data['source.pdf'];receipt=json.loads(data['receipt.json']);need(sha(source)==NATIVE_SHA and source.startswith(b'%PDF-')and b'%%EOF'in source[-1024:],'Historical original native PDF pin');need(receipt['url']==receipt['final_url']==URL and receipt['http_status']==200 and not receipt.get('challenge')and not receipt.get('error')and receipt['sha256']==NATIVE_SHA and receipt['bytes']==len(source),'Historical actual source receipt')
  headers={k.lower():str(v)for k,v in receipt['headers'].items()};need(headers['content-type'].split(';',1)[0].strip().lower()=='application/pdf'and headers['content-disposition']==cfg['qualification']['observed_content_disposition'],'Historical native MIME/filename identity')
  need(sha(data['coverage.json'])==COVERAGE_SHA and sha(data['checkpoint.json'])==CHECKPOINT_SHA,'Exact full172 parser execution report binding');report=json.loads(data['coverage.json']);state=json.loads(data['checkpoint.json']);need(state['config']==cfg and state['config_sha256']==sha(canon(cfg))and state['full_native_parser_executed_once']and not state['forbidden_operations'],'Full native parser/config/runtime/image guards')
  body=gzip.decompress(data['records.jsonl.gz']);need(sha(body)==RECORDS_SHA==state['normalized_outputs']['records.jsonl'],'Whole172 normalized record hash');records=[json.loads(line)for line in body.decode().split('\n')if line];need(len(records)==172 and [r['physical_page']for r in records]==list(range(1,173)),'All physical native pages in order')
  need(all(r['document_id']==IDENT and r['raw_sha256']==NATIVE_SHA and r['page_count']==172 and r['source_url']==URL+'#page='+str(r['physical_page'])for r in records),'Every native page exact source/namespace')
  for witness in cfg['qualification']['native_identity_witnesses']:need(witness['literal']in records[witness['physical_page']-1]['text'],'Historical source city/ordinance/40th/2024 identity witness')
  need(sum(r['image_placeholder_count']for r in records)==sum(r['text'].count('[IMAGE]')for r in records)==46,'Exact intentional image placeholder inventory');need(sum(r['pdf_qualification']['source_word_count']for r in records)==28603,'Complete source word denominator')
  need(sum(bool(r['pdf_qualification'].get('undecoded_cid_literals'))for r in records)==102 and sum(not r['pdf_qualification']['independent_text_engine_characters_agree']for r in records)==102,'All102 source CID/engine page gaps retained');need(sum(r['pdf_qualification']['detected_table_cells']for r in records)==sum(r['pdf_qualification']['independent_table_cells_agree']for r in records)==745,'All canonical detected cells preserved')
  need(report['native_document_complete']and report['source_page_traversal_complete']and report['physical_pages']==report['normalized_record_count']==172,'Whole retained document coverage');need(report['start_end_consistent']is None and not report['closing_acquisition_performed']and not state['closing_acquisition_performed'],'Single old acquisition is not a fabricated closing sweep')
  for flag in ['pdf_extractable_text_reconciled','all_tables_detected','source_logical_structure_qualified','publication_text_complete','publication_complete','attachments_complete','required_external_legal_dependencies_complete','edition_complete','current_adopted_edition_qualified','jurisdiction_complete']:need(report[flag]is False,'Historical unresolved dimension lifted: '+flag)
  comparison=json.loads(data['cached-whole172-comparison.json']);need(comparison['passed']and comparison['pages']==172 and comparison['other_field_difference_count']==0 and comparison['all_172_legal_text_exact']and comparison['all_IMAGE_positions_and_metadata_equal_except_ID_ref'],'Complete prior-IR comparison')
  need(sha(data['records.csv'])==state['normalized_outputs']['records.csv'],'Native CSV binding');csv.field_size_limit(64*1024*1024);export=list(csv.DictReader(io.StringIO(data['records.csv'].decode(),newline='')));need(len(export)==172,'Native CSV full page inventory')
  for r,c in zip(records,export):need(c['id']==r['id']and c['text']==r['text']and int(c['physical_page'])==r['physical_page']and c['raw_sha256']==NATIVE_SHA,'Native CSV page/text source binding')
  return []
 except Exception as error:return ['Historical UPOC source qualification: '+str(error)]
