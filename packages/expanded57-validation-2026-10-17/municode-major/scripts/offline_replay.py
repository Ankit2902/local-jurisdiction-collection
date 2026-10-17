"""Read-only retained-evidence verification; all replay outputs go to temporary directories."""
import sys
sys.dont_write_bytecode=True
import hashlib,json,tempfile,shutil,subprocess,os
from pathlib import Path
from normalize import normalize
import native_samples
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assignment=json.loads((ROOT/'assignment.json').read_text());results=json.loads((ROOT/'results.json').read_text());assert len(results)==len(assignment)==13
 assert sorted(r['sequence'] for r in results)==sorted(a['sequence'] for a in assignment)
 report={'passed':True,'assignment_count':13,'primary_table_source_checks':[],'primary_replays':[],'native_replays':[],'publisher_pdf_checks':[],'complete_corpus_claims':0}
 for r in results:
  assert r['complete_corpus'] is False
  for path in r['evidence_paths']+r['script_paths']:assert (ROOT/path).is_file(),path
  name=r['jurisdiction'].lower().replace(' ','-')
  qa_path=ROOT/'qa/primary-tables'/name/'table-dom-qa.json'
  if qa_path.exists():
   qa=json.loads(qa_path.read_text());assert qa['passed'] and qa['network_requests_sent']==0 and all(c['passed'] and not c['mismatches'] for c in qa['checks'])
   normalized=next(d/'normalized/sections.jsonl' for d in [ROOT/'http'/name,ROOT/'recovery'/name,ROOT/'browser'/name] if (d/'normalized/sections.jsonl').exists());assert sha(normalized)==qa['normalized_jsonl_sha256']
   assert {'tag','rowspan','colspan','rendered_cell_innerText_whitespace_normalized'}==set(qa['checks'][0]['fields_checked'])
  for d in [ROOT/'http'/name,ROOT/'recovery'/name,ROOT/'browser'/name]:
   if not (d/'receipt.json').exists():continue
   receipt=json.loads((d/'receipt.json').read_text())
   for x in receipt.get('responses',[]):assert sha(d/x['file'])==x['sha256'],str(d/x['file'])
   if (d/'samples.json').exists() and (d/'normalized/verification.json').exists():
    expected=json.loads((d/'normalized/verification.json').read_text())
    with tempfile.TemporaryDirectory() as temp:
     check=normalize(d,Path(temp));assert check['outputs_sha256']==expected['outputs_sha256'],str(d)
     from lxml import html
     for record in [json.loads(l) for l in (Path(temp)/'sections.jsonl').read_text().splitlines()]:
      if not record['tables']:continue
      source=html.fragment_fromstring(record['html'],create_parent=True);source_rows=[len(t.xpath('.//tr')) for t in source.xpath('.//table')];parsed_rows=[len(t) for t in record['tables']];assert source_rows==parsed_rows,(str(d),record['node_id'])
      report['primary_table_source_checks'].append({'jurisdiction':r['jurisdiction'],'node_id':record['node_id'],'rows':parsed_rows,'source_HTML_rows_match':True})
    report['primary_replays'].append({'jurisdiction':r['jurisdiction'],'records':check['record_count'],'tables':check['table_count'],'output_hashes_equal':True})
   pdf=d/'publisher-export.pdf'
   if pdf.exists():
    from pypdf import PdfReader
    expected=receipt['publisher_download']['sha256'];assert sha(pdf)==expected
    p=PdfReader(pdf);assert len(p.pages)>0 and p.pages[0].extract_text().strip();report['publisher_pdf_checks'].append({'jurisdiction':r['jurisdiction'],'pages':len(p.pages),'source_sha256_equal':True,'first_page_text':True})
 with tempfile.TemporaryDirectory() as temp:
  sandbox=Path(temp);native_samples.ROOT=sandbox
  for name,cfg in native_samples.SOURCES.items():
   source=ROOT/'native'/name;dest=sandbox/'native'/name;dest.mkdir(parents=True)
   path=source/('source.'+cfg['format']);receipt=json.loads(path.with_name(path.name+'.receipt.json').read_text());assert sha(path)==receipt['sha256']
   for p in [path,path.with_name(path.name+'.receipt.json')]:shutil.copyfile(p,dest/p.name)
   native_samples.run(name,True)
   for fname in ['normalized.jsonl','normalized.csv']:assert sha(source/fname)==sha(dest/fname),(name,fname)
   expected=json.loads((source/'validation.json').read_text());report['native_replays'].append({'name':name,'records':expected['record_count'],'output_hashes_equal':True})
 if (ROOT/'aurora-current/verify_aurora.py').exists():
  cp=subprocess.run([sys.executable,str(ROOT/'aurora-current/verify_aurora.py')],cwd=ROOT/'aurora-current',env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},text=True,capture_output=True,check=True)
  report['additional_family_replays']=[{'jurisdiction':'Aurora','records':15,'replay_and_native_export_equivalence':True,'stdout':cp.stdout}]
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
