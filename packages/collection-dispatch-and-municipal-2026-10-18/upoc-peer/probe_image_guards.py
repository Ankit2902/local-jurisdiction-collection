"""Synthetic guard-branch probe. Original decoders are stubbed, never executed."""
import contextlib, hashlib, json, pathlib, sys
from unittest.mock import patch
sys.dont_write_bytecode=True
candidate=pathlib.Path(sys.argv[1]).resolve();sys.path.insert(0,str(candidate))
from collectors.encodeplus import retained_native as m
from pdfminer.pdftypes import PDFStream
from pdfminer.psparser import LIT
from pypdf.generic import EncodedStreamObject,DecodedStreamObject,NameObject,NumberObject
def run():
    original_calls=[]
    def stub(*a,**k):
        original_calls.append('stubbed_original_decoder_reached')
        return b'NO_IMAGE_DATA_EXISTS_IN_THIS_PROBE'
    forms=[]
    for keys in [('W','H'),('Width','Height'),('/W','/H'),('/Width','/Height')]:
        forms.append(('PDFStream:'+','.join(keys),lambda k=keys:PDFStream({k[0]:1,k[1]:1,'BPC':8,'CS':LIT('RGB')},b'NO_IMAGE_DATA').get_data()))
    forms.append(('PDFStream:SubtypeImage',lambda:PDFStream({'Subtype':LIT('Image')},b'NO_IMAGE_DATA').get_data()))
    def pypdf_call(cls,attrs):
        s=cls();s.update({NameObject(k):NameObject(v)if isinstance(v,str)else NumberObject(v)for k,v in attrs.items()});return s.get_data()
    for cls in [EncodedStreamObject,DecodedStreamObject]:
        for attrs in [{'/W':1,'/H':1},{'/Width':1,'/Height':1},{'/Subtype':'/Image'}]:
            forms.append((cls.__name__+':'+','.join(attrs),lambda c=cls,a=attrs:pypdf_call(c,a)))
    results=[]
    with contextlib.ExitStack()as stack:
        for cls in [PDFStream,EncodedStreamObject,DecodedStreamObject]:stack.enter_context(patch.object(cls,'get_data',stub))
        for name,action in forms:
            before=len(original_calls)
            try:
                with m.guards():action()
                refused=False
            except AssertionError as e:
                refused=str(e)=='forbidden_network_or_image_operation'
            results.append({'source_form':name,'refused':refused,'original_decoder_calls':len(original_calls)-before})
        before=len(original_calls)
        with m.guards():control=PDFStream({'Type':LIT('Font')},b'TEXT_FONT_SENTINEL').get_data()
        control_ok=control==b'NO_IMAGE_DATA_EXISTS_IN_THIS_PROBE'and len(original_calls)==before+1
    source=candidate/'collectors/encodeplus/retained_native.py'
    return {'retained_native_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'image_guard_cases':results,'all_image_forms_refused_before_stub':all(r['refused']and r['original_decoder_calls']==0 for r in results),'nonimage_font_text_stream_allowed':control_ok,'real_image_bytes_decoded':0,'native_parser_calls':0,'publisher_calls':0,'synthetic_only':True}
if __name__=='__main__':print(json.dumps(run(),indent=2))
