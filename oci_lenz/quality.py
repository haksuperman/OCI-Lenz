"""Deterministic, alias-only overview measurements; lower loss is better.

Compare only the same inventory/label footprint. No aesthetic/reachability claim,
model calls, topology changes or movement of model-owned rectangles occurs here.
"""
import math
import xml.etree.ElementTree as E
from .architecture import make_scene,seed_plan,check_plan,apply_design
from .diagram_model import diagram_graph
from .routing import native_paths,path_quality,visible_rectangle,intersects
from .typography import text_width
from .composition import measure,boundary_space
from .database_services import DB_SYSTEMS
from .managed_data import KINDS as MANAGED_KINDS


def conflict_pairs(paths,nodes):
    """Normalize only evidenced same-owner shared prefixes for comparison."""
    def owner(path):
        source,target=path['source'],path['target']
        sk=nodes.get(source,{}).get('kind');tk=nodes.get(target,{}).get('kind')
        if sk=='drg' and tk in ('ipsec_tunnel','vcn','rpc','virtual_circuit'):return source
        if tk=='drg' and sk in ('rpc','virtual_circuit','ipsec_tunnel'):return target
        if sk!='backend_set':return None
        kind=nodes.get(target,{}).get('kind')
        if kind in ('lb','nlb'):return target  # Native ownership arrow is reversed.
        if kind in ('compute','vnic','db_node','backend_endpoint','unknown','mysql_db_system','autonomous_database',*DB_SYSTEMS,*MANAGED_KINDS):return source
        return None
    def orient(path,key):
        points=path['points'] if path['source']==key else list(reversed(path['points']))
        clean=[]
        for point in points:
            if not clean or point!=clean[-1]:clean.append(point)
        return {**path,'source':key,'target':path['target'] if path['source']==key else path['source'],
                'network':True,'points':clean}
    def trim(left,right):
        a=list(left['points']);b=list(right['points'])
        while len(a)>1 and len(b)>1 and a[0]==b[0]:
            origin=a[0]
            def vector(end):
                dx,dy=end[0]-origin[0],end[1]-origin[1]
                if dx and dy:return None
                return (0 if dx==0 else (1 if dx>0 else -1),0 if dy==0 else (1 if dy>0 else -1))
            direction=vector(a[1])
            if direction is None or direction!=vector(b[1]):break
            length=min(math.dist(origin,a[1]),math.dist(origin,b[1]))
            point=(round(origin[0]+direction[0]*length,6),round(origin[1]+direction[1]*length,6))
            for seq in (a,b):
                if math.dist(point,seq[1])<1e-6:seq.pop(0)
                seq[0]=point
        return {**left,'points':a},{**right,'points':b}
    for i,left in enumerate(paths):
        for right in paths[i+1:]:
            key=owner(left)
            if key is not None and key==owner(right):yield trim(orient(left,key),orient(right,key))
            else:yield ({**left,'network':True},{**right,'network':True})


def edge_conflicts(paths,nodes):
    """Keep raw crossings and overlaps measurable, even with visible bridges."""
    crossings=0;overlap=0
    for pair in conflict_pairs(paths,nodes):
        result=path_quality(pair)
        crossings+=result['network_edge_crossings'];overlap+=result['network_overlap_length']
    return {'edge_crossings':crossings,'edge_overlap_length':round(overlap,3)}


