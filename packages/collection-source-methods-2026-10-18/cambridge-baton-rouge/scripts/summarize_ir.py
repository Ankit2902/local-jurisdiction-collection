"""Read actual normalized IR only; no native parser/network/image operations."""
import sys
sys.dont_write_bytecode=True
import json,collections,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
rows=[r for p in sorted((ROOT/'run/items').glob('*.json'))for r in json.loads(p.read_text())['records']]
assert len(rows)==606 and len({r['id']for r in rows})==606
reasons=collections.Counter();review=[]
for r in rows:
 q=r['pdf_qualification']
 for condition in q['review_conditions']:
  category=condition.split(':')[-1]if'::'in condition else condition;reasons[category]+=1
 if q['review_conditions']:review.append({'id':r['id'],'raw_ref':r['raw_ref'],'raw_sha256':r['raw_sha256'],'review_conditions':q['review_conditions'],'unmapped_or_private_use_codepoints':q['unmapped_or_private_use_codepoints']})
q=[r['pdf_qualification']for r in rows];cells=sum(x['detected_table_cells']for x in q);agree=sum(x['independent_table_cells_agree']for x in q)
links=[{'owner':r['id'],'raw_sha256':r['raw_sha256'],'source_page':r['physical_page'],'annotation':link,'requiredness_and_external_closure_qualified':False}for r in rows for link in r['links']]
d={'normalized_physical_pages':606,'detected_IMAGE_markers':sum(r['image_placeholder_count']for r in rows),'detected_tables':sum(x['detected_table_count']for x in q),'detected_cells':cells,'independent_cells_agree':agree,'independent_cells_disagree':cells-agree,'source_word_ownership_complete_pages':sum(x['source_word_ownership_complete']for x in q),'source_words_cover_deduplicated_glyph_characters_pages':sum(x['source_words_cover_deduplicated_glyph_characters']for x in q),'qualified_engine_character_disagreement_pages':sum(not x['independent_text_engine_characters_agree']for x in q),'raw_engine_character_disagreement_pages':sum(not x['raw_independent_text_engine_characters_agree']for x in q),'review_pages':len(review),'unmapped_or_private_use_pages':sum(bool(x['unmapped_or_private_use_codepoints'])for x in q),'review_condition_counts':dict(reasons),'review_page_details':review,'annotation_occurrences':len(links),'source_originals_unchanged':True,'legal_semantic_complete':False,'full_publication_qualified':False,'image_detection_limit':'Copied standard parser uses metadata-only raster bboxes and detected map/blank-vector placeholders; general mixed-vector illustration detection has stated limits. Detected427 is not blanketproof allpossibleillustrations found. Native originals retained; no pixels extracted/rendered/OCRed.','no_separate_images_or_image_API_calls':True,'scope':'Standard file_pages extraction diagnostics; detector grids with known disagreement are not fullyqualified canonicallegal tables.'}
(ROOT/'extraction-diagnostics.json').write_text(json.dumps(d,indent=2)+'\n')
(ROOT/'native-annotation-link-inventory.json').write_text(json.dumps({'occurrences':len(links),'links':links,'links_requested':0,'external_dependency_qualification':False},indent=2)+'\n')
print(json.dumps({k:v for k,v in d.items()if k not in ['review_page_details','review_condition_counts']},indent=2))
