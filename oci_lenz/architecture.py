"""Apply model-owned rectangles to native diagrams without re-gridding them."""
import copy
import math
import hashlib
import xml.etree.ElementTree as E
from .diagram_model import diagram_graph as graph
from .display import scope_title
from .typography import card_metrics,style_card,header_metrics,wrap_text,text_width

from .database_services import DB_SYSTEMS,node_owner,REFERENCES

GATEWAY_KINDS=('internet','nat','service')
OVERVIEW_EDGE_KINDS=('backend','lb_id','drg_id','drg_network','peer_id','db_system_id','cpe_id','ipsec_id','gateway_id','cross_connect_mapping','cross_connect_group_id','vm_cluster_id',*REFERENCES)


class LayoutFormatError(ValueError):
    """Retired top-level layout format; no source fields in CLI diagnostics."""


def container_font(kind):
    return {'region':14,'compartment':13,'service_group':15}.get(kind,12)


def compact_snapshot(snapshot):
    result=copy.deepcopy(snapshot)
    for r in result['resources']:
        details=r.get('display_details',[])
        selected=r.get('summary_details',details[:3])
        if r['kind'] not in ('vcn','subnet'):
            selected=[value for value in selected if value.startswith(('Private: ','Public: ','IP: ','Customer: ','Oracle: '))]
        r['display_details']=list(selected)
    return result


def make_scene(snapshot,view='detail'):
    if view not in ('detail','overview'):raise ValueError('unknown architecture view')
    from .draw import build_document
    compact=compact_snapshot(snapshot)
    doc=E.fromstring(build_document(compact,detail_pages=view=='detail'))
    if view=='overview':
        from .presentation import service_frames
        service_frames(doc,snapshot)
    root=doc.find('diagram/mxGraphModel/root')
    cells={c.get('id'):c for c in root}
    nodes,edges=graph(snapshot)
    compact_nodes,_=graph(compact)
    hidden={k for k,r in nodes.items() if view=='overview' and (r['kind'] in ('vnic','route','nsg') or (r['kind']=='db_node' and nodes.get(node_owner(r),{}).get('kind') in DB_SYSTEMS))}
    display_targets={}
    if view=='overview':
        for i,e in enumerate(edges):
            if e['kind']=='backend' and e['target'] in hidden and nodes[e['target']]['kind']=='db_node':
                target=node_owner(nodes[e['target']]);display_targets[i]=target
                c=cells['edge-'+str(i)];c.set('ociEvidenceTarget',e['target']);c.set('target',target)
                parents=[];p=cells[e['source']].get('parent')
                while p in cells:parents.append(p);p=cells[p].get('parent')
                parents.append('1');p=cells[target].get('parent')
                while p not in parents:p=cells[p].get('parent')
                c.set('parent',p)
    if view=='overview':
        flow_nodes={key for e in edges if e['kind'] in OVERVIEW_EDGE_KINDS and e['source'] not in hidden and e['target'] not in hidden for key in (e['source'],e['target'])}
        hidden|={k for k,r in nodes.items() if r['kind']=='unknown' and k not in flow_nodes}
    for k in hidden:
        if k in cells:
            cells[k].set('visible','0')
            g=cells[k].find('mxGeometry')
            for f in ('x','y','width','height'):g.set(f,'0')
    keys=sorted(k for k,c in cells.items() if k not in hidden and c.get('vertex')=='1' and (k in nodes or k.startswith('layout-')))
    aliases={key:'n'+str(i) for i,key in enumerate(keys)}
    items={}
    for key in keys:
        c=cells[key];a=aliases[key]
        kind=nodes[key]['kind'] if key in nodes else ('region' if key=='layout-region' else ('service_group' if key.startswith('layout-service-') else 'compartment'))
        container=kind in ('vcn','subnet','ipsec','cross_connect_group','region','compartment','service_group')
        width=170
        if kind in GATEWAY_KINDS:
            resource=compact_nodes[key]
            measured=[text_width(resource['name'],12),*[text_width(value,10) for value in resource.get('display_details',[])]]
            width=math.ceil(min(152,max(76,max(measured)+16)))
        items[a]={'kind':kind,'parent':aliases.get(c.get('parent'),''),
                  'min_width':220 if container else width,
                  'min_height':64 if container else card_metrics(compact_nodes[key],width)['height'],
                  'container':container}
        if not container:items[a]['representation']='name_tag' if kind in ('backend_set','lpg','ipsec_tunnel','exascale_db_storage_vault','vm_cluster_network') else 'icon_label'
        if container:
            header=header_metrics(c.get('value',''),220,container_font(kind))
            items[a]['header_height']=header['header_height']
            items[a]['min_height']=max(64,header['header_height']+12)
        if kind=='subnet':items[a]['public']=bool(nodes[key].get('public'))
        if kind=='service_group':items[a]['shared']=snapshot['presentation']['groups'][int(key.rsplit('-',1)[1])].get('role')=='shared'
    gateway_groups=[]
    for vcn in (k for k in keys if nodes.get(k,{}).get('kind')=='vcn'):
        members=[k for k in keys if nodes.get(k,{}).get('kind') in GATEWAY_KINDS and nodes[k].get('vcn_id')==vcn and items[aliases[k]]['parent']==aliases[vcn]]
        members.sort(key=lambda k:(GATEWAY_KINDS.index(nodes[k]['kind']),k))
        if members:gateway_groups.append({'vcn':aliases[vcn],'members':[aliases[k] for k in members],'max_gap':12,'edge_inset':40})
    request={'view':view,'items':items,'edges':[{'id':'e'+str(i),'source':aliases[e['source']],'target':aliases[display_targets.get(i,e['target'])],'kind':e['kind']} for i,e in enumerate(edges) if e['source'] in aliases and display_targets.get(i,e['target']) in aliases and not ((e['kind']=='ipsec_id' and nodes[e['target']]['kind']=='ipsec') or (e['kind']=='cross_connect_group_id' and nodes[e['target']]['kind']=='cross_connect_group'))],'gateway_groups':gateway_groups,'target_aspect_ratio':1.7}
    from .composition import policy
    request['design_policy']=policy()
    from .network_layout import network_groups
    networks=network_groups(nodes,edges,aliases)
    signature_data=(keys,items,request['edges'],gateway_groups)
    if networks:
        request['network_groups']=networks
        signature_data+=(networks,)
    from .connector_rules import guides
    from .draw import icon_extent
    offsets={a:(8+icon_extent(nodes[k]['kind'])[1]/2 if k+'-icon' in cells else None)
             for k,a in aliases.items() if not items[a]['container']}
    request['connector_guides']=guides({'items':items,'edges':[e for e in request['edges'] if e['kind'] in OVERVIEW_EDGE_KINDS]},offsets)
    signature=hashlib.sha256(repr(signature_data).encode()).hexdigest()
    return {'view':view,'items':items,'region':aliases['layout-region'],'aliases':aliases,'keys':{v:k for k,v in aliases.items()},'request':request,'signature':signature,'xml':E.tostring(doc,encoding='unicode')}


