"""Deterministic Unicode-aware label sizing and native editable label cells."""
import unicodedata
from html import escape


def text_width(text,font_size):
    return sum(font_size*(1 if unicodedata.east_asian_width(c) in ('W','F') else (0.33 if c.isspace() else 0.6)) for c in text)


def wrap_text(text,width,font_size):
    def advance(char):
        return text_width(char,font_size)
    def measured(value):return text_width(value,font_size)
    result=[]
    for logical in str(text).split('\n'):
        chunks=[];remaining=logical
        while measured(remaining)>width and len(remaining)>1:
            used=0;limit=0
            for char in remaining:
                if limit and used+advance(char)>width:break
                used+=advance(char);limit+=1
            # Prefer natural name boundaries; retain every original character.
            boundaries=[i+1 for i,c in enumerate(remaining[:limit]) if c.isspace() or c in '-_/.:']
            split=next((i for i in reversed(boundaries) if i>=max(1,limit//2)),limit)
            chunks.append(remaining[:split]);remaining=remaining[split:]
        if chunks and chunks[-1][-1].isalnum() and 0<len(remaining)<3 and remaining.isascii() and remaining.isalnum():
            # A long opaque identifier still needs hard wrapping, but a final
            # one-letter line is unnecessary when the preceding line can share.
            while len(remaining)<3 and len(chunks[-1])>3 and measured(chunks[-1][-1]+remaining)<=width:
                remaining=chunks[-1][-1]+remaining;chunks[-1]=chunks[-1][:-1]
        result.extend([*chunks,remaining])
    return '\n'.join(result)


def header_metrics(text,width,font_size=12):
    value=wrap_text(text,max(1,width-24),font_size)
    return {'text':value,'header_height':max(48,12+(font_size+4)*len(value.split('\n')))}


def card_metrics(resource,width):
    name=wrap_text(resource['name'],width-16,12)
    details=wrap_text('\n'.join(resource.get('display_details',[])),width-16,10)
    name_height=max(16,16*len(name.splitlines()))
    detail_height=0 if not details else 13*len(details.splitlines())
    return {'name':name,'details':details,'name_height':name_height,'detail_height':detail_height,
            'height':max(110,66+name_height+6+detail_height+10)}


def style_card(root,cell,resource,width):
    metrics=card_metrics(resource,width);key=cell.get('id')
    icon=root.find("mxCell[@id='"+key+"-icon']")
    g=icon.find('mxGeometry') if icon is not None else None
    top=float(g.get('y',0))+float(g.get('height'))+3 if g is not None else 8
    def value(text):return escape(text).replace('\n','<br>')
    label='<div style="font-size:12px;line-height:16px;color:#213A44"><b>'+value(metrics['name'])+'</b></div>'
    if metrics['details']:label+='<div style="font-size:10px;line-height:13px;color:#52646C;margin-top:2px">'+value(metrics['details'])+'</div>'
    cell.set('value',label)
    cell.set('style',f'group;ociNativeLabel=1;html=1;whiteSpace=wrap;align=center;verticalAlign=top;spacing=0;spacingTop={top};spacingLeft=8;spacingRight=8;fillColor=none;strokeColor=none;')
