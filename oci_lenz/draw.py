"""Draw.io skill helpers: official editable stencils, deterministic rendering, validation."""
import base64,copy,json,os,shutil,subprocess,sys,urllib.parse,zlib
from pathlib import Path
import xml.etree.ElementTree as E
from .model import graph
ROOT=Path(__file__).resolve().parents[1]
if not (ROOT/'assets/oci/library.xml').exists(): ROOT=Path(sys.prefix)/'share/oci-lenz'
ICONS={'compute':3,'vnic':78,'vcn':17,'subnet':17,'lb':18,'backend_set':18,'route':29,'service':31,'internet':32,'nat':33,'nsg':114}

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

def render(snapshot, layout=None):
    nodes,edges=graph(snapshot); doc=E.Element('mxfile',host='OCI-Lenz')
    pages=[('region','Region summary',set(nodes))]
    for v in sorted((r for r in nodes.values() if r['kind']=='vcn'),key=lambda r:r['id']):
        ids={v['id']}|{r['id'] for r in nodes.values() if r.get('vcn_id')==v['id']}
        for _ in range(4):
            for e in edges:
                if e['target'] in ids: ids.add(e['source'])
        ids|={e['target'] for e in edges if e['source'] in ids}
        pages.append((v['id'],v['name'],ids))
    for page,title,ids in pages:
        diagram=E.SubElement(doc,'diagram',id=page,name=title)
        root=E.SubElement(E.SubElement(diagram,'mxGraphModel',page='0',background='#ffffff'),'root')
        E.SubElement(root,'mxCell',id='0');E.SubElement(root,'mxCell',id='1',parent='0')
        ordered=sorted(ids,key=lambda k:({'vcn':0,'subnet':1}.get(nodes[k]['kind'],2),nodes[k]['kind'],k))
        positions={}
        def box(rid,label,x,y,w,h,parent='1',container=False):
            style='rounded=1;whiteSpace=wrap;html=0;'+('fillColor=#F4F7FA;strokeColor=#8798A5;verticalAlign=top;align=left;spacing=8;' if container else 'fillColor=#ffffff;strokeColor=#B0BEC5;verticalAlign=bottom;spacingBottom=8;fontSize=12;')
            c=E.SubElement(root,'mxCell',id=rid,value=label,vertex='1',parent=parent,style=style)
            E.SubElement(c,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),**{'as':'geometry'})
        subnets=[k for k in ordered if nodes[k]['kind']=='subnet']
        vcns=[k for k in ordered if nodes[k]['kind']=='vcn']
        children={s:[] for s in subnets}
        for k in ordered:
            r=nodes[k]; sub=r.get('subnet_id') or next(iter(r.get('subnet_ids',[])),None)
            if r['kind']=='backend_set':
                lb=nodes.get(r.get('lb_id'),{}); sub=next(iter(lb.get('subnet_ids',[])),None)
            if r['kind']=='compute': sub=next((v.get('subnet_id') for v in nodes.values() if v.get('instance_id')==k),None)
            if sub in children: children[sub].append(k)
        for i,k in enumerate(vcns): box(k,nodes[k]['name']+' / VCN',20,70+i*850,1320,810,container=True)
        for i,k in enumerate(subnets):
            parent=nodes[k].get('vcn_id','1'); parent=parent if parent in ids else '1'
            siblings=[s for s in subnets if nodes[s].get('vcn_id')==parent]; j=siblings.index(k) if k in siblings else i
            box(k,('Public' if nodes[k].get('public') else 'Private')+' Subnet / '+nodes[k]['name'],30+(j%2)*630,70+(j//2)*350,600,320,parent,True)
        other=0
        for k in ordered:
            r=nodes[k]
            if r['kind'] in ('vcn','subnet'): continue
            parent=next((s for s,items in children.items() if k in items),None)
            if parent: j=children[parent].index(k); x,y=20+(j%3)*185,60+(j//3)*145
            else:
                parent=r.get('vcn_id');parent=parent if parent in ids else '1'
                x,y=35+(other%6)*205,470 if parent!='1' else 930+(other//6)*160; other+=1
            w,h=170,125
            if layout and k in layout and parent in children:
                # Layout is positional only; it cannot add/remove graph elements.
                x,y=layout[k]['x'],layout[k]['y']
            positions[k]={'x':x,'y':y}
            box(k,r['name']+'\n'+r['kind'],x,y,w,h,parent)
            icon(root,k,r['kind'],58,10)
        note=E.SubElement(root,'mxCell',id='notice',value='Configured relationships only — not traffic reachability. 대상 미확인 = unresolved target.',vertex='1',parent='1',style='text;whiteSpace=wrap;fontSize=14;')
        E.SubElement(note,'mxGeometry',x='20',y='10',width='1200',height='45',**{'as':'geometry'})
        for i,e in enumerate(edges):
            if e['source'] not in ids or e['target'] not in ids: continue
            c=E.SubElement(root,'mxCell',id='edge-'+str(i),source=e['source'],target=e['target'],value=e['label'] or e['kind'],edge='1',parent='1',style='edgeStyle=orthogonalEdgeStyle;rounded=0;html=0;fontSize=10;labelBackgroundColor=#ffffff;endArrow=block;')
            if e['kind'] in ('vcn_id','subnet_id','instance_id','lb_id') or (e['kind']=='subnet_ids' and nodes[e['source']].get('subnet_ids',[None])[0]==e['target']):
                c.set('style',c.get('style')+'opacity=0;textOpacity=0;strokeOpacity=0;')
            elif e['kind'] in ('nsg_ids','route_table_id'):
                c.set('style',c.get('style')+'dashed=1;strokeColor=#748A96;')
            E.SubElement(c,'mxGeometry',relative='1',**{'as':'geometry'})
    return E.tostring(doc,encoding='unicode')

def validate(xml,snapshot):
    doc=E.fromstring(xml); nodes,edges=graph(snapshot)
    if len(doc.findall('diagram'))!=1+sum(r['kind']=='vcn' for r in nodes.values()): raise ValueError('page count')
    for page in doc.findall('diagram'):
        cells=list(page.iter('mxCell')); ids={c.get('id') for c in cells}
        if len(ids)!=len(cells):raise ValueError('duplicate cell')
        resource_cells={c.get('id') for c in cells if c.get('vertex')=='1' and c.get('id')!='notice' and not any(c.get('id').startswith(k+'-i-') or c.get('id')==k+'-icon' for k in nodes)}
        if not resource_cells<=set(nodes): raise ValueError('invented resource')
        cellmap={c.get('id'):c for c in cells}
        rectangles={}
        for rid in resource_cells:
            c=cellmap[rid]; parent=c.get('parent')
            if parent=='1': continue
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
        if page.get('id')=='region':
            if not set(nodes)<=ids:raise ValueError('missing resources')
            actual={(c.get('source'),c.get('target'),c.get('value')) for c in cells if c.get('edge')=='1'}
            expected={(e['source'],e['target'],e['label'] or e['kind']) for e in edges}
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
