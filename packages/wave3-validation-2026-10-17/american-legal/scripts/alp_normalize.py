import re
from bs4 import BeautifulSoup
def clean(n):
 for e in n.select('script,style,button,.code-options,.annotation-drawer,.clearfix'):e.decompose()
 return n

def cells(node):
 return [{'table_index':ti,'row_index':ri,'cell_index':ci,'tag':c.name,'text':c.get_text(' ',strip=True),'rowspan':int(c.get('rowspan',1)),'colspan':int(c.get('colspan',1))} for ti,t in enumerate(node.find_all('table')) for ri,tr in enumerate(t.find_all('tr')) for ci,c in enumerate(tr.find_all(['td','th'],recursive=False))]

def normalize_html(html,row,url,kind):
 soup=BeautifulSoup(html,'html.parser'); scope=soup.select_one('.codenav__section-body') or soup
 chunks=scope.select('[id^="section-"]'); records=[]
 if chunks:
  for ch in chunks:
   head=ch.select_one('.toc-destination')
   if not head:continue
   title=head.get_text(' ',strip=True)
   if not re.match(r'^(?:SEC\.|§|\d)',title,re.I):continue
   docid=(head.get('id') or '').removeprefix('rid-');clean(ch)
   text=ch.get_text('\n',strip=True)
   if len(text)<=len(title)+10:continue
   citation=re.match(r'(?:SEC\.\s*|§\s*)?([\d]+[\w.\-]*[\d\w])',title,re.I)
   tables=[[[c.get_text(' ',strip=True) for c in tr.find_all(['td','th'],recursive=False)] for tr in t.find_all('tr')] for t in ch.find_all('table')]
   records.append({'jurisdiction':row['jurisdiction'],'state':row['state'],'source_family':'American Legal','source_url':url.rsplit('/',1)[0]+'/'+docid if re.fullmatch(r'0-0-0-\d+',docid) else url,'document_id':docid,'citation':citation.group(1) if citation else title,'heading':title,'text':text,'table_count':len(tables),'tables':tables,'table_cells':cells(ch),'cross_references':[{'label':a.get_text(' ',strip=True),'href':a.get('href')} for a in ch.find_all('a',href=True)],'acquisition_kind':kind,'complete_section':True})
 else:
  # Publisher exports contain source heading .Section/.Heading rather than React chunks.
  clean(scope)
  heads=scope.select('.Section,.Heading,.toc-destination')
  heads=[h for h in heads if not any(p in heads for p in h.parents)]
  for h in heads:
   title=h.get_text(' ',strip=True)
   if not re.match(r'^(?:SEC\.|§|\d+[.\-])',title,re.I):continue
   parts=[str(h)]
   for sibling in h.next_siblings:
    if getattr(sibling,'name',None) and sibling in heads:break
    parts.append(str(sibling))
   fragment=BeautifulSoup(''.join(parts),'html.parser');text=fragment.get_text('\n',strip=True)
   if len(text)<len(title)+10:continue
   citation=re.match(r'(?:SEC\.\s*|§\s*)?([\d]+[\w.\-]*[\d\w])',title,re.I)
   tables=[[[c.get_text(' ',strip=True) for c in tr.find_all(['td','th'],recursive=False)] for tr in t.find_all('tr')] for t in fragment.find_all('table')]
   docid=(h.get('id') or h.get('name') or '').removeprefix('rid-')
   records.append({'jurisdiction':row['jurisdiction'],'state':row['state'],'source_family':'American Legal','source_url':url.rsplit('/',1)[0]+'/'+docid if re.fullmatch(r'0-0-0-\d+',docid) else url,'document_id':docid,'citation':citation.group(1) if citation else title,'heading':title,'text':text,'table_count':len(tables),'tables':tables,'table_cells':cells(fragment),'cross_references':[{'label':a.get_text(' ',strip=True),'href':a.get('href')} for a in fragment.find_all('a',href=True)],'acquisition_kind':kind,'complete_section':True})
 return records

