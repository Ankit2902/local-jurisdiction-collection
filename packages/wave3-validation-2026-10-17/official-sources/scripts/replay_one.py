#!/usr/bin/env python3
"""Offline one-jurisdiction replay of fresh acquisition; no network and no mutation of inputs."""
import argparse,json,pathlib,importlib.util
import normalize_all as n
p=argparse.ArgumentParser();p.add_argument('--sequence',type=int,required=True);p.add_argument('--raw',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--supplement',type=pathlib.Path);a=p.parse_args();raw=a.raw.resolve();row=next(r for r in json.loads((n.BASE/'assignment.json').read_text()) if r['sequence']==a.sequence);n.verify_raw(raw)
if a.sequence==58:
 rows=n.pdf_segments(row,raw/'58-alarm-export-native.pdf',range(9,12),r'^Section 2\.01\s',r'^Section\s+(2\.\d+)\s+(.+)$','Arlington Texas Alarm Systems ArticleII','https://www.arlingtontx.gov/files/assets/city/v/2/city-secretary/documents/city-code-of-ordinances/alarm-systems-chapter.pdf',[f'2.0{i}' for i in range(1,8)],r'ALARM SYSTEMS|2\.\d+|ARTICLE II - \d+')
elif a.sequence==99:
 rows=n.pdf_segments(row,raw/'99-code-native-native.pdf',range(3),r'^§ 1-1\.\s',r'^§\s+(1-\d+(?:\.\d+)?)\.\s+(.+)$','Arlington County Virginia Code Chapter1','https://www.arlingtonva.us/files/sharedassets/public/v/5/county-board/documents/code/ch.-1-general-provisions.pdf',['1-1','1-2','1-3','1-4','1-5','1-6','1-7','1-7.1','1-8','1-9'],r'ARLINGTON COUNTY CODE(?: GENERAL PROVISIONS)?|1-\d+|Code Updated September 2011')
elif a.sequence==80:
 rows=n.pdf_segments(row,raw/'80-part1.pdf',range(2,6),r'^§ 1\. Citation$',r'^§\s+(\d+)\.\s+(.+)$','Worcester Revised Ordinances PartI Chapter1','https://www.worcesterma.gov/city-clerk/document-center/revised-ordinances-2008-1.pdf',[str(i) for i in range(1,9)],r'\d+')
elif a.sequence==78:rows=n.spokane(row,raw)
elif a.sequence in [71,85]:
 spec=importlib.util.spec_from_file_location('municode_one',n.BASE/'scripts/municode/normalize.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);report=m.normalize(raw,a.out)
 if a.sequence==85 and a.supplement:
  rows=[];receipt=json.loads((raw/'receipt.json').read_text())
  for l in (a.out/'sections.jsonl').read_text().splitlines():
   r=json.loads(l);r.update(jurisdiction=row['jurisdiction'],state='TN',id=r['node_id'],citation=r['heading'],publication='Chattanooga Part I Charter Compilation',publication_family='charter',record_unit='legal_section',raw_ref=str((raw/'samples.json').relative_to(n.BASE)),raw_sha256=n.sha((raw/'samples.json').read_bytes()));rows.append(r)
  rows+=n.chattanooga_code(m,None,row,supplement=a.supplement.resolve(),source=raw,current_path=raw);report=n.write_rows(a.out,85,rows)
 print(json.dumps(report,indent=2));raise SystemExit(0)
elif a.sequence==87:
 inventory=n.ep.inventory((raw/'87-encodeplus-toc.html').read_text(),'https://online.encodeplus.com/regs/savannah-ga/','Savannah');rows=[]
 for ident,file in [('499','87-section499.html'),('500','87-section500.html'),('501','87-section501.html'),('7137','87-impact-fee7137.html')]:
  node=next(x for x in inventory['nodes'] if x['section_id']==ident);f=raw/file;url=json.loads((raw/(file+'.receipt.json')).read_text())['final_url'];r,ch,_=n.ep.parse_section(f.read_text(),node,url,'Savannah',n.sha(f.read_bytes()));r.update(state='GA',id=ident,text=r['full_text'],publication='Savannah Code of Ordinances',record_unit='fee_attachment' if ident=='7137' else 'legal_section',raw_ref=str(f.relative_to(n.BASE)));rows.append(r)
print(json.dumps(n.write_rows(a.out,a.sequence,rows),indent=2))
