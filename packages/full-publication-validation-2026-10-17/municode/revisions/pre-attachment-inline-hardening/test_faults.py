"""Synthetic network-free fault tests exercise the real orchestrator/model/resume path; not live evidence."""
import sys
sys.dont_write_bytecode=True
import argparse,base64,copy,json,tempfile,unittest,shutil
from pathlib import Path
from urllib.parse import urlparse,parse_qs
from unittest.mock import patch
from model import atomic,sha,digest,write_outputs,reconcile_publication
import collect
from verify import verify
PDF=b'%PDF-1.4\nfixture nonimage attachment\n%%EOF'
ROOT_URL='https://library.municode.com/zz/fixture/codes/test_publication'
PRODUCT={'Model':{'ProductID':17,'ProductName':'Test Publication','Client':{'ClientID':2,'ClientName':'Fixture Municipality','State':{'StateAbbreviation':'ZZ'}}}}
JOB={'Id':99,'ProductId':17,'Name':'Test Edition'}
CC={'codes':[{'productId':17,'productName':'Test Publication','contentTypeId':'CODES','hideInLibrary':False}]}
TREE={'Id':'17','Heading':'Test Publication','Data':{'DocType':0},'Children':[{'Id':'CH','Heading':'Chapter 1','Data':{'DocType':2},'Children':[{'Id':'S1','Heading':'Section 1','Data':{'DocType':1},'Children':[]},{'Id':'S2','Heading':'Section 2','Data':{'DocType':1},'Children':[]}]}]}
DOCS=[{'Id':'CH','Title':'Chapter 1','DocType':2,'Content':'<p>Container-owned legal preamble.</p>'},{'Id':'S1','Title':'Section 1','DocType':1,'Content':'<p>An operative requirement.</p><table><tr><th>Unit</th><th>Rate</th></tr><tr><td rowspan="2">Family</td><td>100</td></tr></table><a data-nodeid="S2">Section2</a><img src="https://mcclibrary.blob.core.usgovcloudapi.net/fixture/diagram.png"><a href="https://mcclibrary.blob.core.usgovcloudapi.net/fixture/appendix.pdf">Required appendix</a>'},{'Id':'S2','Title':'Section 2','DocType':1,'Content':'<p>A second operative requirement.</p>'}]
class FakeBrowser:
 fail_after=None;calls=0;urls=[]
 def __init__(self,url,out):self.requests=0
 def request(self,url,binary=False):
  self.requests+=1;type(self).calls+=1;type(self).urls.append((url,binary))
  if self.fail_after and self.requests>self.fail_after:raise KeyboardInterrupt('synthetic interruption after committed content')
  path=urlparse(url).path
  if binary:
   if 'diagram' in url:raise AssertionError('Image request forbidden')
   if url.endswith('/drawing'):return {'response':{'url':url,'status':200,'headers':{'content-type':'image/png'},'body':'','image_omitted':True,'omission_reason':'HEAD image MIME; no body downloaded'},'access_stop':None}
   body=PDF;mime='application/pdf'
  else:
   if '/localapi/' in path:data={'ClientID':2,'ClientName':'Fixture Municipality','State':{'StateAbbreviation':'ZZ'}}
   elif '/ClientContent/' in path:data=CC
   elif '/Products/name' in path:data=PRODUCT
   elif '/Jobs/latest/' in path:data=JOB
   elif '/codesToc/' in path:data=TREE
   elif path.endswith('/CodesContent/docIds'):data=DOCS
   elif path.endswith('/CodesContent'):data={'Docs':[{'Id':'17','DocType':4,'Content':None}]}
   else:raise ValueError('Unexpected synthetic request '+url)
   body=json.dumps(data).encode();mime='application/json'
  return {'response':{'url':url,'status':200,'headers':{'content-type':mime},'body':base64.b64encode(body).decode()},'access_stop':None}
 def close(self):pass

