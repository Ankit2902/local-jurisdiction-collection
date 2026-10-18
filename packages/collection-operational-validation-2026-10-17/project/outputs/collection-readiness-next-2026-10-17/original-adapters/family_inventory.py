"""Offline source-backed publication/edition/navigation ledger, no acquisition."""
import argparse,re
from pathlib import Path
from urllib.parse import urljoin
from source_common import *
def run(flagstaff_source,king_source,out):
 flag=Path(flagstaff_source);king=Path(king_source);frames=load(flag/'opening-frames.json');
 for frame in frames:
  if sha((flag/frame['path']).read_bytes())!=frame['sha256']:raise ValueError('Family frame hash mismatch: '+frame['path'])
 tf=next(x for x in frames if 'FlagstaffTOC.pl' in x['url']);vf=next(x for x in frames if 'versionMenu.pl' in x['url']);toc=BeautifulSoup((flag/tf['path']).read_bytes(),'html.parser');vers=BeautifulSoup((flag/vf['path']).read_bytes(),'html.parser');pubs=[]
 for p in toc.select('p.codeHead'):
  a=p.find('a',href=True)
  if a:pubs.append({'label':clean(a.get_text(' ',strip=True)),'source_url':urljoin(tf['url'],a['href']),'source_id':a.get('id'),'primary_scope_status':'included_in_primary_checkbox_tree' if a.get('id') in ['muni','flagstaffch'] else 'separate_publication_not_collected'})
 opts=[{'label':clean(x.get_text(' ',strip=True)),'value':x.get('value'),'selected':x.has_attr('selected')} for x in vers.select('option')]
 nav=next(x for x in frames if '/html/FlagstaffNT.html' in x['url']);s=BeautifulSoup((flag/nav['path']).read_bytes(),'html.parser');main=s.select_one('#mainContent');navdata={'source_url':nav['url'],'source_sha256':nav['sha256'],'disposition':'source_navigation_cover_only','reason':'Native source presents three publication navigation panels, no operative provisions; primary descendants come from City Code source checkbox tree','panels':[clean(x.get_text(' ',strip=True)) for x in main.select('.ntpage')] if main else []}
 ks=load(king/'checkpoint.json');index=next(x for x in ks['artifacts'] if x['role']=='index-start');
 if sha((king/index['path']).read_bytes())!=index['sha256']:raise ValueError('King index hash mismatch')
 bs=BeautifulSoup(decode((king/index['path']).read_bytes())[0],'html.parser');related=[]
 for a in bs.select('a[href]'):
  label=clean(a.get_text(' ',strip=True))
  if re.search(r'Board of Health.*Code|Board of Health code',label,re.I):related.append({'label':label,'source_url':urljoin(ks['source_url'],a['href']),'status':'separate_compilation_not_collected'})
 result={'schema':'original-publication-family-ledger-1','whole_jurisdiction_complete':False,'flagstaff':{'source_url':load(flag/'receipt.json')['source_url'],'publications':pubs,'edition_options':opts,'current_edition_policy':'Only native current archive=html; historical options not collected. Current code currency comes from publisher disclaimer, not nearest historical month.','navigation_disposition':navdata,'evidence_frame_hashes':{tf['path']:tf['sha256'],vf['path']:vf['sha256']}},'king_county':{'source_url':ks['source_url'],'primary_documents':ks['inventory'],'related_publications':related,'index_hash':index['sha256'],'scope':'All source-listed County Code HTML/Word documents including Charter and editorial matter; separate compilations and adopted external layers need separate qualification'}};save(Path(out),result);return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--flagstaff-source',required=True);p.add_argument('--king-source',required=True);p.add_argument('--out',required=True);a=p.parse_args();run(a.flagstaff_source,a.king_source,a.out)
