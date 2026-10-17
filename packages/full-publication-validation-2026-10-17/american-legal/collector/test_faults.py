#!/usr/bin/env python3
"""Network-free faults exercise production collection, caches, resume and independent nested TOC verifier."""
import argparse,contextlib,copy,hashlib,io,json,shutil,tempfile
from pathlib import Path
from types import SimpleNamespace
import collect
from model import *
from transport import save
from verify import verify

def fixtures():
 identity={'client_slug':'fixturecity','jurisdiction':'Fixture City','state':'OH','version_uuid':'fixture-edition-1','version_name':'Fixture edition','currency_info':'Synthetic fault fixture only','code_uuid':'fixture-code','code_slug':'fixture_code','code_title':'Fixture Code','is_pdf':False}
 roots=[{'id':1,'doc_id':'ROOT','title':'Fixture Code','has_children':True}];code={'uuid':'fixture-code','slug':'fixture_code','title':'Fixture Code','is_pdf':False,'sections':roots}
 version={'uuid':'fixture-edition-1','name':'Fixture edition','currency_info':'Synthetic fault fixture only','client_slug':'fixturecity','toc':[code]}
 state={'codes':{'currClient':{'slug':'fixturecity','name':'Fixture City','region':{'slug':'oh'}},'selectedVersion':version}}
 overview=('<html><script>window._redux_state = JSON.parse('+json.dumps(json.dumps(state))+')</script></html>').encode()
 nodes={1:{'id':1,'doc_id':'ROOT','code_uuid':'fixture-code','children':[{'id':2,'doc_id':'BRANCH','title':'TITLE II','has_children':True,'parent_doc_id':'ROOT'},{'id':3,'doc_id':'LEAF-A','title':'Sec. 1 First rule','has_children':False,'parent_doc_id':'ROOT'}]},2:{'id':2,'doc_id':'BRANCH','code_uuid':'fixture-code','children':[{'id':4,'doc_id':'LEAF-B','title':'Sec. 2 Middle rule','has_children':False,'parent_doc_id':'BRANCH'},{'id':5,'doc_id':'LEAF-C','title':'Sec. 3 Last rule','has_children':False,'parent_doc_id':'BRANCH'}]}}
 raw={'https://codelibrary.amlegal.com/codes/fixturecity/latest/overview':overview}
 for n,v in nodes.items():raw[f'https://codelibrary.amlegal.com/api/section-toc/{n}/']=json.dumps(v).encode()
 # Real parser structures, nested table/cell boundaries and span attributes are deliberately exercised.
 for n,did,title in [(1,'ROOT','Fixture Code'),(2,'BRANCH','TITLE II'),(3,'LEAF-A','Sec. 1 First rule'),(4,'LEAF-B','Sec. 2 Middle rule'),(5,'LEAF-C','Sec. 3 Last rule')]:
  table='<table><tr><th colspan="2">Uses</th></tr><tr><td>Allowed</td><td>Restricted</td></tr></table>' if n==4 else ''
  asset='<img src="https://files.amlegal.com/fixture.png">' if n==3 else ''
  html=f'<div><div id="rid-{did}" className="Section">{title}</div><div id="rid-{did}-body">Operative provision {n} has its own body.{table}{asset}</div></div>'
  raw[f'https://codelibrary.amlegal.com/api/render-section/fixturecity/fixture-edition-1/fixture_code/{did}/0/']=json.dumps({'id':n,'doc_id':did,'title':title,'html':html}).encode()
 from PIL import Image
 out=io.BytesIO();Image.new('RGB',(1,1)).save(out,format='PNG');raw['https://files.amlegal.com/fixture.png']=out.getvalue()
 return raw
