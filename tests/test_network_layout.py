import copy
import unittest
import xml.etree.ElementTree as E
from oci_lenz.model import sample,graph
from oci_lenz.display import prepare_display
from oci_lenz.architecture import make_scene
from oci_lenz import routing


class NetworkLayoutTests(unittest.TestCase):
    def test_alias_only_groups_follow_actual_vpn_and_drg_relationships(self):
        s=prepare_display(sample('ipsec-vpn'));before=copy.deepcopy(s)
        scene=make_scene(s,view='overview');groups=scene['request']['network_groups'];a=scene['aliases']
        vpn=next(g for g in groups if g['kind']=='vpn')
        self.assertEqual(vpn['connection'],a['qa-vpn'])
        self.assertEqual(vpn['tunnels'],[a['qa-tunnel-0'],a['qa-tunnel-1']])
        self.assertEqual(vpn['cpe'],a['qa-cpe']);self.assertEqual(vpn['drg'],a['qa-drg'])
        drg=next(g for g in groups if g['kind']=='drg')
        self.assertEqual(drg['vcns'],[a['vcn']])
        self.assertFalse(any(item['kind']=='drg_attachment' for item in scene['items'].values()))
        self.assertNotIn('Synthetic',str(groups));self.assertNotIn('198.51.100',str(groups))
        self.assertEqual(s,before)

    def test_peer_pairs_deduplicate_hints_only_and_keep_unknown_peer(self):
        s=prepare_display(sample('network-peering'));before=graph(s)
        scene=make_scene(s,view='overview');a=scene['aliases']
        groups=scene['request']['network_groups']
        local=[g for g in groups if g['kind']=='local_peer']
        self.assertEqual(len(local),1)
        self.assertEqual(set(local[0]['endpoints']),{a['qa-lpg-a'],a['qa-lpg-b']})
        remote=next(g for g in groups if g['kind']=='remote_peer')
        self.assertIn(a['unknown:qa-outside-rpc'],remote['endpoints'])
        self.assertEqual(graph(s),before)
        self.assertEqual(sum(e['kind']=='peer_id' for e in before[1]),3)

    def test_inventory_without_network_resources_has_no_new_layout_contract(self):
        self.assertNotIn('network_groups',make_scene(prepare_display(sample()))['request'])

    def test_router_keeps_clear_crossing_short_but_detours_around_overlap(self):
        occupied=[((100,20),(100,100))]
        points=routing.route((20,60),(180,60),[],occupied=occupied)
        self.assertEqual(points,[(20,60),(180,60)])
        self.assertEqual(points,routing.route((20,60),(180,60),[],occupied=occupied))
        self.assertEqual(routing.segment_conflict(points[0],points[-1],*occupied[0]),(1,0))
        parallel=[((40,60),(160,60))]
        points=routing.route((20,60),(180,60),[],occupied=parallel)
        self.assertTrue(any(p[1]!=60 for p in points))

    def test_unavoidable_crossing_does_not_fail_or_change_endpoints(self):
        wall=(90,0,20,40)
        points=routing.route((20,60),(180,60),[wall],occupied=[((100,40),(100,10000))])
        self.assertEqual(points[0],(20,60));self.assertEqual(points[-1],(180,60))
        self.assertTrue(all(not routing.intersects(a,b,wall) for a,b in zip(points,points[1:])))

    def test_quality_counts_crossings_and_overlaps_but_not_shared_endpoints(self):
        paths=[{'source':'a','target':'b','network':True,'points':[(0,50),(100,50)]},
               {'source':'c','target':'d','network':True,'points':[(50,0),(50,100)]}]
        self.assertEqual(routing.path_quality(paths)['network_edge_crossings'],1)
        paths[1]['points']=[(20,50),(80,50)]
        self.assertEqual(routing.path_quality(paths)['network_overlap_length'],60)
        paths[1].update(source='a',points=[(0,50),(0,100)])
        self.assertEqual(routing.path_quality(paths),{'network_edge_crossings':0,'network_overlap_length':0})

    def test_native_network_routing_preserves_geometry_and_api_endpoints(self):
        root=E.Element('root')
        positions={'a':(20,100),'b':(220,100),'c':(120,20),'d':(120,220)}
        for key,(x,y) in positions.items():
            cell=E.SubElement(root,'mxCell',id=key,vertex='1',parent='1')
            E.SubElement(cell,'mxGeometry',x=str(x),y=str(y),width='20',height='20')
        for key,source,target in [('e1','a','b'),('e2','c','d')]:
            cell=E.SubElement(root,'mxCell',id=key,edge='1',parent='1',source=source,target=target,style='endArrow=block;')
            E.SubElement(cell,'mxGeometry',relative='1')
        nodes={key:{'kind':'rpc'} for key in positions}
        original={c.get('id'):E.tostring(c.find('mxGeometry')) for c in root if c.get('vertex')=='1'}
        routing.route_native_edges(root,nodes)
        self.assertEqual(routing.path_quality(routing.native_paths(root,nodes))['network_overlap_length'],0)
        from oci_lenz.line_jumps import crossing_report
        self.assertEqual(crossing_report(routing.native_paths(root,nodes),nodes)['unbridged_crossings'],0)
        self.assertEqual({c.get('id'):E.tostring(c.find('mxGeometry')) for c in root if c.get('vertex')=='1'},original)
        self.assertEqual([(c.get('source'),c.get('target')) for c in root if c.get('edge')=='1'],[('a','b'),('c','d')])
        first_paths=routing.native_paths(root,nodes)
        routing.route_native_edges(root,nodes)
        paths=routing.native_paths(root,nodes)
        self.assertEqual(paths,first_paths)
        self.assertEqual(routing.path_quality(paths)['network_overlap_length'],0)
        self.assertEqual(crossing_report(paths,nodes)['unbridged_crossings'],0)

    def test_shared_drg_port_junction_is_not_an_unrelated_crossing(self):
        paths=[{'source':'a','target':'drg','network':True,'points':[(100,0),(20,0),(0,0)]},
               {'source':'b','target':'drg','network':True,'points':[(20,100),(20,0),(0,0)]}]
        self.assertEqual(routing.path_quality(paths),{'network_edge_crossings':0,'network_overlap_length':0})

    def test_drg_fanin_refines_earlier_routes_against_later_branches(self):
        root=E.Element('root')
        positions={'drg':(20,150),'a0':(450,280),'a1':(650,410),'a2':(250,20),'a3':(450,20),'a4':(450,410),'a5':(250,410)}
        for key,(x,y) in positions.items():
            c=E.SubElement(root,'mxCell',id=key,vertex='1',parent='1')
            E.SubElement(c,'mxGeometry',x=str(x),y=str(y),width='100',height='70')
        for key in ('a0','a1','a2','a3','a4','a5'):
            c=E.SubElement(root,'mxCell',id='e'+key,edge='1',source=key,target='drg',parent='1',style='')
            E.SubElement(c,'mxGeometry',relative='1')
        nodes={k:{'kind':'drg' if k=='drg' else 'drg_attachment'} for k in positions}
        routing.route_native_edges(root,nodes)
        self.assertEqual(routing.path_quality(routing.native_paths(root,nodes))['network_overlap_length'],0)
        from oci_lenz.line_jumps import crossing_report
        self.assertEqual(crossing_report(routing.native_paths(root,nodes),nodes)['unbridged_crossings'],0)