def args(out,resume=False,limit=None):return argparse.Namespace(registry=None,target=None,url=ROOT_URL,client_name=['Fixture Municipality'],client_id=2,state='ZZ',out=Path(out),product_id=[17],resume=resume,max_items=limit,batch_size=25,allow_asset_host=[])
def run_fixture(out,resume=False,limit=None):
 with patch.object(collect,'Browser',FakeBrowser):report=collect.Run(args(out,resume,limit)).execute()
 cp=json.loads((Path(out)/'checkpoint.json').read_text());cp['evidence_kind']='synthetic_unit_fixture';atomic(Path(out)/'checkpoint.json',cp);write_outputs(Path(out),cp);return cp

def replace_unit(folder,cp,name,transform):
 entry=cp['units'][name];receipt=json.loads((folder/entry['receipt']).read_text());path=folder/receipt['body_file'];payload=json.loads(path.read_text());payload=transform(payload);body=json.dumps(payload).encode();atomic(path,body);receipt['sha256']=sha(body);atomic(folder/entry['receipt'],receipt)
 for e in list(cp['units'].values())+cp['responses']:
  if e['receipt']==entry['receipt']:e['sha256']=receipt['sha256']

def save(folder,cp):atomic(folder/'checkpoint.json',cp);write_outputs(folder,cp)
class FaultTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.folder=Path(self.tmp.name)/'run';FakeBrowser.fail_after=None;FakeBrowser.calls=0;self.cp=run_fixture(self.folder)
 def tearDown(self):FakeBrowser.fail_after=None;self.tmp.cleanup()
 def rejected(self):
  with self.assertRaises((ValueError,FileNotFoundError,KeyError)):verify(self.folder)
 def test_baseline_and_container_ownership(self):
  r=verify(self.folder);self.assertTrue(r['publication_complete']);records,coverage=reconcile_publication(self.folder,self.cp,17);self.assertEqual(len(records),3);self.assertEqual(coverage['parsed_container_count'],1);self.assertEqual(records[0]['text'],'Container-owned legal preamble.');self.assertFalse(coverage['live_publication_complete'])
 def test_image_omission_no_download(self):
  self.assertFalse(any('diagram' in url for url,binary in FakeBrowser.urls));records,r=reconcile_publication(self.folder,self.cp,17);self.assertIn('[IMAGE]',records[1]['text']);self.assertNotIn('<img',records[1]['html']);self.assertEqual(r['image_omission_count'],1);self.assertEqual(r['required_asset_count'],1)
 def test_image_forms_and_image_only_leaf(self):
  from image_policy import sanitize
  forms=['<img src="x.png">','<h2><img src="x.png"></h2>','<picture><source srcset="x.webp 1x, y.png 2x"><img src="x.png"></picture>','<svg><image href="x.png"></image></svg>','<svg><image xlink:href="x.png"></image></svg>','<div style="background:url(x)">Rule</div>','<style>.a{background:url(x.png)}</style>','<object type="image/svg+xml" data="x"></object>','<a href="x.png">Diagram</a>']
  for html in forms:
   clean,meta=sanitize(html,ROOT_URL);self.assertIn('[IMAGE]',clean);self.assertTrue(meta);self.assertNotIn('<img',clean);self.assertNotIn('<svg',clean);self.assertNotIn('<picture',clean);self.assertNotIn('url(',clean)
  replace_unit(self.folder,self.cp,'content-root:17',lambda a:[*a[:2],{**a[2],'Content':'<img src="https://example.gov/only.png">'}]);save(self.folder,self.cp);records,r=reconcile_publication(self.folder,self.cp,17);self.assertEqual(records[-1]['text'],'[IMAGE]');self.assertTrue(r['publication_complete'])
 def test_extensionless_image_head_omission(self):
  url='https://mcclibrary.blob.core.usgovcloudapi.net/fixture/drawing'
  modified=[*DOCS[:2],{**DOCS[2],'Content':'<a href="'+url+'">Drawing</a>'}];out=Path(self.tmp.name)/'extensionless'
  with patch(__name__+'.DOCS',modified):cp=run_fixture(out)
  records,r=reconcile_publication(out,cp,17);self.assertIn('[IMAGE]',records[-1]['text']);self.assertNotIn('href=',records[-1]['html']);self.assertTrue(r['publication_complete']);self.assertEqual((out/json.loads((out/cp['units']['asset:'+digest(url)]['receipt']).read_text())['body_file']).stat().st_size,0)
 def test_missing_document(self):replace_unit(self.folder,self.cp,'content-root:17',lambda a:a[:-1]);save(self.folder,self.cp);self.rejected()
 def test_duplicated_document(self):replace_unit(self.folder,self.cp,'content-root:17',lambda a:a+[a[0]]);save(self.folder,self.cp);self.rejected()
 def test_corrupt_body(self):
  e=self.cp['units']['content-root:17'];r=json.loads((self.folder/e['receipt']).read_text());(self.folder/r['body_file']).write_bytes(b'corrupt');self.rejected()
 def test_wrong_edition_request(self):
  e=self.cp['units']['content-root:17'];receipt=json.loads((self.folder/e['receipt']).read_text());receipt['request']['url']=receipt['request']['url'].replace('jobId=99','jobId=100');atomic(self.folder/e['receipt'],receipt)
  for ent in list(self.cp['units'].values())+self.cp['responses']:
   if ent['receipt']==e['receipt']:ent['request']=receipt['request']
  save(self.folder,self.cp);self.rejected()
 def test_interrupted_cannot_pass(self):self.cp['phase']='interrupted';self.cp['publications']['17'].pop('end_units');save(self.folder,self.cp);self.rejected()
 def test_source_drift(self):replace_unit(self.folder,self.cp,'job-end:17',lambda j:{**j,'Id':100});save(self.folder,self.cp);self.rejected()
 def test_missing_asset(self):self.cp['assets']={};save(self.folder,self.cp);self.rejected()
 def test_corrupt_asset(self):
  e=self.cp['units'][next(k for k in self.cp['units'] if k.startswith('asset:'))];r=json.loads((self.folder/e['receipt']).read_text());(self.folder/r['body_file']).write_bytes(b'bad attachment');self.rejected()
 def test_limit_always_incomplete(self):
  limited=Path(self.tmp.name)/'limited';run_fixture(limited,limit=1)
  with self.assertRaises(ValueError):verify(limited)
 def test_resume_matches_uninterrupted_outputs(self):
  resumed=Path(self.tmp.name)/'resumed';FakeBrowser.fail_after=7
  with self.assertRaises(KeyboardInterrupt):
   with patch.object(collect,'Browser',FakeBrowser):collect.Run(args(resumed)).execute()
  before=json.loads((resumed/'checkpoint.json').read_text());self.assertIn('content-root:17',before['units']);old_receipt=before['units']['content-root:17']['receipt'];FakeBrowser.fail_after=None;run_fixture(resumed,resume=True);after=json.loads((resumed/'checkpoint.json').read_text());self.assertEqual(old_receipt,after['units']['content-root:17']['receipt'])
  for name in ['sections.jsonl','sections.csv','coverage.json']:self.assertEqual((self.folder/'publications/17'/name).read_bytes(),(resumed/'publications/17'/name).read_bytes())
  self.assertTrue(verify(resumed)['publication_complete'])
 def test_corrupt_resume_cache_refused_before_network(self):
  e=self.cp['units']['content-root:17'];r=json.loads((self.folder/e['receipt']).read_text());(self.folder/r['body_file']).write_bytes(b'bad');before=FakeBrowser.calls
  with patch.object(collect,'Browser',FakeBrowser):
   with self.assertRaises(ValueError):collect.Run(args(self.folder,resume=True))
  self.assertEqual(before,FakeBrowser.calls)
 def test_resume_identity_mismatch_refused(self):
  a=args(self.folder,resume=True);a.state='YY'
  with self.assertRaises(ValueError):collect.Run(a)
if __name__=='__main__':unittest.main(verbosity=2)
