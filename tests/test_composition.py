"""Composition scoring must see avoidable space without moving AI geometry."""
import copy
import json
import unittest
from oci_lenz.composition import measure,policy


class CompositionTests(unittest.TestCase):
    def fixture(self):
        scene={'region':'n0','items':{
            'n0':{'kind':'region','container':True,'parent':'','min_width':220,'min_height':64,'header_height':48},
            'n1':{'kind':'subnet','container':True,'parent':'n0','min_width':220,'min_height':64,'header_height':48},
            'n2':{'kind':'lb','container':False,'parent':'n1','min_width':170,'min_height':80},
            'n3':{'kind':'backend_set','container':False,'parent':'n1','min_width':170,'min_height':44}},
            'request':{'edges':[{'id':'e0','source':'n3','target':'n2','kind':'lb_id'}]}}
        boxes={'n0':{'x':20,'y':90,'width':320,'height':360},
               'n1':{'x':36,'y':154,'width':220,'height':224},
               'n2':{'x':61,'y':218,'width':170,'height':80},
               'n3':{'x':61,'y':322,'width':170,'height':44}}
        return scene,boxes

    def test_empty_bands_are_not_hidden_by_spreading_children_or_translating_them(self):
        scene,boxes=self.fixture()
        boxes['n1']['height']+=200;boxes['n0']['height']+=200
        compact=measure(scene,boxes)
        spread=copy.deepcopy(boxes);spread['n3']['y']+=160
        expanded=measure(scene,spread)
        self.assertGreater(expanded['metrics']['excess_gap_ratio'],compact['metrics']['excess_gap_ratio'])
        # Old trailing-slack calculation rewarded this artificial spread.
        self.assertAlmostEqual(expanded['metrics']['avoidable_whitespace_ratio'],compact['metrics']['avoidable_whitespace_ratio'])
        shifted=copy.deepcopy(boxes)
        for k in ('n2','n3'):shifted[k]['x']+=10
        self.assertEqual(measure(scene,shifted)['metrics']['avoidable_whitespace_ratio'],compact['metrics']['avoidable_whitespace_ratio'])

    def test_card_inflation_and_alignment_drift_receive_specific_alias_feedback(self):
        scene,boxes=self.fixture()
        scene['items']['n2']['kind']=scene['items']['n3']['kind']='compute'
        before=copy.deepcopy((scene,boxes))
        good=measure(scene,boxes)
        bad=copy.deepcopy(boxes);bad['n3']['x']+=20;bad['n3']['width']+=30
        report=measure(scene,bad)
        self.assertGreater(report['metrics']['card_inflation_ratio'],good['metrics']['card_inflation_ratio'])
        self.assertGreater(report['metrics']['alignment_error'],good['metrics']['alignment_error'])
        self.assertTrue(any(r['id']=='n3' and r['issue']=='card_inflation' for r in report['feedback']))
        self.assertEqual((scene,boxes),before)
        self.assertNotIn('ocid',json.dumps(report))

    def test_empty_snapshot_and_large_gateway_clearance_are_not_fake_design_errors(self):
        scene,boxes=self.fixture();scene['items']={'n0':scene['items']['n0']};boxes={'n0':boxes['n0']}
        report=measure(scene,boxes)
        self.assertEqual(report['metrics']['avoidable_whitespace_ratio'],0)
        self.assertEqual(report['metrics']['alignment_error'],0)
        self.assertEqual(policy()['network_corridor'],64)

    def test_alignment_only_follows_evidenced_one_to_one_flow_in_same_vcn(self):
        scene,boxes=self.fixture()
        scene['items']['n1']['kind']='vcn'
        self.assertEqual(measure(scene,boxes)['metrics']['flow_alignment_error'],0)
        boxes['n3']['x']+=40
        report=measure(scene,boxes)
        self.assertGreater(report['metrics']['flow_alignment_error'],0)
        scene['request']['edges']=[]
        self.assertEqual(measure(scene,boxes)['metrics']['flow_alignment_error'],0)

    def test_resource_count_changes_footprints_not_a_fixed_page_size(self):
        scene,boxes=self.fixture()
        report=measure(scene,boxes)
        feedback=next(f for f in report['feedback'] if f['id']=='n0')
        self.assertLess(feedback['suggested_width'],boxes['n0']['width'])
        self.assertNotIn('page_width',policy())

    def test_sparse_container_is_not_hidden_by_its_large_parent(self):
        scene,boxes=self.fixture();boxes['n0']['width']=5000
        boxes['n1']['width']=500
        report=measure(scene,boxes)
        self.assertGreater(report['metrics']['worst_container_whitespace_ratio'],.3)
        self.assertTrue(any(f['id']=='n1' and f['issue']=='avoidable_whitespace' for f in report['feedback']))

    def test_unrelated_kinds_are_not_forced_into_one_alignment_row(self):
        scene,boxes=self.fixture();boxes['n3']['x']+=60
        self.assertEqual(measure(scene,boxes)['metrics']['alignment_error'],0)

    def test_empty_subnet_keeps_header_but_cannot_expand_without_content(self):
        scene,boxes=self.fixture()
        for key in ('n2','n3'):del scene['items'][key];del boxes[key]
        boxes['n1']['height']=500
        report=measure(scene,boxes)
        self.assertTrue(any(f['id']=='n1' and f['issue']=='empty_container_inflation' for f in report['feedback']))

    def test_single_evidenced_fastconnect_branch_stays_on_drg_axis(self):
        scene,boxes=self.fixture()
        scene['items']['n2']['kind']='drg';scene['items']['n3']['kind']='virtual_circuit'
        scene['request']['edges']=[]
        scene['request']['network_groups']=[{'kind':'drg','drg':'n2','remote_members':[],
                                             'fastconnect_members':['n3'],'ipsec_members':[],'vcns':[]}]
        aligned=measure(scene,boxes)
        boxes['n3']['x']+=120
        shifted=measure(scene,boxes)
        self.assertGreater(shifted['metrics']['network_alignment_error'],aligned['metrics']['network_alignment_error'])
        self.assertTrue(any(f['id']=='n3' and f['issue']=='network_axis' for f in shifted['feedback']))
        scene['request']['network_groups']=[]
        self.assertEqual(measure(scene,boxes)['metrics']['network_alignment_error'],0)

    def test_multiple_circuits_are_not_forced_on_top_of_each_other(self):
        scene,boxes=self.fixture()
        scene['items']['n2']['kind']=scene['items']['n3']['kind']='virtual_circuit'
        scene['items']['n1']['kind']='drg'
        scene['request']['network_groups']=[{'kind':'drg','drg':'n1','remote_members':[],
                                             'fastconnect_members':['n2','n3'],'ipsec_members':[],'vcns':[]}]
        self.assertEqual(measure(scene,boxes)['metrics']['network_alignment_error'],0)

    def test_unknown_remote_endpoint_is_aligned_only_with_its_observed_peer(self):
        scene,boxes=self.fixture()
        scene['items']['n2']['kind']='drg';scene['items']['n3']['kind']='rpc'
        scene['items']['n4']={'kind':'unknown','container':False,'parent':'n0','min_width':170,'min_height':64}
        boxes['n4']={'x':500,'y':100,'width':170,'height':64}
        scene['request']['network_groups']=[{'kind':'drg','drg':'n2','remote_members':['n3','n4']}]
        self.assertEqual(measure(scene,boxes)['metrics']['network_alignment_error'],0)
        scene['request']['network_groups'].append({'kind':'remote_peer','endpoints':['n3','n4']})
        self.assertGreater(measure(scene,boxes)['metrics']['network_alignment_error'],0)

    def test_wide_subnet_spanning_a_row_is_not_centered_with_every_small_subnet(self):
        scene,boxes=self.fixture()
        boxes['n0'].update(width=900,height=700)
        boxes['n1'].update(y=300,width=700)
        boxes['n2']['y']=364;boxes['n3']['y']=468
        scene['items']['n4']={**scene['items']['n1'],'parent':'n0'}
        boxes['n4']={'x':520,'y':154,'width':220,'height':64}
        self.assertEqual(measure(scene,boxes)['metrics']['alignment_error'],0)
