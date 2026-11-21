"""Readable proper crossings are distinct from ambiguous contacts and overlaps."""
import copy
import unittest
import xml.etree.ElementTree as E
from oci_lenz.routing import route,route_native_edges,native_paths
from oci_lenz.line_jumps import crossing_report


class LineJumpTests(unittest.TestCase):
    def paths(self):
        return [{'source':'a','target':'b','points':[(0,100),(200,100)],'network':True,'jump_style':'arc'},
                {'source':'c','target':'d','points':[(100,0),(100,200)],'network':True,'jump_style':'arc'}]

    def test_clear_crossing_uses_a_short_straight_route_instead_of_a_long_detour(self):
        wire=[((100,0),(100,200))]
        self.assertEqual(route((0,100),(200,100),[],wire),[(0,100),(200,100)])

    def test_straight_shortcut_cannot_bypass_near_endpoint_contact_guard(self):
        from oci_lenz.routing import contact_conflict
        self.assertFalse(contact_conflict((0,100),(200,100),(100,0),(100,200)))
        self.assertTrue(contact_conflict((0,100),(200,100),(100,95),(100,200)))
        self.assertTrue(contact_conflict((0,100),(200,100),(50,100),(150,100)))
        self.assertNotEqual(route((0,100),(200,100),[],[((100,95),(100,200))]),[(0,100),(200,100)])

    def test_safe_proper_crossing_is_bridged_but_still_counted(self):
        paths=self.paths();before=copy.deepcopy(paths)
        self.assertEqual(crossing_report(paths,{}),{'bridged_crossings':1,'unbridged_crossings':0})
        self.assertEqual(paths,before)

    def test_style_alone_never_hides_endpoint_contacts_bends_or_obstacles(self):
        paths=self.paths();paths[1]['jump_style']='none'
        self.assertEqual(crossing_report(paths,{})['unbridged_crossings'],1)
        paths=self.paths();paths[1]['points']=[(100,100),(100,200)]
        self.assertEqual(crossing_report(paths,{})['bridged_crossings'],0)
        paths=self.paths();paths[1]['points']=[(100,0),(100,100),(180,100)]
        self.assertEqual(crossing_report(paths,{})['bridged_crossings'],0)
        self.assertEqual(crossing_report(self.paths(),{},[(98,98,4,4)])['bridged_crossings'],0)

    def test_shared_backend_prefix_does_not_get_a_fake_bridge(self):
        paths=[dict(source='s',target='a',points=[(0,0),(0,50),(100,50),(100,100)],network=True,jump_style='arc'),
               dict(source='s',target='b',points=[(0,0),(0,50),(60,50),(60,100)],network=True,jump_style='arc')]
        nodes={'s':{'kind':'backend_set'},'a':{'kind':'compute'},'b':{'kind':'compute'}}
        self.assertEqual(crossing_report(paths,nodes),{'bridged_crossings':0,'unbridged_crossings':0})

    def test_crowded_crossovers_are_not_claimed_safe(self):
        paths=self.paths()
        paths.append(dict(source='e',target='f',points=[(0,105),(200,105)],network=True,jump_style='arc'))
        self.assertEqual(crossing_report(paths,{}),{'bridged_crossings':0,'unbridged_crossings':2})

    def test_native_styles_are_editable_and_reversed_lb_ownership_survives_replay(self):
        root=E.Element('root');nodes={}
        for key,kind,x,y in [('lb','lb',180,20),('s','backend_set',180,250),('vm','compute',180,450)]:
            nodes[key]={'kind':kind}
            c=E.SubElement(root,'mxCell',id=key,vertex='1',parent='1')
            E.SubElement(c,'mxGeometry',x=str(x),y=str(y),width='100',height='60')
        for key,source,target,style in [('owner','s','lb','startArrow=block;endArrow=none;'),('backend','s','vm','endArrow=block;')]:
            c=E.SubElement(root,'mxCell',id=key,edge='1',source=source,target=target,parent='1',style=style)
            E.SubElement(c,'mxGeometry',relative='1')
        original=copy.deepcopy(root);route_native_edges(root,nodes);route_native_edges(original,nodes)
        self.assertEqual(E.tostring(root),E.tostring(original))
        owner=root.find("mxCell[@id='owner']")
        self.assertEqual((owner.get('source'),owner.get('target')),('s','lb'))
        self.assertIn('startArrow=open;',owner.get('style'))
        for c in root.findall("mxCell[@edge='1']"):
            self.assertIn('jumpStyle=arc;',c.get('style'));self.assertIn('jumpSize=8;',c.get('style'))
        for p in native_paths(root,nodes):
            self.assertTrue(all(a[0]==b[0] or a[1]==b[1] for a,b in zip(p['points'],p['points'][1:])))

    def test_one_drg_can_use_a_clean_vertical_bus_for_parallel_tunnels(self):
        from oci_lenz.quality import edge_conflicts
        root=E.Element('root');nodes={'drg':{'kind':'drg'}}
        positions={'drg':(80,180),**{'t'+str(i):(450,40+i*120) for i in range(4)}}
        for key,(x,y) in positions.items():
            nodes.setdefault(key,{'kind':'ipsec_tunnel'})
            c=E.SubElement(root,'mxCell',id=key,vertex='1',parent='1')
            E.SubElement(c,'mxGeometry',x=str(x),y=str(y),width='100',height='60')
        for i in range(4):
            c=E.SubElement(root,'mxCell',id='e'+str(i),source='drg',target='t'+str(i),edge='1',parent='1',style='endArrow=block;')
            E.SubElement(c,'mxGeometry',relative='1')
        route_native_edges(root,nodes);paths=native_paths(root,nodes)
        self.assertEqual(edge_conflicts(paths,nodes),{'edge_crossings':0,'edge_overlap_length':0})
        for p in paths:
            ys=[y for x,y in p['points']]
            self.assertTrue(ys==sorted(ys) or ys==sorted(ys,reverse=True))
