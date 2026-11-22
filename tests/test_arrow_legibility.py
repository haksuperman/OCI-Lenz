"""Readable arrows are a reusable layout/routing contract, not a picture patch."""
import copy,unittest
import xml.etree.ElementTree as E
from oci_lenz.connector_rules import readability_groups,readability
from oci_lenz.routing import route_native_edges,native_paths,intersects
from oci_lenz.quality import revision_decision

class ArrowLegibilityTests(unittest.TestCase):
    def request(self):
        return {'items':{k:{'kind':kind,'container':False,'parent':'p'} for k,kind in [('a','backend_set'),('b','compute'),('c','compute')]},
                'edges':[{'id':'e1','source':'a','target':'b','kind':'backend'},{'id':'e2','source':'a','target':'c','kind':'backend'}]}
    def boxes(self):return {'a':dict(x=100,y=0,width=100,height=40),'b':dict(x=100,y=60,width=100,height=40),'c':dict(x=100,y=120,width=100,height=40)}
    def test_connected_gap_is_measured_without_moving_or_reparenting(self):
        req=self.request();boxes=self.boxes();before=copy.deepcopy((req,boxes));groups=readability_groups(req)
        self.assertTrue(groups['corridors']);r=readability(groups,boxes)
        self.assertGreater(r['metrics']['connector_clearance_shortfall'],0)
        self.assertEqual((req,boxes),before)
        boxes['b']['y']=120;boxes['c']['y']=240
        self.assertEqual(readability(groups,boxes)['metrics']['connector_clearance_shortfall'],0)
    def test_stacked_targets_need_a_row_corridor_not_just_column_alignment(self):
        groups=readability_groups(self.request());boxes=self.boxes()
        self.assertGreater(readability(groups,boxes)['metrics']['fanout_row_obstructions'],0)
        boxes['c']['y']=boxes['b']['y'];boxes['c']['x']=260
        self.assertEqual(readability(groups,boxes)['metrics']['fanout_row_obstructions'],0)
    def test_all_service_edges_receive_corridor_guidance(self):
        req=self.request();req['edges'][0]['kind']='project_id';req['edges'][1]['kind']='api_backend'
        self.assertEqual(len(readability_groups(req)['corridors']),2)
    def root(self,positions,relations):
        root=E.Element('root');nodes={}
        for key,kind,x,y in positions:
            nodes[key]={'kind':kind};c=E.SubElement(root,'mxCell',id=key,vertex='1',parent='1')
            E.SubElement(c,'mxGeometry',x=str(x),y=str(y),width='100',height='40')
        for key,source,target,kind in relations:
            c=E.SubElement(root,'mxCell',id=key,source=source,target=target,edge='1',parent='1',style='endArrow=open;',ociRelationKind=kind)
            E.SubElement(c,'mxGeometry',relative='1')
        return root,nodes
    def test_two_independent_owners_have_distinct_arrow_landing_points(self):
        root,nodes=self.root([('a','backend_set',20,20),('b','backend_set',240,20),('t','compute',130,220)],[('e1','a','t','backend'),('e2','b','t','backend')])
        route_native_edges(root,nodes);paths=native_paths(root,nodes)
        self.assertNotEqual(paths[0]['points'][-1],paths[1]['points'][-1])
        for p in paths:
            a,b=p['points'][-2:];self.assertGreaterEqual(abs(a[0]-b[0])+abs(a[1]-b[1]),24)
    def test_same_owner_ports_keep_the_same_landing_identity(self):
        root,nodes=self.root([('a','backend_set',20,20),('t','compute',20,220)],[('e1','a','t','backend'),('e2','a','t','backend')])
        route_native_edges(root,nodes);paths=native_paths(root,nodes)
        self.assertEqual(paths[0]['points'][-1],paths[1]['points'][-1])
    def test_stacked_fanout_uses_a_side_bus_without_touching_another_target(self):
        root,nodes=self.root([('s','backend_set',180,20),('a','compute',180,220),('b','compute',180,380)],[('e1','s','a','backend'),('e2','s','b','backend')])
        old=copy.deepcopy(root);route_native_edges(root,nodes);paths=native_paths(root,nodes)
        second=next(p for p in paths if p['target']=='b')
        self.assertFalse(any(intersects(a,b,(180,220,100,40)) for a,b in zip(second['points'],second['points'][1:])))
        self.assertTrue(any(x<156 or x>304 for x,y in second['points']))
        route_native_edges(old,nodes);self.assertEqual(E.tostring(root),E.tostring(old))
    def test_common_bus_applies_to_configured_function_backends_too(self):
        root,nodes=self.root([('s','api_deployment',180,20),('a','function',80,220),('b','function',280,220)],[('e1','s','a','api_backend'),('e2','s','b','api_backend')])
        route_native_edges(root,nodes);paths=native_paths(root,nodes)
        self.assertEqual(paths[0]['points'][:2],paths[1]['points'][:2])
        self.assertTrue(all(a[0]==b[0] or a[1]==b[1] for p in paths for a,b in zip(p['points'],p['points'][1:])))
    def quality(self):
        metrics={k:0 for k in ('resource_intersections','title_intersections','nonorthogonal_segments','unbridged_crossings','edge_overlap_length','flow_reversals','connector_alignment_errors','crowded_arrowheads','short_arrow_shafts')}
        metrics.update(canvas_area=10000,connector_clearance_shortfall=1,fanout_row_obstructions=2)
        return dict(version=5,scene_signature='synthetic',loss=10,metrics=metrics)
    def test_more_area_is_accepted_when_connection_readability_improves(self):
        before=self.quality();after=copy.deepcopy(before);after['metrics'].update(canvas_area=20000,connector_clearance_shortfall=0,fanout_row_obstructions=0);after['loss']=12
        self.assertTrue(revision_decision(before,after)['accepted'])
    def test_more_area_still_cannot_buy_an_intrusion_or_ambiguous_head(self):
        for field in ('resource_intersections','crowded_arrowheads'):
            before=self.quality();after=copy.deepcopy(before);after['metrics'].update(canvas_area=20000,connector_clearance_shortfall=0,fanout_row_obstructions=0);after['metrics'][field]=1;after['loss']=1
            self.assertFalse(revision_decision(before,after)['accepted'])
    def test_area_growth_without_readability_gain_is_not_a_fix(self):
        before=self.quality();after=copy.deepcopy(before);after['metrics']['canvas_area']=20000;after['loss']=1
        self.assertEqual(revision_decision(before,after)['reason'],'canvas_growth')

    def test_general_router_leaves_clearance_from_unrelated_card_borders(self):
        from oci_lenz.routing import route
        points=route((20,60),(220,60),[(80,20,70,100)])
        self.assertTrue(all(not intersects(a,b,(72,12,86,116)) for a,b in zip(points,points[1:])))
    def test_micropixel_roundoff_is_not_a_visible_intrusion(self):
        self.assertFalse(intersects((100,20),(100,80),(100-1e-8,20,50,60)))
        self.assertTrue(intersects((101,20),(101,80),(100,20,50,60)))

    def test_native_start_arrow_is_measured_at_the_api_source(self):
        from oci_lenz.connector_rules import arrow_visibility
        paths=[{'source':'set','target':'lb','points':[(0,0),(0,24)],'start_arrow':'open'},
               {'source':'other','target':'set','points':[(24,0),(0,0)],'end_arrow':'open'}]
        metrics,_=arrow_visibility(paths)
        self.assertEqual(metrics['crowded_arrowheads'],1)
        self.assertEqual(metrics['short_arrow_shafts'],0)
    def test_three_owners_have_separate_landings_on_a_native_icon(self):
        root,nodes=self.root([('a','backend_set',0,20),('b','backend_set',160,20),('c','backend_set',320,20),('t','compute',160,220)],[(f'e{i}',key,'t','backend') for i,key in enumerate(('a','b','c'))])
        target=root.find("mxCell[@id='t']");target.set('style','ociNativeLabel=1;');target.find('mxGeometry').set('height','80')
        glyph=E.SubElement(root,'mxCell',id='t-icon',vertex='1',parent='t');E.SubElement(glyph,'mxGeometry',x='30',y='8',width='40',height='40')
        route_native_edges(root,nodes);paths=native_paths(root,nodes)
        from oci_lenz.connector_rules import arrow_visibility
        self.assertEqual(arrow_visibility(paths)[0]['crowded_arrowheads'],0)
        self.assertEqual(len({p['points'][-1] for p in paths}),3)
    def test_a_reserved_connection_corridor_is_not_an_excess_gap(self):
        from oci_lenz.composition import measure,policy
        req=self.request();req['edges']=req['edges'][:1];del req['items']['c']
        req['items']['p']={'kind':'subnet','container':True,'parent':'','min_width':220,'min_height':64,'header_height':48}
        for key in ('a','b'):req['items'][key].update(min_width=100,min_height=40)
        boxes={'p':dict(x=0,y=0,width=300,height=300),'a':dict(x=40,y=50,width=100,height=40),'b':dict(x=40,y=162,width=100,height=40)}
        self.assertEqual(measure({'items':req['items'],'request':req},boxes)['metrics']['excess_gap_ratio'],0)
        self.assertEqual(policy()['connector_corridor'],72)

    def test_row_bus_can_move_past_a_title_before_taking_a_long_side_detour(self):
        from oci_lenz.branch_routes import branch_tree
        paths=branch_tree((230,60),(230,84),[('a',(130,220),(130,196)),('b',(330,220),(330,196))],
                          [(180,20,100,40),(80,220,100,40),(280,220,100,40),(80,130,120,18)])
        self.assertIsNotNone(paths)
        self.assertTrue(all(len(points)<=4 for points in paths.values()))
        self.assertTrue(all(points[1][0]==230 and points[1][1]>=156 for points in paths.values()))

    def test_non_lb_relationship_family_uses_the_same_visible_row_bus(self):
        root,nodes=self.root([('s','compute',180,20),('a','nsg',80,220),('b','nsg',280,220)],[('e1','s','a','nsg_ids'),('e2','s','b','nsg_ids')])
        route_native_edges(root,nodes)
        for p in native_paths(root,nodes):self.assertGreater(p['points'][1][1],84)
    def test_the_same_branch_tree_rotates_to_horizontal_resource_flows(self):
        from oci_lenz.branch_routes import branch_tree
        paths=branch_tree((60,230),(84,230),[('a',(220,130),(196,130)),('b',(220,330),(196,330))],
                          [(20,180,40,100),(220,80,40,100),(220,280,40,100)],direction='right')
        self.assertIsNotNone(paths)
        self.assertEqual(paths['a'][:2],paths['b'][:2])
        self.assertTrue(all(a[0]==b[0] or a[1]==b[1] for points in paths.values() for a,b in zip(points,points[1:])))
