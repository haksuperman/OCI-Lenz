"""Apply model-owned rectangles to native diagrams without re-gridding them."""
import copy
import math
import hashlib
import xml.etree.ElementTree as E
from .model import graph
from .display import resource_label
from .typography import card_metrics,style_card


def compact_snapshot(snapshot):
    result=copy.deepcopy(snapshot)
    for r in result['resources']:
        details=r.get('display_details',[])
        selected=r.get('summary_details') or details[:3]
        r['display_details']=list(selected)
        if len(details)>len(selected):r['display_details'].append('More: information index')
    return result


def make_scene(snapshot,view='detail'):
    if view not in ('detail','overview'):raise ValueError('unknown architecture view')
    from .draw import render
    compact=compact_snapshot(snapshot)
    doc=E.fromstring(render(compact))
    if view=='overview':
        from .presentation import service_frames
        service_frames(doc,snapshot)
    root=doc.find('diagram/mxGraphModel/root')
    cells={c.get('id'):c for c in root}
    nodes,edges=graph(snapshot)
    compact_nodes,_=graph(compact)
    hidden={k for k,r in nodes.items() if view=='overview' and r['kind'] in ('vnic','route','nsg')}
    for k in hidden:
        if k in cells:
            cells[k].set('visible','0')
            g=cells[k].find('mxGeometry')
            for f in ('x','y','width','height'):g.set(f,'0')
    keys=sorted(k for k,c in cells.items() if k not in hidden and c.get('vertex')=='1' and (k in nodes or k.startswith('layout-')))
    aliases={key:'n'+str(i) for i,key in enumerate(keys)}
    items={};boxes={}
    def absolute(key):
        c=cells[key];g=c.find('mxGeometry');x=float(g.get('x',0));y=float(g.get('y',0));p=c.get('parent')
        if p in aliases:
            px,py=absolute(p);x+=px;y+=py
        return x,y
    for key in keys:
        c=cells[key];g=c.find('mxGeometry');a=aliases[key]
        kind=nodes[key]['kind'] if key in nodes else ('region' if key=='layout-region' else ('service_group' if key.startswith('layout-service-') else 'compartment'))
        container=kind in ('vcn','subnet','region','compartment','service_group')
        items[a]={'kind':kind,'parent':aliases.get(c.get('parent'),''),
                  'min_width':220 if container else 170,
                  'min_height':64 if container else card_metrics(compact_nodes[key],170)['height'],
                  'container':container}
        if kind=='subnet':items[a]['public']=bool(nodes[key].get('public'))
        if kind=='service_group':items[a]['shared']=snapshot['presentation']['groups'][int(key.rsplit('-',1)[1])].get('role')=='shared'
        # The seed is only used by explicit --no-ai and test fixtures.
        x,y=absolute(key)
        boxes[a]={'id':a,'x':int(x),'y':int(y),'width':int(float(g.get('width'))),'height':int(float(g.get('height')))}
    request={'view':view,'items':items,'edges':[{'id':'e'+str(i),'source':aliases[e['source']],'target':aliases[e['target']],'kind':e['kind']} for i,e in enumerate(edges) if e['source'] in aliases and e['target'] in aliases],'target_aspect_ratio':1.7}
    signature=hashlib.sha256(repr((keys,items,request['edges'])).encode()).hexdigest()
    return {'view':view,'items':items,'region':aliases['layout-region'],'aliases':aliases,'keys':{v:k for k,v in aliases.items()},'boxes':boxes,'request':request,'signature':signature,'xml':E.tostring(doc,encoding='unicode')}


def seed_plan(scene):
    children={k:[] for k in scene['items']}
    for k,item in scene['items'].items():
        if item['parent'] in children:children[item['parent']].append(k)
    sizes={};relative={}
    def measure(k):
        item=scene['items'][k];w=item['min_width'];h=item['min_height']
        if children[k]:
            columns=3 if item['kind']=='subnet' else 2
            y=64
            for start in range(0,len(children[k]),columns):
                x=24;rowh=0
                for child in children[k][start:start+columns]:
                    cw,ch=measure(child);relative[child]=(x,y);x+=cw+24;rowh=max(rowh,ch)
                w=max(w,x);y+=rowh+24
            h=max(h,y)
        sizes[k]=(w,h);return w,h
    measure(scene['region']);placements=[]
    def position(k,x,y):
        w,h=sizes[k];placements.append({'id':k,'x':x,'y':y,'width':w,'height':h})
        for child in children[k]:
            dx,dy=relative[child];position(child,x+dx,y+dy)
    position(scene['region'],20,90)
    return {'version':2,'scene_signature':scene['signature'],'placements':placements,'routes':[]}


