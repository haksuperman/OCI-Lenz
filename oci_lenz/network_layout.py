"""Alias-only placement of API-confirmed DRG endpoints, without Attachment cards."""

NETWORK_KINDS=('drg','lpg','rpc','ipsec','ipsec_tunnel','cpe','virtual_circuit','cross_connect','cross_connect_group')


def network_groups(nodes,edges,aliases):
    def resolve(reference):
        return reference if reference in aliases else ('unknown:'+reference if reference and 'unknown:'+reference in aliases else None)
    def target(source,kind):
        return next((e['target'] for e in edges if e['source']==source and e['kind']==kind and e['target'] in aliases),None)
    groups=[];seen=set()
    for key in sorted(aliases):
        kind=nodes.get(key,{}).get('kind')
        if kind in ('lpg','rpc'):
            peer=target(key,'peer_id')
            if peer:
                pair=tuple(sorted((key,peer)))
                if pair not in seen:
                    seen.add(pair);groups.append({'kind':'local_peer' if kind=='lpg' else 'remote_peer','endpoints':[aliases[k] for k in pair]})
        if kind=='drg':
            left=set();right=set();above=set()
            for edge in edges:
                if edge['kind']!='drg_network' or edge['source']!=key or edge['target'] not in aliases:continue
                endpoint=edge['target'];endpoint_kind=nodes[endpoint]['kind'];network_type=edge.get('network_type')
                if network_type=='VCN' or endpoint_kind=='vcn':left.add(endpoint)
                elif network_type=='IPSEC_TUNNEL' or endpoint_kind=='ipsec_tunnel':right.add(endpoint)
                elif network_type=='REMOTE_PEERING_CONNECTION' or endpoint_kind=='rpc':above.add(endpoint)
            for member in sorted(aliases):
                member_kind=nodes.get(member,{}).get('kind')
                if member_kind=='ipsec' and resolve(nodes[member].get('drg_id'))==key:
                    right.add(member);cpe=resolve(nodes[member].get('cpe_id'))
                    if cpe:right.add(cpe)
                    right.update(t for t in aliases if nodes.get(t,{}).get('kind')=='ipsec_tunnel' and target(t,'ipsec_id')==member)
                if member_kind=='rpc' and resolve(nodes[member].get('drg_id'))==key:above.add(member)
            for member in list(above):
                peer=target(member,'peer_id')
                if peer:above.add(peer)
            fastconnect={k for k in aliases if nodes.get(k,{}).get('kind')=='virtual_circuit' and resolve(nodes[k].get('gateway_id'))==key}
            fastconnect.update(e['target'] for e in edges if e['kind']=='drg_network' and e['source']==key and e['target'] in aliases and (e.get('network_type')=='VIRTUAL_CIRCUIT' or nodes[e['target']]['kind']=='virtual_circuit'))
            for _ in range(len(nodes)):
                before=len(fastconnect)
                fastconnect.update(e['target'] for e in edges if e['kind']=='cross_connect_mapping' and e['source'] in fastconnect and e['target'] in aliases)
                fastconnect.update(e['target'] for e in edges if e['kind']=='cross_connect_group_id' and e['source'] in fastconnect and e['target'] in aliases)
                fastconnect.update(k for k in aliases if nodes.get(k,{}).get('kind')=='cross_connect' and resolve(nodes[k].get('cross_connect_group_id')) in fastconnect)
                if len(fastconnect)==before:break
            if left or right or above or fastconnect:
                group={'kind':'drg','drg':aliases[key],'vcns':[aliases[k] for k in sorted(left)],
                    'ipsec_members':[aliases[k] for k in sorted(right)],'remote_members':[aliases[k] for k in sorted(above)],'branch_gap':64}
                if fastconnect:group['fastconnect_members']=[aliases[k] for k in sorted(fastconnect)]
                groups.append(group)
        if kind=='virtual_circuit':
            group={'kind':'fastconnect','circuit':aliases[key],'targets':[aliases[e['target']] for e in edges if e['source']==key and e['kind']=='cross_connect_mapping' and e['target'] in aliases]}
            gateway=resolve(nodes[key].get('gateway_id'))
            if gateway:group['gateway']=aliases[gateway]
            groups.append(group)
        if kind=='ipsec':
            group={'kind':'vpn','connection':aliases[key],
                   'tunnels':[aliases[t] for t in sorted(aliases) if nodes.get(t,{}).get('kind')=='ipsec_tunnel' and target(t,'ipsec_id')==key]}
            for field in ('drg_id','cpe_id'):
                endpoint=resolve(nodes[key].get(field))
                if endpoint:group[field[:-3]]=aliases[endpoint]
            groups.append(group)
    return groups


