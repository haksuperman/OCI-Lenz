"""Synthetic regressions for connectors crossing network titles."""
import unittest
import xml.etree.ElementTree as E
from oci_lenz.routing import route_native_edges,intersects


class TitleRoutingTests(unittest.TestCase):
    def diagram(self,fanout=False):
        root=E.Element('root')
        def cell(key,x,y,w,h,parent='1',value='',style=''):
            c=E.SubElement(root,'mxCell',id=key,parent=parent,vertex='1',value=value,style=style)
            E.SubElement(c,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h))
        cell('network',20,180,500,260,value='Private Subnet / Synthetic\n가상 네트워크 제목',
             style='verticalAlign=top;align=left;spacing=12;fontSize=12;')
        cell('backend',60,20,100,80)
        cell('left',40,120,100,80,parent='network')
        nodes={'network':{'kind':'subnet'},'backend':{'kind':'backend_set'},'left':{'kind':'compute'}}
        targets=['left']
        if fanout:
            cell('right',300,120,100,80,parent='network');nodes['right']={'kind':'compute'};targets.append('right')
        for target in targets:
            c=E.SubElement(root,'mxCell',id='e-'+target,parent='1',source='backend',target=target,edge='1',style='endArrow=block;')
            E.SubElement(c,'mxGeometry',relative='1')
        return root,nodes

    def paths(self,root):
        cells={c.get('id'):c for c in root}
        def rect(key):
            c=cells[key];g=c.find('mxGeometry');x,y,w,h=[float(g.get(f,0)) for f in ('x','y','width','height')]
            if c.get('parent') in cells:
                px,py,_,_=rect(c.get('parent'));x+=px;y+=py
            return x,y,w,h
        paths=[]
        for c in root.findall("mxCell[@edge='1']"):
            style=dict(p.split('=',1) for p in c.get('style','').split(';') if '=' in p)
            def port(key,prefix):
                x,y,w,h=rect(key);return x+w*float(style[prefix+'X']),y+h*float(style[prefix+'Y'])
            paths.append([port(c.get('source'),'exit'),*[(float(p.get('x')),float(p.get('y'))) for p in c.findall('mxGeometry/Array/mxPoint')],port(c.get('target'),'entry')])
        return paths

    def test_incoming_edge_avoids_each_line_of_a_network_title(self):
        root,nodes=self.diagram();before=E.tostring(root.find("mxCell[@id='network']"))
        route_native_edges(root,nodes)
        titles=[(32,192,180,16),(32,208,120,16)]
        for path in self.paths(root):
            for a,b in zip(path,path[1:]):
                self.assertTrue(a[0]==b[0] or a[1]==b[1])
                self.assertFalse(any(intersects(a,b,title) for title in titles))
        self.assertEqual(E.tostring(root.find("mxCell[@id='network']")),before)
        self.assertEqual(root.find("mxCell[@edge='1']").get('target'),'left')

    def test_backend_fanout_avoids_titles_without_dropping_evidence(self):
        root,nodes=self.diagram(fanout=True);route_native_edges(root,nodes)
        for path in self.paths(root):
            for a,b in zip(path,path[1:]):
                self.assertFalse(intersects(a,b,(32,192,180,32)))
        self.assertEqual(len(self.paths(root)),2)
        again,nodes=self.diagram(fanout=True);route_native_edges(again,nodes)
        self.assertEqual(E.tostring(root),E.tostring(again))

    def test_title_clearance_does_not_block_a_direct_container_endpoint(self):
        root,nodes=self.diagram();edge=root.find("mxCell[@edge='1']");edge.set('target','network')
        self.assertEqual(route_native_edges(root,nodes),1)
        self.assertEqual(edge.get('target'),'network')
