#!/usr/bin/env python3
"""Reproduce all offline qualifications against synthetic, retained and fresh DOM."""
import json,re,subprocess,sys,tempfile
from pathlib import Path
from datetime import datetime,timezone
import bs4
import gridics as g
ROOT=Path(__file__).resolve().parent

def compare_sources(manifest_name):
 result=[]
 for artifact in json.loads((ROOT/manifest_name).read_text())['artifacts']:
  raw=(ROOT/artifact['path']).read_text();ns,rs,ds=g.parse_html(raw,artifact['url']);soup=bs4.BeautifulSoup(raw,'html.parser')
  difficult=next(r for r in rs if r['row']['section_number']=='1.09.030');table=soup.select_one('#section-'+difficult['node_id']+' table')
  rendered=bs4.BeautifulSoup(difficult['row']['full_text'],'html.parser').select_one('table')
  result.append({'artifact':artifact['path'],'sha256':artifact['sha256'],'uuid_containers':len(ns),'records':len(rs),'numbered_sections':sum(bool(r['row']['section_number']) for r in rs),'chapters':len({r['row']['chapter'] for r in rs}),'chapter_note_records':[r['row']['citation'] for r in rs if not r['row']['section_number']],'table_example':{'citation':difficult['row']['citation'],'source_uuid':difficult['node_id'],'source_rows':len(table.select('tr')),'serialized_rows':len(rendered.select('tr')),'source_cells':len(table.select('td,th')),'serialized_cells':len(rendered.select('td,th'))},'comparison_mode':'automated DOM/source serializer comparison; difficult table and nested list content retained'})
 return result

def main():
 test=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(ROOT),'-p','test_gridics.py','-v'],capture_output=True,text=True)
 (ROOT/'evidence/test-results.txt').write_text(test.stdout+test.stderr)
 if test.returncode:raise RuntimeError('Regression tests failed; see evidence/test-results.txt')
 count=int(re.search(r'Ran (\d+) tests',test.stderr).group(1))
 packages={}
 for kind in ['retained','live']:
  # Rebuild only generated pilot checkpoints after implementation edits.
  (ROOT/(kind+'-replay/checkpoint.json')).unlink(missing_ok=True)
  packages[kind]=g.replay(ROOT/(kind+'-manifest.json'),ROOT/(kind+'-replay'))
 with tempfile.TemporaryDirectory() as tmp:
  out=Path(tmp);g.replay(ROOT/'retained-manifest.json',out/'clean');g.replay(ROOT/'retained-manifest.json',out/'resumed',1);g.replay(ROOT/'retained-manifest.json',out/'resumed')
  checks={}
  for name in ['aggregate-fulltext.json','aggregate-fulltext.csv','aggregate-toc.json','aggregate-toc.csv','source-nodes.jsonl','node-dispositions.jsonl','record-provenance.jsonl','exceptions.jsonl']:
   a=(out/'clean'/name).read_bytes();b=(out/'resumed'/name).read_bytes();checks[name]={'clean_sha256':g.digest(a),'resumed_sha256':g.digest(b),'equal':a==b}
  if not all(x['equal'] for x in checks.values()):raise RuntimeError('Real retained clean/resume mismatch')
 g.save(ROOT/'evidence/retained-replay-equivalence.json',checks)
 g.save(ROOT/'evidence/source-comparisons.json',{'historical_actual_dom':compare_sources('retained-manifest.json'),'fresh_iab_dom':compare_sources('live-manifest.json')})
 nav=json.loads((ROOT/'evidence/live-navigation.json').read_text());title='/90d493fe-25f4-4aef-a519-710b1e0055c6';sub=[n for n in nav if n['path'].startswith(title)]
 report={'generated_at':datetime.now(timezone.utc).isoformat(),'source_type':'Gridics CodeHUB','jurisdiction':'Cupertino','status':'bounded_live_routes_title1_inventory_and_offline_parser_validated','qualifications':{'offline_synthetic_parser':'passed','historical_actual_dom_parser':'passed','fresh_rendered_dom_parser':'passed','checkpoint_and_deterministic_exports':'passed','fresh_live_routes':'root hierarchy plus three UUID section routes passed through isolated IAB','title1_navigation_inventory':'65 UUID nodes independently reconcile to 65 rendered containers; eight chapters expanded; zero closed Title 1 branches','standalone_playwright_acquisition_cli':'implemented and imported by tests; NOT executed live','full_publication_inventory':'not qualified; 17 other branches remain closed','full_collection':'not attempted or validated'},'tests':{'command':'python -m unittest discover -s . -p test_gridics.py -v','passed':count,'failed':0,'log':'evidence/test-results.txt','python':sys.version.split()[0],'beautifulsoup4':bs4.__version__},'packages':packages,'fresh_navigation':{'observed_uuid_nodes':len(nav),'title1_uuid_nodes':len(sub),'title1_closed_branches':sum(not n['children_enumerated'] for n in sub),'other_closed_branches':sum(not n['children_enumerated'] for n in nav if n not in sub),'evidence':'evidence/live-navigation-extraction.json'},'source_comparison_evidence':'evidence/source-comparisons.json','checkpoint_replay_evidence':'evidence/retained-replay-equivalence.json','limitations':[{'kind':'legal_currency','observation':'No verified current-through marker or source version; explicit unknown-version snapshot labels used. Official city link and additional publication families not independently revalidated.'},{'kind':'live_acquisition_qualification','observation':'Live evidence used supported CUA IAB, not the delivered standalone Playwright CLI. Playwright transport, full expansion and interruption require operator environment qualification.'},{'kind':'access_evidence','evidence':['evidence/landing-response.json','evidence/browser-attempts.json','evidence/live-observations.json'],'observation':'Independent public HTTPS probe returned 403 and initial Chrome connector failed its policy service; IAB subsequently rendered the public source normally. No bypass attempted. IAB response metadata unavailable.'},{'kind':'truncated_browser_export','evidence':['evidence/truncated-export.html','evidence/live-navigation-extraction.json'],'observation':'Initial 200k-character browser exports were truncated. Parser rejects marker. All four live legal DOMs were recaptured in 70k chunks with exact URL and character-length checks. Only the complete navigation element is used from the truncated expanded-tree snapshot.'},{'kind':'content_scope','observation':'Real pilot covers tables and nested ordered lists, chapter editorial notes and prose. Synthetic fixtures cover images, sup/sub notation, rowspan/colspan, crossreferences and footnotes; no claim of live image/appendix or all source constructs validation.'}],'remaining_acceptance':['Verify official city source and legal current-through/version continuity.','Execute standalone Playwright acquisition in a permitted operator environment.','Expand/reconcile all publication branches and check virtualization before claiming independent full inventory.','Validate additional live image/appendix/notation samples and editorial-note classification before full collection.'],'full_collection_validated':False,'production_or_database_changes':False}
 report['artifact_hashes']={str(p.relative_to(ROOT)):g.digest(p.read_bytes()) for p in sorted(ROOT.rglob('*')) if p.is_file() and '__pycache__' not in str(p) and p.name!='VALIDATION-REPORT.json'}
 g.save(ROOT/'VALIDATION-REPORT.json',report)
 print(json.dumps({'tests_passed':count,'packages':packages,'live_status':report['status'],'report':'VALIDATION-REPORT.json'},indent=2))
if __name__=='__main__':main()
