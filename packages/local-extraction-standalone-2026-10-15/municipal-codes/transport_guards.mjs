/** Pure transport guards shared by the standalone runners; no browser or I/O. */
export function validateJob(job){
 const source=new URL(job.section_url),share=job.share_url?new URL(job.share_url):null,exp=new URL(job.export_url);
 if(source.protocol!=='https:'||!source.hostname.endsWith('.municipal.codes')||source.username||source.password||source.search||source.hash)throw Error('Expected public municipal.codes section URL');
 const publication='/'+source.pathname.split('/').filter(Boolean)[0];
 if(!/^[A-Za-z0-9_.-]+$/.test(job.expected_id)||!source.pathname.endsWith('/'+job.expected_id))throw Error('Expected ID/source mismatch');
 if(exp.origin!==source.origin||exp.pathname!==source.pathname+'/export.html'||exp.search!=='?download=true'||exp.hash||exp.username||exp.password)throw Error('Unadvertised/wrong-scope HTML export URL');
 if(share&&(share.origin!==source.origin||share.pathname!==source.pathname+'/share'||share.search||share.hash||share.username||share.password))throw Error('Share URL leaves selected source');
 return {origin:source.origin,publication};
}
export function validateDownloadUrl(downloadUrl,job){
 const {origin}=validateJob(job);let url;
 try{url=new URL(downloadUrl);}catch{throw Error('Invalid download URL');}
 if(url.protocol==='blob:'){
  const inner=new URL(url.pathname);
  if(inner.origin!==origin||inner.username||inner.password)throw Error('Blob download leaves observed publisher origin');
 }else if(url.href!==new URL(job.export_url).href)throw Error('Download URL differs from observed export');
 return true;
}
