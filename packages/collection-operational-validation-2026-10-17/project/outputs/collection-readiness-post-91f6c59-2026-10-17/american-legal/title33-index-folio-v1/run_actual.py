"""One retained source page only. No images/network/full-book replay."""
import hashlib,json,socket,sys
from pathlib import Path
from unittest.mock import patch
import pdfplumber
from associate import associate
root=Path(sys.argv[1]);out=Path(__file__).resolve().parent
source=root/'outputs/collection-readiness-2026-10-17/official/portland-title33-full/raw/21d54cdfe9d2b6a8de80.bin';sha=hashlib.sha256(source.read_bytes()).hexdigest();assert sha=='86ba1da866c9cc1acf56df185abfddff784c23b8fbd4601fbb1c0337abb0f354'
retained=root/'outputs/collection-readiness-followup-2026-10-17/american-legal/research/title33-inferred-structure-v1/current-seven-pages.jsonl';record=next(json.loads(line) for line in retained.open() if json.loads(line)['physical_page']==10)
with patch.object(socket.socket,'connect',side_effect=AssertionError('No network')),patch('PIL.Image.open',side_effect=AssertionError('No image decoding')),pdfplumber.open(source) as doc:
 page=doc.pages[9].dedupe_chars(tolerance=1);words=page.extract_words(x_tolerance=1.5,y_tolerance=3,extra_attrs=['fontname','size'])
 for i,w in enumerate(words):w['id']='pdf-page:10:word:'+str(i)
 result=associate(record['pdfium_qualified_comparison_text'],words,record['id'])
 result.update(source_sha256=sha,source_bytes=source.stat().st_size,physical_page=10,page_count=1855,source_context='Source Title33 chapter index continuation, with original Overlay Zones and Plan Districts group headings; bounded exact-source qualification, no general index classifier',native_stream_source_record_sha256=hashlib.sha256(retained.read_bytes()).hexdigest(),helper_sha256=hashlib.sha256((out/'associate.py').read_bytes()).hexdigest(),network_requests=0,image_decode_calls=0)
 (out/'actual-page10-word-fixture.json').write_text(json.dumps({'text':record['pdfium_qualified_comparison_text'],'words':words,'page_id':record['id'],'source_sha256':sha,'physical_page':10},indent=2)+'\n')
 (out/'actual-page10-associations.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'entries':len(result['entries']),'source_folio_mismatches':[{'citation':e['citation'],'folio':e['folio']} for e in result['entries'] if not e['citation_folio_stem_agrees']],'source_word_count':len(words),'associated_words':len(result['associated_word_ids']),'unassociated_words':len(result['unassociated_word_ids']),'no_full_reading_order_claim':not result['whole_publication_reading_order_qualified']},indent=2))
