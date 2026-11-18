"""Deterministic orthogonal routing around resource cards, without moving them."""
import copy
import heapq
import xml.etree.ElementTree as E
from .typography import text_width


def visible_rectangle(cell,rectangle):
    options=dict(p.split('=',1) for p in cell.get('style','').split(';') if '=' in p)
    if not all('ociContent'+k in options for k in ('X','Y','W','H')):return rectangle
    x,y,_,_=rectangle
    return x+float(options['ociContentX']),y+float(options['ociContentY']),float(options['ociContentW']),float(options['ociContentH'])


def intersects(a,b,rect):
    x,y,w,h=rect
    if a[0]==b[0]:return x<a[0]<x+w and max(min(a[1],b[1]),y)<min(max(a[1],b[1]),y+h)
    if a[1]==b[1]:return y<a[1]<y+h and max(min(a[0],b[0]),x)<min(max(a[0],b[0]),x+w)
    return True


def segment_conflict(a,b,c,d):
    """Return perpendicular contacts and shared collinear length (page units)."""
    if a==b or c==d:return 0,0
    av=a[0]==b[0];cv=c[0]==d[0]
    if av==cv:
        axis=1 if av else 0;fixed=1-axis
        if a[fixed]!=c[fixed]:return 0,0
        overlap=max(0,min(max(a[axis],b[axis]),max(c[axis],d[axis]))-max(min(a[axis],b[axis]),min(c[axis],d[axis])))
        return 0,overlap
    v1,v2,h1,h2=(a,b,c,d) if av else (c,d,a,b)
    return int(min(v1[1],v2[1])<=h1[1]<=max(v1[1],v2[1]) and min(h1[0],h2[0])<=v1[0]<=max(h1[0],h2[0])),0


def path_quality(paths):
    """Count network-involved ambiguity, exempting genuine shared endpoint stubs."""
    crossings=0;overlap=0
    for i,left in enumerate(paths):
        for right in paths[i+1:]:
            if not (left['network'] or right['network']):continue
            if {left['source'],left['target']}=={right['source'],right['target']}:continue
            lp,rp=left['points'],right['points'];contacts=set()
            common={left['source']:lp[0],left['target']:lp[-1]}.keys() & {right['source'],right['target']}
            common_points=set()
            shared_stubs=[]
            for key in common:
                lseq=lp if key==left['source'] else list(reversed(lp))
                rseq=rp if key==right['source'] else list(reversed(rp))
                if lseq[0]!=rseq[0]:continue
                common_points.add(lseq[0])
                le=next((p for p in lseq[1:] if p!=lseq[0]),lseq[0])
                re=next((p for p in rseq[1:] if p!=rseq[0]),rseq[0])
                shared_stubs.append((lseq[0],le,re))
            def on_segment(point,a,b):
                return min(a[0],b[0])<=point[0]<=max(a[0],b[0]) and min(a[1],b[1])<=point[1]<=max(a[1],b[1])
            for a,b in zip(lp,lp[1:]):
                for c,d in zip(rp,rp[1:]):
                    cross,length=segment_conflict(a,b,c,d)
                    if any(p in (a,b) and p in (c,d) for p in common_points):continue
                    overlap+=length
                    if cross:
                        point=(a[0],c[1]) if a[0]==b[0] else (c[0],a[1])
                        if not any(on_segment(point,origin,le) and on_segment(point,origin,re) for origin,le,re in shared_stubs):contacts.add(point)
            crossings+=len(contacts)
    return {'network_edge_crossings':crossings,'network_overlap_length':round(overlap,3)}


def native_paths(root,nodes):
    from .network_layout import NETWORK_KINDS
    cells={c.get('id'):c for c in root}
    def box(key):
        c=cells[key];g=c.find('mxGeometry');x=float(g.get('x',0));y=float(g.get('y',0))
        if c.get('parent') in cells and cells[c.get('parent')].find('mxGeometry') is not None:
            px,py,_,_=box(c.get('parent'));x+=px;y+=py
        return x,y,float(g.get('width',0)),float(g.get('height',0))
    paths=[]
    for c in root:
        if c.get('edge')!='1' or c.get('visible')=='0' or 'opacity=0;' in c.get('style',''):continue
        st=dict(p.split('=',1) for p in c.get('style','').split(';') if '=' in p)
        def endpoint(key,prefix):
            x,y,w,h=box(key);return x+w*float(st[prefix+'X']),y+h*float(st[prefix+'Y'])
        source,target=c.get('source'),c.get('target');parent=c.get('parent')
        px,py,_,_=box(parent) if parent in cells and cells[parent].find('mxGeometry') is not None else (0,0,0,0)
        points=[endpoint(source,'exit'),*[(float(p.get('x'))+px,float(p.get('y'))+py) for p in c.findall('mxGeometry/Array/mxPoint')],endpoint(target,'entry')]
        paths.append({'source':source,'target':target,'network':any(nodes.get(k,{}).get('kind') in NETWORK_KINDS for k in (source,target)),'points':points})
    return paths


