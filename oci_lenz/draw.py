"""Draw.io skill helpers: official editable stencils, deterministic rendering, validation."""
import base64,copy,json,os,shutil,subprocess,sys,urllib.parse,zlib
from pathlib import Path
import xml.etree.ElementTree as E
from functools import lru_cache
from .diagram_model import diagram_graph as graph
from .display import resource_label,network_label
ROOT=Path(__file__).resolve().parents[1]
if not (ROOT/'assets/oci/library.xml').exists(): ROOT=Path(sys.prefix)/'share/oci-lenz'
ICONS={'compute':3,'vnic':78,'vcn':17,'subnet':17,'lb':18,'route':29,'service':31,'internet':32,'nat':33,'nsg':114,'cpe':21,'drg':30,'rpc':34,'db_system':36,'db_node':35,'virtual_circuit':210,'cross_connect':210}

def edge_label(edge):
    return edge['label'] or {'nsg_ids':'NSG','route_table_id':'Route table','lb_id':'Backend set'}.get(edge['kind'],edge['kind'])

def icon(root, rid, kind, x,y):
    if kind not in ICONS: return
    library=json.loads(E.parse(ROOT/'assets/oci/library.xml').getroot().text)
    item=library[ICONS[kind]]
    xml=urllib.parse.unquote(zlib.decompress(base64.b64decode(item['xml']),-15).decode())
    src=E.fromstring(xml)
    cells=[c for c in src.iter('mxCell') if c.get('id') not in ('0','1')]
    scale=54/max(item['w'],item['h'])
    originals={c.get('id'):c for c in cells}
    def rectangle(key):
        c=originals[key];g=c.find('mxGeometry');xx,yy,w,h=(float(g.get(f,0)) for f in ('x','y','width','height'))
        if c.get('parent') in originals:
            px,py,_,_=rectangle(c.get('parent'));xx+=px;yy+=py
        return xx,yy,w,h
    if kind in ('virtual_circuit','cross_connect'):
        # The official entry is a decorated connector: import only its SVG
        # symbol, never its decorative edge as an invented API relationship.
        glyph=copy.deepcopy(next(c for c in cells if 'shape=image;' in c.get('style','') and 'image=data:image/svg+xml,' in c.get('style','')))
        x,y,w,h=rectangle(glyph.get('id'));glyph.set('parent','1')
        g=glyph.find('mxGeometry');g.set('x',str(x));g.set('y',str(y))
        cells=[glyph];originals={glyph.get('id'):glyph};scale=54/max(w,h)
    painted={}
    for c in cells:
        styles=dict(p.split('=',1) for p in c.get('style','').split(';') if '=' in p)
        if kind in ('virtual_circuit','cross_connect') or styles.get('fillColor','none')!='none' or styles.get('strokeColor','none')!='none':painted[c.get('id')]=rectangle(c.get('id'))
    if not painted:raise ValueError('official icon contains no painted geometry')
    ox=min(r[0] for r in painted.values());oy=min(r[1] for r in painted.values())
    right=max(r[0]+r[2] for r in painted.values());bottom=max(r[1]+r[3] for r in painted.values())
    group=E.SubElement(root,'mxCell',id=rid+'-icon',value='',style='group',vertex='1',parent=rid)
    if kind in ('virtual_circuit','cross_connect'):group.set('ociOfficialIcon','Oracle OCI Library.xml:210 FastConnect SVG')
    E.SubElement(group,'mxGeometry',x=str(x),y=str(y),width=str((right-ox)*scale),height=str((bottom-oy)*scale),**{'as':'geometry'})
    for c in cells:
        # The toolkit's built-in caption is cleared, so its rectangle must not
        # leave an invisible band between the symbol and our native label.
        if c.get('value') and c.get('id') not in painted and not any(v.get('parent')==c.get('id') for v in cells):continue
        c=copy.deepcopy(c); c.set('value',''); old=c.get('id'); parent=c.get('parent','1')
        c.set('id',rid+'-i-'+old); c.set('parent',rid+'-icon' if parent=='1' else rid+'-i-'+parent)
        for g in c.iter('mxGeometry'):
            for key in ('x','y','width','height'):
                if key in g.attrib:
                    value=float(g.get(key))
                    if parent=='1' and key in ('x','y'): value-=ox if key=='x' else oy
                    g.set(key,str(value*scale))
        root.append(c)


