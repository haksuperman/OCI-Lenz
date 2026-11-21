"""Inventory-independent connector regressions; no OCI or model calls."""
import copy
import unittest
import xml.etree.ElementTree as E

from oci_lenz.routing import conflict_aware, route_native_edges, native_paths
from oci_lenz.quality import edge_conflicts
from oci_lenz.connector_rules import readability_groups, readability


class ConnectionReadabilityTests(unittest.TestCase):
    def test_backend_and_unknown_edges_participate_in_conflict_routing(self):
        for source, target in [('lb','backend_set'), ('nlb','backend_set'),
                               ('backend_set','compute'), ('backend_set','unknown'),
                               ('subnet','nat'), ('compute','nsg')]:
            self.assertTrue(conflict_aware({'a':{'kind':source},'b':{'kind':target}},'a','b'))

    def test_only_single_owner_unknowns_get_proximity_hints(self):
        items={k:{'kind':kind,'container':False} for k,kind in
               [('a','backend_set'),('b','backend_set'),('u','unknown'),('shared','unknown'),('v','compute')]}
        edges=[{'source':'a','target':t,'kind':'backend'} for t in ('u','shared','v')]
        edges.append({'source':'b','target':'shared','kind':'backend'})
        original=copy.deepcopy((items,edges))
        groups=readability_groups({'items':items,'edges':edges})
        self.assertEqual(groups['nearby'],[{'source':'a','target':'u'}])
        self.assertEqual((items,edges),original)

    def test_proximity_is_measured_not_reparented_or_silently_moved(self):
        groups={'nearby':[{'source':'a','target':'u'}],'fanouts':[]}
        boxes={'a':{'x':10,'y':10,'width':170,'height':40},
               'u':{'x':210,'y':10,'width':170,'height':40}}
        original=copy.deepcopy(boxes)
        self.assertEqual(readability(groups,boxes)['metrics']['remote_unknown_targets'],0)
        self.assertEqual(boxes,original)
        boxes['u']['x']=1500
        report=readability(groups,boxes)
        self.assertEqual(report['metrics']['remote_unknown_targets'],1)
        self.assertEqual(report['feedback'][0]['issue'],'remote_unknown_target')

    def test_parallel_fanout_order_is_measured_from_actual_geometry(self):
        groups={'nearby':[],'fanouts':[{'source':'s','targets':['a','b']}]}
        boxes={'s':{'x':0,'y':0,'width':80,'height':40},
               'a':{'x':0,'y':100,'width':80,'height':40},
               'b':{'x':120,'y':100,'width':80,'height':40}}
        self.assertEqual(readability(groups,boxes)['metrics']['fanout_misalignment'],0)
        boxes['b']['y']=250
        self.assertGreater(readability(groups,boxes)['metrics']['fanout_misalignment'],0)

    def test_compact_multirow_backend_grids_are_not_forced_into_one_long_row(self):
        boxes={str(i):{'x':(i%3)*194,'y':(i//3)*100,'width':170,'height':76} for i in range(9)}
        groups={'nearby':[],'fanouts':[{'source':'s','targets':sorted(boxes)}]}
        self.assertEqual(readability(groups,boxes)['metrics']['fanout_misalignment'],0)

    def test_scene_carries_rules_for_every_new_layout_and_reports_old_remote_geometry(self):
        from oci_lenz.architecture import make_scene,seed_plan
        from oci_lenz.display import prepare_display
        from oci_lenz.model import sample
        from oci_lenz.quality import assess
        snapshot=sample('edge-waf');display=prepare_display(snapshot)
        scene=make_scene(display,view='overview')
        rules=scene['request']['connection_readability']
        self.assertTrue(rules['nearby'])
        plan=seed_plan(scene);boxes={p['id']:p for p in plan['placements']}
        pair=rules['nearby'][0]
        boxes[pair['target']]['x']=boxes[scene['region']]['x']+5000
        region=boxes[scene['region']]
        region['width']=max(region['width'],boxes[pair['target']]['x']+boxes[pair['target']]['width']-region['x']+24)
        result=assess(display,{'version':3,'overview':plan})
        self.assertGreater(result['metrics']['remote_unknown_targets'],0)
        self.assertIn('remote_unknown_targets',result['issues'])

    def test_unrelated_backend_wires_use_clear_jumps_and_replay_exactly(self):
        root=E.Element('root');nodes={}
        for key,kind,x,y in [('a','backend_set',20,20),('b','backend_set',280,20),
                             ('x','compute',280,260),('y','unknown',20,260)]:
            nodes[key]={'kind':kind}
            c=E.SubElement(root,'mxCell',id=key,vertex='1',parent='1')
            E.SubElement(c,'mxGeometry',x=str(x),y=str(y),width='100',height='60')
        for key,source,target in [('e1','a','x'),('e2','b','y')]:
            c=E.SubElement(root,'mxCell',id=key,source=source,target=target,edge='1',parent='1',style='endArrow=block;')
            E.SubElement(c,'mxGeometry',relative='1')
        original=copy.deepcopy(root);route_native_edges(root,nodes)
        report=edge_conflicts(native_paths(root,nodes),nodes)
        self.assertEqual(report['edge_overlap_length'],0)
        from oci_lenz.line_jumps import crossing_report
        self.assertEqual(crossing_report(native_paths(root,nodes),nodes)['unbridged_crossings'],0)
        route_native_edges(original,nodes)
        self.assertEqual(E.tostring(root),E.tostring(original))
        for path in native_paths(root,nodes):
            self.assertTrue(all(a[0]==b[0] or a[1]==b[1] for a,b in zip(path['points'],path['points'][1:])))
