"""Independent synthetic edge probes, not live publication validation."""
import importlib.util,json,sys,tempfile,copy,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];source=ROOT/'collectors/municode';sys.path.insert(0,str(source));import model as m

def fixture(folder,leaf='<p>Operative requirement applies.</p>',container='<p>Parent-only legal requirement.</p>',ctype=2):
 tree={'Id':'1','Heading':'Code','Data':{'DocType':0},'Children':[{'Id':'CH','Heading':'Chapter1','Data':{'DocType':2},'Children':[{'Id':'S1','Heading':'Section1','Data':{'DocType':1},'Children':[]}]}]}
 product={'Model':{'ProductID':1,'ProductName':'Code','Client':{'ClientID':2,'ClientName':'Example','State':{'StateAbbreviation':'EX'}}}};job={'Id':3,'ProductId':1};inv={'codes':[{'productId':1}]};docs={'Docs':[{'Id':'CH','Title':'Chapter1','DocType':ctype,'Content':container},{'Id':'S1','Title':'Section1','DocType':1,'Content':leaf}]};landing={'Docs':[{'Id':'1','DocType':4,'Content':''}]};cp={'source_url':'https://library.municode.com/ex/example/codes/code','client_id':2,'expected_identity':{'client_names':['Example'],'state':'EX'},'units':{},'publications':{},'phase':'finished','binding':{'implementation':{}},'assets':{}}
 def put(name,obj,url):
  body=json.dumps(obj).encode();bf='raw/'+name+'.json';rf='raw/'+name+'.receipt.json';(folder/'raw').mkdir(exist_ok=True);(folder/bf).write_bytes(body);req={'url':url};rr={'request':req,'body_file':bf,'sha256':m.sha(body),'status':200};(folder/rf).write_text(json.dumps(rr));cp['units'][name]={'request':req,'receipt':rf,'sha256':rr['sha256']}
 for name,obj,url in [('product',product,'https://library.municode.com/api/Products/name?clientId=2&productName=Code'),('job',job,'https://library.municode.com/api/Jobs/latest/1'),('inventory-start',inv,'https://library.municode.com/api/ClientContent/2'),('toc',tree,'https://library.municode.com/api/codesToc/fullTree?productId=1&jobId=3&nodeId=1'),('content',docs,'https://library.municode.com/api/CodesContent?productId=1&jobId=3&docIds=1'),('landing',landing,'https://library.municode.com/api/CodesContent?productId=1&jobId=3&nodeId=1')]:put(name,obj,url)
 sig=m.digest({'inventory':inv,'product':product,'job':job,'toc':tree});cp['publications']['1']={'toc_unit':'toc','product_unit':'product','job_unit':'job','job_id':3,'toc_hash':m.digest(tree),'content_units':['content'],'root_landing_unit':'landing','start_signature':sig,'end_units':{'inventory':'inventory-start','product':'product','job':'job','toc':'toc'},'end_signature':sig};return cp

def main():
 mixed='<p>Before image text.</p><img id="i1" src="ordinary.png"><picture><source srcset="small.png 1x, large.png 2x"><img src="fallback.png"></picture><svg><image href="map.png"/></svg><p style="background-image:url(css.png)">CSS label</p><img src="data:image/png;base64,AAAA"><video poster="poster.png"></video><style>.legal-map{background-image:url(sheet.png)}</style><object data="data:image/png;base64,AAAA" type="image/png"></object><table><tr><td>Outer cell<img src="cell.png"><table><tr><td>Nested cell<img src="nested.png"></td></tr></table></td></tr></table><p>After image text.</p>'
 probes=[('baseline',{},True),('omitted_direct_image',{'leaf':'<p>Operative rule.</p><img src="https://example.gov/diagram.png">'},True),('svg_image_href',{'leaf':'<p>Operative rule.</p><svg><image href="https://example.gov/diagram.png"></image></svg>'},True),('svg_image_xlink',{'leaf':'<p>Operative rule.</p><svg><image xlink:href="https://example.gov/diagram.png"></image></svg>'},True),('image_only_leaf',{'leaf':'<img src="https://example.gov/map.png">'},True),('mixed_images_nested_table',{'leaf':mixed},True),('required_nonimage_attachment',{'leaf':'<p>Adopted standard incorporated by reference <a href="https://example.gov/document/123">Standard</a></p>'},False),('heading_only_leaf',{'leaf':'<h2>Section1</h2>'},False),('unknown_empty_container',{'container':'','ctype':999},False)]
 out=[]
 for name,kw,expected in probes:
  with tempfile.TemporaryDirectory() as td:
   f=Path(td);cp=fixture(f,**kw)
   try:
    records,r=m.reconcile_publication(f,cp,1);actual=r['publication_complete'];error=None
    if name in ['omitted_direct_image','svg_image_href','svg_image_xlink','image_only_leaf','mixed_images_nested_table']:
     leaf=next(x for x in records if x['node_id']=='S1');assert leaf['heading']=='Section1' and '[IMAGE]' in leaf['text'] and leaf['image_omissions'],'Source identity/placeholder metadata missing';assert not re.search(r'<(?:img|svg|image|picture)\b|data:image/|url\s*\(',leaf['html'],re.I),'Active image remains in normalized HTML';assert 'data:image/' not in json.dumps(leaf) and 'data:image/' not in json.dumps(r),'Image payload copied into normalized omission/reference metadata'
     if name=='mixed_images_nested_table':assert leaf['text'].count('[IMAGE]')>=8 and len(leaf['tables'])==2 and '[IMAGE]' in leaf['html'].split('<table>')[-1],'Nested table image placeholder lost'
   except Exception as ex:actual=False;error=repr(ex)
   out.append({'test':name,'expected_complete':expected,'actual_complete':actual,'passed':actual==expected,'error':error})
 print(json.dumps({'synthetic':True,'network_requests_sent':0,'image_policy':'literal [IMAGE]; no separate image acquisition','source_module_sha256':{n:m.sha((source/n).read_bytes()) for n in ['model.py','image_policy.py']},'probes':out,'passed':all(x['passed'] for x in out)},indent=2));return 0 if all(x['passed'] for x in out) else 2
if __name__=='__main__':raise SystemExit(main())
