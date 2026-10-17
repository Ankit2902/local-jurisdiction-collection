"""Assignment-derived current source routes; no absolute runtime paths."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ASSIGNMENT=json.loads((ROOT/'assignment.json').read_text())
def slug(a):return re.sub(r'[^a-z0-9]+','-',a['jurisdiction'].lower()).strip('-')
URLS={}
for a in ASSIGNMENT:
 lead=a['source_lead_url']
 if a['sequence']==95:lead='https://library.municode.com/la/baton_rouge%2C_east_baton_rouge_parish'
 if a['sequence']==96:lead='https://library.municode.com/nv/clark_county'
 URLS[a['sequence']]=lead.rstrip('/')+'/codes/code_of_ordinances'
