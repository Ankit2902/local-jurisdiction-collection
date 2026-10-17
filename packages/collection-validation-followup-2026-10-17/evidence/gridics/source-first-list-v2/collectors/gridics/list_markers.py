"""Source list metadata and conservative marker projection; never infer custom CSS."""
import hashlib,json,re

SUPPORTED={'decimal','decimal-leading-zero','upper-alpha','lower-alpha','upper-latin','lower-latin','upper-roman','lower-roman','none','disc','circle','square','unordered-default'}
TYPE_STYLES={'1':'decimal','A':'upper-alpha','a':'lower-alpha','I':'upper-roman','i':'lower-roman'}


def safe(value):
    if isinstance(value,str) and re.search(r'data\s*:\s*image/',value,re.I):
        return {'embedded_image_omitted':True,'source_sha256':hashlib.sha256(value.encode()).hexdigest()}
    if isinstance(value,(str,int,float,bool)) or value is None:
        return value
    if isinstance(value,list):return [safe(v) for v in value]
    if isinstance(value,dict):return {k:safe(v) for k,v in value.items()}
    return {'source_type':type(value).__name__,'source_sha256':hashlib.sha256(str(value).encode()).hexdigest()}


def declared_style(node):
    style=node.get('style','')
    found=re.search(r'(?:^|;)\s*list-style-type\s*:\s*([^;]+)',style,re.I)
    if found:return found.group(1).strip().lower()
    if re.search(r'(?:^|;)\s*list-style\s*:',style,re.I):return 'unqualified-shorthand'
    if node.name=='ul':return {'disc':'disc','circle':'circle','square':'square'}.get(node.get('type'),'unqualified-html-type' if node.has_attr('type') else 'unordered-default')
    return TYPE_STYLES.get(node.get('type','1'),'unqualified-html-type')


def policy(node):
    style=declared_style(node);classes=list(node.get('class') or [])
    reasons=[]
    if node.has_attr('data-list-marker-unqualified'):reasons.append('Unqualified source marker formatting retained explicitly')
    if classes:reasons.append('Custom list class marker formatting has no retained, interpreted CSS proof')
    if style not in SUPPORTED:reasons.append('Unsupported or unknown declared list marker style')
    if re.search(r'(?:list-style-image|counter-reset|counter-increment)\s*:',node.get('style',''),re.I):
        reasons.append('Custom counter or image-marker declaration is unqualified')
    return {'style':style,'qualified':not reasons,'reasons':reasons,'classes':classes}


def integer(value):
    try:
        if not re.fullmatch(r'[+-]?\d+',str(value).strip()):return None
        return int(value)
    except (ValueError,TypeError):return None


def marker(value,style):
    if style in {'none','unordered-default'}:return ''
    if style in {'disc','circle','square'}:return {'disc':'• ','circle':'◦ ','square':'▪ '}[style]
    if style not in SUPPORTED:return ''
    if style in {'upper-alpha','lower-alpha','upper-latin','lower-latin'} and value>0:
        label=''
        while value:
            value,remainder=divmod(value-1,26);label=chr(65+remainder)+label
        label=label.lower() if style.startswith('lower') else label
    elif style in {'upper-roman','lower-roman'} and 0<value<4000:
        label=''
        for amount,letters in [(1000,'M'),(900,'CM'),(500,'D'),(400,'CD'),(100,'C'),(90,'XC'),(50,'L'),(40,'XL'),(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]:
            while value>=amount:label+=letters;value-=amount
        label=label.lower() if style=='lower-roman' else label
    elif style=='decimal-leading-zero':label=('-' if value<0 else '')+str(abs(value)).zfill(2)
    else:label=str(value)
    return label+'. '


def list_metadata(soup):
    rows=[]
    for order,node in enumerate(soup.find_all(['ol','ul']),1):
        selected=policy(node);children=node.find_all('li',recursive=False)
        value=integer(node.get('start',len(children) if node.has_attr('reversed') else 1));step=-1 if node.has_attr('reversed') else 1
        reasons=list(selected['reasons'])
        if value is None:reasons.append('Malformed source list start value')
        items=[]
        for position,li in enumerate(children,1):
            if li.has_attr('value'):value=integer(li['value'])
            custom=bool(li.get('class')) or li.has_attr('type') or bool(re.search(r'(?:list-style|counter-)\s*[-a-z]*\s*:',li.get('style',''),re.I))
            if custom:reasons.append('Per-item custom marker formatting is unqualified')
            if value is None:reasons.append('Malformed source list-item value')
            items.append({'position':position,'counter_value':value,'source_attributes':safe({k:li[k] for k in ['class','value','style','type'] if li.has_attr(k)})})
            if value is not None:value+=step
        rows.append({'order':order,'tag':node.name,'source_attributes':safe({k:node[k] for k in ['class','style','type','start','reversed'] if node.has_attr(k)}),'declared_style':safe(selected['style']),'marker_format_qualified':not reasons,'qualification_errors':sorted(set(reasons)),'items':items,'source_list_sha256':hashlib.sha256(str(node).encode()).hexdigest()})
    return rows


def insert_markers(soup):
    # Projection is deliberately empty for unqualified custom formatting. The
    # original class/style/counter metadata remains; no punctuation is guessed.
    for node in soup.find_all(['ol','ul']):
        selected=policy(node);children=node.find_all('li',recursive=False)
        value=integer(node.get('start',len(children) if node.has_attr('reversed') else 1));step=-1 if node.has_attr('reversed') else 1
        for li in children:
            if li.has_attr('value'):value=integer(li['value'])
            per_item=bool(li.get('class')) or li.has_attr('type') or bool(re.search(r'(?:list-style|counter-)\s*[-a-z]*\s*:',li.get('style',''),re.I))
            if selected['qualified'] and not per_item and value is not None:
                prefix=marker(value,selected['style'])
                if prefix:li.insert(0,prefix)
            if value is not None:value+=step
