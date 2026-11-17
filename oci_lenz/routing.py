"""Deterministic orthogonal routing around resource cards, without moving them."""
import heapq
import xml.etree.ElementTree as E


def intersects(a,b,rect):
    x,y,w,h=rect
    if a[0]==b[0]:return x<a[0]<x+w and max(min(a[1],b[1]),y)<min(max(a[1],b[1]),y+h)
    if a[1]==b[1]:return y<a[1]<y+h and max(min(a[0],b[0]),x)<min(max(a[0],b[0]),x+w)
    return True


def route(start,end,obstacles):
    xs=sorted({start[0],end[0],*[v for x,y,w,h in obstacles for v in (max(0,x-12),x+w+12)]})
    ys=sorted({start[1],end[1],*[v for x,y,w,h in obstacles for v in (max(0,y-12),y+h+12)]})
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
            nxt=(ni,nj,nd)
            if newcost>=costs.get(nxt,float('inf')):continue
            costs[nxt]=newcost;previous[nxt]=state
            heapq.heappush(queue,(newcost+abs(b[0]-end[0])+abs(b[1]-end[1]),newcost,nxt))
    raise ValueError('no clear edge corridor')


def route_native_edges(root,nodes):
    cells={c.get('id'):c for c in root}
    def rectangle(key):
        c=cells[key];g=c.find('mxGeometry');p=c.get('parent')
        x=float(g.get('x',0));y=float(g.get('y',0))
        if p in cells and cells[p].find('mxGeometry') is not None:
            px,py,_,_=rectangle(p);x+=px;y+=py
        return x,y,float(g.get('width',0)),float(g.get('height',0))
    rectangles={k:rectangle(k) for k in nodes if k in cells and nodes[k]['kind'] not in ('vcn','subnet') and cells[k].get('visible')!='0'}
    def port(rect,other):
        x,y,w,h=rect;tx,ty,tw,th=other
        dx=tx+tw/2-x-w/2;dy=ty+th/2-y-h/2
        if abs(dx)/max(w,1)>abs(dy)/max(h,1):return ((x+w if dx>=0 else x),y+h/2),(1 if dx>=0 else 0,0.5)
        return (x+w/2,(y+h if dy>=0 else y)),(0.5,1 if dy>=0 else 0)
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
        x,y,w,h=rectangle(source);targets=[rectangle(connections[e.get('id')][1]) for e in group]
        if not all(ty>=y+h+24 for tx,ty,tw,th in targets):continue
        start=(x+w/2,y+h);branch=(start[0],(start[1]+min(t[1] for t in targets))/2)
        if any(rx<branch[0]<rx+rw and ry<branch[1]<ry+rh for rx,ry,rw,rh in rectangles.values()):continue
        trunks[source]=(route(start,branch,list(rectangles.values())),branch)
    routed=0
    for c in root:
        style=c.get('style','')
        if c.get('edge')!='1' or c.get('visible')=='0' or 'opacity=0;' in style:continue
        source,target,reverse=connections[c.get('id')]
        a,b=rectangle(source),rectangle(target)
        start,exit_port=port(a,b);end,entry_port=port(b,a)
        obstacles=list(rectangles.values())
        g=c.find('mxGeometry');parent=rectangle(c.get('parent')) if c.get('parent') in cells and cells[c.get('parent')].find('mxGeometry') is not None else (0,0,0,0)
        existing=g.find("Array[@as='points']")
        bends=[(float(p.get('x'))+parent[0],float(p.get('y'))+parent[1]) for p in existing] if existing is not None else []
        if reverse:bends.reverse()
        points=[start]+bends+[end]
        if source in trunks and c in fanouts[source]:
            trunk,branch=trunks[source];start=trunk[0];exit_port=(0.5,1)
            end=(b[0]+b[2]/2,b[1]);entry_port=(0.5,0)
            approach=(end[0],end[1]-12)
            if any(rx<approach[0]<rx+rw and ry<approach[1]<ry+rh for rx,ry,rw,rh in obstacles):
                points=trunk+route(branch,end,obstacles)[1:]
            else:
                points=trunk+route(branch,approach,obstacles)[1:]+[end]
        elif existing is None or any(p[0]!=q[0] and p[1]!=q[1] for p,q in zip(points,points[1:])) or any(intersects(p,q,r) for p,q in zip(points,points[1:]) for r in obstacles):points=route(start,end,obstacles)
        if reverse:
            points.reverse();exit_port,entry_port=entry_port,exit_port
        if existing is not None:g.remove(existing)
        array=E.SubElement(g,'Array',**{'as':'points'})
        for x,y in points[1:-1]:E.SubElement(array,'mxPoint',x=str(x-parent[0]),y=str(y-parent[1]))
        c.set('style',style+f'edgeStyle=none;noEdgeStyle=1;orthogonal=1;rounded=0;exitX={exit_port[0]};exitY={exit_port[1]};entryX={entry_port[0]};entryY={entry_port[1]};')
        routed+=1
    return routed
