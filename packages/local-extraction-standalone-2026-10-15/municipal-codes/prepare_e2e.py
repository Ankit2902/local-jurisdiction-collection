#!/usr/bin/env python3
"""Validate fresh script receipts, construct inventories and bounded exports. No network."""
import argparse,json,re,tempfile
from urllib.parse import urlsplit,urljoin
from pathlib import Path
from bs4 import BeautifulSoup
import municipal_codes_cli as m
ROOT=Path(__file__).resolve().parent

def load_capture(folder,ident):
 p=folder/(ident+'.receipt.json');r=m.read_json(p);raw=folder/r['raw_artifact_path'];data=raw.read_bytes()
 if not r['accepted']:raise m.QualificationError('Rejected acquisition '+str(p))
 if m.sha(data)!=r['sha256']:raise m.QualificationError('Capture SHA mismatch')
 if r['browser_state'].get('dom_sha256')!=r['sha256'] or r['after_capture'].get('dom_sha256')!=r['sha256']:raise m.QualificationError('No consistent before/raw/after SHA')
 if r['navigation_error'] or r['readiness_error']:raise m.QualificationError('Navigation/readiness failure')
 if r['browser_state']['url']!=r['job']['url'] or r['after_capture']['url']!=r['job']['url']:raise m.QualificationError('Wrong capture URL')
 return r,raw,data.decode('utf8')

def currency(html):
 s=BeautifulSoup(html,'html.parser');footer=s.select_one('#site-footer') or s.select_one('.site-footer')
 if footer is None:
  footer=next((f for f in s.select('footer') if 'current through' in f.get_text(' ',strip=True)),None)
 if footer is None:return ''
 # An article's editorial/statutory footnote footer must never stand in for legal currency.
 for candidate in footer.select('b, p'):
  value=candidate.get_text(' ',strip=True)
  if 'current through' in value:return value
 return ''

def signature(inv):return m.sha(m.canonical(inv['nodes']))

def discover_publications(folder,base,primary_currency):
 receipt,raw,html=load_capture(folder,'publications');soup=BeautifulSoup(html,'html.parser');families=[];seen=set();origin=urlsplit(base)
 for anchor in soup.select('main a[href]'):
  url=urljoin(receipt['job']['url'],anchor['href']);u=urlsplit(url)
  is_family=u.netloc==origin.netloc and not u.query and bool(re.fullmatch('/[A-Z][A-Za-z0-9]*',u.path))
  is_reference=('enactments?' in url or u.netloc!=origin.netloc)
  if not (is_family or is_reference) or url in seen:continue
  seen.add(url);primary=url.rstrip('/')==base.rstrip('/');title=anchor.get_text(' ',strip=True)
  item=dict(publication_id='municipal-code' if primary else ('publisher:'+u.path[1:] if is_family else 'reference:'+m.sha(url.encode())[:16]),publication_title=title,publication_base=url,source_url=url,source_version='discovery:'+receipt['sha256'],scope_disposition='in_scope_for_bounded_validation' if primary else 'unresolved',scope_reason='Primary code sampled only; whole publication incomplete' if primary else 'Observed additional family/reference; substantive scope decision pending',raw_currency_text=primary_currency if primary else '',legal_currency_normalized=None,legal_currency_precision=None,evidence=dict(raw_artifact_path='raw/publications-discovery.html',raw_sha256=receipt['sha256'],locator=dict(kind='href',value=anchor['href'])),publication_kind='code_family' if is_family else 'reference')
  item['discovery_display_title']=title;item['currency_status']='observed_displayed_current_through' if primary else 'not_observed_in_contents_capture'
  if primary:item['publication_title']=m.read_json(folder/'chapter.receipt.json')['browser_state']['title'].split(' | ')[-1]
  for rp in folder.glob('family-*.receipt.json'):
   r=m.read_json(rp)
   if r['job'].get('publication_base')==url and r['accepted']:
    item['publication_title']=r['browser_state']['title'].removeprefix('Contents of ');item['inventory_receipt_sha256']=m.sha(rp.read_bytes())
  families.append(item)
 if not any(f['publication_id']=='municipal-code' for f in families):raise m.QualificationError('Primary publication absent from fresh discovery')
 return families

