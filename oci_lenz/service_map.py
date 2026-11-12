"""Compact service presentation. Groups are explicit; topology remains unchanged."""
import math
import xml.etree.ElementTree as E
from .model import graph


def groups_for(snapshot):
    nodes,_=graph(snapshot)
    groups=snapshot.get('presentation',{}).get('groups',[])
    seen=set()
    for g in groups:
        for v in g['vcn_ids']:
            if v in seen or nodes.get(v,{}).get('kind')!='vcn':
                raise ValueError('invalid presentation membership')
            seen.add(v)
    remaining=sorted(k for k,r in nodes.items() if r['kind']=='vcn' and k not in seen)
    compartments={}
    for k in remaining:compartments.setdefault(nodes[k].get('compartment_id') or 'unspecified',[]).append(k)
    groups=[*groups,*[{'label':'Compartment '+str(i+1),'vcn_ids':vs,'automatic':True}
                     for i,(_,vs) in enumerate(sorted(compartments.items()))]]
    return groups


def render_service_map(snapshot, layout=None):
    from .draw import render
    groups=groups_for(snapshot)
    doc=E.fromstring(render(snapshot))
    doc.set('style','service-map')
    nodes,edges=graph(snapshot)
    for page in doc.findall('diagram'):
        summary=page.get('id')=='region'
        root=page.find('mxGraphModel/root')
        cells={c.get('id'):c for c in root}
        vcns=sorted(k for k,r in nodes.items() if r['kind']=='vcn' and k in cells)
        # Replace API-compartment frames with explicit user presentation frames.
        for c in list(root):
            if c.get('id','').startswith('layout-compartment-'):root.remove(c)
        def rect(k,x,y,w,h,parent=None):
            c=cells[k]
            if parent is not None:c.set('parent',parent)
            geo=c.find('mxGeometry')
            for field,value in zip(('x','y','width','height'),(x,y,w,h)):geo.set(field,str(value))
        def add(k,label,x,y,w,h,parent,style):
            c=E.SubElement(root,'mxCell',id=k,value=label,vertex='1',parent=parent,style=style)
            E.SubElement(c,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),**{'as':'geometry'})
            cells[k]=c
        def size(k):
            g=cells[k].find('mxGeometry');return float(g.get('width')),float(g.get('height'))
        def card(k,x,y,parent):
            rect(k,x,y,110,78,parent)
            c=cells[k];c.set('value',nodes[k]['name']);c.set('style','text;whiteSpace=wrap;html=0;fontSize=10;verticalAlign=bottom;spacingBottom=3;')
            if nodes[k]['kind']=='backend_set':
                ports=sorted({str(b['port']) for b in nodes[k].get('backends',[])})
                if ports:c.set('value',nodes[k]['name']+'\n:'+','.join(ports))
            if k+'-icon' in cells:rect(k+'-icon',28,3,54,54)
        backend_cluster={}
        for e in sorted(edges,key=lambda e:(e['source'],e['target'])):
            if e['kind']=='backend':backend_cluster.setdefault(e['target'],e['source'])
        for v in vcns:
            subnets=sorted((k for k,r in nodes.items() if r['kind']=='subnet' and r.get('vcn_id')==v and k in cells),key=lambda k:(not nodes[k].get('public',False),k))
            shared=next((g.get('role')=='shared' for g in groups if v in g['vcn_ids']),False)
            y=48;vwidth=320;empty_subnets=[];populated=0
            for si,sub in enumerate(subnets):
                members=[k for k in nodes if k in cells and cells[k].get('parent')==sub]
                visible=[]
                for k in members:
                    if summary and nodes[k]['kind']=='vnic':
                        cells[k].set('visible','0');rect(k,0,0,0,0)
                    else:visible.append(k)
                # The saved skill positions supply stable ordering, compact grid supplies bounds.
                visible.sort(key=lambda k:({'lb':0,'backend_set':1,'compute':2,'vnic':3}.get(nodes[k]['kind'],4),backend_cluster.get(k,'~'),(layout or {}).get(k,{}).get('y',0),(layout or {}).get(k,{}).get('x',0),k))
                if not visible:
                    empty_subnets.append(sub);continue
                columns=min(4,max(2,math.ceil(math.sqrt(len(visible) or 1))))
                for j,k in enumerate(visible):card(k,18+(j%columns)*130,44+(j//columns)*96,sub)
                h=52+max(1,math.ceil(len(visible)/columns))*96
                subwidth=24+columns*130
                # Shared-service horizontal lanes are optional and wrap after two subnets.
                if shared and summary:
                    if populated%2==0:shared_row_y=y;shared_row_h=0;shared_row_x=18
                    x=shared_row_x;shared_row_x+=subwidth+16
                    sy=shared_row_y;shared_row_h=max(shared_row_h,h)
                    y=shared_row_y+shared_row_h+18
                else:x=18;sy=y;y+=h+18
                populated+=1
                rect(sub,x,sy,subwidth,h,v)
                vwidth=max(vwidth,x+subwidth+18)
            empty_columns=2 if len(empty_subnets)>2 else 1
            for j,sub in enumerate(empty_subnets):
                sx=18+(j%empty_columns)*300;sy=y+(j//empty_columns)*72
                rect(sub,sx,sy,284,56,v);vwidth=max(vwidth,sx+302)
            if empty_subnets:y+=math.ceil(len(empty_subnets)/empty_columns)*72
            extras=[k for k in nodes if k in cells and cells[k].get('parent')==v and nodes[k]['kind'] not in ('subnet','vcn')]
            visible=[]
            for k in sorted(extras):
                if summary and nodes[k]['kind'] in ('nsg','route'):
                    cells[k].set('visible','0');rect(k,0,0,0,0)
                else:visible.append(k)
            # Compact network support strip, independent of application backend paths.
            for j,k in enumerate(visible):
                card(k,12+(j%3)*100 if summary else vwidth+12+(j%2)*100,y+(j//3)*88 if summary else 64+(j//2)*100,v)
                cells[k].find('mxGeometry').set('width','90')
                if k+'-icon' in cells:cells[k+'-icon'].find('mxGeometry').set('x','18')
            height=y+((len(visible)+2)//3)*88+14 if summary else max(y,64+((len(visible)+1)//2)*100)+14
            if not summary:vwidth+=220
            rect(v,0,0,vwidth,height)
            c=cells[v];c.set('value',nodes[v]['name']+' / VCN')
        panel_style='rounded=0;fillColor=none;strokeColor=#D6C9BF;verticalAlign=top;align=left;spacing=10;fontSize=14;fontStyle=1;whiteSpace=wrap;'
        present=[]
        for i,g in enumerate(groups):
            vs=[v for v in g['vcn_ids'] if v in vcns]
            if not vs:continue
            key=('layout-compartment-' if g.get('automatic') else 'layout-service-')+str(i)
            # Pack variable-sized VCNs into shelves, avoiding unbounded single rows.
            target=max(max(size(v)[0] for v in vs)+24, min(1200,math.sqrt(sum(size(v)[0]*size(v)[1] for v in vs)*1.6)))
            x=12;vy=36;rowh=0;w=0
            placements=[]
            for v in vs:
                vw,vh=size(v)
                if x>12 and x+vw+12>target:vy+=rowh+16;x=12;rowh=0
                placements.append((v,x,vy,vw,vh));x+=vw+12;rowh=max(rowh,vh);w=max(w,x)
            h=vy+rowh+12
            add(key,g['label'],0,0,w,h,'layout-region',panel_style)
            for v,vx,vy,vw,vh in placements:rect(v,vx,vy,vw,vh,key)
            present.append((key,g.get('role')=='shared' and summary))
        top=[k for k,shared in present if not shared];bottom=[k for k,shared in present if shared]
        # Adapt shelf width to actual content; no reference-image canvas dimensions.
        target=max([size(k)[0]+32 for k in top]+[800])
        if top:target=max(target,math.sqrt(sum(size(k)[0]*size(k)[1] for k in top)*3.4))
        width=0;y=48;x=16;rh=0
        for k in top:
            w,h=size(k)
            if x>16 and x+w+16>target:y+=rh+18;x=16;rh=0
            rect(k,x,y,w,h);x+=w+16;rh=max(rh,h);width=max(width,x)
        y+=rh+18
        x=16;bottom_height=0
        for k in bottom:
            w,h=size(k);rect(k,x,y,w,h);x+=w+16;bottom_height=max(bottom_height,h)
        if not summary:
            x=width;y=48
        width=max(width,x+390,800)
        notes=('Reading this diagram\n\nService panels: explicit presentation groups.\nOrange dotted frames: VCNs and subnets.\nSolid arrows: configured LB/backend relations.\n\nOverview omits VNIC, NSG and route-table\nshapes and technical links for readability.\nOpen VCN pages for network details.\n\nNo traffic reachability is inferred.\nUnresolved targets remain explicitly marked.\n\nScope: Compute, LB, VCN, subnets, gateways.\nDB, OKE, DRG and peering are excluded.')
        if not summary:
            routes=[e for e in edges if e['kind']=='route' and e['source'] in cells and e['target'] in cells]
            nsg=[e for e in edges if e['kind']=='nsg_ids' and e['source'] in cells and e['target'] in cells]
            notes='Network configuration\n\nRoutes (configured next hops)\n'+'\n'.join(nodes[e['source']]['name']+' → '+nodes[e['target']]['name']+' | '+e['label'] for e in routes)
            notes+='\n\nNSG attachments\n'+'\n'.join(nodes[e['source']]['name']+' → '+nodes[e['target']]['name'] for e in nsg)
            notes+='\n\nDashed links: network configuration.\nSolid links: LB / backend configuration.\nNo traffic reachability is inferred.\n\nService groups are explicit presentation metadata.\nDB / OKE / DRG / peering are out of scope.'
        add('layout-notes',notes,x,y,max(360,width-x-16),max(300,bottom_height) if summary else max((size(k)[1] for k in top),default=300),'layout-region','text;whiteSpace=wrap;align=left;verticalAlign=top;fontSize=12;spacing=14;')
        height=y+max(bottom_height,300)+20
        if not summary:height=max(height,48+max((size(k)[1] for k in top),default=300)+20)
        # Keep out-of-scope/unknown cards visible and distinct below the service panels.
        loose=[k for k in nodes if k in cells and cells[k].get('parent') in ('1','layout-region') and k not in vcns]
        for j,k in enumerate(sorted(loose)):
            card(k,16+(j%6)*130,height+(j//6)*110,'layout-region')
        if loose:height+=((len(loose)+5)//6)*110+20
        rect('layout-region',20,90,width,height)
        synthetic=bool(snapshot.get('coverage')) and all(c.get('source')=='synthetic' for c in snapshot['coverage'])
        cells['notice'].set('value','OCI-Lenz | Service architecture'+(' — SYNTHETIC' if synthetic else '')+'\nConfigured inventory and backend relationships | IPs and OCIDs hidden')
        rect('notice',20,10,max(width,800),60)
        # Put frame cells before their children in serialization for editor friendliness.
        def depth(c):
            p=c.get('parent');d=0
            while p in cells:d+=1;p=cells[p].get('parent')
            return d
        for c in sorted(list(root),key=lambda c:(depth(c),c.get('id'))):root.remove(c);root.append(c)
        def ancestor(a,b):
            parents=[];p=cells[a].get('parent')
            while p in cells:parents.append(p);p=cells[p].get('parent')
            p=cells[b].get('parent')
            while p not in parents:p=cells[p].get('parent')
            return p
        for c in root:
            if c.get('edge')!='1':continue
            a,b=c.get('source'),c.get('target');c.set('parent',ancestor(a,b))
            edge=edges[int(c.get('id').split('-')[1])]
            if not summary and edge['kind'] in ('route','nsg_ids','route_table_id'):
                c.set('style',c.get('style')+'textOpacity=0;')
            if summary and edge['kind'] not in ('backend','lb_id'):
                c.set('visible','0')
            if edge['kind'] in ('backend','lb_id'):
                # Backend sets are API children of LB; retain evidence direction in XML.
                c.set('style','edgeStyle=orthogonalEdgeStyle;rounded=0;html=0;fontSize=9;strokeColor=#444444;endArrow=block;labelBackgroundColor=#F7F6F3;')
                c.find('mxGeometry').set('y','-8')
                if edge['kind']=='lb_id':
                    c.set('style',c.get('style')+'startArrow=block;endArrow=none;')
                else:
                    # Ports remain on the editable Backend Set label, not repeated over arrows.
                    c.set('style',c.get('style')+'textOpacity=0;')
    return E.tostring(doc,encoding='unicode')
