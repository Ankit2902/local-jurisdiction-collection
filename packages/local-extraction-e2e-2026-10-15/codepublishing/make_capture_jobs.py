"""Create bounded next-stage browser jobs using accepted retained navigation only."""
import argparse
import json
from pathlib import Path
from urllib.parse import urljoin
import re
import cp_collect as cp

BASE=Path(__file__).resolve().parent

def jobs(stage, captures, slugs=None):
    rows=[]
    routes=json.loads((BASE/'routes.json').read_text())
    for route in routes:
        slug=route['slug']
        if slug=='foster-city-ca' or (slugs and slug not in slugs):continue
        root=route['discovery_url'];d=Path(captures)/slug
        if stage=='title':
            path=d/('family-toc.receipt.json' if slug=='flagstaff-az' else 'root-confirmed.receipt.json')
            r=json.loads(path.read_text());assert r['accepted'];b=r['browser_state']
            a=next(a for a in b['all_links'] if re.match(r'^Title\s+(1|I)\b',a['label'],re.I))
            url=urljoin(b['url'],a['href']);wait='#mainContent h1.Title'
        elif stage=='chapter':
            r=json.loads((d/'title.receipt.json').read_text());assert r['accepted'];b=r['browser_state']
            candidates=[a for a in b['main_links'] if a['container_class'] in ('CHTOC','TitleTOC_inner') and a['href']]
            if not candidates:raise ValueError('No independently observed chapter links for '+slug)
            url=urljoin(b['url'],candidates[0]['href']);wait='#mainContent h3.Cite'
        elif stage=='root-post':
            url=root;wait='frame#toc' if slug=='flagstaff-az' else 'a[href*="01.html"]'
        else:raise ValueError(stage)
        if not cp.allowed(root,url):raise ValueError('Out of scope')
        rows.append({'slug':slug,'id':stage,'url':url,'root_url':root,'kind':'legal' if stage=='chapter' else 'navigation','wait_selector':wait})
    return rows

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stage',choices=['title','chapter','root-post'],required=True);p.add_argument('--captures',default=str(BASE/'current-cua'));p.add_argument('--slug',action='append');p.add_argument('--out')
    args=p.parse_args();value=jobs(args.stage,args.captures,args.slug)
    if args.out:cp.save(args.out,value)
    print(json.dumps(value,indent=2))
