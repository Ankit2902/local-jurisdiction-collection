"""All resource dictionaries, not page/glyph normalization. Guarded font-only stream metadata."""
import collections,hashlib,io,json,pathlib,sys,time
P=pathlib.Path(__file__).resolve().parents[3];R=P/'github/local-jurisdiction-collection';sys.path.insert(0,str(R))
from collectors.encodeplus import retained_native
from pypdf import PdfReader
from fontTools.ttLib import TTFont
from pdfminer.cmapdb import FileUnicodeMap,CMapParser
S=R/'packages/collection-dispatch-and-municipal-2026-10-18/upoc-2024/actual-retained-full172';O=pathlib.Path(__file__).resolve().parent;sha=lambda x:hashlib.sha256(x).hexdigest()
assert sha((R/'collectors/encodeplus/retained_native.py').read_bytes())=='f7ef2d7ec3e12454c13be9fcb099c93f806b0a3ed451501bfc84f8707bb04bf3'
data=(S/'raw/source.pdf').read_bytes();assert sha(data)=='877c6e874d4de7873d22dd51443fd5c42169445ad2955db3836841a105a57102';t=time.monotonic();fonts={};resources=[];fontstreams={}
def refid(x):
 ref=x if hasattr(x,'idnum') else getattr(x,'indirect_reference',None)
 return str(ref.idnum)+':'+str(ref.generation) if ref else 'direct'
with retained_native.guards() as calls:
 reader=PdfReader(io.BytesIO(data),strict=True)
 for pnum,page in enumerate(reader.pages,1):
  fs=page['/Resources'].get('/Font',{});fs=fs.get_object() if hasattr(fs,'get_object') else fs
  for resource in fs:
   rawref=fs.raw_get(resource);font=rawref.get_object();key=refid(rawref);resources.append({'page':pnum,'resource':str(resource),'font_object':key})
   if key in fonts:continue
   item={'object':key,'basefont':str(font.get('/BaseFont')),'subtype':str(font.get('/Subtype')),'encoding':str(font.get('/Encoding')),'ToUnicode':None}
   if font.get('/ToUnicode'):
    cm=font['/ToUnicode'].get_data();um=FileUnicodeMap();CMapParser(um,io.BytesIO(cm)).run();item['ToUnicode']={'object':refid(font.raw_get('/ToUnicode')),'sha256':sha(cm),'bytes':len(cm),'cid_to_unicode':{str(k):v for k,v in um.cid2unichr.items()}}
   desc=font.get('/DescendantFonts');d=desc[0].get_object() if desc else font;item['cid_to_gid']=str(d.get('/CIDToGIDMap'));fd=d.get('/FontDescriptor');fd=fd.get_object() if fd else None
   if fd:
    item['descriptor_name']=str(fd.get('/FontName'))
    for fk in ['/FontFile','/FontFile2','/FontFile3']:
     if fk not in fd:continue
     bs=fd[fk].get_data();fm={'object':refid(fd.raw_get(fk)),'kind':fk,'sha256':sha(bs),'bytes':len(bs)};fontstreams[fm['sha256']]=bs
     if fk=='/FontFile2':
      tt=TTFont(io.BytesIO(bs));order=tt.getGlyphOrder();fm['tables']=list(tt.keys());fm['glyph_count']=len(order);fm['unicode_gid_pairs']={str(k):tt.getGlyphID(v) for k,v in (tt.getBestCmap() if 'cmap' in tt else {}).items()};fm['glyph_name_gid_pairs']={n:i for i,n in enumerate(order) if not n.startswith('glyph') and n!='.notdef'}
      if 'glyf' in tt:
       fm['glyph_program_hashes']={str(i):sha(tt['glyf'][n].compile(tt['glyf'])) for i,n in enumerate(order) if tt['glyf'][n].numberOfContours!=0}
       fm['hmtx']={str(i):list(tt['hmtx'][n]) for i,n in enumerate(order) if tt['glyf'][n].numberOfContours!=0}
      tt.close()
     item['font_program']=fm
   fonts[key]=item
 report={'source_sha256':sha(data),'guard_sha256':sha((R/'collectors/encodeplus/retained_native.py').read_bytes()),'scope':'All172 page font resource dictionaries and font/CMap streams only; no page content parsing, glyph extraction, native normalized replay or images','resources':resources,'fonts':fonts,'forbidden_calls':calls[:],'seconds':time.monotonic()-t,'executed_source_sha256':sha(pathlib.Path(__file__).read_bytes())}
assert not calls;(O/'font-resource-inventory.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'fonts':len(fonts),'font_programs':len(fontstreams),'seconds':report['seconds'],'summary':[{k:f.get(k) for k in ['object','basefont','subtype','cid_to_gid']}|{'ToUnicode':len((f.get('ToUnicode')or{}).get('cid_to_unicode',{})),'cmap':len(f.get('font_program',{}).get('unicode_gid_pairs',{})),'used_pages':len({r['page'] for r in resources if r['font_object']==f['object']})} for f in fonts.values()]},indent=2))