class FakeBrowser:
 sources=fixtures();interrupt_after=None;wrong_resume=False;render_calls=0;calls=[]
 def __init__(self):type(self).render_calls=0;type(self).calls=[]
 def call(self,op,url=None,**kw):
  cls=type(self);cls.calls.append((op,url))
  if '/render-section/' in (url or ''):
   cls.render_calls+=1
   if cls.interrupt_after is not None and cls.render_calls>cls.interrupt_after:raise KeyboardInterrupt('Injected durable interruption')
  b=cls.sources[url]
  if cls.wrong_resume and '/overview' in url:b=b.replace(b'fixture-edition-1',b'fixture-edition-2')
  import base64
  return {'body':base64.b64encode(b).decode(),'url':url,'status':200,'headers':{'content-type':'image/png' if url.endswith('.png') else 'text/html' if 'overview' in url else 'application/json'},'browser':'synthetic-no-network','runtime':'synthetic'}
 def close(self):pass

def args(path,resume=False,limit=None):return SimpleNamespace(out=path,resume=resume,url='https://codelibrary.amlegal.com/codes/fixturecity/latest/overview',jurisdiction='Fixture City',state='OH',publication='fixture_code',identity_alias=[],assets='download',strategy='traverse',max_items=limit)
def execute(a):
 with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):return collect.run(a)
def expect_reject(folder):
 try:
  report=verify(folder)
  assert not report['publication_complete'],'Fault incorrectly passed as complete'
 except (AssertionError,KeyError,ValueError,FileNotFoundError,json.JSONDecodeError):return
 raise AssertionError('Fault was not rejected')