def seed_plan(scene):
    children={k:[] for k in scene['items']}
    for k,item in scene['items'].items():
        if item['parent'] in children:children[item['parent']].append(k)
    gateway_rows={group['vcn']:group['members'] for group in scene['request'].get('gateway_groups',[])}
    sizes={};relative={}
    def measure(k):
        item=scene['items'][k];w=item['min_width'];h=item['min_height']
        if children[k]:
            columns=3 if item['kind']=='subnet' else (1 if item['kind'] in ('ipsec','cross_connect_group') else 2)
            y=max(64,item.get('header_height',48)+16)
            gateways=gateway_rows.get(k,[])
            ordinary=[child for child in children[k] if child not in gateways]
            for start in range(0,len(ordinary),columns):
                x=24;rowh=0
                for child in ordinary[start:start+columns]:
                    cw,ch=measure(child);relative[child]=(x,y);x+=cw+24;rowh=max(rowh,ch)
                w=max(w,x);y+=rowh+24
            if gateways:
                x=24;rowh=0
                for child in gateways:
                    cw,ch=measure(child);relative[child]=(x,y);x+=cw+8;rowh=max(rowh,ch)
                w=max(w,x+16);y+=rowh+24
            h=max(h,y)
        sizes[k]=(w,h);return w,h
    measure(scene['region']);placements=[]
    def position(k,x,y):
        w,h=sizes[k];placements.append({'id':k,'x':x,'y':y,'width':w,'height':h})
        for child in children[k]:
            dx,dy=relative[child];position(child,x+dx,y+dy)
    position(scene['region'],20,90)
    from .network_layout import orient_seed
    orient_seed(scene,placements)
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
            if p['x']<q['x']+12 or p['y']<q['y']+scene['items'][parent].get('header_height',48) or p['x']+p['width']>q['x']+q['width']-12 or p['y']+p['height']>q['y']+q['height']-12:
                issues.append('outside parent '+k+' '+parent)
        for other in siblings.setdefault(parent,[]):
            q=boxes[other]
            if p['x']<q['x']+q['width'] and q['x']<p['x']+p['width'] and p['y']<q['y']+q['height'] and q['y']<p['y']+p['height']:
                issues.append('overlap '+k+' '+other)
        siblings[parent].append(k)
    for group in scene['request'].get('gateway_groups',[]):
        if group['vcn'] not in boxes or any(key not in boxes for key in group['members']):continue
        members=group['members'];parent=boxes[group['vcn']];near={key:set() for key in members}
        for key in members:
            p=boxes[key];item=scene['items'][key]
            if p['width']>item['min_width']+16 or p['height']>item['min_height']+8:issues.append('gateway footprint '+key)
            for other in members:
                if other==key:continue
                q=boxes[other]
                horizontal=abs(p['y']-q['y'])<=8 and 0<=q['x']-p['x']-p['width']<=group['max_gap']
                vertical=abs(p['x']+p['width']/2-q['x']-q['width']/2)<=8 and 0<=q['y']-p['y']-p['height']<=group['max_gap']
                if horizontal or vertical:near[key].add(other);near[other].add(key)
        reached={members[0]};pending=[members[0]]
        while pending:
            for key in near[pending.pop()]-reached:reached.add(key);pending.append(key)
        left=min(boxes[k]['x'] for k in members);top=min(boxes[k]['y'] for k in members)
        right=max(boxes[k]['x']+boxes[k]['width'] for k in members);bottom=max(boxes[k]['y']+boxes[k]['height'] for k in members)
        insets=(left-parent['x'],parent['x']+parent['width']-right,top-parent['y']-scene['items'][group['vcn']].get('header_height',48),parent['y']+parent['height']-bottom)
        area=sum(boxes[k]['width']*boxes[k]['height'] for k in members)
        if len(reached)!=len(members) or min(insets)>group['edge_inset'] or (right-left)*(bottom-top)>3*area:
            issues.append('gateway cluster '+group['vcn'])
    from .network_layout import direction_issues
    issues.extend(direction_issues(scene,boxes))
    from .connector_rules import alignment_issues,VERSION
    if plan.get('connector_rule_version')==VERSION:
        issues.extend(alignment_issues(scene['request'].get('connector_guides',[]),plan))
    elif plan.get('connector_rule_version') is not None:issues.append('unsupported connector rule version')
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
            item=scene['items'][scene['aliases'][key]]
            if item['container']:
                kind=item['kind'];font=container_font(kind)
                c.set('value',header_metrics(c.get('value',''),p['width'],font)['text'])
                c.set('style',c.get('style')+f'fontSize={11 if kind=="subnet" else font};')
                if kind in ('vcn','subnet'):
                    c.set('style',c.get('style')+('strokeWidth=1.3;dashPattern=4 3;' if kind=='vcn' else 'strokeWidth=0.7;strokeColor=#C6977D;dashPattern=2 3;'))
            if key in nodes and nodes[key]['kind'] not in ('vcn','subnet','ipsec','cross_connect_group'):
                style_card(page.find('mxGraphModel/root'),c,compact_nodes[key],p['width'])
                icon=cells.get(key+'-icon')
                if icon is not None:
                    ig=icon.find('mxGeometry');ig.set('x',str((p['width']-float(ig.get('width')))/2))
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
            if page.get('id')=='region' and (e['kind'] not in OVERVIEW_EDGE_KINDS or cells[e['source']].get('visible')=='0' or cells[c.get('target')].get('visible')=='0'):
                c.set('visible','0')
            if e['kind'] in ('route','route_table_id','nsg_ids'):
                c.set('style',c.get('style')+'textOpacity=0;')
            if e['kind'] in ('ipsec_id','cross_connect_group_id') and nodes[e['target']]['kind'] in ('ipsec','cross_connect_group') and cells[e['source']].get('parent')==e['target']:
                c.set('visible','0')
            if e['kind'] in ('lb_id','db_system_id'):c.set('style',c.get('style')+'startArrow=block;endArrow=none;textOpacity=0;')
            if e['kind'] in REFERENCES or e['kind']=='vm_cluster_id':c.set('style',c.get('style')+'textOpacity=0;')
            if e['kind']=='backend':c.set('style',c.get('style')+'textOpacity=0;')
            if e['kind'] in ('drg_id','drg_network','peer_id','cpe_id','ipsec_id','gateway_id','cross_connect_mapping','cross_connect_group_id'):
                c.set('style',c.get('style')+'textOpacity=0;')
                if e['kind']=='peer_id':c.set('style',c.get('style')+'dashed=1;')
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
    from .diagram_model import diagram_resources
    resources=diagram_resources(snapshot)
    if not resources:
        c=E.SubElement(root,'mxCell',id='index-notice',value='No resources in this snapshot. Check coverage.json for collection status.',vertex='1',parent='1',style='text;whiteSpace=wrap;html=0;fontSize=12;align=left;verticalAlign=top;spacing=10;')
        E.SubElement(c,'mxGeometry',x='30',y='30',width='1100',height='54',**{'as':'geometry'})
    y=30
    for i,r in enumerate(sorted(resources,key=lambda r:(r['kind'],r['id']))):
        lines=[r['name']+' / '+r['kind'],*r.get('display_details',[])]
        if r['kind']=='vcn' and r.get('compartment_id') and not snapshot.get('presentation',{}).get('redacted'):
            lines.append('Compartment: '+r['compartment_id'])
        for rule in r.get('rules',[]):lines.append(rule.get('destination','')+' → '+nodes.get(rule.get('network_entity_id'),{}).get('name','대상 미확인'))
        for key in r.get('nsg_ids',[]):lines.append('NSG: '+nodes.get(key,{}).get('name','대상 미확인'))
        value=wrap_text('\n'.join(lines),1080,12);height=max(54,20+16*len(value.split('\n')))
        c=E.SubElement(root,'mxCell',id='information-'+str(i),value=value,vertex='1',parent='1',style='text;whiteSpace=wrap;html=0;fontSize=12;align=left;verticalAlign=top;spacing=10;strokeColor=#D6C9BF;fillColor=#FAF9F6;')
        E.SubElement(c,'mxGeometry',x='30',y=str(y),width='1100',height=str(height),**{'as':'geometry'});y+=height+10


