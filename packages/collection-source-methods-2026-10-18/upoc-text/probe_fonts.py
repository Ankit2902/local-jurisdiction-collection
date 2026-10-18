"""Bounded PDF font/CMap metadata only under corrected no-image native guards."""
import hashlib,io,json,pathlib,sys,time
P=pathlib.Path(__file__).resolve().parents[3];R=P/'github/local-jurisdiction-collection';sys.path.insert(0,str(R))
from collectors.encodeplus import retained_native
from pypdf import PdfReader
from fontTools.ttLib import TTFont
S=R/'packages/collection-dispatch-and-municipal-2026-10-18/upoc-2024/actual-retained-full172';O=pathlib.Path(__file__).resolve().parent
h=lambda data:hashlib.sha256(data).hexdigest()
assert h((R/'collectors/encodeplus/retained_native.py').read_bytes())=='f7ef2d7ec3e12454c13be9fcb099c93f806b0a3ed451501bfc84f8707bb04bf3'
data=(S/'raw/source.pdf').read_bytes();assert h(data)=='877c6e874d4de7873d22dd51443fd5c42169445ad2955db3836841a105a57102'
report={'source_sha256':h(data),'guard_sha256':h((R/'collectors/encodeplus/retained_native.py').read_bytes()),'selected_pages':[7,9,12,100],'fonts':{},'pages':[]};t=time.monotonic()
with retained_native.guards() as calls:
 reader=PdfReader(io.BytesIO(data),strict=True);assert len(reader.pages)==172
 for number in report['selected_pages']:
  page=reader.pages[number-1];fonts=page['/Resources'].get('/Font',{});pagefonts=[]
  for resource,ref in fonts.items():
   f=ref.get_object();key=str(ref);pagefonts.append({'resource':str(resource),'font_ref':key})
   if key in report['fonts']:continue
   item={'resource':str(resource),'font_ref':key,'font_keys':list(f),'subtype':str(f.get('/Subtype')),'basefont':str(f.get('/BaseFont')),'encoding':str(f.get('/Encoding'))}
   if f.get('/ToUnicode'):
    cm=f['/ToUnicode'].get_data();item['ToUnicode']={'sha256':h(cm),'bytes':len(cm),'text':cm.decode('latin1')}
   descendants=f.get('/DescendantFonts') or [f]
   for idx,dref in enumerate(descendants):
    d=dref.get_object();item['descendant_keys']=list(d);item['cid_system_info']=str(d.get('/CIDSystemInfo'));item['cid_to_gid_map']=str(d.get('/CIDToGIDMap'))
    if d.get('/CIDToGIDMap') and hasattr(d['/CIDToGIDMap'],'get_data'):
     m=d['/CIDToGIDMap'].get_data();item['cid_gid_map']={'sha256':h(m),'bytes':len(m),'nonzero_pairs':[[i//2,int.from_bytes(m[i:i+2],'big')] for i in range(0,len(m),2) if int.from_bytes(m[i:i+2],'big')]}
    fd=d.get('/FontDescriptor');fd=fd.get_object() if fd else None
    if not fd:continue
    item['descriptor']={str(k):str(v) for k,v in fd.items() if k not in ['/FontFile','/FontFile2','/FontFile3']}
    for name in ['/FontFile','/FontFile2','/FontFile3']:
     if name not in fd:continue
     fb=fd[name].get_data();meta={'name':name,'sha256':h(fb),'bytes':len(fb),'stream_subtype':str(fd[name].get('/Subtype'))}
     try:
      font=TTFont(io.BytesIO(fb));meta['tables']=list(font.keys());meta['glyph_order']=font.getGlyphOrder();meta['cmaps']=[{'platform':c.platformID,'encoding':c.platEncID,'format':c.format,'unicode':c.isUnicode(),'mapping':{str(k):v for k,v in c.cmap.items()}} for c in font['cmap'].tables] if 'cmap' in font else [];meta['best_cmap']={str(k):v for k,v in (font.getBestCmap() or {}).items()};font.close()
     except Exception as exc:meta['font_parse_error']=type(exc).__name__+':'+str(exc)
     item['embedded_font']=meta
   report['fonts'][key]=item
  report['pages'].append({'physical_page':number,'fonts':pagefonts})
 report['forbidden_calls']=calls[:]
assert not report['forbidden_calls'];report['seconds']=time.monotonic()-t;report['executed_source_sha256']=h(pathlib.Path(__file__).read_bytes())
(O/'bounded-font-probe.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'fonts':len(report['fonts']),'seconds':report['seconds'],'forbidden_calls':calls,'font_summaries':[{k:v for k,v in f.items() if k not in ['embedded_font','cid_gid_map','ToUnicode']}|{'font_cmap_entries':len(f.get('embedded_font',{}).get('best_cmap',{})),'has_ToUnicode':'ToUnicode'in f} for f in report['fonts'].values()]},indent=2))
