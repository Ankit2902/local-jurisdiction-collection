#!/usr/bin/env python3
"""Codex/browser-free bounded intake of ordinary Code Publishing SaveHTML exports.
Requires operator acquisition receipt and expected currency; no network calls.
"""
import argparse,copy,csv,hashlib,json,re,shutil,subprocess,sys
from pathlib import Path
from bs4 import BeautifulSoup,Tag
import cp_collect as cp
HERE=Path(__file__).resolve().parent
ROUTES={r['slug']:r for r in json.loads((HERE/'routes.json').read_text())}
SLUGS=['flagstaff-az','fremont-ca','san-carlos-ca','burien-wa','renton-wa']
def norm(s):return ' '.join(s.split())
def sha(b):return hashlib.sha256(b).hexdigest()
def read_export(receipt_path,expected_currency):
    receipt_path=Path(receipt_path).resolve();r=json.loads(receipt_path.read_text());slug=r['metadata']['slug']
    if slug not in SLUGS or r['export_format']!='HTML' or not cp.allowed(ROUTES[slug]['discovery_url'],r['source_url']):raise ValueError('Export jurisdiction/format/source URL mismatch')
    raw=cp.safe_path(receipt_path.parent,r['raw_artifact']).read_bytes()
    if sha(raw)!=r['raw_sha256']:raise ValueError('Publisher download SHA256 mismatch')
    soup=BeautifulSoup(cp.decode(raw),'html.parser')
    if soup.select_one('form#saveForm,form#myForm,#challenge-form') or cp.BLOCKED.search(soup.title.get_text() if soup.title else ''):raise ValueError('Download is navigation/challenge instead of publisher export')
    main=soup.select_one('#mainContent');heads=main.select('h3.Cite') if main else []
    if not main or not heads:raise ValueError('Missing legal export headings')
    currencies={norm(x['headerdisc']) for x in main.select('[headerdisc]') if x['headerdisc'].strip()}
    if not currencies:
        currencies={norm(x) for x in re.findall(r'The [^.]*? (?:is|are) current through [^.]*\.',soup.get_text(' ',strip=True))}
    if currencies!={norm(expected_currency)}:raise ValueError('Missing, mixed or unexpected publisher currency')
    name=ROUTES[slug]['jurisdiction']+(' City Code' if slug=='flagstaff-az' else ' Municipal Code')
    labels={norm(x['headertitle']) for x in main.select('[headertitle]') if x['headertitle'].strip()}
    if slug=='flagstaff-az':
        if not soup.title or soup.title.get_text(strip=True)!='Flagstaff' or 'Flagstaff City Code' not in soup.get_text(' ',strip=True):raise ValueError('Flagstaff publication identity mismatch')
    elif labels!={name}:raise ValueError('Publisher human-readable code name mismatch')
    return r,raw,main,name

def bounded_selection(main,chapter_numbers):
    if not 1<=len(chapter_numbers)<=3 or len(set(chapter_numbers))!=len(chapter_numbers):raise ValueError('Choose1–3 distinct observed chapters')
    children=list(main.children);title=main.select_one('h1.Title')
    if not title or title.parent is not main:raise ValueError('Unqualified nested title layout')
    chapters=[(i,e) for i,e in enumerate(children) if isinstance(e,Tag) and e.name=='h2' and 'CH' in e.get('class',[])]
    if not chapters:raise ValueError('Unqualified export chapter layout')
    wanted=set(chapter_numbers);chosen=[];ranges=[]
    for n,(start,h) in enumerate(chapters):
        m=re.match(r'^CHAPTER\s+([0-9]+(?:[.-][0-9]+)*)\b',norm(h.get_text(' ',strip=True)),re.I)
        if m and m.group(1) in wanted:
            end=chapters[n+1][0] if n+1<len(chapters) else len(children)
            # A final export footer is outside legal body ranges. This pilot only
            # admits a final chapter if its range does not contain a footer.
            block=children[start:end]
            if any(isinstance(x,Tag) and (x.get('id') in ['pgFooter','disclaimer'] or x.find(id='pgFooter')) for x in block):raise ValueError('Final chapter/footer boundary requires explicit qualification')
            chosen.extend(copy.copy(x) for x in block);ranges.append({'chapter':m.group(1),'heading':norm(h.get_text(' ',strip=True)),'source_child_start':start,'source_child_end_exclusive':end,'serialized_range_sha256':sha(''.join(map(str,block)).encode())})
    if {r['chapter'] for r in ranges}!=wanted:raise ValueError('Requested chapter absent or duplicate/unqualified chapter heading')
    derived='<main id="mainContent">'+str(copy.copy(title))+''.join(map(str,chosen))+'</main>'
    return derived.encode(),ranges

