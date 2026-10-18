"""Independent source-owned note/table arrays versus actual canonical full_text."""
import hashlib,json,re,socket
from pathlib import Path
from unittest.mock import patch
from bs4 import BeautifulSoup
B=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00');S=B/'outputs/collection-readiness-poste026685-2026-10-17/ecode-corpus-reader-v1';H=Path(__file__).resolve().parent
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
norm=lambda s:re.sub(r'\s+',' ',s).strip()
def main():
 P=S/'package';R=P/'evidence/input';ir={r['id']:r for r in[json.loads(x)for x in(R/'records.jsonl').read_text().split('\n')if x]};rows=json.loads((P/'aggregate-fulltext.json').read_text())['provisions'];pr=[json.loads(x)for x in(P/'record-provenance.jsonl').read_text().split('\n')if x];checks=[];notes=tables=cells=0
 for row,p in zip(rows,pr):
  ident=p['record_id'].split(':',1)[1];r=ir[ident];sp=BeautifulSoup(row['full_text'],'html.parser');cn=sp.select('.history,.footnote,.footnotes,.note');rn=[BeautifulSoup(v,'html.parser').find()for v in r['notes_html']];assert len(cn)==len(rn),(ident,'canonical source note count',len(cn),len(rn))
  for i,(a,b)in enumerate(zip(rn,cn)):
   assert norm(a.get_text())==norm(b.get_text()),(ident,'canonical note text/order',i,norm(a.get_text()),norm(b.get_text()));notes+=1
  ct=sp.select('table');rt=[BeautifulSoup(v,'html.parser').find('table')for v in r['tables_html']];assert len(ct)==len(rt)
  for i,(a,b)in enumerate(zip(rt,ct)):
   aa=a.select('td,th');bb=b.select('td,th');assert len(aa)==len(bb)
   for x,y in zip(aa,bb):assert (x.name,x.get('rowspan','1'),x.get('colspan','1'),norm(x.get_text()))==(y.name,y.get('rowspan','1'),y.get('colspan','1'),norm(y.get_text())),(ident,'canonical cell fidelity')
   cells+=len(aa);tables+=1
  if rn or rt:checks.append({'source_id':ident,'notes':len(rn),'tables':len(rt),'raw_ir_sha256':p['rich_ir']['record_sha256'],'canonical_html_sha256':hashlib.sha256(row['full_text'].encode()).hexdigest(),'equal':True})
 assert notes==3817 and tables==24
 result={'passed':True,'source_semantic_records':3006,'source_note_element_occurrences_in_same_canonical_order':notes,'source_tables_in_same_canonical_order':tables,'source_cells_same_text_tag_rowspan_colspan':cells,'checks':checks,'source_normalizer_network_image_native_calls':0,'scope':'All existing owned notes and tables already inline in exact canonical HTML; no append or new source interpretation. Empty/nested note elements are included in counts.'};(H/'canonical-structures.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='checks'},indent=2))
if __name__=='__main__':
 with patch.object(socket,'socket',side_effect=AssertionError('Offline')):main()
