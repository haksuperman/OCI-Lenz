"""Trim hints must preserve the accepted branch tree, not squeeze its corridors."""
import copy
import json
import unittest
import xml.etree.ElementTree as E
from oci_lenz.architecture import apply_scope_heading
from oci_lenz.composition import boundary_space
from oci_lenz.quality import revision_decision


class BoundarySpaceTests(unittest.TestCase):
    def fixture(self):
        items={'n0':dict(parent='',container=True,min_width=220,min_height=64,header_height=48),
               'n1':dict(parent='n0',container=False,min_width=170,min_height=80),
               'n2':dict(parent='n0',container=False,min_width=170,min_height=80)}
        boxes={'n0':dict(x=20,y=90,width=900,height=600),
               'n1':dict(x=180,y=230,width=170,height=80),
               'n2':dict(x=180,y=430,width=170,height=80)}
        paths=[dict(source='n1',target='n2',points=[(265,310),(265,430)])]
        return dict(items=items),boxes,paths

    def test_guidance_trims_only_boundary_space_without_moving_input(self):
        scene,boxes,paths=self.fixture();before=copy.deepcopy((scene,boxes,paths))
        report=boundary_space(scene,boxes,paths)
        hint=report['feedback'][0]
        self.assertEqual(hint['issue'],'unused_boundary_space')
        self.assertEqual(hint['bounds'],dict(x=164,y=182,width=220,height=344))
        self.assertGreater(report['metrics']['unused_boundary_area_ratio'],.5)
        self.assertEqual((scene,boxes,paths),before)
        self.assertEqual(report,boundary_space(scene,boxes,paths))
        self.assertNotIn('source',json.dumps(report))

    def test_side_bus_bends_are_real_occupied_space(self):
        scene,boxes,paths=self.fixture()
        paths[0]['points']=[(265,310),(600,310),(600,400),(265,400),(265,430)]
        hint=boundary_space(scene,boxes,paths)['feedback'][0]
        self.assertGreaterEqual(hint['bounds']['x']+hint['bounds']['width'],608)
        self.assertGreater(hint['bounds']['width'],220)

    def test_foreign_wire_bend_inside_frame_is_also_protected(self):
        scene,boxes,paths=self.fixture()
        paths.append(dict(source='outside-a',target='outside-b',points=[(0,600),(700,600),(700,800)]))
        hint=boundary_space(scene,boxes,paths)['feedback'][0]
        self.assertGreaterEqual(hint['bounds']['x']+hint['bounds']['width'],708)
        self.assertGreaterEqual(hint['bounds']['y']+hint['bounds']['height'],608)

    def test_header_and_minimum_size_are_preserved_for_empty_frame(self):
        scene,boxes,paths=self.fixture();scene['items']={'n0':scene['items']['n0']};boxes={'n0':boxes['n0']}
        hint=boundary_space(scene,boxes,[])['feedback'][0]
        self.assertEqual(hint['bounds'],dict(x=20,y=90,width=220,height=64))

    def test_nested_frame_hint_contains_current_child_frame(self):
        scene,boxes,paths=self.fixture()
        scene['items']['n3']=dict(parent='n0',container=True,min_width=220,min_height=64,header_height=80)
        boxes['n3']=dict(x=500,y=200,width=250,height=340)
        result=boundary_space(scene,boxes,paths)
        outer=next(h for h in result['feedback'] if h['id']=='n0')['bounds']
        self.assertGreaterEqual(outer['x']+outer['width'],766)
        self.assertGreaterEqual(outer['y']+outer['height'],556)

    def test_straight_through_crossing_does_not_pin_old_blank_border(self):
        scene,boxes,paths=self.fixture()
        paths.append(dict(source='outside-a',target='outside-b',points=[(0,350),(1100,350)]))
        self.assertEqual(boundary_space(scene,boxes,paths)['feedback'][0]['bounds']['width'],220)

    def test_compact_frame_has_no_suggestion_to_expand_or_move(self):
        scene,boxes,paths=self.fixture();boxes['n0'].update(x=164,y=182,width=220,height=344)
        report=boundary_space(scene,boxes,paths)
        self.assertEqual(report['feedback'],[])
        self.assertEqual(report['metrics']['unused_boundary_area_ratio'],0)

    def test_container_arrow_landing_at_border_is_not_cropped_off(self):
        scene,boxes,paths=self.fixture()
        paths.append(dict(source='outside',target='n0',points=[(1100,380),(920,380)]))
        hint=boundary_space(scene,boxes,paths)['feedback'][0]
        self.assertEqual(hint['trim']['right'],0)

    def test_top_bus_retains_room_below_measured_title(self):
        scene,boxes,paths=self.fixture();scene['items']['n0']['header_height']=80
        paths.append(dict(source='n1',target='n2',points=[(265,200),(500,200),(500,430)]))
        hint=boundary_space(scene,boxes,paths)['feedback'][0]
        self.assertLessEqual(hint['bounds']['y']+80,192)

    def test_tight_existing_header_never_forces_an_expanding_hint(self):
        scene,boxes,paths=self.fixture();scene['items']={'n0':scene['items']['n0']}
        scene['items']['n0']['header_height']=92
        boxes={'n0':dict(x=20,y=90,width=220,height=100)}
        report=boundary_space(scene,boxes,[])
        self.assertEqual(report['feedback'],[])
        self.assertEqual(report['metrics']['unused_boundary_area_ratio'],0)

    def test_whitespace_gain_cannot_buy_more_bends_or_longer_detours(self):
        before=dict(version=6,scene_signature='synthetic',loss=10,metrics=dict(canvas_area=1000,edge_bends=3,route_detour_ratio=.2))
        for field in ('edge_bends','route_detour_ratio'):
            after=copy.deepcopy(before);after['loss']=1;after['metrics']['canvas_area']=800;after['metrics'][field]+=1
            with self.subTest(field=field):
                self.assertEqual(revision_decision(before,after)['reason'],'regression_'+field)

    def test_smaller_boundary_with_same_arrows_is_accepted(self):
        before=dict(version=6,scene_signature='synthetic',loss=10,metrics=dict(canvas_area=1000,edge_bends=3,route_detour_ratio=.2))
        after=copy.deepcopy(before);after['loss']=9;after['metrics']['canvas_area']=800
        self.assertTrue(revision_decision(before,after)['accepted'])

    def test_scope_heading_follows_trimmed_region_with_constant_gap(self):
        doc=E.fromstring('<mxfile><diagram><mxGraphModel><root><mxCell id="notice"><mxGeometry/></mxCell><mxCell id="layout-region"><mxGeometry x="20" y="240" width="800" height="500"/></mxCell></root></mxGraphModel></diagram></mxfile>')
        region=doc.find(".//mxCell[@id='layout-region']/mxGeometry")
        before=dict(region.attrib)
        apply_scope_heading(doc,{'scope':dict(region='synthetic',compartments=[])})
        heading=doc.find(".//mxCell[@id='notice']/mxGeometry")
        self.assertEqual(float(heading.get('y'))+float(heading.get('height'))+16,240)
        self.assertEqual(region.attrib,before)
