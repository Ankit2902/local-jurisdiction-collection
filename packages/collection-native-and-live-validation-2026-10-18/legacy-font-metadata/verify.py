"""Read-only original-font metadata and five-page diagnostic replay."""
from pathlib import Path
import json,sys
import study as m
from write_inventory import project

def verify_result(actual,expected):
 assert m.canon(actual)==m.canon(expected),'Original font metadata, mappings, unresolved inventory or finite probes differ'
 assert actual['new_Unicode_mappings']==0 and actual['prior30mapping_proof_reproduces_exactly']
 assert len(actual['unresolved_CID_inventory'])==71 and sum(x['occurrences'] for x in actual['unresolved_CID_inventory'])==4447
 assert all(x['Unicode']is None and x['qualified']is False and not x['source_semantic_glyph_name_available'] for x in actual['unresolved_CID_inventory'])
 assert sum(s['known_mapping_count'] for s in actual['source_semantic_mapping_search'])==30
 assert actual['source_known_occurrences_carried_from_retained_ledger']==3382 and actual['selected_body_pages']==[9,38,107,169,170]
 assert not actual['full102page_content_reparse'] and actual['no_current_edition_or_installed_font_substitution'] and actual['no_source_PDF_or_legal_text_rewrite'] and not actual['network_image_decode_extract_render_OCR_calls']

def main():
 root=Path(__file__).resolve().parent;files=[p for p in root.rglob('*') if p.is_file() and '__pycache__'not in p.parts and not p.name.endswith('.log')];before={p.relative_to(root).as_posix():m.SHA(p.read_bytes()) for p in files};actual=m.read(root/'STUDY.json');verify_result(actual,m.study());inv,csvtext=project(actual);assert m.read(root/'UNRESOLVED-INVENTORY.json')==inv and (root/'unresolved-cids.csv').read_bytes()==csvtext.encode(),'Inventory JSON/CSV differs from source-bound study';assert before=={p.relative_to(root).as_posix():m.SHA(p.read_bytes()) for p in files};print(json.dumps({'passed':True,'readonly_source_and_evidence_unchanged':True,'prior30mappings_exact':True,'new_original_source_Unicode_mappings':0,'remaining_font_CID_pairs':71,'remaining_occurrences_retained_ledger':4447,'known_occurrences_retained_ledger':3382,'actual_body_pages':[9,38,107,169,170],'xref_metadata_objects':actual['metadata_census_scope']['xref_object_metadata_examined'],'native_raw_CID_passthrough_geometry_matches':sum(n['native_target_CID_passthrough_geometry_matches'] for n in actual['finite_native_probes']),'known_space_geometry_not_matched':sum(n['native_target_geometry_unresolved'] for n in actual['finite_native_probes']),'no_full102_content_parse':True,'network_image_decode_extract_render_OCR_calls':0,'study_sha256':m.SHA((root/'STUDY.json').read_bytes())},indent=2,sort_keys=True))
if __name__=='__main__':main()
