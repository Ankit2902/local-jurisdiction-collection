"""Publisher refusal qualification for retained ordinary browser HTML; no challenge interaction."""
import re
from bs4 import BeautifulSoup
from source_common import transport,clean
def guard_html(raw,url,status,headers):
 h={k.lower():str(v) for k,v in headers.items()};title=''
 if raw:
  match=re.search(br'<title\b[^>]*>(.*?)</title\s*>',raw[:100000],re.I|re.S)
  if match:title=BeautifulSoup(match.group(1),'html.parser').get_text(' ',strip=True)
 challenge=bool(re.search(r'^(?:just a moment|attention required|access denied|verify (?:you are|that you)|checking your browser|security verification|human verification|captcha)',clean(title),re.I)) or b'/cdn-cgi/challenge-platform/' in raw[:100000].lower()
 if status in [403,429] or h.get('cf-mitigated','').lower()=='challenge' or h.get('retry-after') or challenge:
  transport.stop(url,status,headers,'Ordinary browser publisher refusal/challenge: '+title)
  raise RuntimeError('Publisher access stop retained; no automatic retry or challenge interaction: '+url)
 return title