def anchor(h):
    a=h.find('a',id=True);n=h.find('a',attrs={'name':True})
    return h.get('id') or (a.get('id') if a else None) or (n.get('name') if n else None)

def audit(derived,rows,nodes):
    source=BeautifulSoup(derived,'html.parser');legal=source.select('h3.Cite')
    expected=[cp.NUMBER.match(norm(h.get_text(' ',strip=True))).group(1) for h in legal]
    if [r['section_number'] for r in rows if r['section_number']]!=expected:raise ValueError('Numbered source inventory/order differs')
    locators=[anchor(h) for h in legal]
    if None in locators or len(locators)!=len(set(locators)):raise ValueError('Missing or duplicated actual export locator')
    actual=[n['locator']['value'] for n in nodes if n['node_kind']=='section']
    if actual!=locators or any(n['locator']['kind']!='html-id' for n in nodes if n['node_kind']=='section'):raise ValueError('Observed anchor rewrite lost')
    toc=[a['href'].lstrip('#') for a in source.select('.CiteTOC a[href]')]
    if toc and set(toc)!=set(locators):raise ValueError('Export section TOC denominator mismatch')
    clean=copy.deepcopy(source)
    for e in clean.select(cp.SKIP):e.decompose()
    export=BeautifulSoup(''.join(r['full_text'] for r in rows),'html.parser')
    paragraphs=[norm(p.get_text(' ',strip=True)) for p in clean.select('p') if p.get_text(strip=True)]
    text=norm(export.get_text(' ',strip=True))
    if paragraphs!=[norm(p.get_text(' ',strip=True)) for p in export.select('p') if p.get_text(strip=True)]:raise ValueError('Complete source paragraph text/order differs')
    text_source=copy.deepcopy(clean)
    for h in text_source.select('h1,h2,h3,h4,h5,h6'):h.decompose()
    if norm(text_source.get_text(' ',strip=True))!=text:raise ValueError('Complete owned body text/order differs')
    counts={}
    for tag in ['table','tr','td','th','sup','sub','ol','ul','li','blockquote']:
        sig=lambda e:(norm(e.get_text(' ',strip=True)),e.get('rowspan'),e.get('colspan'),e.get('type'),e.get('start'))
        if [sig(e) for e in clean.select(tag)]!=[sig(e) for e in export.select(tag)]:raise ValueError('Structure differs '+tag)
        counts[tag]=len(clean.select(tag))
    if any(not r['code_name'] or not r['title'] or not r['chapter'] for r in rows):raise ValueError('Observed hierarchy/display name missing')
    return {'numbered_sections':len(legal),'records':len(rows),'number_order_equal':True,'source_anchor_ids':locators,'paragraphs_checked':len(paragraphs),'complete_bodies_equal':True,'structure_counts':counts,'toc_anchor_inventory_equal':bool(toc)}