def run_tests(out=None):
 receipt={'schema_version':1,'test_kind':'synthetic production-path fault injection; not live publication proof','tests':[]}
 original=collect.Browser;collect.Browser=FakeBrowser
 try:
  with tempfile.TemporaryDirectory(prefix='amlegal-faults-') as tmp:
   root=Path(tmp);baseline=root/'baseline';FakeBrowser.interrupt_after=None;assert execute(args(baseline))==0;report=verify(baseline);assert report['publication_complete'] and report['independently_recomputed_branch_count']==2 and report['table_count']==1;receipt['tests'].append({'name':'positive_nested_independent_inventory','passed':True,'nodes':5,'branches':2,'table_cells':3})
   assert not any(op in ['binary','head'] and url.endswith('.png') for op,url in FakeBrowser.calls),'Image network request occurred';assert '[IMAGE]' in (baseline/'sections.jsonl').read_text();receipt['tests'].append({'name':'production_no_image_fetch_literal_placeholder','passed':True})
   def fault(name,fn):
    folder=root/name;shutil.copytree(baseline,folder);fn(folder);expect_reject(folder);receipt['tests'].append({'name':name,'passed':True})
   fault('omitted_normalized_middle_record',lambda d:(d/'sections.jsonl').write_bytes(b'\n'.join((d/'sections.jsonl').read_bytes().splitlines()[:3])+b'\n'))
   fault('duplicated_normalized_record',lambda d:(d/'sections.jsonl').write_bytes((d/'sections.jsonl').read_bytes()+(d/'sections.jsonl').read_bytes().splitlines()[0]+b'\n'))
   fault('corrupt_retained_body',lambda d:(d/json.loads((d/'requests.json').read_text())['fetch:https://codelibrary.amlegal.com/api/render-section/fixturecity/fixture-edition-1/fixture_code/LEAF-B/0/']['file']).write_bytes(b'corrupt'))
   def remove_branch(d):
    inv=json.loads((d/'inventory.json').read_text());inv['nodes']=[n for n in inv['nodes'] if n['document_id']!='LEAF-B'];save(d/'inventory.json',inv)
   fault('middle_branch_omission_all_top_roots_retained',remove_branch)
   def edition(d):
    req=json.loads((d/'requests.json').read_text());e=req['overview-start'];data=(d/e['file']).read_bytes().replace(b'fixture-edition-1',b'fixture-edition-2');(d/e['file']).write_bytes(data);e['sha256']=digest(data);save(d/'requests.json',req)
   fault('wrong_edition_source_with_updated_cache_hash',edition)
   def interrupted(d):
    m=json.loads((d/'run.json').read_text());m['status']='interrupted';save(d/'run.json',m)
   fault('interrupted_run_with_complete_looking_outputs',interrupted)
   fault('missing_required_asset_ledger_entry',lambda d:save(d/'assets.json',[]))
   fault('corrupted_checkpoint_inventory_binding',lambda d:save(d/'checkpoint.json',{'inventory_sha256':'wrong','acquired_ids':[]}))
   good_native='<html><body>'+''.join(json.loads(FakeBrowser.sources[f'https://codelibrary.amlegal.com/api/render-section/fixturecity/fixture-edition-1/fixture_code/{n["document_id"]}/0/'])['html'] for n in json.loads((baseline/'inventory.json').read_text())['nodes'])+'</body></html>'
   native_good=native_records(good_native.encode(),json.loads((baseline/'inventory.json').read_text()),report['publication_identity'],'https://export.amlegal.com/fixture','fixture');assert len(native_good)==5 and len({b for r in native_good for b in r['body_block_ids']})==10;assert '[IMAGE]' in ''.join(r['text'] for r in native_good);receipt['tests'].append({'name':'positive_nested_native_partition_exact_once_with_images','passed':True})
   # A native export retaining every top-level root but omitting a middle nested provision must fail.
   identity=report['publication_identity'];inventory=json.loads((baseline/'inventory.json').read_text());html='<html><body>'+''.join(json.loads(v)['html'] for v in [] )+'</body></html>'
   parts=[]
   for n in inventory['nodes']:
    if n['document_id']=='LEAF-B':continue
    parts.append(f'<div id="rid-{n["document_id"]}">{n["heading"]}</div><div id="rid-{n["document_id"]}-body">Own source.</div>')
   try:native_records(('<html><body>'+''.join(parts)+'</body></html>').encode(),inventory,identity,'https://export.amlegal.com/fixture','fixture');raise RuntimeError('Truncated native passed')
   except AssertionError:receipt['tests'].append({'name':'truncated_native_export_keeps_all_top_roots','passed':True})
   resumed=root/'resumed';FakeBrowser.interrupt_after=2;assert execute(args(resumed))==2;expect_reject(resumed);checkpoint=json.loads((resumed/'checkpoint.json').read_text());assert len(checkpoint['acquired_ids'])==2
   FakeBrowser.interrupt_after=None;assert execute(args(resumed,resume=True))==0;assert FakeBrowser.render_calls==3,'Resume refetched completed legal bodies';verify(resumed)
   for name in ['sections.jsonl','sections.csv','pdf-pages.jsonl','inventory.json']:assert (resumed/name).read_bytes()==(baseline/name).read_bytes(),'Resume output differs'
   receipt['tests'].append({'name':'production_interruption_resume_vs_uninterrupted','passed':True,'durably_completed_before_interrupt':2,'resumed_legal_requests':3,'total_nodes':5})
   wrong=root/'wrong-resume';shutil.copytree(resumed,wrong);FakeBrowser.wrong_resume=True;assert execute(args(wrong,resume=True))==2;expect_reject(wrong);FakeBrowser.wrong_resume=False;receipt['tests'].append({'name':'resume_rejects_changed_live_edition','passed':True})
   limited=root/'limited';assert execute(args(limited,limit=2))==2;limited_report=verify(limited);assert not limited_report['publication_complete'] and not limited_report['inventory_complete'];receipt['tests'].append({'name':'explicit_limit_cannot_complete','passed':True})
   mixed='<p>Before.</p><img id="image-id" src="raster.png"><picture><source srcset="a.png 1x,b.png 2x"><img src="fallback.png"></picture><svg><image href="map.png"/><use xlink:href="symbol.svg#x"/></svg><p style="background-image:url(background.png)">CSS text</p><style>.x{background:url(sheet.png)}</style><video poster="poster.png"></video><object type="image/png" data="data:image/png;base64,AAAA"></object><table><tr><td>Outer<img src="cell.png"><table><tr><td>Inner<img src="nested.png"></td></tr></table></td></tr></table><p>After.</p>'
   item={'document_id':'A','internal_id':99,'heading':'Section A','path':['Section A'],'parent_id':None,'has_children':False};record=html_record({'doc_id':'A','id':99,'html':'<h2 id="rid-A">Section A</h2>'+mixed},item,{},'https://example.invalid/','fixture');html=record['html'];assert '[IMAGE]' in html and 'id="image-id"' in html;assert not re.search(r'<(?:img|picture|svg|image|use)\b|data:image/|url\s*\(|poster=',html,re.I);assert len(record['tables'])==2 and record['table_parent_indices']==[None,0];assert '[IMAGE]' in record['tables'][1][0][0]['text'];assert record['text'].count('[IMAGE]')>=8;assert all(a['disposition']=='image-placeholder' for a in record['assets']);receipt['tests'].append({'name':'mixed_images_svg_srcset_css_poster_objects_nested_cells','passed':True})
   only=html_record({'doc_id':'A','id':99,'html':'<h2 id="rid-A">Section A</h2><img src="map.png">'},item,{},'https://example.invalid/','fixture');assert only['content_classification']=='intentional-image-placeholder' and '[IMAGE]' in only['text'];receipt['tests'].append({'name':'image_only_is_intentional_not_incomplete','passed':True})
   adopted=refs('<p>Official Standard is incorporated by reference <a href="https://example.invalid/document/123">Standard</a></p>','https://example.invalid/')[0];assert any(a['url'].endswith('/document/123') and a['disposition']=='required-asset' for a in adopted);receipt['tests'].append({'name':'explicit_extensionless_nonimage_incorporation_required','passed':True})
   from compare import comparisons
   complete=[json.loads(v) for v in (baseline/'sections.jsonl').read_bytes().splitlines()];changed=copy.deepcopy(complete);changed[3]['text']=changed[3]['heading']+'partial paragraph';assert not all(r['passed'] for r in comparisons(changed,complete));receipt['tests'].append({'name':'full_renderer_comparison_rejects_body_truncation_with_all_ids','passed':True})
   class TypeCache:
    def __init__(self,mime,body=b''):self.mime=mime;self.body=body;self.calls=[]
    def fetch(self,url,op='fetch'):
     self.calls.append((op,url));return (b'' if op=='head' else self.body),{'response':{'url':url,'headers':{'content-type':self.mime}},'file':'fixture','sha256':digest(self.body),'bytes':len(self.body)}
   cache=TypeCache('image/png');ledger={};asset=collect.asset_fetch('https://example.invalid/document/123',cache,ledger,'download','attachment');assert asset['status']=='image-placeholder' and cache.calls==[('head','https://example.invalid/document/123')];receipt['tests'].append({'name':'extensionless_image_HEAD_only_no_GET','passed':True})
   cache=TypeCache('application/octet-stream');ledger={};asset=collect.asset_fetch('https://example.invalid/document/123',cache,ledger,'download','attachment');assert asset['status']=='unresolved-type' and len(cache.calls)==1;receipt['tests'].append({'name':'ambiguous_mime_never_grabs_possible_image_body','passed':True})
   cache=TypeCache('text/css',b'.x{background:url(data:image/png;base64,AAAA)}');ledger={};collect.asset_fetch('https://example.invalid/style.css',cache,ledger,'download','stylesheet');assert any(v['status']=='image-placeholder' and u.startswith('inline-image:') for u,v in ledger.items());assert all('base64' not in u for u in ledger);assert len(cache.calls)==2;receipt['tests'].append({'name':'CSS_inline_image_reference_hash_no_binary_fetch','passed':True})
   if out:
    import zipfile
    fixture=Path(out).parent/'fixtures'/'nested-synthetic.zip';fixture.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(fixture,'w',zipfile.ZIP_DEFLATED) as z:
     for p in baseline.rglob('*'):
      if p.is_file():z.write(p,str(p.relative_to(baseline)))
 finally:collect.Browser=original
 receipt['passed']=all(t['passed'] for t in receipt['tests']);receipt['count']=len(receipt['tests'])
 if out:save(Path(out),receipt)
 print(json.dumps(receipt,indent=2));return receipt
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--receipt',type=Path);a=p.parse_args();run_tests(a.receipt)
