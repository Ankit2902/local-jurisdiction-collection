"""Bounded Emeryville first-party Charter HTML acquisition -> two records + full node inventory.
This qualifies a separate Charter only, never the complete Municipal Code.
"""
import argparse,csv,datetime,json,re,sys
from pathlib import Path
from bs4 import BeautifulSoup
from discover import get,sha
URL='https://www.emeryville.org/Government/About-Emeryville/Charter-City'
FIELDS='jurisdiction code_name division title subtitle chapter subchapter article part subpart section_number section_name citation full_text source_url scrape_date'.split()

def parse(data,selected=('100','200'),scrape_date=None):
    soup=BeautifulSoup(data,'html.parser');main=soup.select_one('#main-content')
    if main is None:raise ValueError('Missing first-party main source container')
    rows=[];nodes=[];provenance=[];seen=set()
    panels=main.select('.oc-wysiwyg-container-panel')
    for panel_index,panel in enumerate(panels):
        article=panel.find(['h2','h3','h4']);article=article.get_text(' ',strip=True) if article else ''
        if not article.startswith('Article '):raise ValueError('Unknown Charter article profile')
        for paragraph_index,p in enumerate(panel.select('.oc-wysiwyg-container-panel-content > p')):
            if not p.get_text(' ',strip=True):continue
            bold=p.find('strong');m=re.fullmatch(r'Section (\d+)\. (.+)',bold.get_text(' ',strip=True) if bold else '')
            if not m:raise ValueError('Unprofiled operative paragraph must not disappear')
            number,name=m.groups()
            if number in seen:raise ValueError('Duplicate Charter section')
            seen.add(number);body=BeautifulSoup(str(p),'html.parser');body.strong.decompose();text=body.get_text('\n',strip=True)
            if not text:raise ValueError('Empty operative source')
            locator={'panel_index':panel_index,'paragraph_index':paragraph_index,'container':'#main-content .oc-wysiwyg-container-panel .oc-wysiwyg-container-panel-content > p'}
            nodes.append({'node_id':'charter::'+number,'article':article,'section_number':number,'section_name':name,'source_url':URL,'locator':locator,'disposition':'included_sample' if number in selected else 'excluded_validation_scope','source_order':len(nodes)})
            if number not in selected:continue
            row=dict.fromkeys(FIELDS,'');row.update(jurisdiction='Emeryville, CA',code_name='City Charter',article=article,section_number=number,section_name=name,citation='Section '+number+'. '+name,full_text=text,source_url=URL,scrape_date=scrape_date or datetime.date.today().isoformat());rows.append(row)
            provenance.append({'node_id':'charter::'+number,'raw_sha256':sha(data),'locator':locator,'semantic_html':str(p)})
    if seen!=set(['100','200','201','202','300','301','302','400']):raise ValueError('First-party Charter structure changed; requalify profile')
    if {r['section_number'] for r in rows}!=set(selected):raise ValueError('Requested sections absent')
    return rows,nodes,provenance

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--input',type=Path,help='Optional retained replay; omitting performs live HTTP');a=ap.parse_args()
    if a.out.exists():raise ValueError('Fresh output required')
    a.out.mkdir(parents=True);source=a.out/'raw/charter.html';started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    if a.input:source.parent.mkdir(parents=True);source.write_bytes(a.input.read_bytes());receipt={'status':'retained_replay','url':URL,'sha256':sha(source.read_bytes())}
    else:
        receipt=get(URL,source)
        if receipt['status']!='downloaded':raise RuntimeError(receipt.get('error'))
    data=source.read_bytes();rows,nodes,provenance=parse(data,scrape_date=started[:10]);meta={'scope':'bounded_charter_sample','full_municipal_code_qualified':False,'source_sha256':sha(data),'record_count':len(rows),'independent_source_nodes':len(nodes)}
    (a.out/'fulltext.json').write_text(json.dumps({'metadata':meta,'provisions':rows},ensure_ascii=False,indent=2)+'\n')
    with (a.out/'fulltext.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
    with (a.out/'fulltext.csv').open(encoding='utf-8-sig',newline='') as f:assert list(csv.DictReader(f))==rows
    for name,items in [('source-nodes',nodes),('record-provenance',provenance)]: (a.out/(name+'.jsonl')).write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in items))
    report=meta|{'status':'passed_bounded_charter_only','transport':receipt,'argv':sys.argv,'started_at':started,'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'csv_json_equal':True,'parser_sha256':sha(Path(__file__).read_bytes()),'limitations':['Municipal Code remains separate and unqualified by this alternative.','City page explains November4,2014 Charter adoption; no current-through amendment marker asserted.']}
    (a.out/'E2E-VALIDATION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['status','record_count','independent_source_nodes','csv_json_equal']},indent=2))
if __name__=='__main__':main()
