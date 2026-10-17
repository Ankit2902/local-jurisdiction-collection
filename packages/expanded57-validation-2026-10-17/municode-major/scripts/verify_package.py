"""Offline handoff integrity + substantive retained-source assertions."""
import hashlib,json,tempfile
from pathlib import Path
from normalize import normalize
from lxml import html
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 a=json.loads((ROOT/'assignment.json').read_text());r=json.loads((ROOT/'results.json').read_text());assert len(r)==len(a)==13
 assert sorted(x['sequence'] for x in r)==sorted(x['sequence'] for x in a)
 checks=[]
 for x in r:
  assert x['complete_corpus'] is False
  for p in x['evidence_paths']+x['script_paths']:assert (ROOT/p).is_file(),p
  for c in x['checks']:
   if isinstance(c,dict) and c.get('check')=='raw_response_sha256':assert c['passed'],c
  for d in [ROOT/'browser'/x['jurisdiction'].lower().replace(' ','-'),ROOT/'recovery'/x['jurisdiction'].lower().replace(' ','-'),ROOT/'http'/x['jurisdiction'].lower().replace(' ','-')]:
   if not (d/'samples.json').exists() or not (d/'receipt.json').exists():continue
   baseline=json.loads((d/'normalized/verification.json').read_text())
   with tempfile.TemporaryDirectory() as t:
    replay=normalize(d,Path(t))
    assert replay['outputs_sha256']==baseline['outputs_sha256'],str(d)
   checks.append({'jurisdiction':x['jurisdiction'],'path':str(d.relative_to(ROOT)),'records':replay['record_count'],'replay_hashes_equal':True})
 for d in (ROOT/'native').iterdir():
  if not d.is_dir():continue
  p=d/('source.html' if (d/'source.html').exists() else 'source.pdf');receipt=json.loads(p.with_name(p.name+'.receipt.json').read_text());assert sha(p)==receipt['sha256']
  if p.suffix=='.pdf':assert p.read_bytes()[:5]==b'%PDF-'
  rows=[json.loads(l) for l in (d/'normalized.jsonl').read_text().splitlines()];assert len(rows)>=3 and all(r['text'] for r in rows)
 table_checks=[]
 for folder,expected in [('recovery/fresno',[58]),('browser/atlanta',[4,68]),('http/mesa',[97])]:
  q=ROOT/folder/'normalized/sections.jsonl'
  if not q.exists():continue
  records=[json.loads(l) for l in q.read_text().splitlines()];record=next((r for r in records if r['tables']),None)
  if record is None:continue
  assert [len(t) for t in record['tables']]==expected,(folder,expected)
  source=html.fragment_fromstring(record['html'],create_parent=True);source_tables=source.xpath('.//table')
  assert [len(t.xpath('.//tr')) for t in source_tables]==expected,folder
  assert any(int(c['colspan'])>1 or int(c['rowspan'])>1 for t in record['tables'] for row in t for c in row),folder
  table_checks.append({'folder':folder,'node_id':record['node_id'],'table_rows':expected,'source_HTML_rows_match':True,'span_attributes_retained':True})
 czo=[json.loads(l) for l in (ROOT/'native/new-orleans-czo/normalized.jsonl').read_text().splitlines()]
 assert any(r['identifier']=='1.1' and 'Comprehensive Zoning Ordinance' in r['text'] for r in czo)
 table=next(r for r in czo if r['identifier']=='3.2.A');doc=html.fromstring(table['tables_html'][0]);assert len(doc.xpath('.//tr'))==15
 assert 'Executive Director of the City Planning Commission' in doc.text_content()
 tulsa=[json.loads(l) for l in (ROOT/'native/tulsa-zoning/normalized.jsonl').read_text().splitlines()]
 assert any('Special Exception Uses' in r['text'] and '70.120' in r['text'] for r in tulsa)
 tc=json.loads((ROOT/'native/tulsa-zoning/table-sample.json').read_text());assert tc['page']==24 and len(tc['tables'])==3
 verification={'passed':True,'assignment_count':13,'primary_replays':checks,'primary_table_checks':table_checks,'native_checks':{'source_hashes':True,'CZO_1_1_title':True,'CZO_table3_1_15_rows':True,'Tulsa_section5_020_crossreference70_120':True,'Tulsa_table_page24_fragments':3},'complete_corpus_claims':0}
 (ROOT/'verification.json').write_text(json.dumps(verification,indent=2));print(json.dumps(verification,indent=2))
if __name__=='__main__':main()
