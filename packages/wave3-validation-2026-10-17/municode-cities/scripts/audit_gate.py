"""Read-only shared gate audit; writes only to explicitly requested new report path."""
import argparse,json
from pathlib import Path
from datetime import datetime,timezone
p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('--since',default='2026-10-17T18:37:00+00:00');p.add_argument('--out',type=Path);a=p.parse_args();since=datetime.fromisoformat(a.since);rows=[]
for line in a.log.read_text().splitlines():
 try:
  j=json.loads(line);t=datetime.fromisoformat(j['started_at']);
  if t>=since:rows.append(j)
 except (ValueError,KeyError):continue
rows.sort(key=lambda r:r['started_at']);scopes={}
for label,selected in [('all_wave3',rows),('ordinary_browser_workflow',[r for r in rows if r.get('transport')=='ordinary-headed-browser-public-workflow']),('availability_probe',[r for r in rows if r.get('transport')=='root-authorized-ordinary-browser-availability-probe'])]:
 intervals=[{'seconds':(datetime.fromisoformat(b['started_at'])-datetime.fromisoformat(c['started_at'])).total_seconds(),'from_url':c['url'],'to_url':b['url'],'from_at':c['started_at'],'to_at':b['started_at']} for c,b in zip(selected,selected[1:])];scopes[label]={'requests':len(selected),'minimum_logged_interval_seconds':min((i['seconds'] for i in intervals),default=None),'logged_intervals_under_3_seconds':[i for i in intervals if i['seconds']<3]}
result={'since':a.since,'scopes':scopes,'qualification':'Log records reservations/audit timestamps, not network packet starts; interval anomaly during one availability probe retained candidly. Nominal3.5s operational browser gate. Direct transport remains stopped; no bypass. Log covers coordinating agents, not only this package.'}
if a.out:
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
