"""LB and NLB share configured-IP relationships without identity-read prerequisites."""
import copy,json,unittest
from oci_lenz.model import sample,graph
from oci_lenz.diagram_model import diagram_graph
from oci_lenz.display import prepare_display
from oci_lenz.draw import render,validate

class BackendParityTests(unittest.TestCase):
    def snapshot(self,nlb=True):
        s=sample();lb=next(r for r in s['resources'] if r['kind']=='lb')
        if nlb:lb.update(kind='nlb',subnet_id=lb.pop('subnet_ids')[0])
        return s
    def edge(self,s):return next(e for e in graph(s)[1] if e['kind']=='backend')
    def test_nlb_ip_matching_uses_the_same_evidence_rule_as_lb(self):
        for metadata in ({},{'target_resolution_status':'permission_denied'}, {'target_resolution_status':'outside_scope'}, {'target_resolution_stage':'get_instance','target_resolution_status':'failed'}):
            s=self.snapshot();b=next(r for r in s['resources'] if r['kind']=='backend_set')['backends'][0]
            b.update(target_id='ocid1.privateip.oc1.synthetic.unavailable',**metadata)
            e=self.edge(s);self.assertEqual(e['target'],'compute');self.assertIn('ip_address',e['evidence'])
            self.assertEqual(self.edge(self.snapshot(False))['target'],e['target'])
    def test_recorded_other_private_ip_id_does_not_disable_configured_ip_relation(self):
        s=self.snapshot();next(r for r in s['resources'] if r['kind']=='vnic')['private_ip_ids']=['observed-private-ip']
        next(r for r in s['resources'] if r['kind']=='backend_set')['backends'][0]['target_id']='unavailable-reference'
        self.assertEqual(self.edge(s)['target'],'compute')
    def test_ambiguous_or_other_vcn_ip_is_not_invented_into_a_vm(self):
        s=self.snapshot();bs=next(r for r in s['resources'] if r['kind']=='backend_set');bs['backends'][0]['target_id']='unavailable-reference'
        nic=next(r for r in s['resources'] if r['kind']=='vnic');other=copy.deepcopy(nic);other['id']='other-nic';s['resources'].append(other)
        self.assertTrue(self.edge(s)['target'].startswith('unknown:'))
        s['resources'].remove(other);nic.update(vcn_id='outside-vcn',subnet_id='outside-subnet')
        self.assertTrue(self.edge(s)['target'].startswith('unknown:'))
    def test_registered_backend_stays_visible_without_vm_failure_caption(self):
        s=self.snapshot();next(r for r in s['resources'] if r['kind']=='backend_set')['backends'][0].update(target_id='unavailable-reference',ip_address='10.0.1.210')
        display=prepare_display(s);nodes,edges=diagram_graph(display)
        endpoint=next(nodes[e['target']] for e in edges if e['kind']=='backend')
        self.assertEqual(endpoint['kind'],'backend_endpoint');self.assertEqual(endpoint['display_details'],['IP: 10.0.1.210'])
        xml=render(display);validate(xml,display)
        self.assertNotIn('VM 확인 불가',xml);self.assertNotIn('대상 미확인 (',xml)
        self.assertNotIn('10.0.1.210',render(prepare_display(s,redact=True)))
    def test_same_vm_two_ports_preserves_two_configured_edges(self):
        s=self.snapshot();bs=next(r for r in s['resources'] if r['kind']=='backend_set');b=bs['backends'][0];b['target_id']='unavailable-reference';bs['backends'].append(dict(b,port=8443))
        edges=[e for e in graph(s)[1] if e['kind']=='backend']
        self.assertEqual([e['target'] for e in edges],['compute','compute']);self.assertEqual(len({e['label'] for e in edges}),2)
        validate(render(prepare_display(s)),prepare_display(s))

    def test_registered_ip_never_requires_extra_identity_api_calls(self):
        from oci_lenz.nlb_backends import resolve_nlb_backends
        for ip in ('10.0.1.10','10.0.1.210'):
            s=self.snapshot();b=next(r for r in s['resources'] if r['kind']=='backend_set')['backends'][0]
            b.update(target_id='ocid1.privateip.oc1.synthetic.unavailable',ip_address=ip)
            resolve_nlb_backends(lambda *a,**k:self.fail('unnecessary identity query'),lambda *a,**k:self.fail('invented resource'),s,'sample')
            self.assertIn(b['target_resolution_status'],('ip_match','ip_registration'))
