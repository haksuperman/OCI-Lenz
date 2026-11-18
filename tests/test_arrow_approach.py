"""Arrowheads enter a face normally; side-by-side VPN links enter from the side."""
import unittest
import xml.etree.ElementTree as E
from oci_lenz.routing import route_native_edges,native_paths
from oci_lenz.model import sample
from oci_lenz.display import prepare_display
from oci_lenz.draw import render


class ArrowApproachTests(unittest.TestCase):
    def route(self,positions,kinds):
        root=E.Element('root')
        for key,(x,y,w,h) in positions.items():
            c=E.SubElement(root,'mxCell',id=key,parent='1',vertex='1')
            E.SubElement(c,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h))
        c=E.SubElement(root,'mxCell',id='edge',source='source',target='target',edge='1',parent='1',style='endArrow=block;')
        E.SubElement(c,'mxGeometry',relative='1')
        nodes={k:{'kind':kind} for k,kind in kinds.items()}
        route_native_edges(root,nodes)
        return root,native_paths(root,nodes)[0]['points']

    def test_horizontal_tunnel_arrow_enters_left_face_from_left_not_from_above(self):
        root,points=self.route({'source':(20,140,100,80),'target':(300,200,170,44)},
                               {'source':'drg','target':'ipsec_tunnel'})
        previous,end=next(p for p in reversed(points[:-1]) if p!=points[-1]),points[-1]
        self.assertAlmostEqual(end[0],300)
        self.assertAlmostEqual(previous[1],end[1])
        self.assertLess(previous[0],end[0])
        self.assertEqual((root[-1].get('source'),root[-1].get('target')),('source','target'))

    def test_wide_tunnel_right_of_drg_does_not_choose_top_face_by_aspect_ratio(self):
        _,points=self.route({'source':(20,20,100,80),'target':(300,160,170,44)},
                             {'source':'drg','target':'ipsec_tunnel'})
        self.assertAlmostEqual(points[-1][0],300)
        self.assertAlmostEqual(points[-1][1],182)

    def test_vertical_arrow_enters_top_face_from_above(self):
        _,points=self.route({'source':(20,20,100,80),'target':(180,300,170,44)},
                             {'source':'backend_set','target':'compute'})
        previous,end=next(p for p in reversed(points[:-1]) if p!=points[-1]),points[-1]
        self.assertAlmostEqual(previous[0],end[0]);self.assertLess(previous[1],end[1])

    def test_synthetic_lb_supplies_an_observed_documentation_address(self):
        s=sample();lb=next(r for r in s['resources'] if r['kind']=='lb')
        self.assertEqual(lb['ip_addresses'],[{'ip_address':'192.0.2.20','is_public':True}])
        doc=E.fromstring(render(prepare_display(s)))
        label=doc.find("diagram/mxGraphModel/root/mxCell[@id='lb']").get('value')
        self.assertIn('192.0.2.20',label)
