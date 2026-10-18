"""Offline typed source-route inventory; does not request publisher destinations."""
import sys
sys.dont_write_bytecode=True
import json,hashlib,urllib.parse
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
def anchors(cell,base):
 return [{'label':a.get_text(' ',strip=True),'source_href':a['href'],'url':urllib.parse.urljoin(base,a['href'])}for a in cell.select('a[href]')]
def main():
 base='https://www.cambridgema.gov/CDD/zoninganddevelopment/Zoning/Amendments/adoptedzoningamendments'
 raw=(ROOT/'source/cambridge-adopted-amendments.html').read_bytes();s=BeautifulSoup(raw,'html.parser');groups=[]
 for i,t in enumerate(s.select('table')):
  rows=t.find_all('tr')
  if len(rows)<2:continue
  header=[x.get_text(' ',strip=True)for x in rows[0].find_all(['td','th'],recursive=False)]
  assert header==['Petition Name','Key Documents','Public Hearings','Final Ordination']
  title=t.find_previous(['h1','h2','h3']).get_text(' ',strip=True);entries=[]
  for ordinal,row in enumerate(rows[1:]):
   cells=row.find_all(['td','th'],recursive=False);assert len(cells)==4
   entries.append({'ordinal':ordinal,'columns':[{'role':header[j],'text':c.get_text(' ',strip=True),'anchors':anchors(c,base)}for j,c in enumerate(cells)],'source_row_sha256':hashlib.sha256(str(row).encode()).hexdigest()})
  groups.append({'heading':title,'source_table_index':i,'rows':entries})
 assert [(g['heading'],len(g['rows']))for g in groups]==[('Adopted Zoning Amendments Not Yet Codified',5),('Codified Zoning Amendments',121)]
 maps=json.loads((ROOT/'source/cambridge-maps.analysis.json').read_text())
 maprows={}
 for a in maps['anchors']:
  if '.pdf'in urllib.parse.urlsplit(a['url']).path.lower():
   maprows.setdefault(a['url'],{'url':a['url'],'source_labels':[]})['source_labels'].append(a['label'])
 assert len(maprows)==17
 index=json.loads((ROOT/'source/90-5918edb057f6.analysis.json').read_text())
 articles={}
 for a in index['anchors']:
  if 'library.municode.com/'in a['url']and'nodeId=ZOOR_ART'in a['url']:articles.setdefault(a['url'],[]).append(a['label'])
 assert len(articles)==23
 allpdf={a['url']for g in groups for row in g['rows']for c in row['columns']for a in c['anchors']if'.pdf'in urllib.parse.urlsplit(a['url']).path.lower()}
 d={'publication_id':'90-5918edb057f6','base_text_route':'https://library.municode.com/ma/cambridge/codes/zoning_ordinance','source_article_links':articles,'export_archive':'https://library.municode.com/downloadarchive/15643','export_options_observed':'Latest or dated older version; PDF entireordinance vs PDF(SupplementOnly) changes; compressedZIP; no archive destination requested','adopted_amendment_tables':groups,'distinct_supporting_PDF_URLs_in_amendment_tables':len(allpdf),'maps':list(maprows.values()),'maps_current_through_source_text':'Ordinance #2025-17 ordained January26,2026 unless otherwise stated; filenames retained separately, no date substitution','print_version_and_subsequent_adopted_amendments_control':True,'source_says_not_all_ordinances_electronic':True,'source_says_full_petition_record_not_listed':True,'publisher_workflow_stopped':True,'publisher_requests_sent':0,'full_publication_inventory_or_edition_qualified':False,'new_PDFs_or_images_acquired':0}
 (ROOT/'cambridge-source-scope.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'article_links':23,'uncodified_rows':5,'codified_rows':121,'map_PDFs':17,'distinct_amendment_table_PDF_URLs':len(allpdf),'publisher_requests':0}))
if __name__=='__main__':main()
