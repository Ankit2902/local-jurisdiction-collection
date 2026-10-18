"""Exact same-source malformed ordinance href alias and fail-closed controls."""
import copy,json,socket
from unittest.mock import patch
from bs4 import BeautifulSoup
from model import native_records,bind_source_asset_aliases
URL='https://files.amlegal.com/pdffiles/Fixture/32195.pdf'
BAD='http://"'+URL
def fixture(valid=True,bad_label='32195',same_owner=False,image=False):
 direct='<a href="'+URL+'">32195</a>' if valid else ''
 a=('<p>Comparative table.</p>'+direct) if not same_owner else '<p>Comparative table.</p>'
 b=('<a type="image/png"' if image else '<a')+' href="http://&quot;'+URL+'">'+bad_label+'</a>'+(direct if same_owner else '')
 html='<html><body><div id="rid-A" class="toc-destination">Comparative Table</div><div id="rid-A-body">'+a+'</div><div id="rid-B" class="toc-destination">Section B</div><div id="rid-B-body">The source rule applies.'+b+'</div></body></html>'
 inv={'nodes':[{'document_id':d,'internal_id':i,'heading':h,'path':[h],'parent_id':None,'has_children':False} for i,d,h in [(1,'A','Comparative Table'),(2,'B','Section B')]]};return html.encode(),inv
def parse(**kwargs):
 html,inv=fixture(**kwargs);return native_records(html,inv,{'version_uuid':'v','code_uuid':'c'},'https://example.invalid/book','sourcehash')
def tests():
 checks=[]
 with patch.object(socket.socket,'connect',side_effect=AssertionError('No network')),patch('PIL.Image.open',side_effect=AssertionError('No image decode')):
  records=parse();a=records[1]['assets'][0];assert a['url']==URL and a['raw']==a['source_attribute']==BAD;assert a['source_alias']['corroborating_direct_references'][0]['document_id']=='A';assert a['source_alias']['numeric_ordinance_citation']=='32195' and a['source_alias']['original_url']==BAD;assert BeautifulSoup(records[1]['html'],'html.parser').a['href']==BAD;assert len({a['url'] for r in records for a in r['assets']})==1;checks.append({'name':'same_source_distinct_owner_exact_URL_numeric_citation_alias_retains_original_href_and_proof','passed':True})
  for name,args in [('absent_corroboration',{'valid':False}),('wrong_numeric_citation',{'bad_label':'32196'}),('same_owner_only',{'same_owner':True})]:
   try:parse(**args)
   except AssertionError:checks.append({'name':name+'_fails_closed','passed':True})
   else:raise AssertionError(name+' accepted')
  altered=copy.deepcopy(records);altered[1]['assets'][0].pop('source_alias');altered[1]['assets'][0]['url']=BAD;altered[0]['publication_identity']=dict(altered[0]['publication_identity'],version_uuid='another-edition')
  try:bind_source_asset_aliases(altered)
  except AssertionError:checks.append({'name':'different_source_edition_cannot_corroborate','passed':True})
  else:raise AssertionError('Wrong-edition corroboration accepted')
  image=parse(valid=False,image=True)[1];assert '[IMAGE]' in image['text'] and all(a['kind']=='image' and a['disposition']=='image-placeholder' and 'source_alias' not in a for a in image['assets']);checks.append({'name':'declared_image_stays_excluded_no_PDF_alias_no_transport_or_decode','passed':True})
 return {'passed':True,'count':len(checks),'tests':checks,'network_calls':0,'image_decode_calls':0}
if __name__=='__main__':print(json.dumps(tests(),indent=2))
