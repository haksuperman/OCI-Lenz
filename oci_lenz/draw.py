"""Draw.io skill helpers: official editable stencils, deterministic rendering, validation."""
import base64,copy,json,os,shutil,subprocess,sys,urllib.parse,zlib
from pathlib import Path
import xml.etree.ElementTree as E
from .model import graph
ROOT=Path(__file__).resolve().parents[1]
if not (ROOT/'assets/oci/library.xml').exists(): ROOT=Path(sys.prefix)/'share/oci-lenz'
ICONS={'compute':3,'vnic':78,'vcn':17,'subnet':17,'lb':18,'backend_set':18,'route':29,'service':31,'internet':32,'nat':33,'nsg':114}

def edge_label(edge):
    return edge['label'] or {'nsg_ids':'NSG','route_table_id':'Route table','lb_id':'Backend set'}.get(edge['kind'],edge['kind'])

def icon(root, rid, kind, x,y):
    if kind not in ICONS: return
    library=json.loads(E.parse(ROOT/'assets/oci/library.xml').getroot().text)
    item=library[ICONS[kind]]
    xml=urllib.parse.unquote(zlib.decompress(base64.b64decode(item['xml']),-15).decode())
    src=E.fromstring(xml)
    cells=[c for c in src.iter('mxCell') if c.get('id') not in ('0','1')]
    group=E.SubElement(root,'mxCell',id=rid+'-icon',value='',style='group',vertex='1',parent=rid)
    E.SubElement(group,'mxGeometry',x=str(x),y=str(y),width='54',height='54',**{'as':'geometry'})
    scale=54/max(item['w'],item['h'])
    # Toolkit library cells may carry a common origin on the top layer.
    top=[c for c in cells if c.get('parent')=='1']
    ox=min((float(c.find('mxGeometry').get('x',0)) for c in top if c.find('mxGeometry') is not None),default=0)
    oy=min((float(c.find('mxGeometry').get('y',0)) for c in top if c.find('mxGeometry') is not None),default=0)
    for c in cells:
        c=copy.deepcopy(c); c.set('value',''); old=c.get('id'); parent=c.get('parent','1')
        c.set('id',rid+'-i-'+old); c.set('parent',rid+'-icon' if parent=='1' else rid+'-i-'+parent)
        for g in c.iter('mxGeometry'):
            for key in ('x','y','width','height'):
                if key in g.attrib:
                    value=float(g.get(key))
                    if parent=='1' and key in ('x','y'): value-=ox if key=='x' else oy
                    g.set(key,str(value*scale))
        root.append(c)

