"""Supplemental official family routing and download-link discovery; no full corpus claim."""
import json
from pathlib import Path
from discover_official import Links
from municode_shared import fetch
from urllib.parse import urljoin
ROOT=Path(__file__).resolve().parent
JOBS=[('charlotte-udo-official-routing','https://www.charlottenc.gov/Growth-and-Development/Planning-and-Development/Zoning/Zoning-Ordinance'),('charlotte-udo-reader','https://charlotteudo.org/'),('charlotte-udo-article1','https://charlotteudo.org/articles/part-i-ordinance-introduction/article-1-title-purpose-applicability'),('memphis-development','https://www.memphistn.gov/unified-development-code/')]
results=[]
for name,url in JOBS:
 p=ROOT/'raw/families'/name/'source.html';r={'name':name,'url':url,'scope':'Supplemental family discovery only; legal section normalization not claimed'}
 try:
  b,receipt=fetch(url,p);parser=Links();parser.feed(b.decode('utf8','replace'));r.update(status='acquired',links=[urljoin(url,u) for u in parser.links if any(t in u.lower() for t in ['.pdf','charter','code','article','version','download'])]);print(name,r['status'],len(b),flush=True)
 except Exception as e:r.update(status='failed',error=str(e));print(name,str(e),flush=True)
 results.append(r)
(ROOT/'family-discovery.json').write_text(json.dumps(results,indent=2))