@lru_cache(maxsize=32)
def icon_extent(kind):
    if kind not in ICONS:return 0,0
    root=E.Element('root');icon(root,'measure',kind,0,0)
    g=root.find("mxCell[@id='measure-icon']/mxGeometry")
    return float(g.get('width')),float(g.get('height'))

def render(snapshot, layout=None, style='architecture',detail_pages=False):
    if style!='architecture':raise ValueError('Only architecture rendering is supported; regenerate legacy layouts.')
    from .architecture import apply_design
    return apply_design(snapshot,layout,detail_pages=detail_pages)


def build_document(snapshot,detail_pages=False):
    """Internal native XML scaffold, with optional VCN pages; not a layout API."""
    nodes,edges=graph(snapshot); doc=E.Element('mxfile',host='OCI-Lenz')
    pages=[('region','Region summary',set(nodes))]
    if detail_pages:
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
        ids=set(ids)
        # Optional network pages include whole observed VPN families.
        for _ in range(len(nodes)):
            before=len(ids)
            for key,r in nodes.items():
                owner=r.get('ipsec_id') if r['kind']=='ipsec_tunnel' else r.get('cross_connect_group_id')
                parent_kind='ipsec' if r['kind']=='ipsec_tunnel' else 'cross_connect_group'
                if r['kind'] in ('ipsec_tunnel','cross_connect') and nodes.get(owner,{}).get('kind')==parent_kind:
                    if key in ids:ids.add(owner)
                    if owner in ids:ids.add(key)
            ids|={e['target'] for e in edges if e['kind']=='cpe_id' and e['source'] in ids and nodes[e['source']]['kind']=='ipsec'}
            if len(ids)==before:break
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
                sub=next((v.get('subnet_id') for v in sorted(nodes.values(),key=lambda n:(n.get('is_primary') is not True,n['id'])) if v.get('instance_id')==k),None)
            if r['kind']=='db_node':
                vnic=nodes.get(r.get('vnic_id'),{})
                sub=vnic.get('subnet_id') or nodes.get(r.get('db_system_id'),{}).get('subnet_id')
            if sub in children and r['kind'] not in ('vcn','subnet'): children[sub].append(k)
        def setbox(k,label,x,y,w,h,parent,kind):
            parents[k]=parent; sizes[k]=(w,h); specs[k]=(label,x,y,w,h,parent,kind)
        cardheight=max([125]+[65+14*len(resource_label(r,width=30).splitlines()) for r in nodes.values()])
        rowstep=cardheight+20
        for sub,items in children.items():
            maxx,maxy=600,230
            for j,k in enumerate(items):
                x,y=25+(j%3)*185,65+(j//3)*rowstep
                setbox(k,resource_label(nodes[k],width=30),x,y,170,cardheight,sub,'card')
                maxx=max(maxx,x+195);maxy=max(maxy,y+rowstep)
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
                setbox(sub,network_label(r,('Public' if r.get('public') else 'Private')+' Subnet / '),x,y,w,h,v,'subnet')
                width=max(width,x+w+25);bottom=max(bottom,y+h+25)
            for j,k in enumerate(extras[v]):
                x,y=25+(j%5)*190,bottom+45+(j//5)*rowstep
                setbox(k,resource_label(nodes[k],width=30),x,y,170,cardheight,v,'card')
                width=max(width,x+195)
            height=bottom+(45+((len(extras[v])+4)//5)*rowstep if extras[v] else 0)+25
            sizes[v]=(width,height)
        # Only API compartment IDs determine compartment membership; display aliases.
        compartments={}
        for v in vcns: compartments.setdefault(nodes[v].get('compartment_id') or 'unspecified',[]).append(v)
        compkeys=[]
        for i,(comp,vs) in enumerate(sorted(compartments.items())):
            ck='layout-compartment-'+str(i);compkeys.append(ck);width,bottom=0,0
            for v,x,y in pack(vs,1):
                w,h=sizes[v];setbox(v,network_label(nodes[v],'VCN / '),x,y,w,h,ck,'vcn')
                width=max(width,x+w+25);bottom=max(bottom,y+h+25)
            sizes[ck]=(max(width,700),max(bottom,150))
        region='layout-region';width,bottom=700,65
        for ck,x,y in pack(compkeys,2):
            comp=sorted(compartments)[compkeys.index(ck)]
            known=snapshot['scope'].get('compartment_names',{}).get(comp)
            label=('Compartment / '+known) if known and not snapshot.get('presentation',{}).get('redacted') else 'Compartment '+str(compkeys.index(ck)+1)
            w,h=sizes[ck];setbox(ck,label,x,y,w,h,region,'compartment')
            width=max(width,x+w+25);bottom=max(bottom,y+h+25)
        for j,k in enumerate(unplaced):
            x,y=25+(j%5)*190,bottom+45+(j//5)*rowstep
            setbox(k,resource_label(nodes[k],width=30),x,y,170,cardheight,region,'card')
            width=max(width,x+195)
        # Subnets whose VCN is outside the scope remain explicit ungrouped containers.
        for sub in subnets:
            if sub not in specs:
                w,h=sizes[sub];setbox(sub,nodes[sub]['name']+' / Subnet',25,bottom,w,h,region,'subnet');bottom+=h+25
                width=max(width,w+50)
        height=bottom+(45+((len(unplaced)+4)//5)*rowstep if unplaced else 0)+25
        setbox(region,'OCI Region / '+snapshot['scope']['region'],20,85,width,height,'1','region')
        for key in sorted(k for k in ids if nodes[k]['kind'] in ('ipsec','cross_connect_group')):
            _,x,y,_,_,parent,_=specs[key];kind=nodes[key]['kind']
            child_kind,field,prefix=('ipsec_tunnel','ipsec_id','IPSec VPN / ') if kind=='ipsec' else ('cross_connect','cross_connect_group_id','FastConnect group / ')
            members=sorted(k for k in ids if nodes[k]['kind']==child_kind and nodes[k].get(field)==key)
            for i,child in enumerate(members):
                setbox(child,resource_label(nodes[child],width=30),24,64+i*rowstep,170,cardheight,key,'card')
            setbox(key,network_label(nodes[key],prefix),x,y,220,max(64,64+len(members)*rowstep),parent,kind)
        def depth(k):
            d=0
            while k in parents: d+=1;k=parents[k]
            return d
        for k in sorted(specs,key=lambda k:(depth(k),k)):
            label,x,y,w,h,parent,kind=specs[k]
            style='rounded=0;whiteSpace=wrap;html=0;fontSize=12;'
            if kind=='card':style+='fillColor=none;strokeColor=none;verticalAlign=bottom;spacingBottom=8;'
            elif kind in ('ipsec','cross_connect_group'):style+='rounded=1;arcSize=8;fillColor=#F3F8FA;strokeColor=#8FAEBB;verticalAlign=top;align=left;spacing=12;fontColor=#213A44;fontStyle=1;'
            elif kind in ('vcn','subnet'):style+='fillColor=none;strokeColor=#C66B3D;dashed=1;dashPattern=4 3;verticalAlign=top;align=left;spacing=12;fontColor=#A34E25;fontStyle=1;'
            else:style+='fillColor=#F7F6F3;strokeColor=#C8C5C0;verticalAlign=top;align=left;spacing=12;fontStyle=1;'
            c=E.SubElement(root,'mxCell',id=k,value=label,vertex='1',parent=parent,style=style)
            E.SubElement(c,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),**{'as':'geometry'})
            if kind=='ipsec':c.set('ociVPNContainer','1')
            if kind=='cross_connect_group':c.set('ociCrossConnectGroup','1')
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
            if e.get('attachment_ids'):
                c.set('ociAttachmentIds',json.dumps(e['attachment_ids'],separators=(',',':')))
                c.set('ociEvidence',e['evidence'])
            if e['kind'] in ('vcn_id','subnet_id','instance_id') or (e['kind']=='subnet_ids' and nodes[e['source']].get('subnet_ids',[None])[0]==e['target']):
                c.set('style',c.get('style')+'opacity=0;textOpacity=0;strokeOpacity=0;')
            elif e['kind'] in ('nsg_ids','route_table_id'):
                c.set('style',c.get('style')+'dashed=1;strokeColor=#748A96;')
            label_x,label_y={'backend':(0,-18),'lb_id':(0,18),'route':(0.45,14),'nsg_ids':(0.65,-12),'route_table_id':(0.65,12)}.get(e['kind'],(0,0))
            E.SubElement(c,'mxGeometry',x=str(label_x),y=str(label_y),relative='1',**{'as':'geometry'})
    return E.tostring(doc,encoding='unicode')

def validate(xml,snapshot):
    doc=E.fromstring(xml); nodes,edges=graph(snapshot)
    if doc.get('style')=='architecture':
        from .architecture import validate_architecture
        return validate_architecture(xml,snapshot)
    if doc.get('pageMode','split') not in ('single','split'):raise ValueError('page mode')
    page_count=1 if doc.get('pageMode')=='single' else 1+sum(r['kind']=='vcn' for r in nodes.values())
    if len(doc.findall('diagram'))!=page_count: raise ValueError('page count')
    for page in doc.findall('diagram'):
        cells=list(page.iter('mxCell')); ids={c.get('id') for c in cells}
        if len(ids)!=len(cells):raise ValueError('duplicate cell')
        vertices={c.get('id') for c in cells if c.get('vertex')=='1' and c.get('id')!='notice' and not any(c.get('id').startswith(k+'-i-') or c.get('id')==k+'-icon' for k in nodes)}
        present_vcns=[k for k in vertices if k in nodes and nodes[k]['kind']=='vcn']
        compartment_count=len({nodes[k].get('compartment_id') or 'unspecified' for k in present_vcns})
        structural={'layout-region'}|{'layout-compartment-'+str(i) for i in range(compartment_count)}
        structural|={'layout-service-'+str(i) for i in range(len(snapshot.get('presentation',{}).get('groups',[])))}
        resource_cells=vertices-structural
        if not resource_cells<=set(nodes): raise ValueError('invented resource')
        cellmap={c.get('id'):c for c in cells}
        for rid in nodes:
            native=cellmap.get(rid)
            if native is not None and nodes[rid]['kind'] in ('drg','cpe') and native.get('parent')!='layout-region':
                raise ValueError('DRG/CPE must remain outside VPN containers')
            if native is not None and nodes[rid]['kind']=='cross_connect':
                owner=nodes[rid].get('cross_connect_group_id')
                expected=owner if owner in ids and nodes.get(owner,{}).get('kind')=='cross_connect_group' else 'layout-region'
                if native.get('parent')!=expected:raise ValueError('CrossConnect parent mismatch')
            if native is not None and nodes[rid]['kind']=='cross_connect_group' and (native.get('ociCrossConnectGroup')!='1' or native.get('parent')!='layout-region'):
                raise ValueError('CrossConnect group mismatch')
            if native is not None and nodes[rid]['kind']=='ipsec_tunnel':
                owner=nodes[rid].get('ipsec_id')
                expected=owner if owner in ids and nodes.get(owner,{}).get('kind')=='ipsec' else 'layout-region'
                if native.get('parent')!=expected:raise ValueError('IPSec tunnel parent mismatch')
            if native is not None and nodes[rid]['kind']=='ipsec' and (native.get('ociVPNContainer')!='1' or native.get('parent')!='layout-region'):
                raise ValueError('IPSec container mismatch')
            if native is not None and 'ociNativeLabel=1;' in native.get('style',''):
                from .typography import card_metrics
                options=dict(p.split('=',1) for p in native.get('style','').split(';') if '=' in p)
                g=native.find('mxGeometry');w,h=float(g.get('width')),float(g.get('height'))
                metrics=card_metrics(nodes[rid],w)
                height=metrics['name_height']+(2+metrics['detail_height'] if metrics['details'] else 0)
                top=float(options.get('spacingTop',0))
                if top<0 or top+height>h:raise ValueError('native label exceeds card')
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
        for c in cells:
            original=c.get('ociEvidenceTarget')
            if original is not None and (original not in ids or nodes.get(original,{}).get('kind')!='db_node' or nodes[original].get('db_system_id')!=c.get('target') or nodes.get(c.get('source'),{}).get('kind')!='backend_set'):
                raise ValueError('invalid DB node display projection')
        for i,e in enumerate(edges):
            c=cellmap.get('edge-'+str(i))
            if c is None:continue
            if e.get('attachment_ids') or c.get('ociAttachmentIds') is not None:
                if c.get('source')!=e['source'] or c.get('target')!=e['target'] or c.get('ociAttachmentIds')!=json.dumps(e.get('attachment_ids',[]),separators=(',',':')) or c.get('ociEvidence')!=e['evidence']:
                    raise ValueError('attachment projection evidence mismatch')
        expected_ids={'edge-'+str(i) for i,e in enumerate(edges) if e['source'] in ids and e['target'] in ids}
        if {c.get('id') for c in cells if c.get('edge')=='1'}!=expected_ids:raise ValueError('relationship IDs mismatch')
        actual={(c.get('source'),c.get('ociEvidenceTarget',c.get('target')),c.get('value')) for c in cells if c.get('edge')=='1'}
        expected={(e['source'],e['target'],edge_label(e)) for e in edges if e['source'] in ids and e['target'] in ids}
        if actual!=expected:raise ValueError('relationship mismatch')
    return True

def find_drawio(binary=None):
    configured=binary or os.environ.get('DRAWIO_BIN')
    if configured:
        candidate=Path(configured).expanduser()
        if candidate.is_file() and os.access(candidate,os.X_OK):return str(candidate)
        return shutil.which(str(configured))
    located=shutil.which('drawio')
    if located:return located
    if sys.platform=='darwin':
        for candidate in (Path('/Applications/draw.io.app/Contents/MacOS/draw.io'),Path.home()/'Applications/draw.io.app/Contents/MacOS/draw.io'):
            if candidate.is_file() and os.access(candidate,os.X_OK):return str(candidate)
    return None


def export(path, binary=None):
    binary=find_drawio(binary)
    if not binary:raise RuntimeError('Install Draw.io Desktop and set DRAWIO_BIN; Linux: use xvfb-run')
    outputs=[]
    for i,page in enumerate(E.parse(path).getroot().findall('diagram'),1):
        output=path.parent/('information-index.png' if page.get('id')=='information-index' else ('architecture.png' if i==1 else f'vcn-{i-1}.png'))
        cmd=[binary,'-x','-f','png','-b','25','-p',str(i),'-o',str(output),str(path)]
        if os.name=='posix' and not os.environ.get('DISPLAY') and shutil.which('xvfb-run'): cmd=['xvfb-run','-a',*cmd]
        subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=120)
        if not output.exists() or output.read_bytes()[:8]!=b'\x89PNG\r\n\x1a\n':raise RuntimeError('PNG export failed')
        outputs.append(output)
    return outputs