def route(start,end,obstacles,occupied=()):
    xs=sorted({start[0],end[0],*[v for x,y,w,h in obstacles for v in (max(0,x-12),x+w+12)]})
    ys=sorted({start[1],end[1],*[v for x,y,w,h in obstacles for v in (max(0,y-12),y+h+12)]})
    if occupied:
        xs=sorted(set(xs)|{max(0,p[0]+offset) for segment in occupied for p in segment for offset in (-8,8)})
        ys=sorted(set(ys)|{max(0,p[1]+offset) for segment in occupied for p in segment for offset in (-8,8)})
    origin=(xs.index(start[0]),ys.index(start[1]),-1)
    goal=(xs.index(end[0]),ys.index(end[1]))
    queue=[(abs(start[0]-end[0])+abs(start[1]-end[1]),0,origin)]
    costs={origin:0};previous={};clear_cache={};count=0
    while queue:
        _,cost,state=heapq.heappop(queue)
        if cost!=costs[state]:continue
        i,j,direction=state;count+=1
        if count>100000:raise ValueError('routing budget exceeded')
        if (i,j)==goal:
            path=[]
            while True:
                path.append((xs[state[0]],ys[state[1]]))
                if state==origin:break
                state=previous[state]
            path.reverse();result=[]
            for point in path:
                if len(result)>1 and ((result[-2][0]==result[-1][0]==point[0]) or (result[-2][1]==result[-1][1]==point[1])):result.pop()
                result.append(point)
            return result
        a=(xs[i],ys[j])
        for ni,nj,nd in ((i-1,j,0),(i+1,j,0),(i,j-1,1),(i,j+1,1)):
            if not 0<=ni<len(xs) or not 0<=nj<len(ys):continue
            b=(xs[ni],ys[nj]);cache_key=tuple(sorted((a,b)))
            if cache_key not in clear_cache:clear_cache[cache_key]=not any(intersects(a,b,r) for r in obstacles)
            if not clear_cache[cache_key]:continue
            newcost=cost+abs(a[0]-b[0])+abs(a[1]-b[1])+(12 if direction not in (-1,nd) else 0)
            if occupied:
                for c,d in occupied:
                    cross,overlap=segment_conflict(a,b,c,d)
                    newcost+=cross*400+overlap*24
            nxt=(ni,nj,nd)
            if newcost>=costs.get(nxt,float('inf')):continue
            costs[nxt]=newcost;previous[nxt]=state
            heapq.heappush(queue,(newcost+abs(b[0]-end[0])+abs(b[1]-end[1]),newcost,nxt))
    raise ValueError('no clear edge corridor')


