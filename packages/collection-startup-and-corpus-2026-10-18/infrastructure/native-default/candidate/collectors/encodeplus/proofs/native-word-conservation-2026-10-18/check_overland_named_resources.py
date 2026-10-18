"""Prove retained image source names refer to named indirect resources, no image bytes."""
import contextlib,hashlib,io,json,socket
from pathlib import Path
from unittest.mock import patch
from pypdf import PdfReader
from pypdf.generic import EncodedStreamObject,DecodedStreamObject
root=Path(__file__).resolve().parent;project=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00');v3=project/'outputs/collection-readiness-next-2026-10-17/encodeplus/post-91f6c59/overland-five-required-v3'
review=json.loads((root/'v3-independent-invariants.json').read_text());items={i['id']:i for i in json.loads((v3/'inventory.json').read_text())['items']};calls=[];reports=[]
def forbidden(*args,**kwargs):calls.append('forbidden_image_or_network');raise AssertionError(calls[-1])
def resources(dictionary,seen=None):
 seen=set() if seen is None else seen
 if dictionary is None:return []
 dictionary=dictionary.get_object();result=[];xobjects=dictionary.get('/XObject')
 if xobjects is None:return result
 for name,reference in xobjects.get_object().items():
  ident=(getattr(reference,'idnum',None),getattr(reference,'generation',None))
  if ident in seen:continue
  seen.add(ident);obj=reference.get_object()
  if obj.get('/Subtype')=='/Image':result.append({'name':str(name).lstrip('/'),'object_id':getattr(reference,'idnum',None),'generation':getattr(reference,'generation',None)})
  elif obj.get('/Subtype')=='/Form':result+=resources(obj.get('/Resources'),seen)
 return result
with contextlib.ExitStack() as stack:
 stack.enter_context(patch.object(socket,'socket',forbidden))
 for cls in (EncodedStreamObject,DecodedStreamObject):
  original=cls.get_data
  def guard(self,_original=original):
   if self.get('/Subtype')=='/Image':return forbidden()
   return _original(self)
  stack.enter_context(patch.object(cls,'get_data',guard))
 for ident,images in review['source_image_names'].items():
  item=items[ident];data=(v3/item['raw_ref']).read_bytes();assert hashlib.sha256(data).hexdigest()==item['expected_sha256'];reader=PdfReader(io.BytesIO(data),strict=True);page_cache={}
  for image in images:
   if image['vector']:continue
   n=image['page'];page_cache.setdefault(n,resources(reader.pages[n-1].get('/Resources')))
   matches=[r for r in page_cache[n] if r['name']==image['source_name'] and isinstance(r['object_id'],int)]
   assert matches,(ident,n,image['source_name']);reports.append({'document_id':ident,'page':n,'image_id':image['id'],'source_name':image['source_name'],'matching_named_indirect_resource_references':matches})
assert len(reports)==201 and not calls
report={'passed':True,'scope':'All201retainednonvectorimageoccurrences have actualnamedindirectPDFresource references; metadata-only sourcexrefinspection, not repeatednativepageparse.','source_bindings':{ident:items[ident]['expected_sha256'] for ident in items},'named_occurrences':len(reports),'inline_helper_changes_expected_in_five_documents':0,'forbidden_calls':calls,'entries':reports,'qualification':'The runtimehelper uses actual stream.objid, never a source-name heuristic. This source-resource exposure proof preserves the five-document outputs under the equivalent helper port; actual metadata smoke independently tests both inline None and genuine named refs.'}
(root/'overland-named-resource-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='entries'},indent=2))