def render(snapshot, layout=None, style='inventory'):
    if style == 'service-map':
        from .service_map import render_service_map
        return render_service_map(snapshot,layout)
    if style not in ('inventory','service-map'):raise ValueError('unknown diagram style')
    nodes,edges=graph(snapshot); doc=E.Element('mxfile',host='OCI-Lenz')
    pages=[('region','Region summary',set(nodes))]
    for v in sorted((r for r in nodes.values() if r['kind']=='vcn'),key=lambda r:r['id']):
        ids={v['id']}|{r['id'] for r in nodes.values() if r.get('vcn_id')==v['id']}
        for _ in range(len(nodes)):
            before=len(ids)
            for e in edges:
                if e['target'] in ids: ids.add(e['source'])
            if len(ids)==before: break
        ids|={e['target'] for e in edges if e['source'] in ids}
        pages.append((v['id'],v['name'],ids))
    for page,title,ids in pages:
        diagram=E.SubElement(doc,'diagram',id=page,name=title)
        root=E.SubElement(E.SubElement(diagram,'mxGraphModel',page='0',background='#ffffff'),'root')
        E.SubElement(root,'mxCell',id='0');E.SubElement(root,'mxCell',id='1',parent='0')
        parents={}; sizes={}; specs={}
        ordered=sorted(ids)
        subnets=[k for k in ordered if nodes[k]['kind']=='subnet']
        vcns=[k for k in ordered if nodes[k]['kind']=='vcn']
        children={s:[] for s in subnets}
        for k in ordered:
            r=nodes[k]; sub=r.get('subnet_id') or next(iter(r.get('subnet_ids',[])),None)
            if r['kind']=='backend_set':
                sub=next(iter(nodes.get(r.get('lb_id'),{}).get('subnet_ids',[])),None)
            if r['kind']=='compute':
                sub=next((v.get('subnet_id') for v in sorted(nodes.values(),key=lambda n:n['id']) if v.get('instance_id')==k),None)
            if sub in children and r['kind'] not in ('vcn','subnet'): children[sub].append(k)
        def setbox(k,label,x,y,w,h,parent,kind):
            parents[k]=parent; sizes[k]=(w,h); specs[k]=(label,x,y,w,h,parent,kind)
        for sub,items in children.items():
            maxx,maxy=600,230
            for j,k in enumerate(items):
                x,y=25+(j%3)*185,65+(j//3)*145
                if layout and k in layout: x,y=layout[k]['x'],layout[k]['y']
                setbox(k,nodes[k]['name'] if nodes[k]['name'].lower().startswith(nodes[k]['kind']) else nodes[k]['name']+'\n'+nodes[k]['kind'],x,y,170,125,sub,'card')
                maxx=max(maxx,x+195);maxy=max(maxy,y+150)
            sizes[sub]=(maxx,maxy)
        attached=set(k for items in children.values() for k in items)
        extras={v:[] for v in vcns}; unplaced=[]
        for k in ordered:
            if k in attached or nodes[k]['kind'] in ('vcn','subnet'): continue
            v=nodes[k].get('vcn_id')
            if v in extras: extras[v].append(k)
            else: unplaced.append(k)
        # Pack siblings into shelves; each row grows to its tallest container.
        def pack(items,columns,origin=(25,65),gap=25):
            x0,y=origin; width=0
            for start in range(0,len(items),columns):
                row=items[start:start+columns];x=x0;rowheight=0
                for k in row:
                    w,h=sizes[k];yield k,x,y
                    x+=w+gap;rowheight=max(rowheight,h)
                width=max(width,x-gap);y+=rowheight+gap
        for v in vcns:
            subs=sorted((s for s in subnets if nodes[s].get('vcn_id')==v),key=lambda s:(not nodes[s].get('public',False),s))
            width,bottom=650,65
            for sub,x,y in pack(subs,2):
                w,h=sizes[sub];r=nodes[sub]
                setbox(sub,('Public' if r.get('public') else 'Private')+' Subnet / '+r['name'],x,y,w,h,v,'subnet')
                width=max(width,x+w+25);bottom=max(bottom,y+h+25)
            for j,k in enumerate(extras[v]):
                x,y=25+(j%5)*190,bottom+45+(j//5)*145
                setbox(k,nodes[k]['name'] if nodes[k]['name'].lower().startswith(nodes[k]['kind']) else nodes[k]['name']+'\n'+nodes[k]['kind'],x,y,170,125,v,'card')
                width=max(width,x+195)
            height=bottom+(45+((len(extras[v])+4)//5)*145 if extras[v] else 0)+25
            sizes[v]=(width,height)
        # Only API compartment IDs determine compartment membership; display aliases.
        compartments={}
        for v in vcns: compartments.setdefault(nodes[v].get('compartment_id') or 'unspecified',[]).append(v)
        compkeys=[]
        for i,(comp,vs) in enumerate(sorted(compartments.items())):
            ck='layout-compartment-'+str(i);compkeys.append(ck);width,bottom=0,0
            for v,x,y in pack(vs,1):
                w,h=sizes[v];setbox(v,nodes[v]['name']+' / VCN',x,y,w,h,ck,'vcn')
                width=max(width,x+w+25);bottom=max(bottom,y+h+25)
            sizes[ck]=(max(width,700),max(bottom,150))
        region='layout-region';width,bottom=700,65
        for ck,x,y in pack(compkeys,2):
            w,h=sizes[ck];setbox(ck,'Compartment '+str(compkeys.index(ck)+1),x,y,w,h,region,'compartment')
            width=max(width,x+w+25);bottom=max(bottom,y+h+25)
        for j,k in enumerate(unplaced):
            x,y=25+(j%5)*190,bottom+45+(j//5)*145
            setbox(k,nodes[k]['name'] if nodes[k]['name'].lower().startswith(nodes[k]['kind']) else nodes[k]['name']+'\n'+nodes[k]['kind'],x,y,170,125,region,'card')
            width=max(width,x+195)
        # Subnets whose VCN is outside the scope remain explicit ungrouped containers.
        for sub in subnets:
            if sub not in specs:
                w,h=sizes[sub];setbox(sub,nodes[sub]['name']+' / Subnet',25,bottom,w,h,region,'subnet');bottom+=h+25
                width=max(width,w+50)
        height=bottom+(45+((len(unplaced)+4)//5)*145 if unplaced else 0)+25
        setbox(region,'OCI Region / '+snapshot['scope']['region'],20,85,width,height,'1','region')
        def depth(k):
            d=0
            while k in parents: d+=1;k=parents[k]
            return d
        for k in sorted(specs,key=lambda k:(depth(k),k)):
            label,x,y,w,h,parent,kind=specs[k]
            style='rounded=0;whiteSpace=wrap;html=0;fontSize=12;'
            if kind=='card':style+='fillColor=none;strokeColor=none;verticalAlign=bottom;spacingBottom=8;'
            elif kind in ('vcn','subnet'):style+='fillColor=none;strokeColor=#C66B3D;dashed=1;dashPattern=4 3;verticalAlign=top;align=left;spacing=12;fontColor=#A34E25;fontStyle=1;'
            else:style+='fillColor=#F7F6F3;strokeColor=#C8C5C0;verticalAlign=top;align=left;spacing=12;fontStyle=1;'
            c=E.SubElement(root,'mxCell',id=k,value=label,vertex='1',parent=parent,style=style)
            E.SubElement(c,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),**{'as':'geometry'})
            if kind=='card':icon(root,k,nodes[k]['kind'],58,10)
        note=E.SubElement(root,'mxCell',id='notice',value=('OCI-Lenz | Synthetic architecture' if snapshot.get('coverage') and all(c.get('source')=='synthetic' for c in snapshot['coverage']) else 'OCI-Lenz | Architecture')+'\nConfigured relationships only — not traffic reachability. Dashed links: NSG / route table. 대상 미확인 = unresolved target.',vertex='1',parent='1',style='text;whiteSpace=wrap;fontSize=14;align=left;')
        E.SubElement(note,'mxGeometry',x='20',y='10',width='1300',height='60',**{'as':'geometry'})
        def common_parent(a,b):
            ancestors=[];p=parents[a]
            while p in parents: ancestors.append(p);p=parents[p]
            ancestors.append('1');p=parents[b]
            while p not in ancestors:p=parents[p]
            return p
        for i,e in enumerate(edges):
            if e['source'] not in ids or e['target'] not in ids: continue
            c=E.SubElement(root,'mxCell',id='edge-'+str(i),source=e['source'],target=e['target'],value=edge_label(e),edge='1',parent=common_parent(e['source'],e['target']),style='edgeStyle=orthogonalEdgeStyle;rounded=0;html=0;fontSize=10;labelBackgroundColor=#F7F6F3;endArrow=block;strokeColor=#424242;')
            if e['kind'] in ('vcn_id','subnet_id','instance_id') or (e['kind']=='subnet_ids' and nodes[e['source']].get('subnet_ids',[None])[0]==e['target']):
                c.set('style',c.get('style')+'opacity=0;textOpacity=0;strokeOpacity=0;')
            elif e['kind'] in ('nsg_ids','route_table_id'):
                c.set('style',c.get('style')+'dashed=1;strokeColor=#748A96;')
            label_x,label_y={'backend':(0,-18),'lb_id':(0,18),'route':(0.45,14),'nsg_ids':(0.65,-12),'route_table_id':(0.65,12)}.get(e['kind'],(0,0))
            E.SubElement(c,'mxGeometry',x=str(label_x),y=str(label_y),relative='1',**{'as':'geometry'})
    return E.tostring(doc,encoding='unicode')

def validate(xml,snapshot):
    doc=E.fromstring(xml); nodes,edges=graph(snapshot)
    if len(doc.findall('diagram'))!=1+sum(r['kind']=='vcn' for r in nodes.values()): raise ValueError('page count')
    for page in doc.findall('diagram'):
        cells=list(page.iter('mxCell')); ids={c.get('id') for c in cells}
        if len(ids)!=len(cells):raise ValueError('duplicate cell')
        vertices={c.get('id') for c in cells if c.get('vertex')=='1' and c.get('id')!='notice' and not any(c.get('id').startswith(k+'-i-') or c.get('id')==k+'-icon' for k in nodes)}
        present_vcns=[k for k in vertices if k in nodes and nodes[k]['kind']=='vcn']
        compartment_count=len({nodes[k].get('compartment_id') or 'unspecified' for k in present_vcns})
        structural={'layout-region'}|{'layout-compartment-'+str(i) for i in range(compartment_count)}
        if doc.get('style')=='service-map':
            from .service_map import groups_for
            structural={'layout-region','layout-notes'}|{('layout-compartment-' if g.get('automatic') else 'layout-service-')+str(i) for i,g in enumerate(groups_for(snapshot)) if any(v in present_vcns for v in g['vcn_ids'])}
        resource_cells=vertices-structural
        if not resource_cells<=set(nodes): raise ValueError('invented resource')
        cellmap={c.get('id'):c for c in cells}
        rectangles={}
        for rid in vertices:
            c=cellmap[rid]; parent=c.get('parent')
            if parent=='1' or c.get('visible')=='0': continue
            g=c.find('mxGeometry');pg=cellmap[parent].find('mxGeometry')
            x,y,w,h=(float(g.get(k,0)) for k in ('x','y','width','height'))
            if x<0 or y<0 or x+w>float(pg.get('width')) or y+h>float(pg.get('height')):
                raise ValueError('resource exceeds container; split inventory or adjust layout')
            for ox,oy,ow,oh in rectangles.setdefault(parent,[]):
                if x<ox+ow and ox<x+w and y<oy+oh and oy<y+h:raise ValueError('overlapping resources')
            rectangles[parent].append((x,y,w,h))
        for c in cells:
            for attr in ('source','target','parent'):
                if c.get(attr) and c.get(attr) not in ids:raise ValueError('dangling cell reference')
        if page.get('id')=='region' and not set(nodes)<=ids:raise ValueError('missing resources')
        actual={(c.get('source'),c.get('target'),c.get('value')) for c in cells if c.get('edge')=='1'}
        expected={(e['source'],e['target'],edge_label(e)) for e in edges if e['source'] in ids and e['target'] in ids}
        if actual!=expected:raise ValueError('relationship mismatch')
    return True

def export(path, binary=None):
    binary=binary or os.environ.get('DRAWIO_BIN') or shutil.which('drawio')
    if not binary and Path('/Applications/draw.io.app/Contents/MacOS/draw.io').exists(): binary='/Applications/draw.io.app/Contents/MacOS/draw.io'
    if not binary:raise RuntimeError('Install Draw.io Desktop and set DRAWIO_BIN; Linux: use xvfb-run')
    outputs=[]
    for i,page in enumerate(E.parse(path).getroot().findall('diagram'),1):
        output=path.parent/('region.png' if i==1 else f'vcn-{i-1}.png')
        cmd=[binary,'-x','-f','png','-b','25','-p',str(i),'-o',str(output),str(path)]
        if os.name=='posix' and not os.environ.get('DISPLAY') and shutil.which('xvfb-run'): cmd=['xvfb-run','-a',*cmd]
        subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=120)
        if not output.exists() or output.read_bytes()[:8]!=b'\x89PNG\r\n\x1a\n':raise RuntimeError('PNG export failed')
        outputs.append(output)
    return outputs
