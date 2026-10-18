"""Bounded logical structure dictionaries only; never read page/image stream data."""
import collections,hashlib,io,json,pathlib,sys
P=pathlib.Path(__file__).resolve().parents[3];R=P/'github/local-jurisdiction-collection';sys.path.insert(0,str(R))
from collectors.encodeplus import retained_native
from pypdf import PdfReader
O=pathlib.Path(__file__).resolve().parent;S=R/'packages/collection-dispatch-and-municipal-2026-10-18/upoc-2024/actual-retained-full172';sha=lambda b:hashlib.sha256(b).hexdigest();data=(S/'raw/source.pdf').read_bytes()
assert sha(data)=='877c6e874d4de7873d22dd51443fd5c42169445ad2955db3836841a105a57102';assert sha((R/'collectors/encodeplus/retained_native.py').read_bytes())=='f7ef2d7ec3e12454c13be9fcb099c93f806b0a3ed451501bfc84f8707bb04bf3'
with retained_native.guards() as calls:
 r=PdfReader(io.BytesIO(data),strict=True);root=r.trailer['/Root']['/StructTreeRoot'];todo=[root.get('/K')];seen=set();roles=collections.Counter();texts=[];nodes=0;pages=[]
 while todo and nodes<1000:
  ref=todo.pop();obj=ref.get_object() if hasattr(ref,'get_object') else ref
  if isinstance(obj,list):todo.extend(reversed(obj));continue
  if not isinstance(obj,dict):continue
  oid=(getattr(ref,'idnum',None),getattr(ref,'generation',None)) if hasattr(ref,'idnum') else ('direct',id(obj))
  if oid in seen:continue
  seen.add(oid);nodes+=1;roles[str(obj.get('/S'))]+=1
  pg=obj.raw_get('/Pg') if '/Pg'in obj else None
  if pg is not None:pages.append(getattr(pg,'idnum',None))
  if '/ActualText'in obj:
   s=str(obj['/ActualText']);texts.append({'object':list(oid),'source_page_objid':getattr(pg,'idnum',None),'value_sha256':sha(s.encode()),'text':s if 'data:image/' not in s.lower() else '[IMAGE]','image_metadata_redacted':'data:image/'in s.lower()})
  if '/K'in obj:todo.append(obj.raw_get('/K'))
 report={'source_sha256':sha(data),'structure_dict_nodes':nodes,'pending_after1000cap':len(todo),'roles':dict(roles),'source_page_objids':sorted(set(p for p in pages if p is not None)),'ActualText':texts,'scope':'OnlyStructTreeRootKdictionary edges; no page or image stream reads, Alt fields/pixels/glyph outlines not consumed','forbidden_calls':calls[:],'executed_source_sha256':sha(pathlib.Path(__file__).read_bytes())}
assert not calls;(O/'structure-metadata-probe.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
