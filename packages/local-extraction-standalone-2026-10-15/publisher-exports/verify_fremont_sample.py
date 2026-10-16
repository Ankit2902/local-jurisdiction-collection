#!/usr/bin/env python3
"""Independent bounded intake and source comparison of the sibling agent's fresh publisher download."""
import argparse,hashlib,json
from pathlib import Path
from bs4 import BeautifulSoup
from export_intake import write_result

def main():
 p=argparse.ArgumentParser();p.add_argument('--source-package',required=True,type=Path);p.add_argument('--out',required=True,type=Path);args=p.parse_args()
 src=args.source_package/'publisher-downloads/fremont-ca'; receipt=json.loads((src/'download-receipt.json').read_text());f=src/'publisher-export.html';b=f.read_bytes()
 assert hashlib.sha256(b).hexdigest()==receipt['raw_sha256']
 prov={'source_url':receipt['source_url'],'jurisdiction':'Fremont, CA','publication':'Fremont Municipal Code','selection_scope':receipt['metadata']['selection'],'retrieved_at':receipt['finished_at'],'artifact_kind':'publisher-export','acquisition_mode':'operator-browser-download','edition_evidence':'Export #current states current through Ordinance 02-2026, passed May5,2026; source comparison below; not independent legal currentness certification.','external_receipt':str(src/'download-receipt.json'),'external_receipt_sha256':hashlib.sha256((src/'download-receipt.json').read_bytes()).hexdigest()}
 r=write_result(f,prov,args.out,expected_format='html',expected_sha=receipt['raw_sha256'],expect=['Title 1','1.05.010','1.30.010','Ordinance 02-2026','Title of Officer','Provision of Code'])
 s=BeautifulSoup(b,'html.parser');current=s.select_one('#current').get_text(' ',strip=True);headings=[e.get_text(' ',strip=True) for e in s.select('h3.Cite')];anchors=[e.get('id') or e.get('name') for e in s.select('h3.Cite a[id],h3.Cite a[name]')]
 root=args.source_package/'current-cua/fremont-ca/root-confirmed.html';rootcurrent=None
 if root.exists():
  rs=BeautifulSoup(root.read_bytes(),'html.parser');rc=rs.select_one('#current');rootcurrent=rc.get_text(' ',strip=True) if rc else None
 assert rootcurrent==current,'publisher root/export edition mismatch or root notice absent'
 assert len(headings)==73,(len(headings),headings[:1]);assert len(anchors)==73;assert len(set(anchors))==73;assert len(r['sample']['tables'])==8
 table=r['sample']['tables'][0]['rows'];assert [x['text'] for x in table[0]]==['','Title of Officer','Provision of Code']
 assert any('Finance services manager' in c['text'] for c in table[1]);assert any('Chapter 5.05' in c['text'] for c in table[1])
 comparison={'source_sha256':receipt['raw_sha256'],'fresh_export_receipt':prov['external_receipt'],'first_section':headings[0],'last_section':headings[-1],'section_count':len(headings),'unique_section_anchors':len(set(anchors)),'table_count':len(r['sample']['tables']),'first_table_rows':len(table),'first_table_header':[x['text'] for x in table[0]],'export_edition_text':current,'current_root_edition_text':rootcurrent,'current_root_sha256':hashlib.sha256(root.read_bytes()).hexdigest() if root.exists() else None,'edition_text_equal':current==rootcurrent if rootcurrent else None,'automated_sample_checks':'PASS','visual_review':'Separate human/agent visual evidence is recorded in evidence/visual-qa.json; replay assertions do not perform visual review','not_proven':['Whole-code coverage (selection is onlyTitle1)','Legal effect or uncodified NewLaws','Other4CodePublishing cities','Unattended transport (this is operator-assisted download)']}
 (args.out/'source-comparison.json').write_text(json.dumps(comparison,indent=2)+'\n');(args.out/'provenance.json').write_text(json.dumps(prov,indent=2)+'\n');print(json.dumps(comparison,indent=2))
if __name__=='__main__':main()