def check_plan(scene,plan):
    issues=[];boxes={}
    for p in plan.get('placements',[]):
        key=p.get('id')
        if key in boxes:issues.append('duplicate '+str(key))
        if key not in scene['items']:issues.append('unknown item');continue
        if any(not isinstance(p.get(f),(int,float)) or isinstance(p.get(f),bool) or not math.isfinite(p[f]) or p[f]<0 or p[f]>50000 for f in ('x','y','width','height')):
            issues.append('invalid dimensions '+key);continue
        item=scene['items'][key]
        if p['width']<item['min_width'] or p['height']<item['min_height']:issues.append('undersized '+key)
        boxes[key]=p
    if set(boxes)!=set(scene['items']):issues.append('missing placements')
    siblings={}
    for k,p in boxes.items():
        parent=scene['items'][k]['parent']
        if parent in boxes:
            q=boxes[parent]
            if p['x']<q['x']+12 or p['y']<q['y']+48 or p['x']+p['width']>q['x']+q['width']-12 or p['y']+p['height']>q['y']+q['height']-12:
                issues.append('outside parent '+k+' '+parent)
        for other in siblings.setdefault(parent,[]):
            q=boxes[other]
            if p['x']<q['x']+q['width'] and q['x']<p['x']+p['width'] and p['y']<q['y']+q['height'] and q['y']<p['y']+p['height']:
                issues.append('overlap '+k+' '+other)
        siblings[parent].append(k)
    edge_ids={e['id'] for e in scene['request']['edges']}
    seen=set()
    for route in plan.get('routes',[]):
        if route.get('id') not in edge_ids or route.get('id') in seen:issues.append('invalid edge route')
        seen.add(route.get('id'))
        points=route.get('points',[])
        if len(points)>32:issues.append('too many route points')
        for p in points:
            if any(not isinstance(p.get(f),(int,float)) or isinstance(p.get(f),bool) or not math.isfinite(p[f]) or not 0<=p[f]<=50000 for f in ('x','y')):issues.append('invalid route point')
    return issues[:24]


def apply_plan(snapshot,scene,plan,region_only=False):
    if plan.get('scene_signature')!=scene['signature']:raise ValueError('layout belongs to a different inventory or label footprint')
    if check_plan(scene,plan):raise ValueError('AI layout failed geometry validation')
    doc=E.fromstring(scene['xml']);doc.set('style','architecture')
    if region_only:
        for page in list(doc.findall('diagram'))[1:]:doc.remove(page)
    boxes={scene['keys'][p['id']]:p for p in plan['placements']}
    nodes,edges=graph(snapshot)
    compact_nodes=graph(compact_snapshot(snapshot))[0]
    route_map={r['id']:r['points'] for r in plan.get('routes',[])}
    for page in doc.findall('diagram'):
        cells={c.get('id'):c for c in page.iter('mxCell')}
        for key,p in boxes.items():
            if key not in cells:continue
            c=cells[key];g=c.find('mxGeometry');parent=boxes.get(c.get('parent'),{'x':0,'y':0})
            if key in nodes and nodes[key]['kind']=='vcn':
                original_parent=scene['items'][scene['aliases'][key]]['parent']
                parent=boxes.get(scene['keys'].get(original_parent),{'x':0,'y':0})
            for f,value in zip(('x','y','width','height'),(p['x']-parent['x'],p['y']-parent['y'],p['width'],p['height'])):g.set(f,str(value))
            if key in nodes and nodes[key]['kind'] not in ('vcn','subnet'):
                style_card(page.find('mxGraphModel/root'),c,compact_nodes[key],p['width'])
                icon=cells.get(key+'-icon')
                if icon is not None:icon.find('mxGeometry').set('x',str((p['width']-54)/2))
        if page.get('id')!='region':
            # Detail pages renumber compartment frames. Preserve the model's
            # internal VCN layout and crop only the surrounding page frames.
            right=24;bottom=100
            for key,c in cells.items():
                if not key.startswith('layout-compartment-'):continue
                children=[v for k,v in cells.items() if v.get('parent')==key and k in nodes and nodes[k]['kind']=='vcn']
                if not children:continue
                geometries=[v.find('mxGeometry') for v in children]
                dx=min(float(g.get('x')) for g in geometries)-24
                dy=min(float(g.get('y')) for g in geometries)-64
                for g in geometries:g.set('x',str(float(g.get('x'))-dx));g.set('y',str(float(g.get('y'))-dy))
                w=max(float(g.get('x'))+float(g.get('width')) for g in geometries)+24
                h=max(float(g.get('y'))+float(g.get('height')) for g in geometries)+24
                g=c.find('mxGeometry');g.set('x',str(right));g.set('y','64');g.set('width',str(w));g.set('height',str(h))
                right+=w+24;bottom=max(bottom,h+88)
            loose=[c for k,c in cells.items() if k in nodes and c.get('parent')=='layout-region']
            if loose:
                gs=[c.find('mxGeometry') for c in loose]
                dx=min(float(g.get('x')) for g in gs)-24
                dy=min(float(g.get('y')) for g in gs)-bottom
                for g in gs:g.set('x',str(float(g.get('x'))-dx));g.set('y',str(float(g.get('y'))-dy))
                right=max(right,max(float(g.get('x'))+float(g.get('width')) for g in gs)+24)
                bottom=max(float(g.get('y'))+float(g.get('height')) for g in gs)+24
            g=cells['layout-region'].find('mxGeometry');g.set('width',str(right));g.set('height',str(bottom))
        for i,e in enumerate(edges):
            c=cells.get('edge-'+str(i))
            if c is None:continue
            if page.get('id')=='region' and e['kind'] not in ('backend','lb_id'):
                c.set('visible','0')
            if e['kind'] in ('route','route_table_id','nsg_ids'):
                c.set('style',c.get('style')+'textOpacity=0;')
            if e['kind']=='lb_id':c.set('style',c.get('style')+'startArrow=block;endArrow=none;textOpacity=0;')
            if e['kind']=='backend':c.set('style',c.get('style')+'textOpacity=0;')
            if 'e'+str(i) in route_map:
                g=c.find('mxGeometry');parent=boxes.get(c.get('parent'),{'x':0,'y':0})
                array=E.SubElement(g,'Array',**{'as':'points'})
                for point in route_map['e'+str(i)]:E.SubElement(array,'mxPoint',x=str(point['x']-parent['x']),y=str(point['y']-parent['y']))
        cells['notice'].set('value','OCI-Lenz | Architecture\nResource names and observed IPs | Overview: LB/backend flow; VCN pages: network links; information index: complete data')
        from .routing import route_native_edges
        route_native_edges(page.find('mxGraphModel/root'),nodes)
    if region_only:return E.tostring(doc,encoding='unicode')
    append_information_index(doc,snapshot,nodes)
    return E.tostring(doc,encoding='unicode')