def assess(snapshot,plan=None,*,xml=None,scene=None):
    from .draw import validate
    scene=scene or make_scene(snapshot,view='overview')
    overview=plan['overview'] if plan is not None else seed_plan(scene)
    if check_plan(scene,overview):raise ValueError('invalid quality assessment geometry')
    if overview.get('scene_signature')!=scene['signature']:raise ValueError('quality assessment inventory mismatch')
    xml=xml if xml is not None else apply_design(snapshot,plan)
    validate(xml,snapshot)
    root=E.fromstring(xml).find('diagram/mxGraphModel/root')
    cells={c.get('id'):c for c in root};nodes,_=diagram_graph(snapshot)
    aliases=scene['aliases'];items=scene['items'];focus=set()
    def box(key):
        cell=cells[key];g=cell.find('mxGeometry')
        x,y,w,h=(float(g.get(f,0)) for f in ('x','y','width','height'))
        parent=cell.get('parent')
        if parent in cells and cells[parent].find('mxGeometry') is not None:
            px,py,_,_=box(parent);x+=px;y+=py
        return x,y,w,h
    cards={key:visible_rectangle(cells[key],box(key)) for key,a in aliases.items() if not items[a]['container']}
    titles=[]
    for key,a in aliases.items():
        if not items[a]['container']:continue
        cell=cells[key];st=dict(p.split('=',1) for p in cell.get('style','').split(';') if '=' in p)
        size=float(st.get('fontSize',12));spacing=float(st.get('spacing',12));x,y,w,h=box(key)
        for i,line in enumerate(cell.get('value','').split('\n')):
            if line:titles.append((key,(x+spacing,y+spacing+i*(size+4),min(max(0,w-2*spacing),text_width(line,size)),size+4)))
    # XML anchor math can differ by ~1e-12 from stored bend coordinates.
    # Snap sub-micropixel noise before orthogonal intersection measurement.
    paths=[{**p,'points':[(round(x,6),round(y,6)) for x,y in p['points']]}
           for p in native_paths(root,nodes)]
    # Use the same fanout-aware conflict metric as native routing refinement.
    conflicts=edge_conflicts(paths,nodes)
    from .line_jumps import crossing_report
    bridges=crossing_report(paths,nodes,[*cards.values(),*(r for _,r in titles)])
    from .connector_rules import arrow_visibility
    visibility,head_focus=arrow_visibility(paths);focus.update(head_focus)
    intrusions=touched_titles=diagonal=bends=0;length=distance=0
    for path in paths:
        points=path['points'];endpoints={path['source'],path['target']}
        segments=[(a,b) for a,b in zip(points,points[1:]) if math.dist(a,b)>1e-6]
        directions=[]
        for a,b in segments:
            length+=abs(a[0]-b[0])+abs(a[1]-b[1])
            direction='v' if abs(a[0]-b[0])<1e-6 else ('h' if abs(a[1]-b[1])<1e-6 else 'd')
            diagonal+=direction=='d';directions.append(direction)
        bends+=sum(a!=b for a,b in zip(directions,directions[1:]))
        if points:distance+=abs(points[0][0]-points[-1][0])+abs(points[0][1]-points[-1][1])
        for key,rectangle in cards.items():
            if key not in endpoints and any(intersects(a,b,rectangle) for a,b in segments):
                intrusions+=1;focus.update(endpoints|{key})
        for key,rectangle in titles:
            if any(intersects(a,b,rectangle) for a,b in segments):
                touched_titles+=1;focus.update(endpoints|{key})
    boxes={p['id']:p for p in overview['placements']};siblings={}
    for key,item in items.items():siblings.setdefault(item['parent'],[]).append(key)
    gateway_pairs={frozenset((a,b)) for g in scene['request'].get('gateway_groups',[]) for a in g['members'] for b in g['members'] if a!=b}
    shortfall=0;spacing_violations=0;slack=0;container_area=0
    for parent,keys in siblings.items():
        for i,key in enumerate(keys):
            p=boxes[key]
            for other in keys[i+1:]:
                q=boxes[other]
                dx=max(0,p['x']-q['x']-q['width'],q['x']-p['x']-p['width'])
                dy=max(0,p['y']-q['y']-q['height'],q['y']-p['y']-p['height'])
                minimum=8 if frozenset((key,other)) in gateway_pairs else (24 if items[key]['container'] or items[other]['container'] else 16)
                deficit=max(0,minimum-math.hypot(dx,dy))/minimum
                if deficit>0.001:
                    spacing_violations+=1;shortfall+=deficit;focus.update(scene['keys'][a] for a in (key,other))
        if parent not in boxes:continue
        p=boxes[parent];required_w=max(boxes[k]['x']+boxes[k]['width'] for k in keys)-p['x']+12
        required_h=max(boxes[k]['y']+boxes[k]['height'] for k in keys)-p['y']+12
        area=p['width']*p['height'];container_area+=area
        excess=max(0,area-required_w*required_h);slack+=excess
        if excess>area*.35:focus.add(scene['keys'][parent])
    region=boxes[scene['region']];area=region['width']*region['height']
    leaf_area=sum(item['min_width']*item['min_height'] for key,item in items.items() if key not in siblings)
    scale=math.sqrt(max(1,leaf_area));edge_count=max(1,len(paths))
    metrics={**visibility,**bridges,'edge_crossings':conflicts['edge_crossings'],
             'edge_overlap_length':conflicts['edge_overlap_length'],
             'resource_intersections':intrusions,'title_intersections':touched_titles,
             'nonorthogonal_segments':diagonal,'spacing_violations':spacing_violations,
             'spacing_shortfall':round(shortfall,6),'edge_bends':bends,
             'route_detour_ratio':round(max(0,length/max(distance,1)-1),6),
             'canvas_area':round(area,3),'canvas_area_ratio':round(area/max(1,leaf_area),6),
             'container_slack_ratio':round(slack/max(1,container_area),6)}
    loss=(1000*(intrusions+touched_titles+diagonal)+100*metrics['unbridged_crossings']+.15*metrics['bridged_crossings']+
          20*metrics['edge_overlap_length']/scale+5*shortfall+
          12*metrics['route_detour_ratio']+2*bends/edge_count+
          .5*metrics['canvas_area_ratio']+2*metrics['container_slack_ratio'])
    loss+=100*visibility['crowded_arrowheads']+10*visibility['short_arrow_shafts']
    issues=[k for k in ('crowded_arrowheads','short_arrow_shafts','resource_intersections','title_intersections','nonorthogonal_segments','unbridged_crossings','edge_overlap_length','spacing_violations') if metrics[k]>0]
    if metrics['container_slack_ratio']>.35:issues.append('excessive_whitespace')
    if metrics['route_detour_ratio']>1:issues.append('route_detours')
    if metrics['unbridged_crossings'] or metrics['edge_overlap_length']:
        for i,left in enumerate(paths):
            for right in paths[i+1:]:
                pair=edge_conflicts((left,right),nodes)
                if pair['edge_crossings'] or pair['edge_overlap_length']:
                    focus.update(p[k] for p in (left,right) for k in ('source','target'))
    design=measure(scene,boxes);metrics.update(design['metrics']);loss+=design['loss']
    boundary=boundary_space(scene,boxes,paths)
    metrics.update(boundary['metrics'])
    loss+=6*metrics['unused_boundary_area_ratio']+2*metrics['worst_boundary_slack_ratio']
    # Boundary hints are actionable first. Projection feedback can also identify
    # internal gaps, but must not override actual branch/shaft space.
    design['feedback']=boundary['feedback']+design['feedback']
    from .connector_rules import readability
    connections=readability(scene['request'].get('connection_readability',{}),boxes)
    metrics.update(connections['metrics']);loss+=8*metrics['unknown_target_distance']+4*metrics['fanout_misalignment']+30*metrics['connector_clearance_shortfall']+8*metrics['fanout_row_obstructions']
    design['feedback'].extend(connections['feedback'])
    if metrics['connector_clearance_shortfall']>.001:issues.append('connector_clearance_shortfall')
    if metrics['fanout_row_obstructions']:issues.append('fanout_row_obstructions')
    if metrics['remote_unknown_targets']:issues.append('remote_unknown_targets')
    if metrics['fanout_misalignment']>.2:issues.append('fanout_misalignment')
    from .connector_rules import alignment_issues
    connector_issues=alignment_issues(scene['request'].get('connector_guides',[]),overview)
    metrics['connector_alignment_errors']=len(connector_issues);loss+=1000*len(connector_issues)
    if connector_issues:issues.append('connector_alignment_errors')
    for key,limit in (('avoidable_whitespace_ratio',.20),('worst_container_whitespace_ratio',.30),('excess_gap_ratio',.25),
                      ('card_inflation_ratio',.15),('alignment_error',.35),
                      ('flow_alignment_error',.20),('flow_reversals',0),
                      ('network_alignment_error',.15),('worst_network_alignment_error',.20)):
        if metrics[key]>limit:issues.append(key)
    if metrics['unused_boundary_area_ratio']>.20:issues.append('unused_boundary_space')
    return {'version':6,'scene_signature':scene['signature'],'status':'needs_review' if issues else 'clear','loss':round(loss,6),
            'metrics':metrics,'issues':issues,'focus':sorted(set(aliases[k] for k in focus if k in aliases)|{f['id'] for f in design['feedback']}),
            'design_feedback':design['feedback'],'connector_feedback':connector_issues}


