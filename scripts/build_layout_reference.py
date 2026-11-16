"""Build a customer-free visual guide using native Oracle toolkit cells."""
import sys
from pathlib import Path
import xml.etree.ElementTree as E
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from oci_lenz.draw import icon,export


def build():
    doc=E.Element('mxfile',host='OCI-Lenz')
    page=E.SubElement(doc,'diagram',id='region',name='Synthetic layout guide')
    root=E.SubElement(E.SubElement(page,'mxGraphModel',page='0',background='#ffffff'),'root')
    E.SubElement(root,'mxCell',id='0');E.SubElement(root,'mxCell',id='1',parent='0')
    def box(key,label,x,y,w,h,parent='1',container=False):
        style=('rounded=0;fillColor=#FAF9F6;strokeColor=#C66B3D;dashed=1;verticalAlign=top;align=left;spacing=14;fontStyle=1;' if container else 'text;fillColor=none;strokeColor=none;verticalAlign=bottom;spacingBottom=8;')+'whiteSpace=wrap;html=0;fontSize=13;'
        c=E.SubElement(root,'mxCell',id=key,value=label,vertex='1',parent=parent,style=style)
        E.SubElement(c,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),**{'as':'geometry'})
    box('title','SYNTHETIC OCI ARCHITECTURE | Layout reference only',30,15,1450,48)
    box('region-frame','OCI REGION / SYNTHETIC — data and topology are illustrative',20,80,1460,910,container=True)
    for i in range(2):
        p='demo-'+str(i)
        box(p+'-vcn','Example service '+('A' if i==0 else 'B')+' / VCN',30+i*710,60,680,810,'region-frame',True)
        box(p+'-public','Public subnet / entry tier',20,65,640,220,p+'-vcn',True)
        box(p+'-private','Private subnet / application tier',20,320,640,270,p+'-vcn',True)
        box(p+'-lb','Load balancer\n192.0.2.'+str(10+i),210,65,180,135,p+'-public')
        icon(root,p+'-lb','lb',63,8)
        for j in range(2):
            key=p+'-vm-'+str(j)
            box(key,'Application VM '+str(j+1)+'\n10.'+str(40+i)+'.1.'+str(10+j),90+j*280,80,180,135,p+'-private')
            icon(root,key,'compute',63,8)
            c=E.SubElement(root,'mxCell',id=p+'-edge-'+str(j),source=p+'-lb',target=key,edge='1',parent=p+'-vcn',style='edgeStyle=orthogonalEdgeStyle;endArrow=block;strokeColor=#435C64;strokeWidth=1.4;')
            E.SubElement(c,'mxGeometry',relative='1',**{'as':'geometry'})
        for j,kind in enumerate(('internet','nat','service')):
            key=p+'-'+kind
            box(key,{'internet':'Internet gateway','nat':'NAT gateway','service':'Service gateway'}[kind],40+j*205,640,180,130,p+'-vcn')
            icon(root,key,kind,63,8)
    output=Path(__file__).resolve().parents[1]/'assets/reference';output.mkdir(exist_ok=True)
    path=output/'layout-guide.drawio';path.write_text(E.tostring(doc,encoding='unicode'))
    export(path)[0].replace(output/'layout-guide.png')


if __name__=='__main__':build()
