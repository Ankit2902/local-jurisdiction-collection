#!/usr/bin/env python3
"""One exact observed URL with copied ordinary gate; no resource/image traversal or retry."""
import pathlib,sys,json,hashlib,datetime
P=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(P/'runtime'));sys.dont_write_bytecode=True
import transport
url=sys.argv[1];name=sys.argv[2]
assert name.replace('-','').replace('_','').isalnum()
out=P/'raw';out.mkdir(exist_ok=True);body=out/(name+'.bin');meta=out/(name+'.receipt.json');assert not body.exists()and not meta.exists(),'Fresh receipt required'
try:
 data,receipt=transport.fetch(url,max_bytes=8000000)
 receipt.update(request_name=name,raw_ref=body.relative_to(P).as_posix(),script_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),executed_transport_sha256=hashlib.sha256((P/'runtime/transport.py').read_bytes()).hexdigest())
 body.write_bytes(data);meta.write_text(json.dumps(receipt,indent=2)+'\n')
 good=receipt['status']==200 and not receipt.get('access_stop')and not receipt.get('policy_omitted_image');print(json.dumps({'url':url,'status':receipt['status'],'bytes':len(data),'sha256':receipt['sha256'],'access_stop':receipt.get('access_stop'),'policy_omitted_image':receipt.get('policy_omitted_image'),'final_url':receipt.get('final_url'),'continued':good}));raise SystemExit(0 if good else 2)
except SystemExit:raise
except BaseException as e:
 meta.write_text(json.dumps({'url':url,'finished_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'error':type(e).__name__+': '+str(e),'script_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'executed_transport_sha256':hashlib.sha256((P/'runtime/transport.py').read_bytes()).hexdigest(),'no_retry_or_alternate_request':True},indent=2)+'\n');print(json.dumps({'error':type(e).__name__+': '+str(e),'continued':False}));raise SystemExit(2)
