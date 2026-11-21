"""Service-independent native-anchor contracts for configured container edges."""

VERSION=1
JUMP_SIZE=8
CROSSING_CLEARANCE=10
LANE_GAP=16
STROKE_WIDTH=1.4
ARROW_SIZE=8


def readability_groups(request):
    """Alias-only layout hints from exact edges; never invent membership."""
    items=request['items'];edges=request['edges'];nearby=[];fanouts={}
    for edge in edges:
        source,target=edge['source'],edge['target'];kind=edge['kind']
        if kind=='lb_id':source,target=target,source
        if kind in ('backend','lb_id','drg_network'):
            fanouts.setdefault(source,set()).add(target)
        if kind not in ('backend','edge_protection','waf_protection','peer_id'):continue
        if items[target]['kind'] not in ('unknown','edge_origin'):continue
        owners={e['source'] for e in edges if e['target']==target}
        if owners=={source}:nearby.append({'source':source,'target':target})
    return {'nearby':sorted(nearby,key=lambda p:(p['source'],p['target'])),
            'fanouts':[{'source':s,'targets':sorted(ts)} for s,ts in sorted(fanouts.items()) if len(ts)>1]}


def readability(groups,boxes):
    """Soft constraints: honor containment even when a short route is impossible."""
    remote=0;distance=0;misalignment=0;feedback=[]
    for pair in groups.get('nearby',[]):
        if any(k not in boxes for k in pair.values()):continue
        a,b=(boxes[pair[k]] for k in ('source','target'))
        dx=max(0,a['x']-b['x']-b['width'],b['x']-a['x']-a['width'])
        dy=max(0,a['y']-b['y']-b['height'],b['y']-a['y']-a['height'])
        limit=2*max(a['width'],b['width'],a['height'],b['height'])
        excess=max(0,(dx+dy-limit)/limit);distance+=excess
        if excess:
            remote+=1;feedback.append({'id':pair['target'],'with':pair['source'],
                                      'issue':'remote_unknown_target','excess':round(excess,3)})
    for group in groups.get('fanouts',[]):
        targets=[boxes[k] for k in group['targets'] if k in boxes]
        if len(targets)<2:continue
        # Different actual subnets can make a single aligned row impossible.
        # This is guidance, never an instruction to reparent or hide a target.
        centers=[(b['x']+b['width']/2,b['y']+b['height']/2) for b in targets]
        # Compact multi-row grids are valid fanouts. Penalize a target that
        # aligns with neither a sibling row nor column, not the grid's span.
        offsets=[min(min(abs(x-u),abs(y-v)) for j,(u,v) in enumerate(centers) if i!=j)
                 for i,(x,y) in enumerate(centers)]
        error=sum(max(0,offset-8) for offset in offsets)/len(offsets)/max(170,max(b['width'] for b in targets))
        misalignment=max(misalignment,error)
        if error:feedback.append({'id':group['source'],'issue':'fanout_alignment','targets':group['targets'],'error':round(error,3)})
    return {'metrics':{'remote_unknown_targets':remote,'unknown_target_distance':round(distance,6),
                       'fanout_misalignment':round(misalignment,6)},'feedback':feedback}


def guides(request,offsets):
    items=request['items'];edges=request['edges'];children={}
    for key,item in items.items():children.setdefault(item.get('parent'),[]).append(key)
    def reference(key):
        if not items[key]['container']:return key
        members=children.get(key,[])
        if len(members)==1 and not items[members[0]]['container']:return members[0]
        return None
    result=[]
    for edge in edges:
        source,target=edge['source'],edge['target']
        if not (items[source]['container'] or items[target]['container']):continue
        # Keep all real endpoints. A guide does not add an edge to the child.
        if sum(e['source']==source and e['kind']==edge['kind'] for e in edges)!=1:continue
        if sum(e['target']==target and e['kind']==edge['kind'] for e in edges)!=1:continue
        a,b=reference(source),reference(target)
        if a is None or b is None:continue
        result.append({'edge':edge['id'],'source':source,'target':target,
                       'source_anchor':a,'target_anchor':b,'axis':'y',
                       'source_offset':offsets.get(a),'target_offset':offsets.get(b),
                       'tolerance':.001})
    return result


def alignment_issues(rules,plan):
    boxes={p['id']:p for p in plan.get('placements',[])};issues=[]
    for rule in rules:
        a,b=rule['source_anchor'],rule['target_anchor']
        if a not in boxes or b not in boxes:continue  # Missing shapes have their own hard error.
        def anchor(key,offset):return boxes[key]['y']+(boxes[key]['height']/2 if offset is None else offset)
        delta=anchor(a,rule['source_offset'])-anchor(b,rule['target_offset'])
        if abs(delta)>rule['tolerance']:
            issues.append('connector glyph row '+rule['edge']+' '+a+' '+b+' offset '+str(round(delta,3)))
    return issues
