import unittest
import xml.etree.ElementTree as E
from oci_lenz.routing import route,intersects,route_native_edges


class RoutingTests(unittest.TestCase):
    def test_backend_edges_share_a_trunk_without_merging_relationships(self):
        root=E.Element('root')
        def card(key,x,y,w,h):
            c=E.SubElement(root,'mxCell',id=key,vertex='1',parent='1')
            E.SubElement(c,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h))
        card('backend',160,20,100,80)
        card('left',20,300,100,80);card('right',300,420,100,80)
        for key,target in (('e1','left'),('e2','right')):
            c=E.SubElement(root,'mxCell',id=key,source='backend',target=target,edge='1',parent='1',style='endArrow=block;')
            E.SubElement(c,'mxGeometry',relative='1')
        nodes={'backend':{'kind':'backend_set'},'left':{'kind':'compute'},'right':{'kind':'compute'}}
        route_native_edges(root,nodes)
        edges=root.findall("mxCell[@edge='1']")
        self.assertEqual(len(edges),2)
        self.assertEqual({e.get('target') for e in edges},{'left','right'})
        points=[[(float(p.get('x')),float(p.get('y'))) for p in e.find('mxGeometry/Array')] for e in edges]
        self.assertEqual(points[0][0],points[1][0])
        self.assertEqual(points[0][0][0],210)
        self.assertGreater(points[0][0][1],100)
        self.assertEqual(points[0][-1],(70,288))
        self.assertEqual(points[1][-1],(350,408))

    def test_orthogonal_path_avoids_intervening_resource(self):
        obstacle=(80,20,70,100)
        points=route((20,60),(220,60),[obstacle])
        self.assertTrue(points)
        self.assertEqual(points[0],(20,60));self.assertEqual(points[-1],(220,60))
        for a,b in zip(points,points[1:]):
            self.assertTrue(a[0]==b[0] or a[1]==b[1])
            self.assertFalse(intersects(a,b,obstacle))

    def test_unobstructed_route_is_deterministic_and_straight(self):
        expected=[(20,20),(200,20)]
        self.assertEqual(route((20,20),(200,20),[]),expected)
        self.assertEqual(route((20,20),(200,20),[]),expected)
