#!/usr/bin/env python3
"""Replay retained official-source bytes into bounded, provenance-bearing legal records."""
import argparse,csv,hashlib,json,pathlib,re,sys,zipfile
from bs4 import BeautifulSoup
import pdfplumber
BASE=pathlib.Path(__file__).resolve().parent

def sha(b):return hashlib.sha256(b).hexdigest()
def clean(t):return re.sub(r'\s+',' ',t).strip()
def soup(b):return BeautifulSoup(b,'html.parser')
def tables(node):
 return [{'caption':clean(t.caption.get_text(' ',strip=True)) if t.caption else None,
  'rows':[[{'text':clean(c.get_text(' ',strip=True)),'tag':c.name,'rowspan':int(c.get('rowspan',1)),'colspan':int(c.get('colspan',1))} for c in tr.find_all(['td','th'],recursive=False)] for tr in t.find_all('tr')],
  'html':str(t)} for t in node.find_all('table')]
def refs(node,url):
 from urllib.parse import urljoin
 return [{'text':clean(a.get_text(' ',strip=True)),'url':urljoin(url,a['href'])} for a in node.select('a[href]')]
def portland_html(data,rawref):
 s=soup(data); records=[];chapter=None;title=clean(s.h1.get_text(' ',strip=True))
 for h in s.select('main h2,main h3'):
  text=clean(h.get_text(' ',strip=True))
  if h.name=='h2' and text.startswith('Chapter '):chapter=text
  if h.name!='h3' or not re.match(r'^\d+\.\d+\.\d+',text):continue
  node=h.parent;link=h.find('a');url='https://www.portland.gov'+link['href'];ident=re.match(r'^(\d+\.\d+\.\d+)\s+(.*)',text)
  body=node.select_one('.field--name-field-section-body');notes=node.select_one('.field--name-field-prefix-note')
  records.append({'jurisdiction':'Portland','state':'OR','publication':title,'hierarchy':[title,chapter],'id':ident[1],'heading':ident[2],'citation':'Portland City Code '+ident[1],'url':url,'text':clean(body.get_text(' ',strip=True)) if body else '', 'source_note':clean(notes.get_text(' ',strip=True)) if notes else '', 'body_html':str(body) if body else '', 'links':refs(node,url),'tables':tables(body) if body else [],'raw_ref':rawref,'record_unit':'section'})
 return records

def baltimore_html(data,rawref):
 s=soup(data);article=s.find('article');records=[];hier=[]
 for h in article.select('h1,h2,h3,h4'):
  cl=h.get('class',[])
  if ('h__section' not in cl and 'h__table' not in cl):
   if h.get('id') and any(x in cl for x in ['h__toc','h__subtitle','h__chapter']):
    lv=int(h.name[1]);hier=[x for x in hier if x[0]<lv]+[(lv,clean(h.get_text(' ',strip=True)))]
   continue
  ident=h.get('id');
  if not ident:continue # Excludes quoted section with empty ID in zoning editors note.
  chunks=[]
  for sib in h.next_siblings:
   if getattr(sib,'name',None) and re.match('^h[1-6]$',sib.name) and (sib.get('id') or 'h__section' in sib.get('class',[])):break
   chunks.append(str(sib))
  body=soup(''.join(chunks));heading=clean(h.get_text(' ',strip=True));url='https://codes.baltimorecity.gov'+ident
  records.append({'jurisdiction':'Baltimore City','state':'MD','publication':hier[0][1] if hier else 'Zoning Tables','hierarchy':[x[1] for x in hier],'id':ident,'heading':heading,'citation':'Baltimore '+('Zoning '+heading if '/zoning-tables/' in ident else (hier[0][1]+' '+heading if hier else heading)),'url':url,'text':clean(body.get_text(' ',strip=True)),'body_html':str(body),'links':refs(body,url),'tables':tables(body),'raw_ref':rawref,'record_unit':'table' if 'h__table' in cl else 'section'})
 return records

def pdf_records(file,jurisdiction,state,url,publication):
 """Page units intentionally retained; PDF section references are not section segmentation."""
 records=[]
 with pdfplumber.open(file) as pdf:
  for i,p in enumerate(pdf.pages):
   text=p.extract_text(layout=False) or '';table_objects=[]
   for t in p.find_tables():
    cells=t.extract();table_objects.append({'bbox':list(t.bbox),'rows':cells,'method':'pdfplumber ruled-line geometry; inspect PDF for authoritative spans'})
   records.append({'jurisdiction':jurisdiction,'state':state,'publication':publication,'hierarchy':[publication],'id':f'{file.stem}:page:{i+1}','heading':clean(text.split('\n')[0]) if text else '[blank page]','citation':f'{publication}, PDF page {i+1}','url':url+f'#page={i+1}','text':text,'section_references':sorted(set(re.findall(r'\b(?:33\.\d+\.\d{3}|295-\d+)\b',text))),'tables':table_objects,'raw_ref':'raw/'+file.name,'record_unit':'pdf_page','pdf_page':i+1})
 return records

