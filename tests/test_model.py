import unittest
from oci_lenz.model import sample, graph
from oci_lenz.draw import render, validate

class ModelTests(unittest.TestCase):
    def test_backend_and_route_evidence(self):
        s=sample(); nodes, edges=graph(s)
        self.assertTrue(any(e['kind']=='backend' and e['target']=='compute' for e in edges))
        self.assertTrue(any(e['kind']=='route' and e['target']=='nat' for e in edges))
        self.assertTrue(all(e['evidence'] for e in edges))
    def test_ambiguous_backend_unknown(self):
        s=sample(); s['resources'].append(dict(s['resources'][-1], id='duplicate'))
        _, edges=graph(s)
        self.assertTrue(any(e['kind']=='backend' and e['target'].startswith('unknown:') for e in edges))
    def test_deterministic_editable_xml(self):
        s=sample(); a=render(s); self.assertEqual(a,render(s)); validate(a,s)
        with self.assertRaises(ValueError): validate(a.replace('source="lb"','source="absent"'),s)

if __name__=='__main__': unittest.main()

class GraphEdgeCases(unittest.TestCase):
    def test_missing_next_hop_and_nsg(self):
        s=sample();s['resources']=[r for r in s['resources'] if r['id'] not in ('nat','app-nsg')]
        n,e=graph(s)
        self.assertEqual(n['unknown:nat']['name'],'대상 미확인')
        self.assertTrue(any(x['target']=='unknown:app-nsg' for x in e))
        validate(render(s),s)
    def test_secondary_vnic_and_multisubnet_lb(self):
        s=sample();s['resources'].append(dict(s['resources'][-1],id='secondary',subnet_id='public',private_ips=['10.0.0.5']))
        next(r for r in s['resources'] if r['id']=='lb')['subnet_ids'].append('private')
        n,e=graph(s)
        self.assertEqual(sum(x['source']=='lb' and x['kind']=='subnet_ids' for x in e),2)
        validate(render(s),s)
    def test_invented_vertex_rejected(self):
        s=sample();xml=render(s).replace('</root>','<mxCell id="invented" vertex="1" parent="1" /></root>',1)
        with self.assertRaises(ValueError):validate(xml,s)
    def test_cross_compartment_vnic_uses_subnet_vcn(self):
        s=sample();s['resources'][-1]['vcn_id']=None
        _,e=graph(s)
        self.assertTrue(any(x['kind']=='backend' and x['target']=='compute' for x in e))
    def test_overlapping_skill_positions_fail(self):
        s=sample()
        xml=render(s,{'compute':{'x':30,'y':60},'vnic':{'x':30,'y':60}})
        with self.assertRaises(ValueError):validate(xml,s)
