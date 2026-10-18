"""Attach retained source only after an inert template has removed image resources.

The raw source remains unchanged on disk. This QA helper never loads or decodes
images, and is independent of every family normalizer.
"""
import hashlib
from pathlib import Path
from html.parser import HTMLParser

JS = r'''raw => {
 const t=document.createElement('template'); t.innerHTML=raw;
 const root=t.content; let replacements=0;
 const mark=e=>{if(!e.parentNode)return;e.replaceWith(document.createTextNode('[IMAGE]'));replacements++};
 const insert=(e,n)=>{if(!n)return;let text=document.createTextNode('[IMAGE]'.repeat(n));
   if(e.tagName==='TABLE'){let cap=document.createElement('caption');cap.append(text);e.prepend(cap)}
   else e.prepend(text);replacements+=n};
 const imageURL=u=>/^data:image\//i.test(u||'')||/\.(png|jpe?g|gif|webp|svg|avif|bmp|ico|tiff?)([?#]|$)/i.test(u||'');
 for(let e of Array.from(root.querySelectorAll('img,picture,svg,image,use,input,object,embed,source'))){
   if(!e.parentNode)continue;let tag=e.tagName.toLowerCase(),url=e.getAttribute('src')||e.getAttribute('data')||'';
   if(['img','picture','svg','image','use'].includes(tag)||(tag==='input'&&(e.getAttribute('type')||'').trim().toLowerCase()==='image')||
       (e.getAttribute('type')||'').trim().toLowerCase().startsWith('image/')||imageURL(url))mark(e);
 }
 for(let e of Array.from(root.querySelectorAll('*'))){if(!e.parentNode)continue;
   if(e.tagName==='A'&&imageURL(e.getAttribute('href'))){e.removeAttribute('href');e.append(document.createTextNode('[IMAGE]'));replacements++}
   let n=0;for(let a of ['background','poster'])if(e.hasAttribute(a)){n++;e.removeAttribute(a)}
   let style=e.getAttribute('style')||'';n+=(style.match(/url\s*\(/gi)||[]).length;
   if(/url\s*\(|image-set\s*\(|@import/i.test(style))e.removeAttribute('style');insert(e,n);
   if(e.tagName==='STYLE'){let count=(e.textContent.match(/url\s*\(/gi)||[]).length;e.replaceWith(document.createTextNode('[IMAGE]'.repeat(count)));replacements+=count;continue}
   if(['SCRIPT','LINK','BASE','META'].includes(e.tagName)){e.remove();continue}
   // Nonimage embedded documents remain fallback text, without an active loader.
   if(['IFRAME','OBJECT','EMBED','SOURCE','AUDIO','VIDEO'].includes(e.tagName))for(let a of ['src','srcdoc','data','autoplay'])e.removeAttribute(a);
   for(let a of Array.from(e.attributes))if(/^on/i.test(a.name))e.removeAttribute(a.name);
   if(['VIDEO','AUDIO','OBJECT','IFRAME'].includes(e.tagName)){let neutral=document.createElement('span');neutral.append(...e.childNodes);e.replaceWith(neutral)}
 }
 let policy=document.createElement('meta');policy.httpEquiv='Content-Security-Policy';
 policy.content="default-src 'none'; img-src 'none'; media-src 'none'; frame-src 'none'; object-src 'none'; style-src 'unsafe-inline'";
 document.head.replaceChildren(policy);document.body.replaceChildren(root);
 if(document.querySelector('img,picture,svg,image,use,[background],[poster]'))throw Error('Active image survived inert preparation');
 return {image_placeholders_inserted:replacements,preparation:'template-inert-before-attachment-v1',image_decoding_or_rendering:false};
}'''

def body_markup(raw):
    # Template fragment parsing discards <body> wrappers. Select their original
    # byte-for-character contents first so head/title metadata never becomes body.
    class Locator(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=False);self.start=None;self.end=None
        def source_offset(self):
            line,col=self.getpos();return sum(len(x)+1 for x in raw.split('\n')[:line-1])+col
        def handle_starttag(self,tag,attrs):
            if tag=='body' and self.start is None:self.start=self.source_offset()+len(self.get_starttag_text())
        def handle_endtag(self,tag):
            if tag=='body' and self.start is not None and self.end is None:self.end=self.source_offset()
    locator=Locator();locator.feed(raw)
    return raw[locator.start:locator.end] if locator.start is not None else raw

def attach_inert_html(page, raw):
    """A template's contents are inert; sanitize before moving nodes to the page."""
    return page.evaluate(JS, body_markup(raw.decode('utf-8') if isinstance(raw,bytes) else raw))

def provenance():
    return {'helper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'preparation':'body-source-template-inert-before-attachment-v2','all_network_blocked':True}
