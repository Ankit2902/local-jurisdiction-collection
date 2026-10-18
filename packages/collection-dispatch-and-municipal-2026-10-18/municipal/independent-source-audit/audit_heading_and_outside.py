"""Original heading callout and outside-article census, independent from producer parser."""
import collections,hashlib,json,pathlib,urllib.parse
from bs4 import BeautifulSoup,Tag
P=pathlib.Path(__file__).resolve().parents[4];O=pathlib.Path(__file__).resolve().parent
S=P/'outputs/collection-readiness-post-91f6c59-2026-10-17/ecode/phoenix-image-context-replay-v2'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cp=json.loads((S/'checkpoint.json').read_text());base=cp['publication_url'];rmap={r['id']:r for r in [json.loads(x) for x in (S/'records.jsonl').read_text().split('\n') if x]};headers={};classification=collections.Counter();unowned=[];calls=[]
for art in cp['artifacts']:
 if art['status']!=200:continue
 f=S/art['path'];assert h(f)==art['sha256'];soup=BeautifulSoup(f.read_bytes(),'html.parser');main=soup.find('main')
 for text in main.find_all(string=True):
  if not str(text).strip() or text.find_parent('article'):continue
  ps=list(text.parents)
  if any(e.name=='ul' and set(e.get('class',[]))&{'toc','contents-toc'} for e in ps):classification['literal_source_TOC_navigation_text']+=1
  elif any('levelnodeactions' in e.get('class',[]) for e in ps):classification['explicit_levelnodeactions_UI_text']+=1
  elif any('page-header' in e.get('class',[]) for e in ps) and ' '.join(str(text).split())=='Contents of Phoenix City Charter':classification['source_contents_heading']+=1
  else:unowned.append({'raw':art['path'],'text':str(text),'parent':str(text.parent)})
 for a in main.find_all('article'):
  ident=a['id'];u=base+'#NT' if ident=='NT' else base+'/'+ident
  head=a.find('header',recursive=False);assert head is not None
  if u in headers:assert headers[u]['html']==str(head);continue
  headers[u]={'id':u,'html':str(head),'text':' '.join(head.stripped_strings),'raw_path':art['path'],'raw_sha256':art['sha256'],'links':[]}
  for link in head.find_all('a'):
   target=urllib.parse.urlsplit(urllib.parse.urljoin(art['url'],link['href']));noteid=target.fragment
   matches=[x for x in a.find_all(id=noteid) if x.find_parent('article') is a]
   assert len(matches)==1 and 'note' in matches[0].get('class',[]) and link.get('class')==['fn']
   assert target.path==urllib.parse.urlsplit(u).path and not target.query
   entry={'owner_id':u,'literal_href':link['href'],'resolved_url':target.geturl(),'visible_label':link.get_text(),'target_note_id':noteid,'target_note_html':str(matches[0]),'same_explicit_article_owner':True,'source_raw_sha256':art['sha256'],'source_raw_path':art['path']}
   assert entry['target_note_html'] in rmap[u]['notes_html'] and link.get_text() in rmap[u]['heading']
   headers[u]['links'].append(entry);calls.append(entry)
assert len(headers)==80 and len(calls)==3 and not unowned
(O/'original-heading-witnesses.json').write_text(json.dumps(list(headers.values()),indent=2)+'\n')
r={'passed':True,'all_source_heading_witnesses':80,'heading_callout_links':calls,'source_outside_article_classifications':dict(classification),'unowned_unclassified_text':unowned,'preexisting_IR_representation_limit':'Three heading fn anchor hrefs are not in the existing body links array/canonical body, which deliberately excludes own heading. All marker labels remain in heading text and all target note bodies/IDs remain intact. A new reader must retain original heading HTML plus exact callout→sameowner note linkage in provenance before claiming all source-link coverage.','image_render_network_pixel_calls':0,'producer_imports':0,'audit_sha256':h(pathlib.Path(__file__))}
(O/'heading-and-outside-review.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
