"""Deterministic Unicode-aware label sizing and native editable label cells."""
import unicodedata
import math
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
    from .draw import icon_extent
    name=wrap_text(resource['name'],width-16,12)
    details=wrap_text('\n'.join(resource.get('display_details',[])),width-16,10)
    name_height=max(16,16*len(name.splitlines()))
    detail_height=0 if not details else 13*len(details.splitlines())
    iw,ih=icon_extent(resource['kind'])
    top=8+ih+3 if ih else 6
    label_height=name_height+(2+detail_height if details else 0)
    return {'name':name,'details':details,'name_height':name_height,'detail_height':detail_height,
            'label_top':top,'label_height':label_height,'icon_width':iw,'icon_height':ih,
            'height':math.ceil(top+label_height+(8 if ih else 6))}


def style_card(root,cell,resource,width):
    metrics=card_metrics(resource,width);key=cell.get('id')
    icon=root.find("mxCell[@id='"+key+"-icon']")
    g=icon.find('mxGeometry') if icon is not None else None
    if g is not None:
        g.set('x',str((width-float(g.get('width')))/2));g.set('y','8')
    logical=resource['kind'] in ('backend_set','lpg','ipsec_tunnel')
    height=float(cell.find('mxGeometry').get('height'))
    top=(height-metrics['label_height'])/2 if logical else metrics['label_top']
    def value(text):return escape(text).replace('\n','<br>')
    name_size=11 if resource['kind'] in ('internet','nat','service') else 12
    label=f'<div style="font-size:{name_size}px;line-height:16px;color:#213A44"><b>'+value(metrics['name'])+'</b></div>'
    if metrics['details']:label+='<div style="font-size:10px;line-height:13px;color:#52646C;margin-top:2px">'+value(metrics['details'])+'</div>'
    cell.set('value',label)
    text_widths=[text_width(line,12) for line in metrics['name'].split('\n')]
    text_widths.extend(text_width(line,10) for line in metrics['details'].split('\n'))
    content_width=min(width,max(metrics['icon_width'],*text_widths)+4)
    x,y,w,h=(0,0,width,height) if logical else ((width-content_width)/2,8 if g is not None else top,content_width,top+metrics['label_height']-(8 if g is not None else top))
    shape='rounded=1;arcSize=12;fillColor=#F1F5F5;strokeColor=#B5C5C9;' if logical else 'group;fillColor=none;strokeColor=none;'
    cell.set('style',shape+f'ociNativeLabel=1;ociContentX={x};ociContentY={y};ociContentW={w};ociContentH={h};html=1;whiteSpace=wrap;align=center;verticalAlign=top;spacing=0;spacingTop={top};spacingLeft=8;spacingRight=8;')
