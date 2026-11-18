import copy
import unittest
from oci_lenz.model import sample,graph
from oci_lenz.display import prepare_display
from oci_lenz.architecture import make_scene,seed_plan,check_plan


class DrgOrientationTests(unittest.TestCase):
    def scene(self):
        s=sample('drg-centered')
        return s,make_scene(prepare_display(s),view='overview')

    def test_per_drg_directions_are_api_based_and_alias_only(self):
        s,scene=self.scene();before=graph(s);a=scene['aliases']
        group=next(g for g in scene['request']['network_groups'] if g['kind']=='drg')
        self.assertEqual(group['vcns'],[a['vcn']])
        self.assertEqual(set(group['remote_members']),{a['remote'],a['unknown:outside']})
        self.assertEqual(set(group['ipsec_members']),{a[k] for k in ('qa-vpn','qa-cpe','qa-tunnel-0','qa-tunnel-1')})
        self.assertEqual(group['branch_gap'],64)
        self.assertNotIn('Synthetic',str(group));self.assertEqual(graph(s),before)

    def test_seed_and_validator_enforce_left_right_and_above(self):
        _,scene=self.scene();plan=seed_plan(scene)
        self.assertEqual(check_plan(scene,plan),[])
        group=next(g for g in scene['request']['network_groups'] if g['kind']=='drg')
        boxes={p['id']:p for p in plan['placements']};drg=boxes[group['drg']]
        for field in ('vcns','ipsec_members','remote_members'):
            bad=copy.deepcopy(plan);box=next(p for p in bad['placements'] if p['id']==group[field][0])
            if field=='vcns':box['x']=drg['x']+drg['width']+64
            elif field=='ipsec_members':box['x']=drg['x']-box['width']-64
            else:box['y']=drg['y']+drg['height']+64
            self.assertTrue(any('DRG '+field in issue for issue in check_plan(scene,bad)))

    def test_multiple_drgs_share_vcn_without_inferred_service_membership(self):
        s,_=self.scene()
        s['resources'] += [{'id':'second-drg','kind':'drg','name':'Synthetic second DRG'},
            {'id':'second-attach','kind':'drg_attachment','name':'Synthetic second attachment','drg_id':'second-drg','network_id':'vcn','network_type':'VCN'}]
        scene=make_scene(prepare_display(s),view='overview');plan=seed_plan(scene)
        self.assertEqual(check_plan(scene,plan),[])
        groups=[g for g in scene['request']['network_groups'] if g['kind']=='drg']
        self.assertEqual(len(groups),2)
        self.assertEqual(groups[0]['vcns'],[scene['aliases']['vcn']]);self.assertEqual(groups[1]['vcns'],[scene['aliases']['vcn']])
