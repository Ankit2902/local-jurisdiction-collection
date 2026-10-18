"""Raw sfnt glyph-program identity only: no glyph outline/point decoding or rendering."""
import hashlib,io,json,pathlib,struct,sys,time
P=pathlib.Path(__file__).resolve().parents[3];R=P/'github/local-jurisdiction-collection';sys.path.insert(0,str(R))
from collectors.encodeplus import retained_native
from pypdf import PdfReader
O=pathlib.Path(__file__).resolve().parent;S=R/'packages/collection-dispatch-and-municipal-2026-10-18/upoc-2024/actual-retained-full172';sha=lambda b:hashlib.sha256(b).hexdigest();data=(S/'raw/source.pdf').read_bytes()
assert sha(data)=='877c6e874d4de7873d22dd51443fd5c42169445ad2955db3836841a105a57102'
assert sha((R/'collectors/encodeplus/retained_native.py').read_bytes())=='f7ef2d7ec3e12454c13be9fcb099c93f806b0a3ed451501bfc84f8707bb04bf3'
inventory=json.loads((O/'font-resource-inventory.json').read_text());observed=json.loads((O/'bounded-used-code-probe.json').read_text());t=time.monotonic()
def sfnt(b):
 assert b[:4]==b'\0\1\0\0';nt=struct.unpack_from('>H',b,4)[0];tables={}
 for i in range(nt):
  tag,checksum,off,n=struct.unpack_from('>4sIII',b,12+16*i);assert off+n<=len(b);tables[tag.decode('latin1')]=b[off:off+n]
 ng=struct.unpack_from('>H',tables['maxp'],4)[0];locfmt=struct.unpack_from('>h',tables['head'],50)[0];size=2 if locfmt==0 else 4;fmt='>H' if size==2 else '>I';off=[struct.unpack_from(fmt,tables['loca'],i*size)[0]*(2 if size==2 else 1) for i in range(ng+1)];nh=struct.unpack_from('>H',tables['hhea'],34)[0]
 def glyph(g):return tables['glyf'][off[g]:off[g+1]]
 def metrics(g):return list(struct.unpack_from('>Hh',tables['hmtx'],4*g)) if g<nh else [struct.unpack_from('>H',tables['hmtx'],4*(nh-1))[0],struct.unpack_from('>h',tables['hmtx'],4*nh+2*(g-nh))[0]]
 return {'tables':tables,'numglyphs':ng,'unitsPerEm':struct.unpack_from('>H',tables['head'],18)[0],'glyph':glyph,'metrics':metrics}
with retained_native.guards() as calls:
 reader=PdfReader(io.BytesIO(data),strict=True);rawfonts={}
 for obj in [620,623,628,626,906]:
  f=reader.get_object(obj);desc=f.get('/DescendantFonts');d=desc[0].get_object() if desc else f;fd=d['/FontDescriptor'];fb=fd['/FontFile2'].get_data();rawfonts[str(obj)+':0']=(fb,sfnt(fb))
 results=[]
 for bad,good in [('620:0','623:0'),('628:0','626:0')]:
  bb,b=rawfonts[bad];gb,g=rawfonts[good];known=inventory['fonts'][good]['font_program']['unicode_gid_pairs'];entries=[];reject=[]
  global_equal={key:sha(b['tables'].get(key,b''))==sha(g['tables'].get(key,b'')) for key in ['fpgm','prep','cvt ']};assert all(global_equal.values()) and b['unitsPerEm']==g['unitsPerEm']
  for uni,gid in known.items():
   gid=int(gid);program=g['glyph'](gid);matches=[x for x in range(b['numglyphs']) if program and b['glyph'](x)==program and b['metrics'](x)==g['metrics'](gid)]
   simple=bool(program) and struct.unpack_from('>h',program,0)[0]>0
   if len(matches)==1 and simple:
    entries.append({'source_font_object':bad,'source_CID':matches[0],'source_CIDToGIDMap':'Identity','Unicode':chr(int(uni)),'Unicode_codepoint':int(uni),'witness_font_object':good,'witness_gid':gid,'witness_basis':'Embedded Unicode cmap; unique byte-identical non-composite raw glyph program and identical raw hmtx/hint-table/unitsPerEm metadata. No character recognition.','raw_glyph_program_sha256':sha(program),'raw_glyph_program_bytes':len(program),'hmtx':g['metrics'](gid)})
   else:reject.append({'Unicode_codepoint':int(uni),'witness_gid':gid,'match_gids':matches,'reason':'No unique nonempty/simple source raw glyph program identity; no extrapolation'})
  used=sorted({z['cid'] for p in observed['pages'] for z in p['glyphs'] if str(z['font_object'])+':0'==bad});mapped={e['source_CID'] for e in entries}
  results.append({'missing_map_font':bad,'same_family_witness_font':good,'source_font_program_sha256':sha(bb),'witness_font_program_sha256':sha(gb),'global_hint_tables_equal':global_equal,'unitsPerEm':b['unitsPerEm'],'entries':entries,'rejected_witness_entries':reject,'bounded_observed_CIDs':used,'bounded_unresolved_CIDs':sorted(set(used)-mapped),'complete_mapping_proven':False})
 root=reader.trailer['/Root'];st=root['/StructTreeRoot'];k=st.get('/K');report={'source_sha256':sha(data),'scope':'Finite partial mapping witnesses from same original source fonts only; no text rewritten','mapping_results':results,'StructTreeRoot_keys':list(st),'StructTreeRoot_K_type':type(k).__name__,'StructTreeRoot_K_length':len(k) if isinstance(k,(list,dict)) else None,'source_MarkInfo':str(root.get('/MarkInfo')),'bounded_marked_content_tags_found':sum(len(p['marked_content_tags']) for p in observed['pages']),'forbidden_calls':calls[:],'fontTools_used_in_this_probe':False,'glyph_outline_or_point_decoding':False,'native_full_replay':False,'seconds':time.monotonic()-t,'executed_source_sha256':sha(pathlib.Path(__file__).read_bytes())}
assert not calls;(O/'raw-font-identity-mapping.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='mapping_results'}|{'mapping_summaries':[{'font':x['missing_map_font'],'proven_partial_entries':len(x['entries']),'bounded_used_CIDs':len(x['bounded_observed_CIDs']),'bounded_unresolved':x['bounded_unresolved_CIDs']} for x in results]},indent=2))
