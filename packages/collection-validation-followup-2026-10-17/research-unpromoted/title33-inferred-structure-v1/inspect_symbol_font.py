"""Exact existing embedded-font provenance, no glyph rendering or substitution."""
import hashlib,io,json,re,sys
from pathlib import Path
from pypdf import PdfReader
from fontTools.ttLib import TTFont
BASE=Path(__file__).resolve().parent;root=Path(sys.argv[1]);s=json.loads((BASE/'sources.json').read_text());data=(root/s['native_source_path']).read_bytes();assert hashlib.sha256(data).hexdigest()==s['native_sha256'];r=PdfReader(io.BytesIO(data));page=r.pages[1287];font=page['/Resources']['/Font']['/C2_2'].get_object();cidfont=font['/DescendantFonts'][0].get_object();descriptor=cidfont['/FontDescriptor'].get_object();tounicode=font['/ToUnicode'].get_data();program=descriptor['/FontFile2'].get_data();tt=TTFont(io.BytesIO(program));mapping=cidfont.get('/CIDToGIDMap');mapdata=mapping.get_object().get_data() if hasattr(mapping,'get_object') and hasattr(mapping.get_object(),'get_data') else None
# This diagnostic does not replace the original private-use Unicode. It records
# whether the source itself explicitly maps it and names its embedded glyph.
records=[]
for m in re.finditer(rb'<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>',tounicode):
 code,unicode=int(m.group(1),16),int(m.group(2),16)
 if unicode!=0xf0b7:continue
 gid=int.from_bytes(mapdata[code*2:code*2+2],'big') if mapdata is not None else code if str(mapping)=='/Identity' else None
 records.append({'source_code':code,'source_code_hex':m.group(1).decode(),'source_ToUnicode':unicode,'glyph_id':gid,'embedded_glyph_name':tt.getGlyphOrder()[gid] if gid is not None else None})
report={'native_source_sha256':s['native_sha256'],'physical_page':1288,'font_resource_name':'/C2_2','font_object_id':getattr(page['/Resources']['/Font'].raw_get('/C2_2'),'idnum',None),'BaseFont':str(font['/BaseFont']),'descendant_BaseFont':str(cidfont['/BaseFont']),'FontDescriptor_FontName':str(descriptor['/FontName']),'ToUnicode_sha256':hashlib.sha256(tounicode).hexdigest(),'ToUnicode_source':tounicode.decode('latin1'),'embedded_FontFile2_sha256':hashlib.sha256(program).hexdigest(),'CIDToGIDMap_sha256':hashlib.sha256(mapdata).hexdigest() if mapdata is not None else str(mapping),'private_use_records':records,'cmap_names_for_F0B7':[{'platformID':t.platformID,'platEncID':t.platEncID,'glyph_name':t.cmap[0xf0b7]} for t in (tt['cmap'].tables if 'cmap' in tt else []) if 0xf0b7 in t.cmap],'embedded_font_tables':list(tt.keys()),'embedded_font_has_cmap':'cmap' in tt,'literal_private_use_codepoint_retained':True,'Unicode_substitution_applied':False,'image_render_decode_or_OCR_calls':0,'scope':'Source-defined symbol proof only; no blanket private-use exemption or whole-publication claim'}
print(json.dumps(report,indent=2))