def milwaukee_sections(file):
 rows=[];current=None
 with pdfplumber.open(file) as pdf:
  for i,p in enumerate(pdf.pages):
   text=p.crop((0,60,p.width,p.height-50)).extract_text() or ''
   for line in text.split('\n'):
    m=re.match(r'^(295-\d{3})\.\s+([^.]+)\.\s*(.*)',line)
    if m:
     current={'jurisdiction':'Milwaukee','state':'WI','publication':'Milwaukee Code Chapter295 Subchapter5 Residential Districts','hierarchy':['Volume2 Building and Zoning Code','Chapter295 Zoning','Subchapter5 Residential Districts'],'id':m[1],'heading':m[2],'citation':'Milwaukee Code of Ordinances '+m[1],'url':'https://city.milwaukee.gov/ImageLibrary/Groups/ccClerk/Ordinances/Volume-2/CH295-sub5.pdf#page='+str(i+1),'record_unit':'section','pdf_page_start':i+1,'pdf_page_end':i+1,'text':m[3],'tables':[],'raw_ref':'raw/'+file.name}
     rows.append(current)
    elif current:current['text']+='\n'+line;current['pdf_page_end']=i+1
 assert [r['id'] for r in rows]==['295-501','295-503','295-505']
 assert 'SINGLE-FAMILY' in rows[0]['text'] and 'MULTI-FAMILY' in rows[0]['text']
 assert '295-311-2' in rows[1]['text'] and 'Table 295-503-1' in rows[1]['text']
 return rows

def links_inventory(data,base):
 from urllib.parse import urljoin
 s=soup(data);root=s.find('main') or s
 return [{'title':clean(a.get_text(' ',strip=True)),'url':urljoin(base,a['href'])} for a in root.select('a[href]')]
