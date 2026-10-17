"""Authoring result matrix from finalized results; never called during verification."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'README.md';text=p.read_text().split('<!-- RECORDED OUTCOMES -->')[0].rstrip()+'\n\n<!-- RECORDED OUTCOMES -->\n\n## Recorded outcomes\n\n'
rows=json.loads((ROOT/'results.json').read_text());text+='|Seq.|Jurisdiction|Status|Legal provisions|PDF-page records|Primary native download|Edition label check|\n|---|---|---|---:|---:|---|---|\n'
for r in rows:
 ed=r['publisher_download'].get('edition_check',{}).get('edition_alignment_status','not tested')
 text+='|'+ '|'.join(str(v).replace('|','/') for v in [r['sequence'],r['jurisdiction'],r['status'],r['record_units']['legal_provisions'],r['record_units']['supplemental_pdf_pages'],r['publisher_download']['status'],ed])+'|\n'
text+='\nPrimary live legal samples and supplemental PDF pages are separate units. Full jurisdiction corpus completeness and production ingestion remain untested for every row. Historical interrupted attempts are retained without double-counting them in this matrix. Read-only replay also verifies those historical bytes.\n';p.write_text(text)
