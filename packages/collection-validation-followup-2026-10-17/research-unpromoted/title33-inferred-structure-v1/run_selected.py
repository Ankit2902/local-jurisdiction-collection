"""Narrow original-source selected-page run. Never a full publication replay."""
import collections,hashlib,importlib.util,json,socket,sys
from pathlib import Path
from unittest.mock import patch
from pdfminer.pdftypes import PDFStream
import pypdfium2
BASE=Path(__file__).resolve().parent;ROOT=Path(sys.argv[1]);module_path=BASE/sys.argv[2];out=BASE/sys.argv[3];assert not out.exists();source=json.loads((BASE/'sources.json').read_text());data=(ROOT/source['native_source_path']).read_bytes();assert hashlib.sha256(data).hexdigest()==source['native_sha256'];spec=importlib.util.spec_from_file_location('selected',module_path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
run=ROOT/'outputs/collection-readiness-2026-10-17/official/portland-title33-full';checkpoint=json.loads((run/'checkpoint.json').read_text());config=json.loads((run/'config.json').read_text());item=next(i for i in checkpoint['items'] if i.get('kind')=='pdf');original=PDFStream.get_data

def guarded(self,*a,**kw):
 assert getattr(self.get('Subtype'),'name',None)!='Image','Image stream decoding forbidden';return original(self,*a,**kw)
with patch.object(PDFStream,'get_data',guarded),patch.object(pypdfium2.PdfPage,'render',side_effect=AssertionError('Raster render forbidden')),patch('PIL.Image.open',side_effect=AssertionError('Image decoder forbidden')),patch.object(socket.socket,'connect',side_effect=AssertionError('Network forbidden')):
 rows,_=module.pages(data,item,config,selected_pages=set(source['selected_physical_pages']))
assert [r['physical_page'] for r in rows]==source['selected_physical_pages'];out.write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rows));print(json.dumps({'passed':True,'kind':'Selected original physical pages only, not full publication validation','source_native_sha256':source['native_sha256'],'parser_sha256':hashlib.sha256(module_path.read_bytes()).hexdigest(),'page_summaries':[{'page':r['physical_page'],'words':r['pdf_qualification']['source_word_count'],'word_ownership':r['pdf_qualification']['source_word_ownership_complete'],'source_glyphs':r['pdf_qualification']['source_words_cover_deduplicated_glyph_characters'],'canonical_text':r['pdf_qualification']['normalized_source_word_characters_agree'],'cells':r['pdf_qualification']['detected_table_cells'],'agree_cells':r['pdf_qualification']['independent_table_cells_agree'],'flags':r['pdf_qualification']['review_conditions']} for r in rows],'image_stream_decode_calls':0,'image_render_calls':0,'network_requests':0},indent=2))
