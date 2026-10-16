#!/usr/bin/env python3
"""Offline qualify actual standalone acquisitions, then invoke portable corpus replay.
A prior CUA full Contents inventory remains explicitly separate from standalone body acquisition.
"""
from pathlib import Path
import argparse
import municipal_codes_cli as m
from prepare_e2e import currency
ROOT=Path(__file__).resolve().parent
SOURCES={'berkeley-ca':[('headed-legal-stable','page'),('headed-ui-export','download')],'petaluma-ca':[('headed-legal-stable','page')],'sonoma-ca':[('headed-legal-stable','page')],'bellingham-wa':[('headed-pilot','page')],'everett-wa':[('headed-ui-export','download')]}

def qualify(folder,slug,kind):
 receipt=m.read_json(folder/'receipt.json');base=m.ROUTES[slug][2];url=receipt['job']['section_url'];expected=receipt['job']['expected_id']
 if kind=='page':
  stage=next(s for s in receipt['stages'] if s['kind']=='page');accepted=stage['accepted'];path=folder/stage['raw_artifact_path'];expected_sha=stage['raw_sha256']
 else:accepted=receipt['accepted'];path=folder/'download.html';expected_sha=receipt['raw_sha256']
 if not accepted:raise m.QualificationError('Rejected acquisition '+str(folder))
 raw=path.read_bytes()
 if m.sha(raw)!=expected_sha:raise m.QualificationError('Raw SHA mismatch')
 rows,notes=m.parse_page(raw.decode('utf8'),url,base)
 if not any(r['node_id']=='dom:'+expected for r in rows):raise m.QualificationError('Expected source node not parsed')
 if any(n.get('status')=='unresolved' for n in notes):raise m.QualificationError('Unresolved parsing issue')
 legal_currency=currency(raw.decode('utf8'))
 if not legal_currency or 'current through' not in legal_currency:raise m.QualificationError('No displayed publication currency')
 stable=None
 if kind=='page' and stage.get('before_sha256') and stage.get('after_sha256'):
  bodies=[];currencies=[]
  for name,digest in [('page-before.html',stage['before_sha256']),('page-after.html',stage['after_sha256'])]:
   data=(folder/name).read_bytes()
   if m.sha(data)!=digest:raise m.QualificationError('Pre/post raw SHA mismatch')
   rr,_=m.parse_page(data.decode('utf8'),url,base);bodies.append([(r['node_id'],r['body_sha256']) for r in rr]);currencies.append(currency(data.decode('utf8')))
  stable=bodies[0]==bodies[1]==[(r['node_id'],r['body_sha256']) for r in rows] and currencies[0]==currencies[1]==legal_currency
  if not stable:raise m.QualificationError('Source version/body changed across retained bracket')
 return dict(path=path,source_url=url,sha256=expected_sha,rows=rows,notes=notes,raw_currency_text=legal_currency,bracket_stable=stable,receipt=receipt,transport=receipt['transport'])

def prepare(out):
 out=Path(out).resolve();out.mkdir(exist_ok=False);results=[]
 for slug,(name,_,base) in m.ROUTES.items():
  sources=[qualify(ROOT/run/slug,slug,kind) for run,kind in SOURCES[slug]];dest=out/slug;inputs=dest/'inputs';inputs.mkdir(parents=True)
  prior=ROOT/'e2e-exports'/slug/'inputs';old=m.read_json(prior/'manifest.json');inv=m.read_json(prior/'inventory.json')
  if m.sha(m.canonical(inv))!=old['inventory']['sha256']:raise m.QualificationError('Prior inventory binding changed')
  if currency((ROOT/'live-final'/slug/'chapter.html').read_text())!=sources[0]['raw_currency_text']:raise m.QualificationError('Prior independent inventory version not aligned to fresh body currency')
  (inputs/'inventory.html').write_bytes((prior/'inventory.html').read_bytes());m.write_json(inputs/'inventory.json',inv)
  manifest=dict(old);manifest.update(source_version='standalone:'+m.sha(m.canonical([s['sha256'] for s in sources])),retrieved_at=sources[0]['receipt']['started_at'],raw_currency_text=sources[0]['raw_currency_text'],snapshots=[],inventory=dict(path='inventory.json',sha256=m.sha(m.canonical(inv)),raw_path='inventory.html',raw_sha256=m.sha((inputs/'inventory.html').read_bytes())),inventory_transport='prior qualified CUA capture; no new standalone full inventory acquired',standalone_acquisition_receipts=[])
  for publication in manifest.get('discovered_publications',[]):
   if publication.get('publication_id')=='municipal-code':publication.update(raw_currency_text=sources[0]['raw_currency_text'],legal_currency_normalized=None,currency_status='observed_displayed_current_through')
  for source in sources:
   filename=source['sha256']+'.html';(inputs/filename).write_bytes(source['path'].read_bytes());manifest['snapshots'].append(dict(path=filename,source_url=source['source_url'],sha256=source['sha256']))
   manifest['standalone_acquisition_receipts'].append(dict(transport=source['transport'],raw_sha256=source['sha256'],script_sha256=source['receipt']['script_sha256'],bracket_stable=source['bracket_stable']))
  # Carry discovery bytes referenced by publications manifest into standalone output.
  m.write_json(inputs/'manifest.json',manifest);metadata=m.replay(inputs/'manifest.json',dest/'exports')
  discovery=ROOT/'e2e-exports'/slug/'exports'/'raw'/'publications-discovery.html';(dest/'exports'/'raw'/'publications-discovery.html').write_bytes(discovery.read_bytes())
  run=m.read_json(dest/'exports'/'run-manifest.json');run.update(raw_currency_text=sources[0]['raw_currency_text'],legal_currency_normalized=None,inventory_transport=manifest['inventory_transport'],standalone_acquisition_receipts=manifest['standalone_acquisition_receipts']);run['artifact_hashes']['raw/publications-discovery.html']=m.sha(discovery.read_bytes());m.write_json(dest/'exports'/'run-manifest.json',run)
  if metadata['record_count']==0:raise m.QualificationError('Qualified standalone bodies emitted zero records')
  result=dict(slug=slug,status='bounded_standalone_source_parse_export_pass',output_records=metadata['record_count'],source_url=base+'/1.01.010',raw_currency_text=sources[0]['raw_currency_text'],sources=[dict(raw_artifact_path=str(s['path'].relative_to(ROOT)),raw_sha256=s['sha256'],transport=s['transport'],bracket_stable=s['bracket_stable'],parsed_records=len(s['rows'])) for s in sources],independent_inventory='previous qualified CUA snapshot, displayed currency matched; not standalone inventory',whole_corpus_validated=False)
  results.append(result);print(slug,metadata['record_count'],flush=True)
 m.write_json(out/'results.json',results);return results
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();prepare(a.out)
