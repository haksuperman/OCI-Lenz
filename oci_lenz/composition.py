"""Content-sized design guidance and alias-only measurements, never a layout engine."""


def policy():
    return {'resource_gap':24,'container_gap':24,'inner_padding':16,
            'connector_corridor':72,'network_corridor':96,'alignment_tolerance':8,
            'card_extra_width':8,'card_extra_height':8,
            'boundary_padding':16,'wire_boundary_clearance':8}


def boundary_space(scene,boxes,paths):
    """Non-mutating crop hints for frames; never repack cards or shorten wires.

    Existing child frames are obstacles too: a parent's hint cannot assume a
    child's future shrink. Native wire endpoints/bends inside a frame preserve
    side buses and terminal lanes, including unrelated crossing wires. Straight
    through segments can cross a smaller border without changing their path.
    The model must still validate a candidate: hints are not automatic resizing.
    """
    items=scene['items'];children={};feedback=[];total=unused=0;worst=0
    for key,item in items.items():children.setdefault(item['parent'],[]).append(key)
    padding=policy()['boundary_padding'];clearance=policy()['wire_boundary_clearance']
    for key,item in sorted(items.items()):
        if not item['container']:continue
        p=boxes[key];x,y=p['x'],p['y'];right=x+p['width'];bottom=y+p['height']
        header=item.get('header_height',48)
        content=[boxes[k] for k in children.get(key,[])]
        # Points outside this frame are not its occupied content. Do not clip
        # a crossing segment at the old border, which would pin empty margins.
        points=[(px,py) for path in paths for px,py in path['points']
                if x<=px<=right and y<=py<=bottom]
        lefts=[b['x']-padding for b in content]+[px-clearance for px,py in points]
        tops=[b['y']-header for b in content]+[py-header-clearance for px,py in points]
        rights=[b['x']+b['width']+padding for b in content]+[px+clearance for px,py in points]
        bottoms=[b['y']+b['height']+padding for b in content]+[py+clearance for px,py in points]
        left=max(x,min(lefts,default=x));top=max(y,min(tops,default=y))
        end_x=min(right,max(rights,default=x+item['min_width']))
        end_y=min(bottom,max(bottoms,default=y+item['min_height']))
        min_height=min(p['height'],max(item['min_height'],header+padding))
        end_x=min(right,max(end_x,left+item['min_width']))
        left=min(left,end_x-item['min_width'])
        end_y=min(bottom,max(end_y,top+min_height));top=min(top,end_y-min_height)
        bounds=dict(x=left,y=top,width=end_x-left,height=end_y-top)
        area=p['width']*p['height'];saved=max(0,area-bounds['width']*bounds['height'])
        total+=area;unused+=saved;worst=max(worst,saved/max(1,area))
        trim=dict(left=left-x,top=top-y,right=right-end_x,bottom=bottom-end_y)
        if max(trim.values())>padding:
            feedback.append({'id':key,'issue':'unused_boundary_space',
                             'bounds':{k:round(v,3) for k,v in bounds.items()},
                             'trim':{k:round(v,3) for k,v in trim.items()},
                             'preserve_children_and_wire_paths':True})
    return {'metrics':{'unused_boundary_area_ratio':round(unused/max(1,total),6),
                       'worst_boundary_slack_ratio':round(worst,6)},
            'feedback':feedback}