def revision_decision(current,candidate,*,initial=None):
    """Prefer measured readable connections over area; never trade protected safety."""
    before,after=current['metrics'],candidate['metrics']
    if current['scene_signature']!=candidate['scene_signature']:
        return {'accepted':False,'reason':'different_inventory'}
    if current['version']!=candidate['version']:return {'accepted':False,'reason':'different_quality_version'}
    protected=('resource_intersections','title_intersections','nonorthogonal_segments','unbridged_crossings','edge_overlap_length','flow_reversals','connector_alignment_errors','crowded_arrowheads','short_arrow_shafts','connector_clearance_shortfall','fanout_row_obstructions')
    for field in protected:
        if after.get(field,0)>before.get(field,0)+1e-6:return {'accepted':False,'reason':'regression_'+field}
    readable=any(after.get(k,0)<before.get(k,0)-1e-6 for k in ('crowded_arrowheads','short_arrow_shafts','connector_clearance_shortfall','fanout_row_obstructions'))
    if readable:
        if after.get('worst_container_whitespace_ratio',0)>max(.5,before.get('worst_container_whitespace_ratio',0)+.1):return {'accepted':False,'reason':'unnecessary_canvas_growth'}
        return {'accepted':True,'reason':'clearer_connections'}
    # Compactness alone must not undo the accepted short orthogonal branches.
    # Keep readability repairs free to resolve genuine pre-existing deficits.
    for field in ('edge_bends','route_detour_ratio'):
        if after.get(field,0)>before.get(field,0)+1e-6:return {'accepted':False,'reason':'regression_'+field}
    reference=(initial or current)['metrics']['canvas_area']
    if after['canvas_area']>reference*1.25:return {'accepted':False,'reason':'canvas_growth'}
    if candidate['loss']>=current['loss']-1e-6:return {'accepted':False,'reason':'not_improved'}
    return {'accepted':True,'reason':'lower_loss'}
