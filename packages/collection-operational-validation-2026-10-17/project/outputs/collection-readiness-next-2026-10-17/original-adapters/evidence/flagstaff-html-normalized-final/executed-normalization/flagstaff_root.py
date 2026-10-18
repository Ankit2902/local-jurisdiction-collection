"""Native primary-publication root inventory, independent of expanded per-title readers."""
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from source_common import clean,decode
URL='https://www.codepublishing.com/AZ/Flagstaff/'
ROOT_TOC_URL=URL+'cgi/FlagstaffTOC.pl?archive=html'
def root_inventory(raw):
 bs=BeautifulSoup(decode(raw)[0],'html.parser');scope=bs.select_one('#divmuni')
 if scope is None:raise ValueError('Native primary City Code root selector absent')
 roots=[]
 for p in scope.find_all('p',recursive=False):
  box=p.select_one('input[name="code"]');a=p.find('a',href=True)
  if a is None:continue
  if box is None and (not a.get('id') or p.select_one('span.ajx') is None):raise ValueError('Native root anchor lacks observed expansion identity')
  u=urljoin(ROOT_TOC_URL,a['href'])
  if not u.startswith(URL+'html/') or not u.lower().endswith('.html'):raise ValueError('Unprofiled primary root route '+u)
  roots.append({'source_url':u,'value':box['value'] if box is not None else a['href'],'label':clean(a.get_text(' ',strip=True)),'source_id':a.get('id')})
 if len(roots)<10 or len({r['source_url'] for r in roots})!=len(roots) or any('Employee' in r['label'] for r in roots):raise ValueError('Primary root scope empty/truncated/duplicate/foreign publication')
 return roots
