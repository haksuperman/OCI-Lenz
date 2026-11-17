"""Explicit presentation panels; resource ownership/evidence is unchanged."""
import xml.etree.ElementTree as E
from .model import graph


def validate_groups(snapshot):
    """Validate explicit VCN membership without inferring any service groups."""
    nodes,_=graph(snapshot);seen=set()
    for group in snapshot.get('presentation',{}).get('groups',[]):
        for vcn in group['vcn_ids']:
            if vcn in seen or nodes.get(vcn,{}).get('kind')!='vcn':
                raise ValueError('invalid presentation membership')
            seen.add(vcn)


def service_frames(doc,snapshot):
    groups=snapshot.get('presentation',{}).get('groups',[])
    if not groups:return
    validate_groups(snapshot)
    root=doc.find('diagram/mxGraphModel/root');cells={c.get('id'):c for c in root}
    cursor=24;max_height=0
    for i,group in enumerate(groups):
        key='layout-service-'+str(i);width=24;height=64
        frame=E.SubElement(root,'mxCell',id=key,value=group['label'],vertex='1',parent='layout-region',
                           style='rounded=0;fillColor=#FAF9F6;strokeColor=#B6C6CB;whiteSpace=wrap;html=0;fontSize=15;fontStyle=1;fontColor=#213A44;align=left;verticalAlign=top;spacing=14;')
        cells[key]=frame
        for vcn in group['vcn_ids']:
            c=cells[vcn];c.set('parent',key);g=c.find('mxGeometry')
            g.set('x',str(width));g.set('y','64');width+=float(g.get('width'))+24
            height=max(height,64+float(g.get('height'))+24)
        E.SubElement(frame,'mxGeometry',x=str(cursor),y='64',width=str(max(width,260)),height=str(max(height,100)),**{'as':'geometry'})
        cursor+=max(width,260)+24;max_height=max(max_height,height)
    for key,c in list(cells.items()):
        if not key.startswith('layout-compartment-'):continue
        if not any(v.get('parent')==key and v.get('vertex')=='1' for v in root):root.remove(c);cells.pop(key);continue
        g=c.find('mxGeometry');g.set('x',str(cursor));g.set('y','64')
        cursor+=float(g.get('width'))+24;max_height=max(max_height,float(g.get('height')))
    g=cells['layout-region'].find('mxGeometry');g.set('width',str(cursor));g.set('height',str(max_height+88))
    for c in root:
        if c.get('edge')!='1':continue
        parents=[];p=cells[c.get('source')].get('parent')
        while p in cells:parents.append(p);p=cells[p].get('parent')
        parents.append('1');p=cells[c.get('target')].get('parent')
        while p not in parents:p=cells[p].get('parent')
        c.set('parent',p)