def prepare(source,out):
 source=source.resolve();out=out.resolve();results=[]
 for slug,(name,_,base) in m.ROUTES.items():
  d=source/slug;dest=out/slug;dest.mkdir(parents=True,exist_ok=False)
  city=dict(slug=slug,whole_corpus_validated=False,transport='CUA-script',issues=[])
  before,p,html=load_capture(d,'inventory-before');inv=m.inventory(html,before['job']['url'],base,'main > ul.contents-toc')
  inv.update(source_raw_path=p.name,source_raw_sha256=before['sha256'])
  city['inventory_nodes']=len(inv['nodes']);city['inventory_before_signature']=signature(inv)
  afterid='inventory-after-verified' if (d/'inventory-after-verified.receipt.json').exists() else 'inventory-after'
  try:
   after,_,h=load_capture(d,afterid);ai=m.inventory(h,after['job']['url'],base,'main > ul.contents-toc');city['inventory_after_signature']=signature(ai)
   city['inventory_stable']=signature(inv)==signature(ai)
  except (m.QualificationError,FileNotFoundError) as e:city['inventory_stable']=False;city['issues'].append(str(e))
  snapshots=[];parsed={};versions=[]
  for ident in ('chapter','difficult','version-after'):
   receipt,raw,h=load_capture(d,ident);rows,notes=m.parse_page(h,receipt['job']['url'],base)
   parsed[ident]=dict(records=rows,notes=notes);m.write_json(dest/(ident+'-parsed.json'),parsed[ident])
   if ident!='version-after':snapshots.append(dict(path=str(raw.resolve()),source_url=receipt['job']['url'],sha256=receipt['sha256']))
   else:versions=rows
  first=parsed['chapter']['records'];city['chapter_records']=len(first);city['difficult_records']=len(parsed['difficult']['records']);city['difficult_notes']=parsed['difficult']['notes']
  city['currency_before']=currency((d/'chapter.html').read_text());city['currency_after']=currency((d/'version-after.html').read_text())
  city['currency_stable']=bool(city['currency_before']) and city['currency_before']==city['currency_after']
  city['chapter_bodies_stable']=[(r['node_id'],r['body_sha256']) for r in first]==[(r['node_id'],r['body_sha256']) for r in versions]
  city['source_stability_passed']=city['inventory_stable'] and city['currency_stable'] and city['chapter_bodies_stable']
  if not city['source_stability_passed']:city['issues'].append('Pre/post source checks incomplete or changed; bounded export remains incomplete')
  families=[]
  for rp in sorted(d.glob('family-*.receipt.json')):
   r=m.read_json(rp);f=dict(id=r['job']['id'],url=r['job']['url'],accepted=r['accepted'],receipt=str(rp.relative_to(ROOT)),scope_disposition='unresolved')
   if r['accepted']:
    r,_,h=load_capture(d,r['job']['id']);fi=m.inventory(h,r['job']['url'],r['job']['publication_base'],'main > ul.contents-toc');m.write_json(dest/(r['job']['id']+'-inventory.json'),fi);f.update(inventory_nodes=len(fi['nodes']),inventory_signature=signature(fi))
   else:f['reason']='Access challenge or unsuccessful navigation; original receipt retained'
   families.append(f)
  city['extra_families']=families
  # Only classify structural nodes actually inspected in retained legal bundles.
  for ident in ('chapter','difficult'):
   rr,_,hh=load_capture(d,ident);ss=BeautifulSoup(hh,'html.parser')
   for note in parsed[ident]['notes']:
    if note.get('status')!='structural' or not note.get('node_id','').startswith('dom:'):continue
    card=ss.find(id=note['node_id'][4:])
    if not card:continue
    try:_,source_url,_=m.node_identity(card,rr['job']['url'],base)
    except m.QualificationError:continue
    for node in inv['nodes']:
     if node['source_url']==source_url:node.update(disposition='structural',evidence=dict(raw_artifact_path='raw/'+rr['sha256']+'.html',raw_sha256=rr['sha256'],node_id=note['node_id'],reason=note['reason']))
  m.write_json(dest/'inventory.json',inv)
  # Relative paths keep manifest usable after package copy. Manifest lives beside retained source.
  manifest=dict(jurisdiction_slug=slug,jurisdiction=name,publication_id='municipal-code',publication_title=name+' Municipal Code',publication_base=base,source_version='inventory:'+signature(inv)+'|currency:'+m.sha(city['currency_before'].encode()),raw_currency_text=city['currency_before'],retrieved_at=before['finished_at'],publication_families_scope='unresolved; bounded primary publication validation',discovered_publications=discover_publications(d,base,city['currency_before']),inventory=dict(path=str((dest/'inventory.json').resolve()),sha256=m.sha(m.canonical(inv)),raw_path=str(p.resolve()),raw_sha256=before['sha256']),snapshots=snapshots)
  # Build a self-contained run input directory so no workspace path dependency leaks.
  inputs=dest/'inputs';inputs.mkdir();m.write_json(inputs/'inventory.json',inv);(inputs/'inventory.html').write_bytes(p.read_bytes())
  manifest['inventory'].update(path='inventory.json',raw_path='inventory.html')
  for snap in manifest['snapshots']:
   raw=Path(snap['path']);target=snap['sha256']+'.html';(inputs/target).write_bytes(raw.read_bytes());snap['path']=target
  m.write_json(inputs/'manifest.json',manifest)
  metadata=m.replay(inputs/'manifest.json',dest/'exports');(dest/'exports'/'raw'/'publications-discovery.html').write_bytes((d/'publications.html').read_bytes());
  run=m.read_json(dest/'exports'/'run-manifest.json');run.update(started_at=before['started_at'],finished_at=m.read_json(d/'version-after.receipt.json')['finished_at'],raw_currency_text=city['currency_before'],legal_currency_normalized=None,publication_families_scope='unresolved',source_stability_checks={k:city[k] for k in ('inventory_stable','currency_stable','chapter_bodies_stable')});run['artifact_hashes']['raw/publications-discovery.html']=m.sha((d/'publications.html').read_bytes());m.write_json(dest/'exports'/'run-manifest.json',run)
  city['export_records']=metadata['record_count'];city['exports_path']=str((dest/'exports').relative_to(ROOT));city['status']='bounded_cua_e2e_pass' if city['source_stability_passed'] else 'bounded_cua_e2e_partial_stability'
  city['export_validation']=m.read_json(dest/'exports'/'validation-report.json')
  results.append(city);print(slug,city['status'],city['inventory_nodes'],city['export_records'],flush=True)
 m.write_json(out/'results.json',results);return results
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',default='live-final');p.add_argument('--out',required=True);a=p.parse_args();prepare(Path(a.source),Path(a.out))
