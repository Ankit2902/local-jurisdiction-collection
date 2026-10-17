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
   internal_html='<h2 id="rid-LEAF-A">Sec. 1 First rule</h2><p id="rid-LEAF-A-body">Standard is incorporated by reference <a href="https://codelibrary.amlegal.com/codes/fixturecity/latest/fixture_code/LEAF-B">Section2</a></p>'
   internal_item=next(n for n in inventory['nodes'] if n['document_id']=='LEAF-A');rec=html_record({'id':internal_item['internal_id'],'doc_id':'LEAF-A','html':internal_html},internal_item,identity,'https://example.invalid/','fixture');assert not rec['assets'] and len(rec['links'])==1;assert bind_reference_graph([rec],inventory)==[] and rec['links'][0]['target_retained'];receipt['tests'].append({'name':'same_publication_incorporation_binds_independent_target_not_external_asset','passed':True})
   bad=copy.deepcopy(rec);bad['links'][0]['target_document_id']='MISSING';assert len(bind_reference_graph([bad],inventory))==1 and not bad['links'][0]['target_retained'];receipt['tests'].append({'name':'missing_internal_reference_target_remains_unresolved','passed':True})
   other=internal_html.replace('/fixture_code/','/different_book/');otherrec=html_record({'id':internal_item['internal_id'],'doc_id':'LEAF-A','html':other},internal_item,identity,'https://example.invalid/','fixture');assert otherrec['assets'][0]['disposition']=='required-asset';receipt['tests'].append({'name':'other_publication_incorporation_still_required','passed':True})
   from transport import Cache,HTTPError,AccessStop
   class MissingBrowser:
    def call(self,op,url=None,**kw):return {'body':'Tm90IGZvdW5k','url':url,'status':404,'headers':{'content-type':'text/plain'}}
   missingcache=Cache(root/'missing-cache',MissingBrowser());ledger={};v=collect.asset_fetch('https://example.invalid/missing.pdf',missingcache,ledger,'download','attachment');assert v['status']=='unavailable' and v['http_status']==404 and (root/'missing-cache'/v['response_file']).read_bytes()==b'Not found';receipt['tests'].append({'name':'unavailable_nonimage_asset_retains_actual_HTTP_response_without_false_completeness','passed':True})
   class BlockCache:
    def fetch(self,*a,**kw):raise AccessStop('Synthetic family block')
   try:collect.asset_fetch('https://example.invalid/blocked.pdf',BlockCache(),{},'download','attachment');raise RuntimeError('Access stop was swallowed')
   except AccessStop:receipt['tests'].append({'name':'asset_access_block_is_fatal_family_stop','passed':True})
   from transport import RunLock
   locktarget=root/'exclusive-output'
   with RunLock(locktarget):
    try:
     with RunLock(locktarget):raise AssertionError('Concurrent output lock accepted')
    except RuntimeError:pass
   with RunLock(locktarget):pass
   receipt['tests'].append({'name':'concurrent_output_lock_rejects_second_writer_and_releases_after_exit','passed':True})
   import pymupdf
   document=pymupdf.open();page=document.new_page(width=400,height=500)
   for y in [100,130,160]:page.draw_line((50,y),(350,y))
   for x in [50,200,350]:page.draw_line((x,100),(x,160))
   for x,y,text in [(60,120,'Use'),(210,120,'Allowed'),(60,150,'Office'),(210,150,'Yes')]:page.insert_text((x,y),text)
   parsed=pdf_pages(document.tobytes(),'fixture-pdf','https://example.invalid/table.pdf')[0];layout=parsed['layout'];assert layout['independent_text_characters_equal'] and layout['image_binary_extraction_count']==0;table=next(t for t in layout['table_candidates'] if t['qualification']=='ruled-grid-geometry');assert table['row_count']==2 and table['column_count']==2 and [[c['text'] for c in row] for row in table['cells']]==[['Use','Allowed'],['Office','Yes']];assert '[IMAGE]' in parsed['text'];receipt['tests'].append({'name':'native_PDF_text_geometry_ruled_table_cells_no_image_extraction','passed':True})
   page2=document.new_page(width=400,height=500);page2.insert_textbox((50,100,170,200),'Left column line one. Left column line two.');page2.insert_textbox((230,100,350,200),'Right column line one. Right column line two.');parsed=pdf_pages(document.tobytes(),'fixture-pdf','https://example.invalid/columns.pdf')[1];assert parsed['layout']['parallel_text_block_pairs'] and not parsed['layout']['reading_order_qualified'];document.close();receipt['tests'].append({'name':'PDF_parallel_columns_require_explicit_reading_order_qualification','passed':True})
   document=pymupdf.open();document.new_page().insert_text((60,80),'Legal rule.');pdfbytes=document.tobytes();document.close();sha=digest(pdfbytes);assets={u:{'status':'retained','sha256':sha,'validation':{'kind':'pdf','pages':1}} for u in ['https://example.invalid/a.pdf','https://example.invalid/b.pdf']};normalized=[];reads=[]
   def read_pdf(a):reads.append(a['sha256']);return pdfbytes
   metadata=normalize_pdf_assets(assets,normalized,read_pdf);assert len(reads)==1 and len(normalized)==1 and metadata['https://example.invalid/b.pdf']['normalized_pdf_shared_bytes'] and not metadata['https://example.invalid/b.pdf']['normalized_pdf_page_ids'];receipt['tests'].append({'name':'required_PDF_attachments_normalize_all_pages_once_with_explicit_same_bytes_alias','passed':True})
   document=pymupdf.open();page=document.new_page(width=400,height=500)
   for y in [100,130,160,190]:page.draw_line((50,y),(350,y))
   for x in [50,350]:page.draw_line((x,100),(x,190))
   page.draw_line((200,130),(200,190))
   for x,y,text in [(60,120,'Uses'),(60,150,'Allowed'),(210,150,'Prohibited'),(60,180,'Office'),(210,180,'Factory')]:page.insert_text((x,y),text)
   parsed=pdf_pages(document.tobytes(),'merged-pdf','https://example.invalid/merged.pdf')[0];table=next(t for t in parsed['layout']['table_candidates'] if t['qualification']=='ruled-grid-geometry');assert table['cells'][0][0]['colspan']==2 and table['cells'][0][1] is None;document.close();receipt['tests'].append({'name':'native_PDF_merged_header_preserves_source_cell_colspan','passed':True})
   import base64
   class HeadUnsupportedBrowser:
    def __init__(self):self.calls=[]
    def call(self,op,url=None,**kw):
     self.calls.append(op);return {'body':base64.b64encode(b'HEAD unsupported' if op=='head' else pdfbytes).decode(),'url':url,'status':405 if op=='head' else 200,'headers':{'content-type':'text/plain' if op=='head' else 'application/pdf'}}
   hb=HeadUnsupportedBrowser();cache=Cache(root/'head-unsupported',hb);ledger={};asset=collect.asset_fetch('https://example.invalid/published.pdf',cache,ledger,'download','attachment');assert asset['status']=='retained' and asset['head_unsupported_status']==405 and hb.calls==['head','binary'];assert cache.entries['head:https://example.invalid/published.pdf']['response']['status']==405;receipt['tests'].append({'name':'known_nonimage_HEAD405_uses_real_GET_and_retains_both_source_receipts','passed':True})
   class RecoverBrowser:
    ready=False
    def call(self,op,url=None,**kw):return {'body':base64.b64encode(b'' if self.ready else b'Originally missing').decode(),'url':url,'status':200 if self.ready else 404,'headers':{'content-type':'application/pdf' if self.ready else 'text/plain'}}
   rb=RecoverBrowser();cache=Cache(root/'recover-cache',rb);url='https://example.invalid/recovered.pdf'
   try:cache.fetch(url,op='head');raise AssertionError('404 accepted')
   except HTTPError:pass
   old=copy.deepcopy(cache.entries['head:'+url]);rb.ready=True;cache.retry_unavailable_assets=True;_,entry=cache.fetch(url,op='head');assert entry['response']['status']==200 and (root/'recover-cache'/old['file']).read_bytes()==b'Originally missing' and any(k.startswith('history:') for k in cache.entries);receipt['tests'].append({'name':'explicit_unavailable_asset_retry_preserves_immutable_old_response_history','passed':True})
   class ExportBrowser(FakeBrowser):
    jobs_created=0;interrupt_once=True
    def call(self,op,url=None,**kw):
     if op!='export':return super().call(op,url,**kw)
     saved=kw.get('resume_export')
     if saved is None:
      type(self).jobs_created+=1;payload={'version':kw['version'],'scope':json.dumps([{'code_slug':kw['code_slug']}]),'output_format':'html','for_print':False};saved={'requested_url':url,'code_uuid':kw['code_uuid'],'code_slug':kw['code_slug'],'version':kw['version'],'payload':payload,'job':{'uuid':'synthetic-export-job','version':kw['version'],'for_print':False},'scope_html':'Synthetic whole-code checkbox scope','post_status':201};save(Path(kw['export_state_file']),saved)
      if type(self).interrupt_once:type(self).interrupt_once=False;raise KeyboardInterrupt('Injected after publisher job creation')
     assert saved['job']['uuid']=='synthetic-export-job';saved.update(status='downloaded',native_sha256=digest(good_native.encode()));save(Path(kw['export_state_file']),saved);return {'body':base64.b64encode(good_native.encode()).decode(),'url':'https://export.amlegal.com/api/export-requests/synthetic-export-job/download/','status':200,'headers':{'content-type':'text/html'},'payload':saved['payload'],'job':saved['job'],'scope_html':saved['scope_html'],'ready_html':'Synthetic ready job','post_status':201,'resumed_existing_job':True}
   collect.Browser=ExportBrowser;native_resume=root/'native-resume';na=args(native_resume);na.strategy='native';assert execute(na)==2 and (native_resume/'export-checkpoint.json').exists();na=args(native_resume,resume=True);na.strategy='native';assert execute(na)==0 and ExportBrowser.jobs_created==1;verify(native_resume);collect.Browser=FakeBrowser;receipt['tests'].append({'name':'interrupted_native_job_resumes_same_bound_UUID_without_new_publisher_POST','passed':True})
   for name,key,value in [('wrong_native_job_checkpoint_scope','code_slug','other_book'),('corrupt_native_job_checkpoint_bytes','native_sha256','wrong')]:
    folder=root/name;shutil.copytree(native_resume,folder);checkpoint=json.loads((folder/'export-checkpoint.json').read_text());checkpoint[key]=value;save(folder/'export-checkpoint.json',checkpoint);expect_reject(folder);receipt['tests'].append({'name':name,'passed':True})
   previous_sources=FakeBrowser.sources;FakeBrowser.sources=copy.deepcopy(previous_sources);url='https://codelibrary.amlegal.com/api/render-section/fixturecity/fixture-edition-1/fixture_code/LEAF-A/0/';payload=json.loads(FakeBrowser.sources[url]);payload['html']+='<p>Standard incorporated by reference <a href="https://codelibrary.amlegal.com/codes/fixturecity/latest/fixture_code/MISSING">Missing section</a></p>';FakeBrowser.sources[url]=json.dumps(payload).encode();broken=root/'broken-internal';assert execute(args(broken))==2;result=verify(broken);assert result['publication_text_complete'] and not result['internal_reference_complete'] and not result['publication_complete'];FakeBrowser.sources=previous_sources;receipt['tests'].append({'name':'production_missing_internal_citation_cannot_pass_combined_publication_complete','passed':True})
   from audit_native import audit
   source_audit=audit(good_native.encode(),native_good);assert source_audit['passed'] and source_audit['source_cell_count']==3;changed=copy.deepcopy(native_good);target=next(r for r in changed if r['tables']);target['tables'][0][0][0]['colspan']=1;assert not audit(good_native.encode(),changed)['passed'];receipt['tests'].append({'name':'independent_original_native_cell_audit_rejects_output_span_tampering','passed':True})
   nested='<div id="rid-A">Section A</div><div id="rid-A-body"><table><tr><td style="background-image:url(paint.png)">Outer<img src="raster.png"><table><tr><th colspan="2">Inner<svg><path/></svg></th></tr></table></td></tr></table></div>';nr=html_record({'doc_id':'A','id':99,'html':nested},item,{},'https://example.invalid/','fixture');check=audit(nested.encode(),[nr]);assert check['passed'] and check['source_table_count']==2 and nr['table_parent_indices']==[None,0];receipt['tests'].append({'name':'independent_original_nested_table_audit_preserves_images_as_literal_placeholders','passed':True})
   # This topology mirrors observed Cleveland publisher passthrough grouping, with no own native body.
   virtual_inventory=copy.deepcopy(inventory);branch=next(n for n in virtual_inventory['nodes'] if n['document_id']=='BRANCH');branch['passthru_doc_id']='LEAF-B';toc_sources={'BRANCH':{'url':'https://codelibrary.amlegal.com/api/section-toc/2/','sha256':'a'*64}};native_without_branch=good_native.replace(json.loads(FakeBrowser.sources['https://codelibrary.amlegal.com/api/render-section/fixturecity/fixture-edition-1/fixture_code/BRANCH/0/'])['html'],'');vr=native_records(native_without_branch.encode(),virtual_inventory,identity,'https://export.amlegal.com/fixture','fixture',inventory_sources=toc_sources);container=next(r for r in vr if r['document_id']=='BRANCH');assert container['kind']=='publisher-toc-passthrough-container' and not container['body_block_ids'] and container['source_sha256']=='a'*64;assert not bind_reference_graph(vr,virtual_inventory);assert len({b for r in vr for b in r['body_block_ids']})==8;receipt['tests'].append({'name':'observed_publisher_passthrough_container_owns_only_TOC_heading_no_child_body_duplicate','passed':True})
   missing=copy.deepcopy(virtual_inventory);next(n for n in missing['nodes'] if n['document_id']=='BRANCH')['passthru_doc_id']='MISSING'
   try:native_records(native_without_branch.encode(),missing,identity,'https://export.amlegal.com/fixture','fixture',inventory_sources=toc_sources);raise RuntimeError('Missing passthrough target accepted')
   except AssertionError:receipt['tests'].append({'name':'passthrough_target_must_be_retained_independent_descendant','passed':True})
   truncated=native_without_branch.replace(json.loads(FakeBrowser.sources['https://codelibrary.amlegal.com/api/render-section/fixturecity/fixture-edition-1/fixture_code/LEAF-B/0/'])['html'],'')
   try:native_records(truncated.encode(),virtual_inventory,identity,'https://export.amlegal.com/fixture','fixture',inventory_sources=toc_sources);raise RuntimeError('Omitted legal child accepted behind passthrough')
   except AssertionError:receipt['tests'].append({'name':'passthrough_container_does_not_hide_missing_operative_child','passed':True})
   from unittest.mock import patch
   import xml.etree.ElementTree as ET
   with patch('PIL.Image.open',side_effect=AssertionError('Image decoder invoked')),patch.object(ET,'fromstring',side_effect=AssertionError('SVG parser invoked')):
    for url,data,mime in [('https://example.invalid/a.png',b'not decoded','application/octet-stream'),('https://example.invalid/a.pdf',b'not decoded','image/png'),('https://example.invalid/opaque',b'\x89PNG\r\n\x1a\ninvalid','application/octet-stream'),('https://example.invalid/a.svg',b'<svg/>','text/plain'),('https://example.invalid/opaque',b'<svg/>','application/octet-stream')]:
     disposition=validate_asset(url,data,mime);assert disposition['kind']=='image-policy-excluded' and not disposition['qualified'] and disposition['placeholder']=='[IMAGE]'
   receipt['tests'].append({'name':'accidental_image_asset_validation_rejects_without_raster_or_SVG_decoder','passed':True})
   upper='<div id="rid-A">Section A</div><div id="rid-A-body"><p>Rule applies.</p><table><tr><td><object type="IMAGE/PNG" data="https://example.invalid/opaque-image"></object><source src="DATA:IMAGE/PNG;base64,SENTINEL"></td></tr></table></div>'
   upper_record=html_record({'doc_id':'A','id':99,'html':upper},item,{},'https://example.invalid/','fixture');assert upper_record['text'].count('[IMAGE]')==2 and 'SENTINEL' not in json.dumps(upper_record) and audit(upper.encode(),[upper_record])['passed']
   class NoImageTransport:
    def fetch(self,*args,**kwargs):raise AssertionError('Image transport invoked')
   ledger={}
   for image in upper_record['assets']:
    assert image['disposition']=='image-placeholder';disposition=collect.asset_fetch(image['url'],NoImageTransport(),ledger,'download',image['kind']);assert not disposition['required'] and disposition['status']=='image-placeholder'
   css='<div id="rid-A">Section A</div><div id="rid-A-body"><p style="background-image:URL(DATA:IMAGE/PNG;base64,SENTINEL)">Rule applies.</p></div>'
   css_record=html_record({'doc_id':'A','id':99,'html':css},item,{},'https://example.invalid/','fixture');assert '[IMAGE]' in css_record['text'] and 'SENTINEL' not in json.dumps(css_record) and not re.search(r'url\(',css_record['html'],re.I)
   receipt['tests'].append({'name':'uppercase_MIME_data_scheme_CSS_placeholder_metadata_no_transport','passed':True})
   inline='<div id="rid-A">Section A</div><div id="rid-A-body"><p>The <em>wo</em>rd applies.</p><table><tr><td>Each <b>Unit</b>.<br>Minimum Lot Width<sup>**</sup><p>(a)<b>Residential Uses</b></p><table><tr><td>A</td><td>B</td></tr></table></td></tr></table></div>'
   inline_record=html_record({'doc_id':'A','id':99,'html':inline},item,{},'https://example.invalid/','fixture');assert inline_record['tables'][0][0][0]['text']=='Each Unit. Minimum Lot Width** (a)Residential Uses A B';assert 'The word applies.' in inline_record['text'] and 'Unit\n.' not in inline_record['text'];assert audit(inline.encode(),[inline_record])['passed'];receipt['tests'].append({'name':'inline_word_punctuation_superscript_adjacency_block_and_nested_cell_boundaries','passed':True})
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
