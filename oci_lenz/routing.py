"""Deterministic orthogonal routing around resource cards, without moving them."""
import copy
import heapq
from bisect import bisect_left,bisect_right
import xml.etree.ElementTree as E
from .typography import text_width
from .load_balancers import LOAD_BALANCER_KINDS
from .managed_data import KINDS as MANAGED_KINDS
from .connector_rules import JUMP_SIZE,CROSSING_CLEARANCE,LANE_GAP,STROKE_WIDTH,ARROW_SIZE

BEND_COST=26
CROSS_COST=16
OVERLAP_COST=24
CONTACT_COST=400


def conflict_aware(nodes,source,target):
    """Every observed visible edge participates, independently of service type."""
    return source in nodes or target in nodes


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


def contact_conflict(a,b,c,d):
    """Proper crossings may jump; overlap or near-end contacts need a detour."""
    cross,overlap=segment_conflict(a,b,c,d)
    if overlap:return True
    if not cross:return False
    point=(a[0],c[1]) if a[0]==b[0] else (c[0],a[1])
    return any(abs(point[0]-p[0])+abs(point[1]-p[1])<CROSSING_CLEARANCE for p in (a,b,c,d))


def path_quality(paths):
    """Count network/DB ambiguity, exempting genuine shared endpoint stubs.

    Metric keys retain their historical network_ prefix for compatibility.
    """
    crossings=0;overlap=0
    for i,left in enumerate(paths):
        for right in paths[i+1:]:
            if not (left['network'] or right['network'] or left.get('conflict_aware') or right.get('conflict_aware')):continue
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
        paths.append({'source':source,'target':target,'network':any(nodes.get(k,{}).get('kind') in NETWORK_KINDS for k in (source,target)),
                      'conflict_aware':conflict_aware(nodes,source,target),'jump_style':st.get('jumpStyle','none'),'points':points})
    return paths


def path_cost(points):
    segments=[(a,b) for a,b in zip(points,points[1:]) if a!=b]
    axes=[a[0]==b[0] for a,b in segments]
    return sum(abs(a[0]-b[0])+abs(a[1]-b[1]) for a,b in segments)+BEND_COST*sum(a!=b for a,b in zip(axes,axes[1:]))


