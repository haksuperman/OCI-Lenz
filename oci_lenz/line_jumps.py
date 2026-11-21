"""Conservative native line-jump classification; no topology edits."""
from .routing import path_quality,segment_conflict

from .connector_rules import JUMP_SIZE,CROSSING_CLEARANCE as CLEARANCE


def crossing_report(paths,nodes,forbidden=()):
    from .quality import conflict_pairs
    bridged=unbridged=0;classified=[]
    for left,right in conflict_pairs(paths,nodes):
        raw=path_quality((left,right))['network_edge_crossings']
        if not raw:continue
        safe=set()
        # Native line jumps are drawn on the later wire. A style flag alone
        # never proves an endpoint, bend, or congested crossing is readable.
        if right.get('jump_style')=='arc':
            for a,b in zip(left['points'],left['points'][1:]):
                for c,d in zip(right['points'],right['points'][1:]):
                    cross,_=segment_conflict(a,b,c,d)
                    if not cross:continue
                    point=(a[0],c[1]) if a[0]==b[0] else (c[0],a[1])
                    if any(abs(point[0]-p[0])+abs(point[1]-p[1])<CLEARANCE for p in (a,b,c,d)):continue
                    x,y=point
                    if any(rx-CLEARANCE<x<rx+w+CLEARANCE and ry-CLEARANCE<y<ry+h+CLEARANCE for rx,ry,w,h in forbidden):continue
                    safe.add(point)
        classified.append((raw,safe))
    all_points=[p for _,points in classified for p in points]
    for raw,points in classified:
        # A crossing cluster cannot be represented by one clean bridge.
        count=min(raw,sum(sum(abs(p[0]-q[0])+abs(p[1]-q[1])<2*CLEARANCE for q in all_points)==1 for p in points))
        bridged+=count;unbridged+=raw-count
    return {'bridged_crossings':bridged,'unbridged_crossings':unbridged}
