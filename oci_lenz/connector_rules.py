"""Service-independent native-anchor contracts for configured container edges."""

VERSION=1


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