def apply_design(snapshot,plan=None,detail_pages=False):
    if plan is not None and plan.get('version')!=3:
        raise LayoutFormatError('Only version-3 architecture layouts are supported; regenerate the layout.')
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
    apply_scope_heading(doc,snapshot)
    return E.tostring(doc,encoding='unicode')


def apply_scope_heading(doc,snapshot):
    for page in doc.findall('diagram'):
        notice=page.find("mxGraphModel/root/mxCell[@id='notice']")
        region=page.find("mxGraphModel/root/mxCell[@id='layout-region']/mxGeometry")
        if notice is None or region is None:continue
        width=float(region.get('width'));text=wrap_text(scope_title(snapshot),max(1,width),14)
        height=18*len(text.split('\n'))+8
        notice.set('value',text)
        notice.set('style','text;whiteSpace=wrap;html=0;fontSize=14;align=left;verticalAlign=top;spacing=0;')
        g=notice.find('mxGeometry');g.set('x',region.get('x','20'));g.set('width',str(width));g.set('height',str(height))
        # Long/multi-compartment titles grow upward; AI geometry is unchanged.
        g.set('y',str(min(10,float(region.get('y'))-height-16)))


def validate_architecture(xml,snapshot):
    from .draw import validate
    doc=E.fromstring(xml);index=doc.find("diagram[@id='information-index']")
    if index is None:raise ValueError('missing information index')
    doc.remove(index);doc.attrib.pop('style',None)
    validate(E.tostring(doc,encoding='unicode'),compact_snapshot(snapshot))
    rows=index.findall('.//mxCell[@vertex="1"]')
    from .diagram_model import diagram_resources
    resources=diagram_resources(snapshot)
    expected={'information-'+str(i) for i in range(len(resources))} if resources else {'index-notice'}
    if len(rows)!=len(expected) or {c.get('id') for c in rows}!=expected:raise ValueError('information index mismatch')
    bottom=0
    for cell in index.findall('.//mxCell[@vertex="1"]'):
        g=cell.find('mxGeometry');x,y,w,h=(float(g.get(k,0)) for k in ('x','y','width','height'))
        required=20+16*len(wrap_text(cell.get('value',''),max(1,w-20),12).split('\n'))
        if not all(math.isfinite(v) for v in (x,y,w,h)) or min(x,y,w,h)<0 or w<=20 or h<required or y<bottom:
            raise ValueError('information index clipping or overlap')
        bottom=y+h

    return True