def append_information_index(doc,snapshot,nodes):
    # A complete editable index keeps many secondary IPs from inflating every VM.
    page=E.SubElement(doc,'diagram',id='information-index',name='Resource information')
    root=E.SubElement(E.SubElement(page,'mxGraphModel',page='0',background='#ffffff'),'root')
    E.SubElement(root,'mxCell',id='0');E.SubElement(root,'mxCell',id='1',parent='0')
    y=30
    for i,r in enumerate(sorted(snapshot['resources'],key=lambda r:(r['kind'],r['id']))):
        lines=[r['name']+' / '+r['kind'],*r.get('display_details',[])]
        if r['kind']=='vcn' and r.get('compartment_id') and not snapshot.get('presentation',{}).get('redacted'):
            lines.append('Compartment: '+r['compartment_id'])
        for rule in r.get('rules',[]):lines.append(rule.get('destination','')+' → '+nodes.get(rule.get('network_entity_id'),{}).get('name','대상 미확인'))
        for key in r.get('nsg_ids',[]):lines.append('NSG: '+nodes.get(key,{}).get('name','대상 미확인'))
        value='\n'.join(lines);height=max(54,20+16*len(lines))
        c=E.SubElement(root,'mxCell',id='information-'+str(i),value=value,vertex='1',parent='1',style='text;whiteSpace=wrap;html=0;fontSize=12;align=left;verticalAlign=top;spacing=10;strokeColor=#D6C9BF;fillColor=#FAF9F6;')
        E.SubElement(c,'mxGeometry',x='30',y=str(y),width='1100',height=str(height),**{'as':'geometry'});y+=height+10


def apply_design(snapshot,plan=None,detail_pages=False):
    if plan is not None and plan.get('version')!=3:
        doc=E.fromstring(apply_plan(snapshot,make_scene(snapshot),plan))
        if not detail_pages:
            for page in list(doc.findall('diagram'))[1:-1]:doc.remove(page)
        doc.set('pageMode','split' if detail_pages else 'single')
        return E.tostring(doc,encoding='unicode')
    overview=make_scene(snapshot,view='overview')
    if plan is None:
        plan={'version':3,'overview':seed_plan(overview)}
        if detail_pages:plan['detail']=seed_plan(make_scene(snapshot))
    summary=E.fromstring(apply_plan(snapshot,overview,plan['overview'],region_only=True)).find('diagram')
    if detail_pages:
        doc=E.fromstring(apply_plan(snapshot,make_scene(snapshot),plan['detail']))
        doc.remove(doc.find('diagram'));doc.insert(0,summary)
    else:
        doc=E.Element('mxfile',host='OCI-Lenz',style='architecture');doc.append(summary)
        append_information_index(doc,snapshot,graph(snapshot)[0])
    doc.set('pageMode','split' if detail_pages else 'single')
    notice=doc.find("diagram/mxGraphModel/root/mxCell[@id='notice']")
    if notice is not None:
        notice.set('value','OCI-Lenz | Whole-environment architecture\nActual resource names and observed addresses | LB/backend configuration links | Complete network/address data: Resource information')
    return E.tostring(doc,encoding='unicode')


def validate_architecture(xml,snapshot):
    from .draw import validate
    doc=E.fromstring(xml);index=doc.find("diagram[@id='information-index']")
    if index is None:raise ValueError('missing information index')
    doc.remove(index);doc.attrib.pop('style',None)
    validate(E.tostring(doc,encoding='unicode'),compact_snapshot(snapshot))
    if len(index.findall('.//mxCell[@vertex="1"]'))!=len(snapshot['resources']):raise ValueError('information index mismatch')
    return True