def direction_issues(scene,boxes):
    issues=[]
    for group in scene['request'].get('network_groups',[]):
        if group['kind']!='drg' or group['drg'] not in boxes:continue
        drg=boxes[group['drg']];gap=group['branch_gap']
        for key in group['vcns']:
            if key in boxes and boxes[key]['x']+boxes[key]['width']>drg['x']-gap:issues.append('DRG vcns must be left '+key+' '+group['drg'])
        for key in group['ipsec_members']:
            if key in boxes and boxes[key]['x']<drg['x']+drg['width']+gap:issues.append('DRG ipsec_members must be right '+key+' '+group['drg'])
        for key in group['remote_members']:
            if key in boxes and boxes[key]['y']+boxes[key]['height']>drg['y']-gap:issues.append('DRG remote_members must be above '+key+' '+group['drg'])
        for key in group.get('fastconnect_members',[]):
            if key in boxes and boxes[key]['y']<drg['y']+drg['height']+gap:issues.append('DRG fastconnect_members must be below '+key+' '+group['drg'])
    return issues


def orient_seed(scene,placements):
    """Explicit diagnostic seed only; never repack model-owned rectangles."""
    groups=[g for g in scene['request'].get('network_groups',[]) if g['kind']=='drg']
    if not groups:return
    boxes={p['id']:p for p in placements};region=boxes[scene['region']]
    controlled={g['drg'] for g in groups}|{k for g in groups for field in ('ipsec_members','remote_members','fastconnect_members') for k in g.get(field,[])}
    ordinary=[p for k,p in boxes.items() if k not in controlled and k!=scene['region']]
    dx=max([p['x']+p['width'] for p in ordinary] or [region['x']])+64
    def move(key,x,y):
        dx,dy=x-boxes[key]['x'],y-boxes[key]['y']
        for child in boxes:
            parent=child
            while parent in scene['items'] and parent!=key:parent=scene['items'][parent]['parent']
            if parent==key:boxes[child]['x']+=dx;boxes[child]['y']+=dy
    above=sorted({k for g in groups for k in g['remote_members']});y=region['y']+scene['items'][scene['region']].get('header_height',48)+24
    cursor=dx;rowheight=0
    for key in above:
        p=boxes[key];move(key,cursor,y);cursor+=p['width']+24;rowheight=max(rowheight,p['height'])
    y+=rowheight+64;placed=set(above)
    for group in groups:
        drg=boxes[group['drg']];right=[k for k in group['ipsec_members'] if k not in placed and scene['items'][k]['parent'] not in group['ipsec_members']]
        rh=sum(max(boxes[k]['height'] for k in right[i:i+2])+16 for i in range(0,len(right),2)) if right else 0
        height=max(drg['height'],rh);move(group['drg'],dx,y+(height-drg['height'])/2);ry=y
        for start in range(0,len(right),2):
            rx=dx+drg['width']+group['branch_gap'];row=right[start:start+2]
            for key in row:
                p=boxes[key];move(key,rx,ry);rx+=p['width']+24;placed.add(key)
            ry+=max(boxes[k]['height'] for k in row)+16
        fastconnect=group.get('fastconnect_members',[])
        roots=[k for k in fastconnect if k not in placed and scene['items'][k]['parent'] not in fastconnect]
        fy=y+height+group['branch_gap']
        for start in range(0,len(roots),2):
            fx=dx;row=roots[start:start+2]
            for key in row:
                p=boxes[key];move(key,fx,fy);fx+=p['width']+24;placed.add(key)
            fy+=max(boxes[k]['height'] for k in row)+24
        y=(fy if roots else y+height)+48
    region['width']=max(p['x']+p['width'] for p in placements if p is not region)-region['x']+24
    region['height']=max(p['y']+p['height'] for p in placements if p is not region)-region['y']+24
