"""Editable OKE Pod subnet annotation, without adding inventory resources."""
import math
import xml.etree.ElementTree as E


def decorate_pod_subnets(root,nodes):
    from .draw import icon
    for cell in list(root):
        resource=nodes.get(cell.get('id'),{})
        if resource.get('kind')!='subnet' or not resource.get('oke_pod_cluster_ids'):continue
        lines=cell.get('value','').split('\n')
        if 'OKE Pod network' not in lines:continue
        row=lines.index('OKE Pod network');lines[row]=''
        cell.set('value','\n'.join(lines));cell.set('ociOkeBadge','1')
        options=dict(p.split('=',1) for p in cell.get('style','').split(';') if '=' in p)
        size=float(options.get('fontSize',12));spacing=float(options.get('spacing',12))
        badge_id=cell.get('id')+'-i-oke-pods-badge'
        badge=E.SubElement(root,'mxCell',id=badge_id,parent=cell.get('id'),vertex='1',
                           value='OKE Pods',ociRoleBadge='oke_pods',
                           style='rounded=1;arcSize=25;whiteSpace=wrap;html=0;fillColor=#E8F2F4;strokeColor=#2F6473;fontColor=#2F6473;fontSize=10;fontStyle=1;align=left;verticalAlign=middle;spacingLeft=24;spacing=0;')
        E.SubElement(badge,'mxGeometry',x=str(spacing),y=str(spacing+row*(size+4)-2),width='100',height='18',**{'as':'geometry'})
        icon(root,badge_id,'oke_cluster',4,2,size=14)


def badge_rectangles(root,box):
    return [(c.get('parent'),box(c.get('id'))) for c in root
            if c.get('ociRoleBadge')=='oke_pods' and c.get('visible')!='0']


def validate_badges(doc,nodes):
    for root in doc.findall('diagram/mxGraphModel/root'):
        cells={c.get('id'):c for c in root};seen=set()
        for badge in root.findall("mxCell[@ociRoleBadge='oke_pods']"):
            parent=badge.get('parent');resource=nodes.get(parent,{})
            if parent in seen or resource.get('kind')!='subnet' or not resource.get('oke_pod_cluster_ids'):
                raise ValueError('invalid OKE Pod badge membership')
            seen.add(parent)
            g=badge.find('mxGeometry');pg=cells[parent].find('mxGeometry')
            x,y,w,h=(float(g.get(k,0)) for k in ('x','y','width','height'))
            if not all(math.isfinite(v) for v in (x,y,w,h)) or x<0 or y<0 or w<90 or h<18 or x+w>float(pg.get('width')) or y+h>float(pg.get('height')):
                raise ValueError('OKE Pod badge clipping')
            glyph=cells.get(badge.get('id')+'-icon')
            if glyph is None or glyph.get('parent')!=badge.get('id') or 'Container Engine for Kubernetes' not in glyph.get('ociOfficialIcon',''):
                raise ValueError('missing official OKE Pod badge icon')
        if any(c.get('ociOkeBadge')=='1' and c.get('id') not in seen for c in root):
            raise ValueError('missing OKE Pod badge')
