"""Independent exact decoded text and word-boundary comparison; source-only."""
import copy,hashlib,json,pathlib,re
from bs4 import BeautifulSoup
P=pathlib.Path(__file__).resolve().parents[5];O=pathlib.Path(__file__).resolve().parent
S=P/'outputs/collection-readiness-post-91f6c59-2026-10-17/ecode/phoenix-image-context-replay-v2';cp=json.loads((S/'checkpoint.json').read_text());rmap={r['id']:r for r in [json.loads(x) for x in (S/'records.jsonl').read_text().split('\n') if x]};seen=set();exact=0;collapsed=0;errors=[];details=[]
for a in cp['artifacts']:
 if a['status']!=200:continue
 f=S/a['path'];assert hashlib.sha256(f.read_bytes()).hexdigest()==a['sha256'];s=BeautifulSoup(f.read_bytes(),'html.parser');main=s.find('main')
 for x in main.find_all('article'):
  u=cp['publication_url']+('#NT' if x['id']=='NT' else '/'+x['id'])
  if u not in rmap or u in seen:continue
  seen.add(u);own=copy.deepcopy(x);own.find('header',recursive=False).decompose()
  for child in list(own.find_all('article')):
   if child.parent:child.decompose()
  for child in list(own.find_all('div',recursive=False)):
   if child.get('class')==['track-indicator','selected','d-none']:child.decompose()
  source=own.get_text();r=rmap[u];values=[BeautifulSoup(r[k],'html.parser').get_text() for k in ['content_html','semantic_html']]
  equal=all(v==source for v in values);norm=lambda z:re.sub(r'\s+',' ',z).strip();co=all(norm(v)==norm(source) for v in values)
  exact+=equal;collapsed+=co
  if not co:errors.append(u)
  details.append({'id':u,'exact_decoded_body_text_equal':equal,'whitespace_collapsed_only_equal':co,'source_text_sha256':hashlib.sha256(source.encode()).hexdigest(),'source_raw_sha256':a['sha256']})
assert len(seen)==73 and not errors
r={'passed':True,'records':len(seen),'exact_decoded_body_text_equal':exact,'word_boundary_comparison_whitespace_collapsed_only_equal':collapsed,'mismatches':errors,'interpretation':'Unlike removing all whitespace, this independent decoded-text comparison preserves word separation, inline-node text boundaries and literal nonwhitespace characters. No producer/body serializer imported.','network_image_decode_render_native_parse_calls':0,'source_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'details':details}
(O/'literal-text-review.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='details'},indent=2))
