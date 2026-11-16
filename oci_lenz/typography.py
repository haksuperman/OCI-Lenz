"""Deterministic Unicode-aware label sizing and native editable label cells."""
import unicodedata
import xml.etree.ElementTree as E


def wrap_text(text,width,font_size):
    result=[]
    for logical in str(text).split('\n'):
        line='';used=0
        for char in logical:
            units=1 if unicodedata.east_asian_width(char) in ('W','F') else (0.33 if char.isspace() else 0.6)
            advance=units*font_size
            if line and used+advance>width:result.append(line);line='';used=0
            line+=char;used+=advance
        result.append(line)
    return '\n'.join(result)


def card_metrics(resource,width):
    name=wrap_text(resource['name'],width-16,12)
    details=wrap_text('\n'.join(resource.get('display_details',[])),width-16,10)
    name_height=max(16,16*len(name.splitlines()))
    detail_height=0 if not details else 13*len(details.splitlines())
    return {'name':name,'details':details,'name_height':name_height,'detail_height':detail_height,
            'height':max(110,66+name_height+6+detail_height+10)}


def style_card(root,cell,resource,width):
    metrics=card_metrics(resource,width);key=cell.get('id')
    cell.set('style','text;whiteSpace=wrap;html=0;textOpacity=0;fillColor=none;strokeColor=none;')
    for suffix,value,y,height,style in (
        ('name',metrics['name'],66,metrics['name_height'],'fontSize=12;fontStyle=1;fontColor=#213A44;'),
        ('details',metrics['details'],72+metrics['name_height'],metrics['detail_height'],'fontSize=10;fontColor=#52646C;')):
        c=E.SubElement(root,'mxCell',id=key+'-label-'+suffix,value=value,vertex='1',parent=key,
                       style='text;whiteSpace=wrap;html=0;align=center;verticalAlign=top;spacing=0;textOpacity=100;'+style)
        E.SubElement(c,'mxGeometry',x='8',y=str(y),width=str(width-16),height=str(max(height,1)),**{'as':'geometry'})