def route(start,end,obstacles,occupied=()):
    xs=sorted({start[0],end[0],*[v for x,y,w,h in obstacles for v in (max(0,x-12),x+w+12)]})
    ys=sorted({start[1],end[1],*[v for x,y,w,h in obstacles for v in (max(0,y-12),y+h+12)]})
    if occupied:
        xs=sorted(set(xs)|{max(0,p[0]+offset) for segment in occupied for p in segment for offset in (-LANE_GAP,LANE_GAP)})
        ys=sorted(set(ys)|{max(0,p[1]+offset) for segment in occupied for p in segment for offset in (-LANE_GAP,LANE_GAP)})
    # Index parallel/crossing segments by their fixed coordinate. A route may
    # traverse thousands of grid edges; scanning every existing wire for each
    # one makes ordinary dense backends unnecessarily expensive.
    vertical={};horizontal={}
    for a,b in occupied:
        if a==b:continue
        if a[0]==b[0]:vertical.setdefault(a[0],[]).append(sorted((a[1],b[1])))
        else:horizontal.setdefault(a[1],[]).append(sorted((a[0],b[0])))
    vx=sorted(vertical);hy=sorted(horizontal)
    def penalty(a,b):
        is_vertical=a[0]==b[0];axis=1 if is_vertical else 0
        low,high=sorted((a[axis],b[axis]));fixed=a[1-axis]
        parallel=vertical if is_vertical else horizontal
        perpendicular=horizontal if is_vertical else vertical
        levels=hy if is_vertical else vx
        overlap=sum(max(0,min(high,q)-max(low,p)) for p,q in parallel.get(fixed,()))
        crossings=sum((CONTACT_COST if min(fixed-p,q-fixed)<CROSSING_CLEARANCE else CROSS_COST)
                      for level in levels[bisect_left(levels,low):bisect_right(levels,high)]
                      for p,q in perpendicular[level] if p<=fixed<=q)
        return crossings+overlap*OVERLAP_COST
    near_cache={}
    def near_wire(point):
        if point not in near_cache:
            x,y=point
            near_cache[point]=(any(abs(x-level)<CROSSING_CLEARANCE and p-CROSSING_CLEARANCE<y<q+CROSSING_CLEARANCE
                                  for level in vx[bisect_left(vx,x-CROSSING_CLEARANCE):bisect_right(vx,x+CROSSING_CLEARANCE)] for p,q in vertical[level]) or
                               any(abs(y-level)<CROSSING_CLEARANCE and p-CROSSING_CLEARANCE<x<q+CROSSING_CLEARANCE
                                  for level in hy[bisect_left(hy,y-CROSSING_CLEARANCE):bisect_right(hy,y+CROSSING_CLEARANCE)] for p,q in horizontal[level]))
        return near_cache[point]
    origin=(xs.index(start[0]),ys.index(start[1]),-1)
    goal=(xs.index(end[0]),ys.index(end[1]))
    queue=[(abs(start[0]-end[0])+abs(start[1]-end[1]),0,origin)]
    costs={origin:0};previous={};clear_cache={};penalty_cache={};count=0
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
            turn=direction not in (-1,nd)
            newcost=cost+abs(a[0]-b[0])+abs(a[1]-b[1])+(BEND_COST if turn else 0)
            if turn and near_wire(a):newcost+=CONTACT_COST
            if occupied:
                if cache_key not in penalty_cache:
                    penalty_cache[cache_key]=penalty(a,b)
                newcost+=penalty_cache[cache_key]
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
    def side_height(key):
        if key+'-icon' in cells:
            _,y,_,h=rectangle(key+'-icon');return y+h/2
        _,y,_,h=rectangles.get(key,rectangle(key));return y+h/2
    def port(key,other,forced=None,aligned_y=None):
        full=rectangle(key);x,y,w,h=rectangles.get(key,full);tx,ty,tw,th=other
        dx=tx+tw/2-x-w/2;dy=ty+th/2-y-h/2
        preferred=forced or ((1 if dx>=0 else 0,0.5) if abs(dx)/max(w,1)>abs(dy)/max(h,1) else (0.5,1 if dy>=0 else 0))
        alternatives=sorted(((0.5,1),(1,0.5),(0,0.5),(0.5,0)),key=lambda p:abs(x+w*p[0]-tx-tw/2)+abs(y+h*p[1]-ty-th/2))
        glyph=rectangle(key+'-icon') if key+'-icon' in cells and 'ociNativeLabel=1;' in cells[key].get('style','') else None
        candidates=[(preferred,aligned_y),(preferred,None),*((a,None) for a in alternatives)]
        for anchor,aligned in candidates:
            point=(x+w*anchor[0],y+h*anchor[1])
            corridor=point
            if glyph is not None:
                gx,gy,gw,gh=glyph
                if anchor[0] in (0,1):
                    point=(gx+gw*anchor[0],gy+gh/2);corridor=(x+w*anchor[0],point[1])
                elif anchor[1]==0:point=(gx+gw/2,gy);corridor=point
            elif key not in rectangles and anchor[0] in (0,1) and aligned is not None:
                st=dict(p.split('=',1) for p in cells[key].get('style','').split(';') if '=' in p)
                font=float(st.get('fontSize',12))
                header=max(48,12+(font+4)*len(cells[key].get('value','').split('\n')))
                if not y+header<=aligned<=y+h-12:continue
                point=(point[0],aligned)
            # A port alone does not constrain the last segment. Approach the
            # face normally from a short OUTSIDE stub, including logical tags.
            # Glyph-side stubs first clear the full caption/content width.
            if anchor[0] in (0,1):corridor=(x-12 if anchor[0]==0 else x+w+12,point[1])
            elif anchor[1]==0:corridor=(point[0],min(y,point[1])-12)
            else:corridor=(point[0],max(y+h,point[1])+12)
            if not any(inside(point,r) or inside(corridor,r) for r in titles) and not any(inside(corridor,r) for other_key,r in rectangles.items() if other_key!=key):
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
                 nodes.get(target,{}).get('kind') in LOAD_BALANCER_KINDS and any('startArrow='+a+';' in edge.get('style','') for a in ('block','open')))
        if reverse:source,target=target,source
        connections[edge.get('id')]=(source,target,reverse)
        sk=nodes.get(source,{}).get('kind');tk=nodes.get(target,{}).get('kind')
        if (sk in LOAD_BALANCER_KINDS and tk=='backend_set') or (sk=='backend_set' and tk in ('compute','vnic','unknown',*MANAGED_KINDS)):
            fanouts.setdefault(source,[]).append(edge)
    trunks={}
    for source,group in fanouts.items():
        if len(group)<2:continue
        x,y,w,h=rectangles.get(source,rectangle(source));targets=[rectangles.get(connections[e.get('id')][1],rectangle(connections[e.get('id')][1])) for e in group]
        if not all(ty>=y+h+24 for tx,ty,tw,th in targets):continue
        start=(x+w/2,y+h);branch=(start[0],(start[1]+min(t[1] for t in targets))/2)
        if any(inside(branch,r) for r in obstacles):continue
        trunks[source]=(start,branch)
    from .network_layout import NETWORK_KINDS
    def is_network(c):return any(nodes.get(c.get(k),{}).get('kind') in NETWORK_KINDS for k in ('source','target'))
    def avoids_conflicts(c):return conflict_aware(nodes,c.get('source'),c.get('target'))
    routed=0;drawn=[];trunk_routes={}
    for p in future:
        source,target,points=p['source'],p['target'],p['points']
        if nodes.get(source,{}).get('kind')=='backend_set' and nodes.get(target,{}).get('kind') in LOAD_BALANCER_KINDS:
            source,target,points=target,source,list(reversed(points))
        drawn.append((source,target,points))
    ordered=[c for c in root if c.get('edge')=='1']
    def branch_order(c):
        if c.get('id') not in connections:return ('',0,0,c.get('id',''))
        source,target,_=connections[c.get('id')];x,y,_,_=rectangle(target)
        return (source,y,x,c.get('id',''))
    ordered.sort(key=branch_order)
    for c in ordered:
        style=c.get('style','')
        if c.get('edge')!='1' or c.get('visible')=='0' or 'opacity=0;' in style:continue
        source,target,reverse=connections[c.get('id')]
        a,b=rectangles.get(source,rectangle(source)),rectangles.get(target,rectangle(target))
        flow=(nodes.get(source,{}).get('kind') in (*LOAD_BALANCER_KINDS,'backend_set') and nodes.get(target,{}).get('kind') in ('backend_set','compute','vnic','unknown',*MANAGED_KINDS))
        downward=flow and a[1]+a[3]+8<=b[1]
        upward=flow and b[1]+b[3]+8<=a[1]
        exit_face=(0.5,1) if downward else ((0.5,0) if upward else None)
        entry_face=(0.5,0) if downward else ((0.5,1) if upward else None)
        if is_network(c) and not flow:
            # Wide short tunnel tags must not choose their TOP merely because
            # normalizing distance by their height makes the vertical score big.
            if a[0]+a[2]+8<=b[0]:exit_face,entry_face=(1,0.5),(0,0.5)
            elif b[0]+b[2]+8<=a[0]:exit_face,entry_face=(0,0.5),(1,0.5)
        start,exit_port,start_corridor=port(source,b,exit_face,aligned_y=side_height(target))
        end,entry_port,end_corridor=port(target,a,entry_face,aligned_y=start[1])
        g=c.find('mxGeometry');parent=rectangle(c.get('parent')) if c.get('parent') in cells and cells[c.get('parent')].find('mxGeometry') is not None else (0,0,0,0)
        existing=g.find("Array[@as='points']")
        occupied=[];foreign_occupied=[]
        if avoids_conflicts(c):
            for previous_source,previous_target,previous_points in drawn:
                if {source,target}=={previous_source,previous_target}:continue
                shared=set()
                if source==previous_source:shared.add(previous_points[0])
                if source==previous_target:shared.add(previous_points[-1])
                if target==previous_source:shared.add(previous_points[0])
                if target==previous_target:shared.add(previous_points[-1])
                # A shared endpoint permits its short native stub, not an
                # unrelated shared corridor or a later reconvergence.
                allowed_prefix=set();branch_clearance={}
                if source==previous_source and nodes.get(source,{}).get('kind')=='drg':
                    # Only the initial normal stub and vertical bus on this
                    # exact DRG face may be shared. Keep all later branches
                    # occupied so divergence/rejoining remains a conflict.
                    for index,(p,q) in enumerate(zip(previous_points,previous_points[1:])):
                        same_bus=abs(p[0]-start_corridor[0])<1e-6 and abs(q[0]-start_corridor[0])<1e-6
                        initial_stub=index==0 and abs(q[0]-start_corridor[0])<1e-6 and abs(q[1]-start_corridor[1])<1e-6
                        if not (initial_stub or same_bus):
                            if abs(p[0]-start_corridor[0])<1e-6 and p[1]==q[1]:
                                dx=q[0]-p[0];step=min(LANE_GAP,abs(dx))*(1 if dx>0 else -1)
                                branch_clearance[(p,q)]=((p[0]+step,p[1]),q)
                            break
                        allowed_prefix.add((p,q))
                segments=[branch_clearance.get((p,q),(p,q)) for p,q in zip(previous_points,previous_points[1:]) if (p,q) not in allowed_prefix and not any(point in (p,q) for point in shared)]
                occupied.extend(segments)
                if previous_source!=source:foreign_occupied.extend(segments)
        if source in trunks and c in fanouts[source]:
            trunk_start,branch=trunks[source]
            if source not in trunk_routes:trunk_routes[source]=route(trunk_start,branch,obstacles,occupied=foreign_occupied)
            trunk=trunk_routes[source]
            start,exit_port,_=port(source,b,(0.5,1))
            end,entry_port,approach=port(target,a,(0.5,0))
            points=trunk+route(branch,approach,obstacles,occupied=occupied)[1:]+[end]
        else:
            collinear=(abs(start[1]-end[1])<1e-6 and all(abs(p[1]-start[1])<1e-6 for p in (start_corridor,end_corridor))) or (abs(start[0]-end[0])<1e-6 and all(abs(p[0]-start[0])<1e-6 for p in (start_corridor,end_corridor)))
            straight=collinear and not any(intersects(start_corridor,end_corridor,r) for r in obstacles) and not any(contact_conflict(start_corridor,end_corridor,u,v) for u,v in occupied)
            if straight:middle=[]
            else:middle=route(start_corridor,end_corridor,obstacles,occupied=occupied)
            points=[]
            for point in [start,*middle,end]:
                if not points or points[-1]!=point:points.append(point)
        if is_network(c) and nodes.get(target,{}).get('kind') in ('drg','rpc','cpe'):
            others=[{'source':u,'target':v,'network':True,'points':pp} for u,v,pp in drawn if {u,v}!={source,target}]
            def score(candidate):
                current={'source':source,'target':target,'network':True,'points':candidate}
                values=[path_quality([current,other]) for other in others]
                return (sum(v['network_overlap_length'] for v in values),path_cost(candidate)+CROSS_COST*sum(v['network_edge_crossings'] for v in values))
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
        # A DB ownership chain can enter and leave the same icon face. Moving
        # only the corridor then causes a short reversal over the incoming wire.
        # Search normal endpoint faces without moving cards or changing evidence.
        from .database_services import MODELS,DB_SYSTEMS
        flexible_ports=any(nodes.get(k,{}).get('kind') in (*MODELS,*DB_SYSTEMS,'db_node','waf','edge_waf','edge_origin') for k in (source,target))
        if flexible_ports and not is_network(c) and not flow and source not in trunks:
            others=[{'source':u,'target':v,'network':True,'points':pp}
                    for u,v,pp in drawn if {u,v}!={source,target}]
            def db_score(candidate):
                current={'source':source,'target':target,'network':True,'points':candidate}
                values=[path_quality([current,other]) for other in others]
                return (sum(v['network_overlap_length'] for v in values),path_cost(candidate)+CROSS_COST*sum(v['network_edge_crossings'] for v in values))
            best=db_score(points)
            if best[:2]!=(0,0):
                for exit_face in ((0.5,0),(0,0.5),(1,0.5),(0.5,1)):
                    for entry_face in ((0.5,0),(0,0.5),(1,0.5),(0.5,1)):
                        alt_start,alt_exit,alt_out=port(source,b,exit_face)
                        alt_end,alt_entry,alt_in=port(target,a,entry_face)
                        try:middle=route(alt_out,alt_in,obstacles,occupied=occupied)
                        except ValueError:continue
                        candidate=[]
                        for point in [alt_start,*middle,alt_end]:
                            if not candidate or candidate[-1]!=point:candidate.append(point)
                        candidate_score=db_score(candidate)
                        if candidate_score<best:
                            points=candidate;exit_port,entry_port=alt_exit,alt_entry;best=candidate_score
        drawn=[p for p in drawn if {p[0],p[1]}!={source,target}]
        drawn.append((source,target,list(points)))
        if reverse:
            points.reverse();exit_port,entry_port=entry_port,exit_port
        if existing is not None:g.remove(existing)
        array=E.SubElement(g,'Array',**{'as':'points'})
        for x,y in points[1:-1]:E.SubElement(array,'mxPoint',x=str(x-parent[0]),y=str(y-parent[1]))
        style=style.replace('startArrow=block;','startArrow=open;').replace('endArrow=block;','endArrow=open;')
        c.set('style',style+f'jumpStyle=arc;jumpSize={JUMP_SIZE};strokeWidth={STROKE_WIDTH};startSize={ARROW_SIZE};endSize={ARROW_SIZE};startFill=0;endFill=0;edgeStyle=none;noEdgeStyle=1;orthogonal=1;rounded=0;exitPerimeter=0;entryPerimeter=0;exitX={exit_port[0]:.15g};exitY={exit_port[1]:.15g};entryX={entry_port[0]:.15g};entryY={entry_port[1]:.15g};')
        routed+=1
    return routed


def route_native_edges(root,nodes):
    """Bounded refinement of overlap, normal contacts and path simplicity."""
    from .quality import edge_conflicts
    from .line_jumps import crossing_report
    count=_route_native_edges(root,nodes)
    for _ in range(2):
        paths=native_paths(root,nodes);quality=edge_conflicts(paths,nodes)
        bridges=crossing_report(paths,nodes)
        score=(bridges['unbridged_crossings'],quality['edge_overlap_length'],sum(path_cost(p['points']) for p in paths)+CROSS_COST*bridges['bridged_crossings'])
        if quality['edge_crossings']==0 and quality['edge_overlap_length']==0:break
        previous=copy.deepcopy(root)
        _route_native_edges(root,nodes,future=paths)
        refined=native_paths(root,nodes);candidate=edge_conflicts(refined,nodes)
        bridges=crossing_report(refined,nodes)
        if (bridges['unbridged_crossings'],candidate['edge_overlap_length'],sum(path_cost(p['points']) for p in refined)+CROSS_COST*bridges['bridged_crossings'])>=score:
            root[:]=list(previous);break
    return count
