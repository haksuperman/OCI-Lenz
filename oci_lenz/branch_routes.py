"""Geometry-only shared branch trees. No resource creation or coordinate presets."""
from .connector_rules import TERMINAL_LENGTH,LANE_GAP


def compact(points):
    result=[]
    for p in points:
        if result and p==result[-1]:continue
        while len(result)>1 and ((result[-2][0]==result[-1][0]==p[0]) or (result[-2][1]==result[-1][1]==p[1])):
            a,b=result[-2:]
            if (b[0]-a[0])*(p[0]-b[0])+(b[1]-a[1])*(p[1]-b[1])<0:break
            result.pop()
        result.append(p)
    return result


def branch_tree(start,out,ends,obstacles,bounds=None,direction='down'):
    """Return orthogonal paths sharing one root; an infeasible tree returns None."""
    def forward(p):
        x,y=p
        return {'down':(x,y),'up':(x,-y),'right':(y,x),'left':(y,-x)}[direction]
    def inverse(p):
        x,y=p
        return {'down':(x,y),'up':(x,-y),'right':(y,x),'left':(-y,x)}[direction]
    def rect(r):
        x,y,w,h=r;corners=[forward(p) for p in ((x,y),(x+w,y+h))]
        return min(p[0] for p in corners),min(p[1] for p in corners),abs(corners[1][0]-corners[0][0]),abs(corners[1][1]-corners[0][1])
    from .routing import intersects
    obs=[rect(r) for r in obstacles];limit=rect(bounds) if bounds is not None else None
    first,stub=forward(start),forward(out)
    targets=[(key,forward(end),forward(approach)) for key,end,approach in ends]
    if not targets or min(a[1] for key,end,a in targets)<stub[1]+8:return None
    candidates=[]
    if max(a[1] for key,end,a in targets)-min(a[1] for key,end,a in targets)<=8:
        lower,upper=stub[1],min(a[1] for key,end,a in targets)
        middle=(lower+upper)/2
        # Container titles can sit at the midpoint. Slide the SAME row bus in
        # its free corridor before considering a long lateral detour.
        levels={lower,upper,middle}
        for x,y,w,h in obs:levels.update(v for v in (y-8,y+h+8) if lower<=v<=upper)
        for level in sorted(levels,key=lambda y:(abs(y-middle),y)):
            candidates.append({key:compact([first,stub,(first[0],level),(end[0],level),approach,end]) for key,end,approach in targets})
    # A multi-row fanout branches from a SIDE bus; it never runs through an
    # earlier target, which could look like an invented target-to-target chain.
    left=min([first[0],*[end[0] for key,end,a in targets]])-LANE_GAP-TERMINAL_LENGTH
    right=max([first[0],*[end[0] for key,end,a in targets]])+LANE_GAP+TERMINAL_LENGTH
    # Derive true card extents instead of assuming a width around target centers.
    relevant=[r for r in obs if any(r[0]<=end[0]<=r[0]+r[2] and r[1]<=end[1]<=r[1]+r[3] for key,end,a in targets)]
    if relevant:
        left=min(r[0] for r in relevant)-LANE_GAP-8
        right=max(r[0]+r[2] for r in relevant)+LANE_GAP+8
    for lane in sorted((left,right),key=lambda x:(abs(x-first[0]),x)):
        candidates.append({key:compact([first,stub,(lane,stub[1]),(lane,approach[1]),approach,end]) for key,end,approach in targets})
    def clear(paths):
        for points in paths.values():
            if limit:
                x,y,w,h=limit
                if any(not(x+4<=p[0]<=x+w-4 and y+4<=p[1]<=y+h-4) for p in points):return False
            for r in obs:
                x,y,w,h=r
                owns=lambda p:x-1e-6<=p[0]<=x+w+1e-6 and y-1e-6<=p[1]<=y+h+1e-6
                obstacle=r if owns(points[0]) or owns(points[-1]) else (x-8,y-8,w+16,h+16)
                if any(intersects(a,b,obstacle) for a,b in zip(points,points[1:])):return False
        return True
    for paths in candidates:
        if clear(paths):return {key:[inverse(p) for p in points] for key,points in paths.items()}
    return None