def write_json(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def write_records(out,name,rows):
 (out/f'{name}.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
 with (out/f'{name}.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['jurisdiction','state','publication','id','heading','citation','url','record_unit','text','table_count','raw_ref']);w.writeheader()
  for r in rows:w.writerow({k:(len(r['tables']) if k=='table_count' else r.get(k,'')) for k in w.fieldnames})

def run(out):
 out.mkdir(parents=True,exist_ok=True);raw=BASE/'raw';hashes=[]
 for mfile in sorted(raw.glob('*.meta.json')):
  m=json.loads(mfile.read_text());ref=m.get('path')
  if ref and m.get('sha256'):
   actual=sha((BASE/ref).read_bytes());assert actual==m['sha256'],f'Raw hash mismatch: {ref}'
   hashes.append({'path':ref,'sha256':actual,'status':m.get('status'),'url':m['url']})
 portland=[]
 for name in ['portland_title1','portland_title18']:portland+=portland_html((raw/f'{name}.html').read_bytes(),f'raw/{name}.html')
 assert len(portland)>50;assert len({r['id'] for r in portland})==len(portland)
 p_tables=sum(len(r['tables']) for r in portland);assert p_tables==3
 # Critical table-bearing noise section and legal cross-reference survived.
 noise=next(r for r in portland if r['id']=='18.10.010');assert noise['tables'] and 'Land Use' in noise['heading']
 assert any(r['links'] for r in portland)
 zoning=pdf_records(raw/'portland_zoning_ch10.pdf','Portland','OR','https://www.portland.gov/sites/default/files/code/10-legal-framewk_0.pdf','Portland Title 33 Chapter 33.10')
 assert len(zoning)==4 and any('33.10.070' in r['section_references'] for r in zoning)
 write_records(out,'portland_sections',portland);write_records(out,'portland_zoning_pdf_pages',zoning)
 pi=links_inventory((raw/'portland_index.html').read_bytes(),'https://www.portland.gov/code')
 titles=[a for a in pi if re.match(r'^Title \d+',a['title'])];assert len(titles)==34
 pc=links_inventory((raw/'portland_charter.html').read_bytes(),'https://www.portland.gov/charter')
 write_json(out/'portland_inventory.json',{'code_titles':titles,'charter_chapters':[a for a in pc if a['title'].startswith('Chapter ')],'other_families':links_inventory((raw/'portland_charter_index.html').read_bytes(),'https://www.portland.gov/charter-code-policies'),'zoning_downloads':links_inventory((raw/'portland_zoning.html').read_bytes(),'https://www.portland.gov/code/33'),'scope_note':'Inventory links, not whole jurisdiction ingestion. Title33 uses separate chapter PDFs and full eFiles printable version; maps/policies separate.'})
 baltimore=[]
 with zipfile.ZipFile(raw/'baltimore_html_bulk.zip') as z:
  assert z.testzip() is None
  base=z.namelist()[0]+'us/md/cities/baltimore/'
  selected=['code/1/index.full.html','code/32/4/index.full.html','code/32/zoning-tables/index.full.html','charter/I/index.full.html']
  source_tables=0
  for suffix in selected:
   member=z.read(base+suffix);source_tables+=len(soup(member).select('article table'))
   baltimore+=baltimore_html(member,'raw/baltimore_html_bulk.zip!'+base+suffix)
  assert source_tables==sum(len(r['tables']) for r in baltimore)
  root_prefix=z.namelist()[0];memberpaths=set(z.namelist());internal_targets=[]
  for r in baltimore:
   for link in r['links']:
    from urllib.parse import urlparse
    u=urlparse(link['url'])
    if u.netloc=='codes.baltimorecity.gov' and u.path.startswith('/us/'):
     target=root_prefix+u.path.lstrip('/').rstrip('/')+'/index.html'
     internal_targets.append(target in memberpaths)
  write_json(out/'baltimore_crossref_checks.json',{'internal_links_checked':len(internal_targets),'target_member_present':sum(internal_targets),'target_member_not_found':len(internal_targets)-sum(internal_targets),'method':'absolute legal links resolved to archive path/index.html; fragments not validated'})
  inventory={'archive_entries':len(z.namelist()),'uncompressed_bytes':sum(i.file_size for i in z.infolist()),'publication_branch':'publication/2026-09-28','families':links_inventory(z.read(base+'index.html'),'https://codes.baltimorecity.gov/'),'code_publications':links_inventory(z.read(base+'code/index.html'),'https://codes.baltimorecity.gov/us/md/cities/baltimore/code'),'selected_members':selected,'archive_sha256':sha((raw/'baltimore_html_bulk.zip').read_bytes()),'all_paths':z.namelist()}
  write_json(out/'baltimore_inventory.json',inventory)
 assert len(baltimore)>100 and len({r['id'] for r in baltimore})==len(baltimore)
 b_tables=sum(len(r['tables']) for r in baltimore);assert b_tables>=37
 assert any('/charter/' in l['url'] for r in baltimore for l in r.get('links',[]))
 write_records(out,'baltimore_sections',baltimore)
 mi=links_inventory((raw/'milwaukee_browser_index.html').read_bytes(),'https://city.milwaukee.gov/cityclerk/lrb/ordinances/tableofcontents')
 write_json(out/'milwaukee_inventory.json',{'publications':[a for a in mi if '/Ordinances/' in a['url'] or a['title'] in ['Salary Ordinance','Positions Ordinance']], 'families':['City Charter','Volume 1 Regulatory Ordinances','Volume 2 Building and Zoning Code; Chapter295 subchapters','Volume 3 Administrative Ordinances','Salary Ordinance','Positions Ordinance'],'scope_note':'Standalone browser TOC success; see raw metadata for tested PDF acquisition status.'})
 milwaukee=[]
 mfile=raw/'milwaukee_residential_native.pdf'
 if mfile.exists() and mfile.read_bytes().startswith(b'%PDF-'):
  milwaukee=pdf_records(mfile,'Milwaukee','WI','https://city.milwaukee.gov/ImageLibrary/Groups/ccClerk/Ordinances/Volume-2/CH295-sub5.pdf','Milwaukee Code Chapter295 Subchapter5 Residential Districts')
  assert len(milwaukee)==35;write_records(out,'milwaukee_zoning_pdf_pages',milwaukee)
  ms=milwaukee_sections(mfile);write_records(out,'milwaukee_sections',ms)
  checkrow=next(row for row in milwaukee[3]['tables'][0]['rows'] if row[0]=='General office')
  assert checkrow==['General office','N','L','N','L','L','N','L','Y','Y']
 summary={'raw_hashes_verified':len(hashes),'portland_section_records':len(portland),'portland_html_tables':p_tables,'portland_zoning_pdf_pages':len(zoning),'portland_zoning_geometry_tables':sum(len(r['tables']) for r in zoning),'baltimore_records':len(baltimore),'baltimore_tables':b_tables,'baltimore_article1_sections':sum('/code/1/' in r['id'] for r in baltimore),'baltimore_zoning_title4_sections':sum('/code/32/4-' in r['id'] for r in baltimore),'baltimore_charter_articleI_sections':sum('/charter/' in r['id'] for r in baltimore),'baltimore_table_records':sum(r['record_unit']=='table' for r in baltimore),'milwaukee_section_records':3 if milwaukee else 0,'milwaukee_pdf_page_records':len(milwaukee),'milwaukee_geometry_tables':sum(len(r['tables']) for r in milwaukee),'checks':['raw byte SHA256 matches acquisition metadata','unique legal record IDs','Portland Title1 and Title18 section counts >50','Portland noise table 18.10.010 preserved with span metadata','Baltimore ZIP CRC integrity','Baltimore selected HTML tables preserve cells/spans; zoning source37 tables preserved across36 table-heading records','legal cross-references retained as absolute links','PDF page records labeled separately from Milwaukee3 section records','Milwaukee General office use-table row matches9 classifications; rotated headers require review']}
 write_json(out/'verification.json',summary);write_json(out/'verified_raw_manifest.json',hashes);print(json.dumps(summary,indent=2));return summary
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--offline',action='store_true',help='Replay retained raw bytes; zero network activity (always true for this script)');ap.add_argument('--out',type=pathlib.Path,default=BASE/'parsed');a=ap.parse_args();run(a.out)
