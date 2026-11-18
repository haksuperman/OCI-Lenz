"""Common connection rules apply to native anchors, not service names or PNGs."""
import copy
import unittest
import xml.etree.ElementTree as E
from oci_lenz.connector_rules import guides,alignment_issues
from oci_lenz.routing import route_native_edges,native_paths


class ConnectorRuleTests(unittest.TestCase):
    def scene(self):
        return {'items':{'n0':{'container':False,'kind':'virtual_circuit'},
                         'n1':{'container':True,'kind':'cross_connect_group'},
                         'n2':{'container':False,'kind':'cross_connect','parent':'n1'}},
                'edges':[{'id':'e0','source':'n0','target':'n1','kind':'cross_connect_mapping'}]}

    def test_single_content_container_uses_its_child_glyph_axis_not_box_midpoint(self):
        request=self.scene();offsets={'n0':26,'n2':26}
        rules=guides(request,offsets)
        self.assertEqual(len(rules),1)
        good={'placements':[{'id':'n0','x':0,'y':100,'width':170,'height':120},
                            {'id':'n1','x':250,'y':40,'width':220,'height':180},
                            {'id':'n2','x':270,'y':100,'width':170,'height':80}]}
        self.assertEqual(alignment_issues(rules,good),[])
        bad=copy.deepcopy(good);bad['placements'][0]['y']-=32
        self.assertTrue(alignment_issues(rules,bad))

    def test_same_rule_applies_to_other_api_owned_containers(self):
        request=self.scene()
        request['items']['n0']['kind']='cpe';request['items']['n1']['kind']='ipsec'
        request['items']['n2']['kind']='ipsec_tunnel';request['edges'][0]['kind']='cpe_id'
        self.assertEqual(len(guides(request,{'n0':24,'n2':None})),1)

    def test_multiple_children_or_mapping_targets_do_not_imply_a_single_child_link(self):
        request=self.scene();request['items']['n3']={**request['items']['n2']}
        self.assertEqual(guides(request,{'n0':26,'n2':26,'n3':26}),[])
        request=self.scene();request['items']['n3']={**request['items']['n1']}
        request['edges'].append({'id':'e1','source':'n0','target':'n3','kind':'cross_connect_mapping'})
        self.assertEqual(guides(request,{'n0':26,'n2':26}),[])

    def native(self,kind='cross_connect_group',blocked=False):
        root=E.Element('root')
        for key,x,y,w,h,style in [('left',20,100,100,60,''),
                ('box',300,40,240,200,'verticalAlign=top;align=left;spacing=12;fontSize=12;')]:
            c=E.SubElement(root,'mxCell',id=key,vertex='1',parent='1',value='Container' if key=='box' else '',style=style)
            E.SubElement(c,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h))
        if blocked:
            c=E.SubElement(root,'mxCell',id='obstacle',vertex='1',parent='1')
            E.SubElement(c,'mxGeometry',x='180',y='110',width='50',height='40')
        c=E.SubElement(root,'mxCell',id='edge',edge='1',source='left',target='box',parent='1',style='endArrow=block;')
        E.SubElement(c,'mxGeometry',relative='1')
        nodes={'left':{'kind':'virtual_circuit'},'box':{'kind':kind}}
        if blocked:nodes['obstacle']={'kind':'compute'}
        return root,nodes

    def test_container_side_port_matches_source_height_instead_of_box_center(self):
        for kind in ('cross_connect_group','ipsec','vcn'):
            with self.subTest(kind=kind):
                root,nodes=self.native(kind);route_native_edges(root,nodes)
                points=native_paths(root,nodes)[0]['points']
                self.assertTrue(all(abs(p[1]-points[0][1])<1e-6 for p in points))

    def test_straight_feasible_route_discards_old_unnecessary_bends(self):
        root,nodes=self.native()
        g=root.find("mxCell[@id='edge']/mxGeometry")
        a=E.SubElement(g,'Array',**{'as':'points'})
        for x,y in ((140,130),(140,100),(280,100),(280,130)):
            E.SubElement(a,'mxPoint',x=str(x),y=str(y))
        route_native_edges(root,nodes)
        points=native_paths(root,nodes)[0]['points']
        self.assertEqual(len(points),2)

    def test_real_obstacle_retains_needed_orthogonal_turns(self):
        root,nodes=self.native(blocked=True);route_native_edges(root,nodes)
        self.assertGreater(len(native_paths(root,nodes)[0]['points']),2)

    def test_every_fresh_ai_plan_repairs_a_misaligned_native_glyph_row(self):
        from unittest.mock import patch
        from oci_lenz.model import sample
        from oci_lenz.display import prepare_display
        from oci_lenz.architecture import make_scene,seed_plan,check_plan
        from oci_lenz.ai import design
        scene=make_scene(prepare_display(sample('fastconnect')),view='overview')
        bad=seed_plan(scene);good=copy.deepcopy(bad)
        rule=scene['request']['connector_guides'][0];boxes={p['id']:p for p in good['placements']}
        boxes[rule['source_anchor']]['y']=boxes[rule['target_anchor']]['y']+rule['target_offset']-rule['source_offset']
        with patch('oci_lenz.ai.request_json',side_effect=[bad,good]) as request:
            result=design(scene,[])
        self.assertEqual(request.call_count,2)
        self.assertIn('connector glyph row',request.call_args.args[0])
        self.assertEqual(result['connector_rule_version'],1)
        self.assertEqual(check_plan(scene,result),[])

    def test_old_saved_geometry_is_flagged_instead_of_silently_claimed_compliant(self):
        from oci_lenz.model import sample
        from oci_lenz.display import prepare_display
        from oci_lenz.architecture import make_scene,seed_plan
        from oci_lenz.quality import assess
        snapshot=prepare_display(sample('fastconnect'));scene=make_scene(snapshot,view='overview')
        plan={'version':3,'overview':seed_plan(scene)}
        report=assess(snapshot,plan)
        self.assertGreater(report['metrics']['connector_alignment_errors'],0)
        self.assertIn('connector_alignment_errors',report['issues'])