def _route_native_edges(root,nodes,future=()):
    cells={c.get('id'):c for c in root}
    def rectangle(key):
        c=cells[key];g=c.find('mxGeometry');p=c.get('parent')
        x=float(g.get('x',0));y=float(g.get('y',0))
        if p in cells and cells[p].find('mxGeometry') is not None:
            px,py,_,_=rectangle(p);x+=px;y+=py
        return x,y,float(g.get('width',0)),float(g.get('height',0))
    rectangles={k:visible_rectangle(cells[k],rectangle(k)) for k in nodes if k in cells and nodes[k]['kind'] not in ('vcn','subnet','ipsec','cross_connect_group') and cells[k].get('visible')!='0'}
    # Container borders remain traversable, but their visible title lines do
    # not. Use the same width estimate as local typography, with a small gap.
    titles=[]
    for key,c in cells.items():
        style=c.get('style','')
        if c.get('visible')=='0' or 'verticalAlign=top;' not in style or 'align=left;' not in style:continue
        if nodes.get(key,{}).get('kind') not in ('vcn','subnet','ipsec','cross_connect_group') and not key.startswith('layout-'):continue
        options=dict(p.split('=',1) for p in style.split(';') if '=' in p)
        size=float(options.get('fontSize',12));spacing=float(options.get('spacing',12))
        x,y,w,h=rectangle(key)
        for i,line in enumerate(c.get('value','').split('\n')):
            if line:titles.append((x+spacing-2,y+spacing+i*(size+4)-2,min(max(0,w-2*spacing),text_width(line,size))+4,size+8))
    obstacles=list(rectangles.values())+titles
    def inside(point,rect):
        x,y,w,h=rect;return x<point[0]<x+w and y<point[1]<y+h
    def port(key,other,forced=None):
        full=rectangle(key);x,y,w,h=rectangles.get(key,full);tx,ty,tw,th=other
        dx=tx+tw/2-x-w/2;dy=ty+th/2-y-h/2
        preferred=forced or ((1 if dx>=0 else 0,0.5) if abs(dx)/max(w,1)>abs(dy)/max(h,1) else (0.5,1 if dy>=0 else 0))
        alternatives=sorted(((0.5,1),(1,0.5),(0,0.5),(0.5,0)),key=lambda p:abs(x+w*p[0]-tx-tw/2)+abs(y+h*p[1]-ty-th/2))
        glyph=rectangle(key+'-icon') if key+'-icon' in cells and 'ociNativeLabel=1;' in cells[key].get('style','') else None
        for anchor in (preferred,*alternatives):
            point=(x+w*anchor[0],y+h*anchor[1])
            corridor=point
            if glyph is not None:
                gx,gy,gw,gh=glyph
                if anchor[0] in (0,1):
                    point=(gx+gw*anchor[0],gy+gh/2);corridor=(x+w*anchor[0],point[1])
                elif anchor[1]==0:point=(gx+gw/2,gy);corridor=point
            if not any(inside(point,r) or inside(corridor,r) for r in titles):
                relative=((point[0]-full[0])/full[2],(point[1]-full[1])/full[3])
                return point,relative,corridor
        raise ValueError('no clear endpoint outside container title')
    # Route in display direction while retaining native API source/target.
    # BackendSet.lb_id points toward the LB; its start arrow displays ownership
    # from the LB down to the set. Both that fanout and backend fanout can share
    # a corridor, but only within the same evidenced owner.
    fanouts={};connections={}
    for edge in root:
        if edge.get('edge')!='1' or edge.get('visible')=='0' or 'opacity=0;' in edge.get('style',''):continue
        source,target=edge.get('source'),edge.get('target')
        reverse=(nodes.get(source,{}).get('kind')=='backend_set' and
                 nodes.get(target,{}).get('kind')=='lb' and 'startArrow=block;' in edge.get('style',''))
        if reverse:source,target=target,source
        connections[edge.get('id')]=(source,target,reverse)
        sk=nodes.get(source,{}).get('kind');tk=nodes.get(target,{}).get('kind')
        if (sk=='lb' and tk=='backend_set') or (sk=='backend_set' and tk in ('compute','vnic','unknown')):
            fanouts.setdefault(source,[]).append(edge)
    trunks={}
    for source,group in fanouts.items():
        if len(group)<2:continue
        x,y,w,h=rectangles.get(source,rectangle(source));targets=[rectangles.get(connections[e.get('id')][1],rectangle(connections[e.get('id')][1])) for e in group]
        if not all(ty>=y+h+24 for tx,ty,tw,th in targets):continue
        start=(x+w/2,y+h);branch=(start[0],(start[1]+min(t[1] for t in targets))/2)
        if any(inside(branch,r) for r in obstacles):continue
        trunks[source]=(route(start,branch,obstacles),branch)
    from .network_layout import NETWORK_KINDS
    def is_network(c):return any(nodes.get(c.get(k),{}).get('kind') in NETWORK_KINDS for k in ('source','target'))
    routed=0;drawn=[(p['source'],p['target'],p['points']) for p in future if p['network']]
    ordered=[c for c in root if c.get('edge')=='1']
    ordered.sort(key=is_network)
    for c in ordered:
        style=c.get('style','')
        if c.get('edge')!='1' or c.get('visible')=='0' or 'opacity=0;' in style:continue
        source,target,reverse=connections[c.get('id')]
        a,b=rectangles.get(source,rectangle(source)),rectangles.get(target,rectangle(target))
        flow=(nodes.get(source,{}).get('kind') in ('lb','backend_set') and nodes.get(target,{}).get('kind') in ('backend_set','compute','vnic','unknown'))
        downward=flow and a[1]+a[3]+8<=b[1]
        upward=flow and b[1]+b[3]+8<=a[1]
        start,exit_port,start_corridor=port(source,b,(0.5,1) if downward else ((0.5,0) if upward else None))
        end,entry_port,end_corridor=port(target,a,(0.5,0) if downward else ((0.5,1) if upward else None))
        g=c.find('mxGeometry');parent=rectangle(c.get('parent')) if c.get('parent') in cells and cells[c.get('parent')].find('mxGeometry') is not None else (0,0,0,0)
        existing=g.find("Array[@as='points']")
        bends=[(float(p.get('x'))+parent[0],float(p.get('y'))+parent[1]) for p in existing] if existing is not None else []
        if reverse:bends.reverse()
        middle=[start_corridor]+bends+[end_corridor]
        occupied=[]
        if is_network(c):
            for previous_source,previous_target,previous_points in drawn:
                if {source,target}=={previous_source,previous_target}:continue
                shared=set()
                if source==previous_source:shared.add(previous_points[0])
                if source==previous_target:shared.add(previous_points[-1])
                if target==previous_source:shared.add(previous_points[0])
                if target==previous_target:shared.add(previous_points[-1])
                occupied.extend((p,q) for p,q in zip(previous_points,previous_points[1:]) if not any(point in (p,q) for point in shared))
        if source in trunks and c in fanouts[source]:
            trunk,branch=trunks[source]
            start,exit_port,_=port(source,b,(0.5,1))
            end,entry_port,_=port(target,a,(0.5,0))
            approach=(end[0],end[1]-12)
            if any(rx<approach[0]<rx+rw and ry<approach[1]<ry+rh for rx,ry,rw,rh in obstacles):
                points=trunk+route(branch,end,obstacles)[1:]
            else:
                points=trunk+route(branch,approach,obstacles)[1:]+[end]
        else:
            if existing is None or any(any(segment_conflict(p,q,u,v)!=(0,0) for u,v in occupied) for p,q in zip(middle,middle[1:])) or any(p[0]!=q[0] and p[1]!=q[1] for p,q in zip(middle,middle[1:])) or any(intersects(p,q,r) for p,q in zip(middle,middle[1:]) for r in obstacles):middle=route(start_corridor,end_corridor,obstacles,occupied=occupied)
            points=[]
            for point in [start,*middle,end]:
                if not points or points[-1]!=point:points.append(point)
        if is_network(c) and nodes.get(target,{}).get('kind') in ('drg','rpc','cpe'):
            others=[{'source':u,'target':v,'network':True,'points':pp} for u,v,pp in drawn if {u,v}!={source,target}]
            def score(candidate):
                current={'source':source,'target':target,'network':True,'points':candidate}
                values=[path_quality([current,other]) for other in others]
                return (sum(v['network_edge_crossings'] for v in values),sum(v['network_overlap_length'] for v in values),sum(abs(p[0]-q[0])+abs(p[1]-q[1]) for p,q in zip(candidate,candidate[1:])))
            best=score(points)
            if best[:2]!=(0,0):
                for anchor in ((0.5,0),(0,0.5),(1,0.5),(0.5,1)):
                    alt_end,alt_port,alt_corridor=port(target,a,anchor)
                    if alt_port==entry_port:continue
                    try:middle=route(start_corridor,alt_corridor,obstacles,occupied=occupied)
                    except ValueError:continue  # Alternative port only; retain the valid baseline.
                    candidate=[]
                    for point in [start,*middle,alt_end]:
                        if not candidate or candidate[-1]!=point:candidate.append(point)
                    candidate_score=score(candidate)
                    if candidate_score<best:points=candidate;end=alt_end;entry_port=alt_port;best=candidate_score
        drawn=[p for p in drawn if {p[0],p[1]}!={source,target}]
        drawn.append((source,target,list(points)))
        if reverse:
            points.reverse();exit_port,entry_port=entry_port,exit_port
        if existing is not None:g.remove(existing)
        array=E.SubElement(g,'Array',**{'as':'points'})
        for x,y in points[1:-1]:E.SubElement(array,'mxPoint',x=str(x-parent[0]),y=str(y-parent[1]))
        c.set('style',style+f'edgeStyle=none;noEdgeStyle=1;orthogonal=1;rounded=0;exitPerimeter=0;entryPerimeter=0;exitX={exit_port[0]:.15g};exitY={exit_port[1]:.15g};entryX={entry_port[0]:.15g};entryY={entry_port[1]:.15g};')
        routed+=1
    return routed


def route_native_edges(root,nodes):
    """Bounded refinement; keep only strictly improved conflict counts."""
    count=_route_native_edges(root,nodes)
    for _ in range(2):
        paths=native_paths(root,nodes);quality=path_quality(paths)
        score=(quality['network_edge_crossings'],quality['network_overlap_length'])
        if score==(0,0):break
        previous=copy.deepcopy(root)
        _route_native_edges(root,nodes,future=paths)
        candidate=path_quality(native_paths(root,nodes))
        if (candidate['network_edge_crossings'],candidate['network_overlap_length'])>=score:
            root[:]=list(previous);break
    return count
