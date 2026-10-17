#!/usr/bin/env python3
"""Offline native export validation; HTML provision replay, PDF text readability and selection binding."""
import json,re,sys,csv
from pathlib import Path
from pypdf import PdfReader
import collect
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'lib'))
import municipal_codes_cli as mc

def main():
 jobs=json.loads((ROOT/'jobs.json').read_text());report=[]
 for slug,folder in [('phoenix','phoenix-final'),('newark','newark-live'),('anchorage','anchorage-browser')]:
  d=ROOT/'evidence'/folder;e=json.loads((d/'publisher-export.json').read_text());j=jobs[slug]
  for native in e['downloads']:
   p=d/native['path'];assert collect.sha(p.read_bytes())==native['sha256'];r={'job':slug,'path':str(p.relative_to(ROOT)),'sha256_verified':True,'scope':'bounded native export; not entire publication'}
   if p.suffix=='.html':
    meta=json.loads((d/'acquisition.json').read_text());recs,notes=mc.parse_page(p.read_text(),meta['url'],j['base']);live=json.loads((d/'parse-details.json').read_text())['source_records'];assert [(x['citation'],x['full_text']) for x in recs]==[(x['citation'],x['full_text']) for x in live]
    rows=[]
    for v in recs:
     row=dict.fromkeys(collect.FIELDS,'');row.update(jurisdiction=j['jurisdiction'],code_name=j['code_name'],section_number=v['section_number'],section_name=v['section_name'],citation=v['citation'],full_text=v['full_text'],source_url=v['source_url'],scrape_date=meta['retrieved_at'][:10]);rows.append(row)
    (d/'native-export-records.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows))
    with (d/'native-export-records.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=collect.FIELDS);w.writeheader();w.writerows(rows)
    r.update(record_count=len(recs),identical_citations_bodies_to_live_dom=True)
   else:
    pdf=PdfReader(p);text='\n'.join(pg.extract_text() or '' for pg in pdf.pages);assert len(text)>100
    selected=next(x for x in json.loads((d/'parse-details.json').read_text())['source_records'] if x['node_id']==e['selected_id']);words=set(re.findall(r'[a-z]{4,}',BeautifulSoup(selected['full_text'],'html.parser').get_text().lower()));pdfwords=set(re.findall(r'[a-z]{4,}',text.lower()));coverage=len(words&pdfwords)/max(1,len(words));assert coverage>.9,(slug,coverage)
    (d/'publisher-export-text.txt').write_text(text);r.update(pages=len(pdf.pages),text_characters=len(text),selected_node_id=e['selected_id'],selected_citation=selected['citation'],selected_body_word_coverage=coverage,limitation='Text readability and selected provision binding only; PDF layout/OCR/corpus completeness not inferred')
   report.append(r)
 # CodePublishing HTML leaf export has independent source anchors; compare operative bodies by citation.
 slug='burlington';d=ROOT/'evidence'/'burlington-leaf-export';e=json.loads((d/'publisher-export.json').read_text());native=e['downloads'][0];p=d/native['path'];assert collect.sha(p.read_bytes())==native['sha256']
 import cp_collect as cp
 page={'url':jobs[slug]['url'],'publication_id':'municipal-code','path':p.name,'sha256':native['sha256'],'content_selector':'#mainContent'}
 snap={'jurisdiction_slug':slug,'jurisdiction':'Burlington','snapshot_id':'native-export','publications':[{'publication_id':'municipal-code','title':jobs[slug]['code_name']}],'retrieved_at':json.loads((d/'acquisition.json').read_text())['retrieved_at']}
 parsed=cp.parse_page(p.read_bytes(),page,snap);rows=parsed['records'];assert len(rows)==3
 live={r['citation']:r for r in json.loads((d/'parse-details.json').read_text())['records']}
 for row in rows:assert cp.plain(row['full_text'])==cp.plain(live[row['citation']]['full_text']),row['citation']
 (d/'native-export-records.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows))
 with (d/'native-export-records.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=collect.FIELDS);w.writeheader();w.writerows(rows)
 report.append({'job':slug,'path':str(p.relative_to(ROOT)),'sha256_verified':True,'record_count':len(rows),'native_format':'publisher HTML','scope':'three observed chapter1 leaves1-1 through1-3','operative_plain_text_equal_to_live_dom':True,'complete_corpus':False})
 collect.save(ROOT/'publisher-export-verification.json',report);print(json.dumps(report,indent=2))
if __name__=='__main__':main()
