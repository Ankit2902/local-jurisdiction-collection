"""Observed ordinary HTML form POST, same persistent gate and refusal/image policy."""
import hashlib,urllib.request,urllib.error,urllib.parse
import transport

def fetch(url,fields,max_bytes=160_000_000):
 transport.reserve(url);body=urllib.parse.urlencode([(k,v) for k,v in fields]).encode();receipt={'url':url,'method':'POST','post_fields':fields,'post_body_sha256':hashlib.sha256(body).hexdigest(),'started_at':transport.now(),'transport':'stdlib urllib; observed public form; no automatic retries'}
 try:
  req=urllib.request.Request(url,data=body,headers={'User-Agent':'CompliSolv municipal publication research/1.0','Content-Type':'application/x-www-form-urlencoded'})
  with urllib.request.build_opener(transport.Redirect()).open(req,timeout=240) as response:
   receipt.update(status=response.status,final_url=response.url,headers=dict(response.headers))
   if response.headers.get_content_type().lower().startswith('image/'):data=b'';receipt['policy_omitted_image']=True
   else:data=response.read(max_bytes+1)
 except urllib.error.HTTPError as error:
  receipt.update(status=error.code,final_url=error.url,headers=dict(error.headers),error=str(error))
  if error.headers.get_content_type().lower().startswith('image/'):
   data=b'';receipt['policy_omitted_image']=True
  else:data=error.read(max_bytes+1)
 if len(data)>max_bytes:raise ValueError('Observed form native response exceeds configured byte limit')
 challenge=any(k.lower()=='cf-mitigated' and 'challenge' in v.lower() for k,v in receipt['headers'].items()) or b'<title>Just a moment' in data[:20000]
 if receipt['status'] in (403,429) or challenge:transport.stop(url,receipt['status'],receipt['headers'],'Observed form refusal/rate limit/challenge');receipt['access_stop']=True
 receipt.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),finished_at=transport.now());return data,receipt
