"""Compact API-owned gateway groups; no business-service inference."""
import copy
import json
import re
import unittest
import xml.etree.ElementTree as E
from oci_lenz.model import sample,graph
from oci_lenz.display import prepare_display
from oci_lenz.architecture import make_scene,seed_plan,check_plan,apply_design
from oci_lenz.draw import validate
from oci_lenz.typography import text_width


class GatewayLayoutTests(unittest.TestCase):
    def test_groups_follow_each_vcn_without_changing_source_membership(self):
        s=prepare_display(sample('overview'));before=copy.deepcopy(graph(s));scene=make_scene(s,view='overview')
        groups=scene['request'].get('gateway_groups',[])
        self.assertEqual(len(groups),3)
        for group in groups:
            self.assertEqual(len(group['members']),3)
            self.assertEqual({scene['items'][key]['kind'] for key in group['members']},{'internet','nat','service'})
            self.assertTrue(all(scene['items'][key]['parent']==group['vcn'] for key in group['members']))
        self.assertNotIn('demo-1-',json.dumps(scene['request']))
        self.assertEqual(graph(s),before)

    def test_gateway_cards_are_narrow_and_seed_is_compact(self):
        s=prepare_display(sample());scene=make_scene(s,view='overview')
        gateways=[key for key,item in scene['items'].items() if item['kind'] in ('internet','nat','service')]
        self.assertTrue(all(scene['items'][key]['min_width']<120 for key in gateways))
        plan=seed_plan(scene);self.assertEqual(check_plan(scene,plan),[])
        boxes={p['id']:p for p in plan['placements']}
        self.assertLessEqual(max(boxes[k]['y'] for k in gateways)-min(boxes[k]['y'] for k in gateways),8)
        xml=apply_design(s,{'version':3,'overview':plan});validate(xml,s)

    def test_scattered_gateways_are_rejected_for_model_repair(self):
        scene=make_scene(prepare_display(sample()),view='overview');plan=seed_plan(scene)
        key=scene['aliases']['service'];boxes={p['id']:p for p in plan['placements']}
        boxes[key]['y']+=400
        parent=scene['items'][key]['parent']
        while parent:
            boxes[parent]['height']+=400;parent=scene['items'][parent]['parent']
        self.assertTrue(any(issue.startswith('gateway cluster') for issue in check_plan(scene,plan)))

    def test_oversized_gateway_cards_are_rejected(self):
        scene=make_scene(prepare_display(sample()),view='overview');plan=seed_plan(scene)
        next(p for p in plan['placements'] if p['id']==scene['aliases']['nat'])['height']+=150
        self.assertTrue(any(issue.startswith('gateway footprint') for issue in check_plan(scene,plan)))

    def test_many_gateways_can_use_a_compact_grid(self):
        raw=sample()
        for i in range(3):raw['resources'].append({'id':'extra-'+str(i),'kind':'nat','name':'Gateway '+str(i),'vcn_id':'vcn'})
        for i,r in enumerate(r for r in raw['resources'] if r['kind'] in ('internet','nat','service')):
            r.update(kind='nat',name='Gateway '+str(i))
        scene=make_scene(prepare_display(raw),view='overview');plan=seed_plan(scene)
        boxes={p['id']:p for p in plan['placements']};group=scene['request']['gateway_groups'][0]
        first=boxes[group['members'][0]];x,y=first['x'],first['y'];w,h=first['width'],first['height']
        for i,key in enumerate(group['members']):boxes[key].update(x=x+(i%3)*(w+8),y=y+(i//3)*(h+8))
        parent=group['vcn']
        while parent:
            boxes[parent]['height']+=h+8;parent=scene['items'][parent]['parent']
        self.assertEqual(check_plan(scene,plan),[])

    def test_gateway_without_its_vcn_in_scope_is_not_guessed_into_a_group(self):
        raw=sample();next(r for r in raw['resources'] if r['id']=='nat')['vcn_id']='outside-vcn'
        scene=make_scene(prepare_display(raw),view='overview');key=scene['aliases']['nat']
        self.assertFalse(any(key in g['members'] for g in scene['request']['gateway_groups']))

    def test_short_bold_gateway_name_keeps_clearance_in_narrow_caption(self):
        raw=sample();next(r for r in raw['resources'] if r['id']=='nat')['name']='Demo-NGW'
        s=prepare_display(raw);doc=E.fromstring(apply_design(s));cell=doc.find("diagram/mxGraphModel/root/mxCell[@id='nat']")
        size=float(re.search(r'font-size:([0-9.]+)px',cell.get('value')).group(1))
        width=float(cell.find('mxGeometry').get('width'))
        self.assertGreaterEqual(width-16-text_width('Demo-NGW',size),6)
