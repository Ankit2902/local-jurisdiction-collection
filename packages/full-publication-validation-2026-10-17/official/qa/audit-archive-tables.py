#!/usr/bin/env python3
"""Independent raw-ZIP table/cell/span comparison for three real operative records; read-only."""
import hashlib,json,pathlib,re,sys,zipfile
from bs4 import BeautifulSoup
run=pathlib.Path(sys.argv[1]);state=json.loads((run/'checkpoint.json').read_text());archive=next(i for i in state['items'] if i['kind']=='zip');z=zipfile.ZipFile(run/archive['raw_ref']);root=z.namelist()[0].split('/')[0];results=[]
def clean(s):return re.sub(r'\s+',' ',s).strip()
def cells(table):
 rows=[]
 for tr in table.find_all('tr'):
  if tr.find_parent('table') is not table:continue
  rows.append([{'text':clean(td.get_text(' ',strip=True)),'rowspan':str(td.get('rowspan','1')),'colspan':str(td.get('colspan','1')),'tag':td.name} for td in tr.find_all(['th','td'],recursive=False)])
 return rows
for line in (run/'records.jsonl').open():
 record=json.loads(line)
 if not record.get('tables') or not any(cell['rowspan']!='1' or cell['colspan']!='1' for table in record['tables'] for row in table['rows'] for cell in row):continue
 path=root+record['id']+'/index.html';raw=z.read(path);source=BeautifulSoup(raw,'html.parser');tables=source.find_all('table');remaining=list(range(len(tables)));matches=[]
 for table in record['tables']:
  match=next((i for i in remaining if cells(tables[i])==table['rows']),None)
  if match is None:raise ValueError('Normalized table does not match an actual source table: '+record['id'])
  remaining.remove(match);matches.append(match)
 if remaining:raise ValueError('Source tables omitted: '+record['id'])
 results.append({'record_id':record['id'],'heading':record['heading'],'source_url':record['source_url'],'source_member':path,'source_member_sha256':hashlib.sha256(raw).hexdigest(),'table_count':len(tables),'cell_count':sum(len(row) for t in record['tables'] for row in t['rows']),'spanned_cell_count':sum(c['rowspan']!='1' or c['colspan']!='1' for t in record['tables'] for row in t['rows'] for c in row),'all_source_rows_cells_text_and_spans_match':True,'operative_sample_values':[c['text'] for t in record['tables'] for row in t['rows'] for c in row if re.fullmatch(r'\$\d+(?:,\d{3})*(?:\.\d+)?',c['text'])][:8]})
 if len(results)==3:break
if len(results)!=3:raise ValueError('Three real table-bearing source records not found')
print(json.dumps({'schema':1,'read_only':True,'network_used':False,'method':'Each normalized row/cell/text/span compared to a unique raw canonical source HTML table. Every table in each selected canonical source member accounted for. Independent implementation; no collector/model imports.','records':results},indent=2))
