"""Deterministic views of the retained source-bound unknown-CID inventory."""
from pathlib import Path
from collections import defaultdict
import json,csv,io

def project(x):
 groups=defaultdict(list)
 for item in x['unresolved_CID_inventory']:groups[item['source_font_object']].append(item)
 finite={(row['source_font_object'],u['cid']) for row in x['finite_actual_operator_rows'] for u in row['units'] if not u['qualified']}
 remaining={'scope':'Exact remaining original-PDF font/CID inventory, priorledgerpositioncoverage; no invented Unicode','native_source_sha256':x['native_source_sha256'],'new_source_supported_mappings':0,'used_unresolved_distinct_pairs':len(x['unresolved_CID_inventory']),'unresolved_occurrences':4447,'finite_body_probe_observed_unresolved_pairs':len(finite),'unresolved_pairs_not_body_reparsed_in_this_study':len(x['unresolved_CID_inventory'])-len(finite),'targets':[{'font_object':obj,'unresolved_distinct_CIDs':len(v),'unresolved_occurrences':sum(r['occurrences'] for r in v),'CIDs':[r['cid'] for r in v],'same_face_witnesses':v[0]['same_face_witness_font_objects'],'all_actual_source_positions':v} for obj,v in sorted(groups.items())],'native_rawCID_passthrough_not_Unicode_witness':True,'required_missing_authority':'Source ToUnicode/cmap or exact same-face embedded explicit semantic glyph witness covering remaining GIDs; not recoverable from CID integers, synthetic names, widths or legal context alone'}
 cols=['font_object','CID','occurrences','physical_pages','target_glyf_sha256','target_glyf_bytes','target_contour_kind','advance_lsb','first_source_position','Unicode_qualified','reason'];b=io.StringIO(newline='');w=csv.DictWriter(b,cols);w.writeheader()
 for v in x['unresolved_CID_inventory']:w.writerow({'font_object':v['source_font_object'],'CID':v['cid'],'occurrences':v['occurrences'],'physical_pages':json.dumps(v['physical_pages']),'target_glyf_sha256':v['target_raw_glyf_sha256'],'target_glyf_bytes':v['target_glyf_bytes'],'target_contour_kind':v['target_contour_kind'],'advance_lsb':json.dumps(v['target_advance_lsb']),'first_source_position':json.dumps(v['first_source_position'],sort_keys=True),'Unicode_qualified':False,'reason':v['reason']})
 return remaining,b.getvalue()
def main():
 root=Path(__file__).resolve().parent;x=json.loads((root/'STUDY.json').read_text());r,csvtext=project(x);a=root/'UNRESOLVED-INVENTORY.json';b=root/'unresolved-cids.csv';assert not a.exists() and not b.exists(),'Never overwrite retained inventory';a.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');b.write_text(csvtext)
if __name__=='__main__':main()