def measure(scene,boxes):
    items=scene['items'];request=scene['request'];children={};feedback=[]
    for key,item in items.items():children.setdefault(item['parent'],[]).append(key)
    def projection(keys,axis):
        dimension='width' if axis=='x' else 'height'
        intervals=sorted((boxes[k][axis],boxes[k][axis]+boxes[k][dimension]) for k in keys)
        merged=[]
        for start,end in intervals:
            if merged and start<=merged[-1][1]:merged[-1][1]=max(end,merged[-1][1])
            else:merged.append([start,end])
        return sum(end-start for start,end in merged),[b[0]-a[1] for a,b in zip(merged,merged[1:])]
    wire_axes={}
    for edge in request.get('edges',[]):
        source,target=edge['source'],edge['target']
        if source not in boxes or target not in boxes:continue
        ancestors=[];key=items[source].get('parent')
        while key in items:ancestors.append(key);key=items[key].get('parent')
        key=items[target].get('parent')
        while key in items and key not in ancestors:key=items[key].get('parent')
        if key not in items:continue
        a,b=boxes[source],boxes[target]
        axis='x' if abs(a['x']+a['width']/2-b['x']-b['width']/2)>abs(a['y']+a['height']/2-b['y']-b['height']/2) else 'y'
        wire_axes.setdefault(key,set()).add(axis)
    whitespace=container_area=excess_gaps=0;worst_whitespace=0
    gap_axes=0;inflation=0;leaves=0;alignment=0;align_pairs=0
    for parent,keys in children.items():
        if parent not in boxes:continue
        p=boxes[parent];item=items[parent]
        # Direction contracts genuinely require extra space around DRG branches.
        network=item['kind']=='region' and bool(request.get('network_groups'))
        budget=96 if network else (72 if parent in wire_axes else 32)
        lengths=[]
        for axis in ('x','y'):
            occupied,gaps=projection(keys,axis)
            lengths.append(occupied+sum(min(gap,64 if network else 24) for gap in gaps))
            excess_gaps+=sum(max(0,gap-budget)/budget for gap in gaps);gap_axes+=len(gaps)
        width=max(item['min_width'],lengths[0]+24+(48 if 'x' in wire_axes.get(parent,set()) else 0))
        height=max(item['min_height'],lengths[1]+item.get('header_height',48)+12+(48 if 'y' in wire_axes.get(parent,set()) else 0))
        area=p['width']*p['height'];excess=max(0,area-width*height)
        whitespace+=excess;container_area+=area
        worst_whitespace=max(worst_whitespace,excess/area)
        if excess/area>.12:
            feedback.append({'id':parent,'issue':'avoidable_whitespace',
                             'ratio':round(excess/area,3),'suggested_width':round(width,2),
                             'suggested_height':round(height,2),'children':sorted(keys)})
        for i,key in enumerate(keys):
            a=boxes[key]
            for other in keys[i+1:]:
                kinds={items[key]['kind'],items[other]['kind']}
                if len(kinds)>1 and not kinds<= {'internet','nat','service'}:continue
                b=boxes[other]
                overlap_x=min(a['x']+a['width'],b['x']+b['width'])-max(a['x'],b['x'])
                overlap_y=min(a['y']+a['height'],b['y']+b['height'])-max(a['y'],b['y'])
                deviation=None
                if overlap_y>=.5*min(a['height'],b['height']):
                    deviation=min(abs(a['y']-b['y']),abs(a['y']+a['height']/2-b['y']-b['height']/2))
                elif overlap_x>=.5*min(a['width'],b['width']):
                    if items[key]['container'] and items[other]['container'] and max(a['width'],b['width'])>1.5*min(a['width'],b['width']):continue
                    deviation=abs(a['x']+a['width']/2-b['x']-b['width']/2)
                    if items[key]['container'] and items[other]['container']:deviation=min(deviation,abs(a['x']-b['x']))
                if deviation is not None:
                    alignment+=max(0,deviation-8)/24;align_pairs+=1
                    if deviation>16:feedback.append({'id':key,'issue':'alignment','with':other,'offset':round(deviation,2)})
    for key,item in items.items():
        if item['container']:
            if key not in children and item['kind']!='region':
                p=boxes[key];area=p['width']*p['height']
                excess=max(0,area-item['min_width']*item['min_height'])
                whitespace+=excess;container_area+=area;worst_whitespace=max(worst_whitespace,excess/area)
                if excess/area>.12:feedback.append({'id':key,'issue':'empty_container_inflation',
                                                   'suggested_width':item['min_width'],'suggested_height':item['min_height']})
            continue
        p=boxes[key];leaves+=1
        extra=max(0,p['width']-item['min_width']-8)/item['min_width']+max(0,p['height']-item['min_height']-8)/item['min_height']
        inflation+=extra
        if extra>.1:feedback.append({'id':key,'issue':'card_inflation',
                                    'suggested_width':item['min_width'],'suggested_height':item['min_height']})
    def vcn(key):
        while key in items:
            if items[key]['kind']=='vcn':return key
            key=items[key]['parent']
        return None
    # Only observed one-to-one edges within the SAME actual VCN form a vertical
    # alignment hint. Fanout and cross-VCN links do not imply a service or column.
    flows=set()
    for edge in request.get('edges',[]):
        source,target=edge['source'],edge['target']
        if source not in items or target not in items:continue
        if edge['kind']=='lb_id':source,target=target,source
        elif edge['kind']!='backend':continue
        if vcn(source) is not None and vcn(source)==vcn(target):flows.add((source,target))
    flow_alignment=0;flow_count=0;reversals=0
    for source,target in sorted(flows):
        if sum(s==source for s,t in flows)!=1 or sum(t==target for s,t in flows)!=1:continue
        a,b=boxes[source],boxes[target];flow_count+=1
        offset=abs(a['x']+a['width']/2-b['x']-b['width']/2)
        flow_alignment+=max(0,offset-8)/max(a['width'],b['width'])
        reversed_flow=b['y']+b['height']+8<=a['y']
        reversals+=reversed_flow
        if offset>16 or reversed_flow:
            feedback.append({'id':source,'issue':'flow_alignment','with':target,'offset':round(offset,2)})
    network_errors=[]
    def axis(source,target,axis_name,tolerance=8):
        a,b=boxes[source],boxes[target];size='width' if axis_name=='x' else 'height'
        desired=a[axis_name]+a[size]/2;actual=b[axis_name]+b[size]/2
        error=max(0,abs(desired-actual)-tolerance)/max(170,a[size],b[size])
        network_errors.append(error)
        if error>.05:feedback.append({'id':target,'issue':'network_axis','with':source,
                                      'axis':axis_name,'suggested_center':round(desired,2)})
    peer_pairs={frozenset(g['endpoints']) for g in request.get('network_groups',[]) if g['kind']=='remote_peer'}
    for group in request.get('network_groups',[]):
        if group['kind']!='drg' or group['drg'] not in boxes:continue
        owner=group['drg']
        for field,kind in (('fastconnect_members','virtual_circuit'),('remote_members','rpc')):
            members=[k for k in group.get(field,[]) if k in boxes and items[k]['kind']==kind]
            if len(members)==1:
                axis(owner,members[0],'x')
                if kind=='rpc':
                    unknown=[k for k in group.get(field,[]) if k in boxes and items[k]['kind']=='unknown']
                    if len(unknown)==1 and frozenset((members[0],unknown[0])) in peer_pairs:axis(members[0],unknown[0],'x')
    metrics={'avoidable_whitespace_ratio':round(whitespace/max(1,container_area),6),
             'worst_container_whitespace_ratio':round(worst_whitespace,6),
             'excess_gap_ratio':round(excess_gaps/max(1,gap_axes),6),
             'card_inflation_ratio':round(inflation/max(1,leaves),6),
             'alignment_error':round(alignment/max(1,align_pairs),6),
             'flow_alignment_error':round(flow_alignment/max(1,flow_count),6),
             'flow_reversals':reversals,
             'network_alignment_error':round(sum(network_errors)/max(1,len(network_errors)),6),
             'worst_network_alignment_error':round(max(network_errors,default=0),6)}
    loss=(4*metrics['avoidable_whitespace_ratio']+2*worst_whitespace+metrics['excess_gap_ratio']+
          8*metrics['card_inflation_ratio']+4*metrics['alignment_error']+
          6*metrics['flow_alignment_error']+20*reversals+
          6*metrics['network_alignment_error']+4*metrics['worst_network_alignment_error'])
    return {'metrics':metrics,'loss':round(loss,6),'feedback':feedback[:24]}
