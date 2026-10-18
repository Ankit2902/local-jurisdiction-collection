"""Actual existing in-Content note ownership; no new note serialization/support."""
from pathlib import Path
import json,hashlib,collections
from bs4 import BeautifulSoup
B=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00');O=Path(__file__).resolve().parent
P=B/'outputs/collection-readiness-post1997ee1-2026-10-17/qa/corpus-readers-municode-encodeplus-v1/FINAL-PACKET';package=P/'fixtures/packages/henderson';root=package/'evidence/input'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();digest=lambda s:hashlib.sha256(s.encode()).hexdigest()
cp=json.loads((root/'checkpoint.json').read_text());pub=cp['publications']['14896'];ir=[json.loads(x)for x in(root/'publications/14896/sections.jsonl').read_text().split('\n')if x];rmap={r['node_id']:r for r in ir};corpus=json.loads((package/'aggregate-fulltext.json').read_text())['provisions'];pr=[json.loads(x)for x in(package/'record-provenance.jsonl').read_text().split('\n')if x];out={x['record_id'].split(':',1)[1]:row for x,row in zip(pr,corpus)}
manifest={str((root/'checkpoint.json').relative_to(B)):sha(root/'checkpoint.json'),str((root/'publications/14896/sections.jsonl').relative_to(B)):sha(root/'publications/14896/sections.jsonl'),str((package/'aggregate-fulltext.json').relative_to(B)):sha(package/'aggregate-fulltext.json')};matches=[];failures=[];docs=0;owner_counts=collections.Counter()
def selected(soup):
 return [t for t in soup.find_all(True)if any(c=='footnote-content' or c.startswith('refeditor') or c.startswith('refnote') for c in t.get('class',[]))]
for name in pub['content_units']:
 u=cp['units'][name];receipt=json.loads((root/u['receipt']).read_text());p=root/receipt['body_file'];assert sha(p)==u['sha256']==receipt['sha256'];manifest[str(p.relative_to(B))]=sha(p);values=json.loads(p.read_bytes())
 for index,d in enumerate(values):
  docs+=1;ident=str(d['Id']);r=rmap[ident];source=d.get('Content')or'';assert digest(source)==r['body_sha256'];assert out[ident]['full_text']==r['html'];assert not d.get('Notes')and not d.get('Footnotes')and not r.get('notes')and not r.get('footnotes_html')
  # Parse only bodies whose literal source classes identify note markup. No DOM
  # mount, URL resolution, collector import, pixel API, or rendering occurs.
  if not any(s in source for s in ['footnote-content','refeditor','refnote']):continue
  a=selected(BeautifulSoup(source,'html.parser'));b=selected(BeautifulSoup(r['html'],'html.parser'));c=selected(BeautifulSoup(out[ident]['full_text'],'html.parser'))
  if len(a)!=len(b)or len(b)!=len(c):failures.append({'doc_id':ident,'reason':'Source/canonical/export note markup count differs','counts':[len(a),len(b),len(c)]});continue
  for ordinal,(x,y,z)in enumerate(zip(a,b,c)):
   plain_equal=x.get_text()==y.get_text()==z.get_text();markup_equal=str(x)==str(y)==str(z)
   if not (plain_equal and markup_equal):failures.append({'doc_id':ident,'ordinal':ordinal,'text_equal':plain_equal,'markup_equal':markup_equal})
   owner_counts[ident]+=1;matches.append({'doc_id':ident,'heading':r['heading'],'parent_id':r['parent_id'],'is_container':r['is_container'],'source_unit':name,'source_body_path':str(p.relative_to(B)),'source_body_sha256':u['sha256'],'raw_doc_array_ordinal':index,'source_field':'Content','source_note_element_ordinal':ordinal,'tag':x.name,'classes':x.get('class',[]),'source_fragment_sha256':digest(str(x)),'canonical_fragment_sha256':digest(str(y)),'export_fragment_sha256':digest(str(z)),'source_text_sha256':digest(x.get_text()),'text_equal':plain_equal,'markup_equal':markup_equal,'nested_image_tags':len(x.find_all(['img','svg','picture','object','embed','source']))})
assert all(sha(B/n)==h for n,h in manifest.items());assert not failures
result={'passed':True,'scope':'Actual full Henderson publication in-body note markup only. Existing canonical html already owns these notes; no new separate Notes/Footnotes schema, append operation or candidate support is qualified. Element counts include nested note-container/paragraph occurrences and are not a claim of distinct note count.','publication_id':'60-primary','product_id':'14896','job_id':pub['job_id'],'whole_publication_docs_checked':docs,'normalized_records':len(ir),'matched_note_element_occurrences':len(matches),'owners':len(owner_counts),'owners_with_parent_body':sum(bool(rmap[i]['is_container'])for i in owner_counts),'failures':failures,'source_files_unchanged':True,'source_parser':'Independent BeautifulSoup html.parser; only selected source-note bodies parsed, never attached/rendered','network_requests':0,'image_operations':0,'separate_raw_fields_populated':0,'matches':matches,'source_manifest':manifest};(O/'inline-note-ownership.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['matches','source_manifest']},indent=2))