def run(receipt_path,out,chapters,expected_currency):
    out=Path(out).resolve()
    if out.exists() and any(out.iterdir()):raise ValueError('Immutable intake output exists; choose fresh --out')
    r,raw,main,name=read_export(receipt_path,expected_currency);derived,ranges=bounded_selection(main,chapters);slug=r['metadata']['slug'];route=ROUTES[slug]
    out.mkdir(parents=True,exist_ok=True);(out/'raw').mkdir();(out/'raw/publisher-export.html').write_bytes(raw);(out/'raw/selected-chapters.html').write_bytes(derived)
    shutil.copyfile(receipt_path,out/'download-receipt.json');(out/'executed-import-script.py').write_bytes(Path(__file__).read_bytes());(out/'executed-parser.py').write_bytes((HERE/'cp_collect.py').read_bytes())
    page={'publication_id':'city-code','content_selector':'#mainContent','url':r['source_url'],'path':'raw/selected-chapters.html','sha256':sha(derived),'publisher_version':expected_currency,'export_original_sha256':sha(raw)}
    snapshot={'jurisdiction_slug':slug,'jurisdiction':route['jurisdiction'],'root_url':route['discovery_url'],'snapshot_id':'publisher-html-'+sha(raw)[:16]+'-'+sha(derived)[:8],'retrieved_at':r['finished_at'],'publications':[{'publication_id':'city-code','title':name,'currency_raw':expected_currency,'scope_status':'bounded_export_chapters_only'}],'pages':[page],'inventory_complete':False,'coherent_publication_version':False}
    cp.save(out/'snapshot.json',snapshot);cp.save(out/'source-lineage.json',{'original_download_sha256':sha(raw),'original_download_bytes':len(raw),'derived_sha256':sha(derived),'derivation':'copy actual title heading and explicit h2.CH sibling ranges; source IDs/text not rewritten','ranges':ranges,'unattended_local_processing':True,'unattended_acquisition':False})
    logs=[]
    for args in [['--out',str(out/'resumed'),'--checkpoint',str(out/'checkpoint.json'),'--stop-after','1'],['--out',str(out/'resumed'),'--checkpoint',str(out/'checkpoint.json')],['--out',str(out/'export')]]:
        command=[sys.executable,str(HERE/'cp_collect.py'),'replay','--snapshot',str(out/'snapshot.json')]+args
        p=subprocess.run(command,capture_output=True,text=True);logs.append({'argv':command,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
        if p.returncode:raise ValueError('Delivered parser CLI failed '+p.stderr[-600:])
    for f in ['aggregate-fulltext.json','aggregate-fulltext.csv','source-nodes.jsonl','node-dispositions.jsonl','record-provenance.jsonl']:
        if (out/'export'/f).read_bytes()!=(out/'resumed'/f).read_bytes():raise ValueError('Clean/resumed difference '+f)
    rows=json.loads((out/'export/aggregate-fulltext.json').read_text())['provisions'];nodes=[json.loads(s) for s in (out/'export/source-nodes.jsonl').read_text().splitlines()]
    with (out/'export/aggregate-fulltext.csv').open(encoding='utf-8-sig',newline='') as f:
        if list(csv.DictReader(f))!=rows:raise ValueError('CSV/JSON difference')
    result={'slug':slug,'status':'operator_publisher_html_download_to_standalone_import_verified','unattended_acquisition':False,'unattended_local_processing':True,'export_format':'HTML','source_url':r['source_url'],'publisher_currency':expected_currency,'downloaded_title_scope':r['metadata']['selection'],'parsed_chapters':chapters,'original_download_sha256':sha(raw),'derived_sha256':sha(derived),'import_script_sha256':sha(Path(__file__).read_bytes()),'parser_sha256':sha((HERE/'cp_collect.py').read_bytes()),'csv_json_equal':True,'restart_equal':True,'whole_corpus_complete':False,'audit':audit(derived,rows,nodes)}
    cp.save(out/'commands.json',logs);cp.save(out/'intake-validation.json',result);return result
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipt',required=True);p.add_argument('--out',required=True);p.add_argument('--chapter',required=True,action='append');p.add_argument('--expected-currency',required=True);a=p.parse_args();print(json.dumps(run(a.receipt,a.out,a.chapter,a.expected_currency),indent=2))
