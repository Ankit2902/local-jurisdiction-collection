"""Read-only binding to retained whole Overland corpus; no network/production imports."""
import argparse,collections,hashlib,json,pathlib,re,shutil
from bs4 import BeautifulSoup
UUID='68642c1d-ce7d-4ab0-a9e3-cf56d6def79a';PDF_SHA='1af70bb8170cf2701cfb9e7ede2b274bf848309ca6fcaa3b7a7eeba9cd426c39'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write_json(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def bind(retained,out):
 retained=pathlib.Path(retained);out=pathlib.Path(out);assert not out.exists();records=[json.loads(x) for x in (retained/'records.jsonl').read_text().splitlines()];assert len(records)==6279 and len({r['id'] for r in records})==6279
 by={r['id']:r for r in records};root=by['1578'];assert root['heading']=='7.36 Collection and Storage of Solid Waste and Recyclables' and root['parent_id']=='1296'
 ids={'1578'}
 while True:
  nextids=ids|{r['id'] for r in records if r['parent_id'] in ids}
  if nextids==ids:break
  ids=nextids
 assert len(ids)==40
 raw=retained/root['raw_path'];assert sha(raw)==root['raw_sha256'];soup=BeautifulSoup(raw.read_bytes(),'html.parser');nodes=soup.find_all('section',attrs={'data-secid':'1578'});assert len(nodes)==1;chapter=nodes[0];children=[n for n in soup.find_all('section',attrs={'data-secid':True}) if '_007-010' in n.get('class',[])];domids=[s['data-secid'] for s in children];assert len(domids)==len(set(domids))==40 and set(domids)==ids
 for sid in ids:
  r=by[sid];assert r['raw_path']==root['raw_path'] and r['raw_sha256']==root['raw_sha256'];assert r['body_sha256']==hashlib.sha256(r['body_html'].encode()).hexdigest()
  assert r['parent_id']==('1296' if sid=='1578' else '1578') and r['source_url'].startswith('https://codes.opkansas.org/municipal-code/doc-view.aspx?secid='+sid+'&')
  assert BeautifulSoup(r['html'],'html.parser').find('section',attrs={'data-secid':sid}) is not None
 assert by['1593']['text'].startswith('"County Solid Waste Regulations" are the regulations adopted by County') and 'Johnson County, Kansas' in by['1593']['text'] and 'Johnson County Code of Regulations for Solid Waste Management, 2010 Edition' in by['1593']['text'] and '(as may be amended from time to time)' in by['1593']['text']
 assert 'Ord. SW-2927 §7, 2011' in by['1593']['text']
 reciprocal=[]
 for sid in domids:
  r=by[sid];matches=[link for link in r['links'] if UUID in link['url']]
  if matches:reciprocal.append({'owner_id':sid,'heading':r['heading'],'links':matches,'text':r['text'],'raw_sha256':r['raw_sha256'],'body_sha256':r['body_sha256']})
 assert any(w['owner_id']=='1586' for w in reciprocal) and any(w['owner_id']=='1612' for w in reciprocal)
 cp=json.loads((retained/'checkpoint.json').read_text());cov=json.loads((retained/'coverage.json').read_text());asset=cp['assets']['https://codes.opkansas.org/municipal-code/doclibrary.aspx?id='+UUID];assert sha(retained/asset['path'])==asset['sha256']==PDF_SHA
 end=retained/'end-0'/pathlib.Path(root['raw_path']).name;assert sha(end)==sha(raw)
 post2011=[]
 for sid in domids:
  history=[x for x in re.findall(r'\(History:.*?\)',by[sid]['text'],re.S)];years=sorted({int(x) for s in history for x in re.findall(r'\b20\d\d\b',s) if int(x)>2011})
  if years:post2011.append({'id':sid,'heading':by[sid]['heading'],'years':years,'history':history})
 assert post2011
 out.mkdir();(out/'raw').mkdir();(out/'chapter-records.jsonl').write_text(''.join(json.dumps(by[sid],ensure_ascii=False,sort_keys=True)+'\n' for sid in domids))
 for src,name in [(raw,'title7-start.html'),(raw.with_name(raw.name+'.receipt.json'),'title7-start.html.receipt.json'),(end,'title7-end.html'),(end.with_name(end.name+'.receipt.json'),'title7-end.html.receipt.json')]:shutil.copy2(src,out/'raw'/name)
 write_json(out/'reciprocal-native-references.json',reciprocal);write_json(out/'county-definition-source.json',by['1593']);write_json(out/'post2011-amendment-evidence.json',post2011)
 proof={'source_run':str(retained),'source_scope':'Current retained2026 whole Overland6279 snapshot; this40node owned chapter is not certified as2011 text','source_corpus_sha256':sha(retained/'records.jsonl'),'source_checkpoint_sha256':sha(retained/'checkpoint.json'),'source_coverage_sha256':sha(retained/'coverage.json'),'started_at':cp['started_at'],'publication_identity':cov['publication_identity'],'observed_edition_pin':cov['edition_pin'],'publisher_edition_id':cov['edition_pin']['publisher_edition_id'],'raw_title7_start_sha256':sha(raw),'raw_title7_end_sha256':sha(end),'raw_start_end_equal':True,'root_owner_id':'1578','root_heading':root['heading'],'owned_units':40,'operative_units':39,'source_dom_order':domids,'source_membership_basis':'Publisher explicit _007-010 body class ancestry across sibling sections; not physical DOM descendant nesting or citation-prefix guess','existing_corpus_row_indices':{r['id']:n+1 for n,r in enumerate(records) if r['id'] in ids},'all40raw_owner_bindings_verified':True,'reciprocal_native_url_uuid':UUID,'same_native_sha256':PDF_SHA,'source_asset_original_metadata':asset,'county_named_by_owner':'1593','county_name':'Johnson County, Kansas','county_regulation_title':'Johnson County Code of Regulations for Solid Waste Management, 2010 Edition (as may be amended from time to time)','county_definition_history':'Ord. SW-2927 §7, 2011','post2011_amended_unit_count':len(post2011),'reusable_as_current_same_source_dependency_graph':True,'reusable_as_2011_edition_equivalent':False,'historical_2011_dependency_closure':False,'new_publisher_requests':0,'image_policy':'literal[IMAGE]; no separate image fetch/decode/extract/render/OCR','unrelated_similar_prefix_owner_excluded':{'id':'1567','heading':by['1567']['heading'],'parent_id':by['1567']['parent_id'],'reason':'Same7.36 prefix occurs under different source parent; not Chapter1578 descendant'}}
 write_json(out/'proof.json',proof);return proof
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--retained',required=True);p.add_argument('--out',required=True);a=p.parse_args();r=bind(a.retained,a.out);print(json.dumps({k:r[k] for k in ['owned_units','operative_units','raw_start_end_equal','post2011_amended_unit_count','reusable_as_current_same_source_dependency_graph','reusable_as_2011_edition_equivalent']},indent=2))
