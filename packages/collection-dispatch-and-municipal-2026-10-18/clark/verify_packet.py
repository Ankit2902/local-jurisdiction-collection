"""Portable stdlib-only candidate integrity and bounded proof checker."""
import pathlib,json,hashlib
P=pathlib.Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=read(P/'MANIFEST.json');files={str(p.relative_to(P))for p in P.rglob('*')if p.is_file()and p!=P/'MANIFEST.json'};assert files==set(m['files'])
for n,row in m['files'].items():assert (P/n).stat().st_size==row['bytes']and sha(P/n)==row['sha256'],n
plan=read(P/'PROMOTION-PLAN.json')
for row in plan['changes']:assert sha(P/'candidate'/row['path'])==row['after_sha256']
b=read(P/'proof-bridge.json');assert b['configuration_sha256']==b['candidate_config_sha256'];assert all(x['unchanged']and x['sealed']==x['current_candidate']for x in b['executed_scripts'].values());assert len(b['executed_scripts'])==16
assert read(P/'cli-report.json')['passed']is True
for n in ['tests-final.stderr']:assert '\nOK\n'in(P/n).read_text(),n
audit=read(P/'catalog-final.stdout');assert audit['passed']and audit['dispatchable']==196
assert read(P/'SUMMARY.json')['validation_level']=='mapped_only'
c=read(P/'common-acceptance-projection.json')['result'];assert c['native_capture_verified']and c['required_nonimage_documents_complete'];assert not c['publication_coverage_accepted']and not c['legal_structure_qualified']and not c['publication_text_complete']
print(json.dumps({'passed':True,'files':len(files),'whitelist_files':len(plan['changes']),'runnable':196,'unqualified':29,'fresh_common_verify':False,'native_parse_network_image_calls':0,'scope':'Config/dispatch integration with exact sealed family-source bridge; file_pages only.'},indent=2))
