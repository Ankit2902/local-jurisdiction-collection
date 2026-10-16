#!/usr/bin/env python3
"""Attach a post-run supported CUA capture and reconcile publication membership."""
import argparse,json,sys
from pathlib import Path
from civicplus import portland_inventory,readj,sha,writej

def main():
 p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--capture',required=True);args=p.parse_args();run=Path(args.run);capture=Path(args.capture);report=readj(run/'E2E-VALIDATION.json');receipt=readj(capture/'capture-receipt.json')
 if report['runtime']!='cua-files' or report['jurisdiction']!='portland-me':raise ValueError('Expected Portland supported CUA run')
 if receipt['finished_at']<report['finished_at']:raise ValueError('Final capture must occur after the full acquisition/parse run')
 for name,h in receipt['files'].items():
  if sha((capture/name).read_bytes())!=h:raise ValueError('Final CUA capture hash mismatch')
 final=portland_inventory((capture/'index.html').read_text(),(capture/'widget.html').read_text());initial=readj(run/'package/inventory.json')['documents'];keys=['node_id','publication_id','label','scope','source_order'];same=[{k:d[k] for k in keys} for d in initial]==[{k:d[k] for k in keys} for d in final]
 report['inventory_recheck']={'method':'Fresh supported CUA capture after acquisition and parse','coherent':same,'final_capture_receipt':receipt,'final_capture_path':str(capture),'initial_documents':len(initial),'final_documents':len(final)};writej(run/'E2E-VALIDATION.json',report);print(json.dumps(report['inventory_recheck']));return 0 if same else 2
if __name__=='__main__':sys.exit(main())
