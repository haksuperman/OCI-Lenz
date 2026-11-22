"""Service-independent native-anchor contracts for configured container edges."""

VERSION=2
JUMP_SIZE=8
CROSSING_CLEARANCE=10
LANE_GAP=24
STROKE_WIDTH=1.8
ARROW_SIZE=10
TERMINAL_LENGTH=24
CONNECTOR_CORRIDOR=72


def readability_groups(request):
    """Alias-only layout hints from exact edges; never invent membership."""
    items=request['items'];edges=request['edges'];nearby=[];fanouts={}
    for edge in edges:
        source,target=edge['source'],edge['target'];kind=edge['kind']
        if kind=='lb_id':source,target=target,source
        if kind in ('backend','lb_id','drg_network','api_backend','mount_export'):
            fanouts.setdefault(source,set()).add(target)
        if kind not in ('backend','edge_protection','waf_protection','peer_id','api_backend'):continue
        if items[target]['kind'] not in ('unknown','edge_origin','backend_endpoint'):continue
        owners={e['source'] for e in edges if e['target']==target}
        if owners=={source}:nearby.append({'source':source,'target':target})
    return {'nearby':sorted(nearby,key=lambda p:(p['source'],p['target'])),
            'fanouts':[{'source':s,'targets':sorted(ts)} for s,ts in sorted(fanouts.items()) if len(ts)>1],
            'corridors':[{'source':e['target'] if e['kind']=='lb_id' else e['source'],
                          'target':e['source'] if e['kind']=='lb_id' else e['target'],
                          'minimum_gap':CONNECTOR_CORRIDOR} for e in edges if e['source']!=e['target']]}


def readability(groups,boxes):
    """Soft constraints: honor containment even when a short route is impossible."""
    remote=0;distance=0;misalignment=0;feedback=[]
    for pair in groups.get('nearby',[]):
        if any(k not in boxes for k in pair.values()):continue
        a,b=(boxes[pair[k]] for k in ('source','target'))
        dx=max(0,a['x']-b['x']-b['width'],b['x']-a['x']-a['width'])
        dy=max(0,a['y']-b['y']-b['height'],b['y']-a['y']-a['height'])
        import math
        count=max((len(g['targets']) for g in groups.get('fanouts',[]) if g['source']==pair['source']),default=1)
        limit=max(2,math.ceil(math.sqrt(count)))*max(a['width'],b['width'],a['height'],b['height'])+CONNECTOR_CORRIDOR
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
    clearance=0;shadows=0
    for pair in groups.get('corridors',[]):
        if pair['source'] not in boxes or pair['target'] not in boxes:continue
        a,b=boxes[pair['source']],boxes[pair['target']]
        dx=max(0,a['x']-b['x']-b['width'],b['x']-a['x']-a['width'])
        dy=max(0,a['y']-b['y']-b['height'],b['y']-a['y']-a['height'])
        gap=max(dx,dy);required=pair['minimum_gap'];deficit=max(0,required-gap)/required
        # Contained ownership arrows are not a demand to move a child outside.
        contains=lambda x,y:x['x']<=y['x'] and x['y']<=y['y'] and x['x']+x['width']>=y['x']+y['width'] and x['y']+x['height']>=y['y']+y['height']
        if contains(a,b) or contains(b,a):continue
        clearance+=deficit
        if deficit:feedback.append({'id':pair['source'],'with':pair['target'],'issue':'connector_corridor','minimum_gap':required})
    for group in groups.get('fanouts',[]):
        targets=[(key,boxes[key]) for key in group['targets'] if key in boxes]
        source=boxes.get(group['source'])
        if source is None:continue
        # Detect near stacked rows behind one another, even if their centers align.
        for i,(key,a) in enumerate(targets):
            for other,b in targets[i+1:]:
                overlap_x=min(a['x']+a['width'],b['x']+b['width'])-max(a['x'],b['x'])
                overlap_y=min(a['y']+a['height'],b['y']+b['height'])-max(a['y'],b['y'])
                vertical=(a['y']>=source['y']+source['height'] and b['y']>=source['y']+source['height']) or (a['y']+a['height']<=source['y'] and b['y']+b['height']<=source['y'])
                horizontal=(a['x']>=source['x']+source['width'] and b['x']>=source['x']+source['width']) or (a['x']+a['width']<=source['x'] and b['x']+b['width']<=source['x'])
                gap_y=max(a['y']-b['y']-b['height'],b['y']-a['y']-a['height'])
                gap_x=max(a['x']-b['x']-b['width'],b['x']-a['x']-a['width'])
                if (vertical and overlap_x>0 and 0<=gap_y<CONNECTOR_CORRIDOR) or (horizontal and overlap_y>0 and 0<=gap_x<CONNECTOR_CORRIDOR):
                    shadows+=1;feedback.append({'id':key,'with':other,'issue':'fanout_row_corridor','source':group['source'],'minimum_gap':CONNECTOR_CORRIDOR})
    return {'metrics':{'connector_clearance_shortfall':round(clearance,6),'fanout_row_obstructions':shadows,'remote_unknown_targets':remote,'unknown_target_distance':round(distance,6),
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


def arrow_visibility(paths):
    """Measure arrowheads independently of canonical API edge direction."""
    import math
    heads=[];short=0;focus=set()
    for path in paths:
        points=[]
        for point in path['points']:
            if not points or math.dist(point,points[-1])>1e-6:points.append(point)
        if len(points)<2:continue
        for prefix,resource,owner,end,near in [('start',path['source'],path['target'],points[0],points[1]),('end',path['target'],path['source'],points[-1],points[-2])]:
            if path.get(prefix+'_arrow','none')=='none':continue
            heads.append((resource,owner,end))
            if math.dist(end,near)<TERMINAL_LENGTH-1e-6:short+=1;focus.add(resource)
    crowded=0
    for i,(resource,owner,point) in enumerate(heads):
        for other,other_owner,position in heads[i+1:]:
            if other==resource and owner!=other_owner and math.dist(point,position)<ARROW_SIZE+2-1e-6:
                crowded+=1;focus.add(resource)
    return {'crowded_arrowheads':crowded,'short_arrow_shafts':short},focus
