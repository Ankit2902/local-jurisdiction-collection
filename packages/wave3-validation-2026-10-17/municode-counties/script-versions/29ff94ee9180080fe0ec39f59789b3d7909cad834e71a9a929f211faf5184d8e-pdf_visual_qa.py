"""Recorded visual findings against retained native PDF table renders; no live calls."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for name,png,expected,lim in [('clark-title30','clark-title30-page19.png',['RS80','Residential Single-Family 80','30.02.02','SMO','Spring Mountain Overlay','30.02.26I'],'Visual Table30.02-1 has district abbreviations and section references. Default PDF region extraction drops many abbreviations/section cells and the final SMO row. Table grid fidelity failed; page text/PDF are retained and the grid is not promoted to normalized legal table.'),('baton-rouge-udc-uses','baton-rouge-udc-ch9-page2.png',['Agriculture','Equestrian','Sec 9.3.3','Group Home','RE/A3'],'Visual Table9.A includes merged category headers, multiline labels and permit symbols. Default extraction splits the table into regions; no complete grid fidelity certification.')]:
 d=ROOT/'native'/name;grid=json.loads((d/'normalized/table-sample.json').read_text());text=json.loads(next(l for l in (d/'normalized/pages.jsonl').read_text().splitlines() if json.loads(l)['page']==grid['page']))['text'];flat=json.dumps(grid['detected_regions']);checks=[{'visually_observed_text':s,'present_in_page_text':s in text,'present_in_default_grid':s in flat} for s in expected]
 rows.append({'publication_folder':str(d.relative_to(ROOT)),'source_pdf_sha256':sha(d/'source.pdf'),'render_path':'evidence/pdf-visual/'+png,'render_sha256':sha(ROOT/'evidence/pdf-visual'/png),'pdf_page':grid['page'],'render_method':'pdftoppm -scale-to1500; source PDF unmodified','visual_review_performed':True,'observed_checks':checks,'normalized_table_fidelity':'failed' if name=='clark-title30' else 'partial_unproven','finding':lim})
(ROOT/'evidence/pdf-visual/qa.json').write_text(json.dumps({'network_requests_sent':0,'findings':rows,'overall_table_fidelity_certified':False},indent=2))
