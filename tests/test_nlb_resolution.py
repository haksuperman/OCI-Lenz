"""Resolve observed NLB references without inventing VM identity or placement."""
import copy,json,unittest
from types import SimpleNamespace as N
import xml.etree.ElementTree as E
from oci_lenz.model import graph,sample
from oci_lenz.diagram_model import diagram_graph
from oci_lenz.display import prepare_display
from oci_lenz.draw import render,validate

class NLBResolutionTests(unittest.TestCase):
    def snapshot(self):
        s=sample();lb=next(r for r in s['resources'] if r['id']=='lb');lb.update(kind='nlb',subnet_id='public');lb.pop('subnet_ids')
        bs=next(r for r in s['resources'] if r['kind']=='backend_set');bs.update(backends_status='ok',backends=[{'target_id':'ocid1.privateip.oc1.synthetic.target','ip_address':None,'port':443}])
        return s
    def resolve(self,s,fail=None,outside=False,ambiguous=False,extra=None):
        from oci_lenz.nlb_backends import resolve_nlb_backends
        req=[];comp='other' if outside else 'sample'
        responses={'get_private_ip':N(id='ocid1.privateip.oc1.synthetic.target',vnic_id='extra-vnic',subnet_id='private',compartment_id=comp,ip_address='10.0.1.31',display_name='NEVER-STORE'),
                   'get_vnic':N(id='extra-vnic',subnet_id='private',private_ip='10.0.1.31',public_ip=None,nsg_ids=[],is_primary=True,freeform_tags={'secret':'NEVER-STORE'}),
                   'list_vnic_attachments':[N(vnic_id='extra-vnic',instance_id='extra-vm')],
                   'get_instance':N(id='extra-vm',display_name='Synthetic Discovered VM',compartment_id='sample',metadata={'secret':'NEVER-STORE'})}
        responses.update(extra or {})
        if ambiguous:responses['list_vnic_attachments'].append(N(vnic_id='extra-vnic',instance_id='conflicting-vm'))
        def call(service,api,*args,**kwargs):
            req.append((service,api,args,kwargs));s['coverage'].append({'service':service,'api':api,'status':'not_found_or_not_authorized' if api==fail else 'ok'})
            return None if api==fail else responses[api]
        def add(obj,kind,**fields):s['resources'].append(dict(id=obj.id,kind=kind,name=getattr(obj,'display_name',None) or kind,**fields))
        resolve_nlb_backends(call,add,s,'sample');return req
    def test_missing_target_follows_ip_vnic_attachment_instance_with_exact_scope(self):
        s=self.snapshot();req=self.resolve(s);nodes,edges=graph(s)
        self.assertTrue(any(e['kind']=='backend' and e['target']=='extra-vm' for e in edges))
        self.assertEqual(nodes['extra-vnic']['private_ip_ids'],['ocid1.privateip.oc1.synthetic.target'])
        self.assertEqual(nodes['extra-vnic']['private_ips'],['10.0.1.31'])
        self.assertNotIn('NEVER-STORE',json.dumps(s))
        self.assertEqual(next(k for svc,a,args,k in req if a=='list_vnic_attachments'),{'compartment_id':'sample','vnic_id':'extra-vnic'})
        self.assertTrue(all(a.startswith(('get_','list_')) for svc,a,args,k in req))
    def test_failure_stays_unknown_with_visible_owned_ip_and_no_count_badge(self):
        s=self.snapshot();self.resolve(s,fail='get_private_ip');canonical=graph(s);display=prepare_display(s)
        nodes,edges=diagram_graph(display);tag=next(nodes[e['target']] for e in edges if e['kind']=='backend')
        self.assertEqual(tag['kind'],'backend_endpoint');self.assertIn('IP 미확인',tag['display_details'])
        self.assertEqual(tag['backend_set_id'],'backend-set');self.assertFalse(nodes['backend-set'].get('backend_badge'))
        xml=render(display);validate(xml,display);cells={c.get('id'):c for c in E.fromstring(xml).find('diagram/mxGraphModel/root')}
        self.assertNotEqual(cells[tag['id']].get('visible'),'0');self.assertEqual(cells[tag['id']].get('parent'),'public')
        self.assertNotIn('대상 미확인 (',cells['backend-set'].get('value'));self.assertNotIn('10.0.1.31',render(prepare_display(s,redact=True)))
        self.assertEqual(graph(s),canonical);self.assertEqual(render(display),xml)
    def test_outside_compartment_does_not_fetch_vnic_or_instance(self):
        s=self.snapshot();req=self.resolve(s,outside=True)
        self.assertEqual([a for svc,a,args,k in req],['get_private_ip'])
        self.assertEqual(next(r for r in s['resources'] if r['kind']=='backend_set')['backends'][0]['target_resolution_status'],'outside_scope')
        self.assertTrue(next(e['target'] for e in graph(s)[1] if e['kind']=='backend').startswith('unknown:'))
    def test_ambiguous_attachment_does_not_invent_a_vm(self):
        s=self.snapshot();req=self.resolve(s,ambiguous=True)
        self.assertFalse(any(a=='get_instance' for svc,a,args,k in req))
        self.assertNotIn('extra-vm',graph(s)[0])
    def test_unique_registered_ip_matching_does_not_require_identity_lookup(self):
        s=self.snapshot();b=next(r for r in s['resources'] if r['kind']=='backend_set')['backends'][0]
        b.update(ip_address='10.0.1.10',target_resolution_status='not_found_or_not_authorized',target_resolution_stage='get_private_ip')
        self.assertEqual(next(e['target'] for e in graph(s)[1] if e['kind']=='backend'),'compute')
        next(r for r in s['resources'] if r['kind']=='vnic')['private_ip_ids']=['different-private-ip']
        self.assertEqual(next(e['target'] for e in graph(s)[1] if e['kind']=='backend'),'compute')
    def test_same_missing_reference_in_two_sets_gets_two_owned_annotations(self):
        s=self.snapshot();bs=next(r for r in s['resources'] if r['kind']=='backend_set');other=copy.deepcopy(bs);other.update(id='other-set',name='Synthetic Other Set');s['resources'].append(other)
        nodes,edges=diagram_graph(prepare_display(s));tags=[r for r in nodes.values() if r['kind']=='backend_endpoint']
        self.assertEqual(len(tags),2);self.assertEqual({r['backend_set_id'] for r in tags},{bs['id'],other['id']})
        validate(render(prepare_display(s)),prepare_display(s))
    def test_existing_target_needs_no_additional_api_reads(self):
        from oci_lenz.nlb_backends import resolve_nlb_backends
        s=self.snapshot();nic=next(r for r in s['resources'] if r['kind']=='vnic');nic['private_ip_ids']=['ocid1.privateip.oc1.synthetic.target']
        resolve_nlb_backends(lambda *a,**k:self.fail('unexpected read'),lambda *a,**k:self.fail('unexpected add'),s,'sample')

    def test_each_missing_chain_read_failure_retains_registration_and_status(self):
        for api in ('get_vnic','list_vnic_attachments','get_instance'):
            with self.subTest(api=api):
                s=self.snapshot();self.resolve(s,fail=api)
                b=next(r for r in s['resources'] if r['kind']=='backend_set')['backends'][0]
                self.assertEqual(b['target_resolution_status'],'not_found_or_not_authorized')
                nodes,edges=diagram_graph(prepare_display(s))
                self.assertTrue(any(r['kind']=='backend_endpoint' for r in nodes.values()))
                self.assertFalse(any(r['id']=='extra-vm' for r in s['resources']))
    def test_missing_explicit_instance_is_read_once_and_scoped_before_add(self):
        s=self.snapshot();b=next(r for r in s['resources'] if r['kind']=='backend_set')['backends'][0]
        b['target_id']='ocid1.instance.oc1.synthetic.vm'
        req=self.resolve(s,extra={'get_instance':N(id=b['target_id'],compartment_id='sample',display_name='Synthetic Direct VM')})
        self.assertEqual([a for svc,a,args,k in req],['get_instance'])
        self.assertEqual(next(e['target'] for e in graph(s)[1] if e['kind']=='backend'),b['target_id'])
    def test_conflicting_returned_vnic_subnet_never_relinks_a_vm(self):
        s=self.snapshot();req=self.resolve(s,extra={'get_vnic':N(id='extra-vnic',subnet_id='outside-subnet')})
        self.assertEqual([a for svc,a,args,k in req],['get_private_ip','get_vnic'])
        self.assertEqual(next(r for r in s['resources'] if r['kind']=='backend_set')['backends'][0]['target_resolution_status'],'conflicting_identity')
    def test_repeated_target_reuses_resolution_without_duplicate_nodes(self):
        s=self.snapshot();bs=next(r for r in s['resources'] if r['kind']=='backend_set');other=copy.deepcopy(bs);other['id']='other-set';s['resources'].append(other)
        req=self.resolve(s)
        self.assertEqual(sum(a=='get_private_ip' for svc,a,args,k in req),1)
        self.assertEqual(sum(r['id']=='extra-vm' for r in s['resources']),1)
        self.assertEqual(sum(e['kind']=='backend' and e['target']=='extra-vm' for e in graph(s)[1]),2)
    def test_known_vnic_with_missing_vm_still_follows_attachment(self):
        s=self.snapshot();nic=next(r for r in s['resources'] if r['kind']=='vnic');nic.update(id='extra-vnic',instance_id='extra-vm',private_ip_ids=['ocid1.privateip.oc1.synthetic.target'])
        self.resolve(s)
        self.assertEqual(next(e['target'] for e in graph(s)[1] if e['kind']=='backend'),'extra-vm')
    def test_ip_only_unmatched_registration_gets_visible_tag_and_scope_anchor(self):
        s=self.snapshot();bs=next(r for r in s['resources'] if r['kind']=='backend_set');bs['backends'][0].pop('target_id')
        display=prepare_display(s);nodes,edges=diagram_graph(display)
        self.assertEqual(sum(r['kind']=='backend_endpoint' for r in nodes.values()),1)
        validate(render(display,detail_pages=True),display)

    def test_annotation_ip_is_local_only_and_native_owner_is_enforced(self):
        from oci_lenz.architecture import make_scene
        s=self.snapshot();next(r for r in s['resources'] if r['kind']=='backend_set')['backends'][0]['ip_address']='10.0.1.31'
        display=prepare_display(s);scene=make_scene(display,view='overview')
        self.assertNotIn('10.0.1.31',json.dumps(scene['request']))
        self.assertNotIn('ocid1.privateip',json.dumps(scene['request']))
        doc=E.fromstring(render(display));root=doc.find('diagram/mxGraphModel/root')
        node=next(r for r in diagram_graph(display)[0].values() if r['kind']=='backend_endpoint')
        root.find("mxCell[@id='"+node['id']+"']").set('parent','private')
        with self.assertRaises(ValueError):validate(E.tostring(doc,encoding='unicode'),display)

    def test_lookup_failure_does_not_hide_a_configured_ip_relation(self):
        s=self.snapshot();b=next(r for r in s['resources'] if r['kind']=='backend_set')['backends'][0]
        b.update(ip_address='10.0.1.10',target_resolution_status='not_found_or_not_authorized',target_resolution_stage='get_instance')
        self.assertEqual(next(e['target'] for e in graph(s)[1] if e['kind']=='backend'),'compute')

    def test_observed_target_ip_survives_later_failure_without_rewriting_registration(self):
        s=self.snapshot();b=next(r for r in s['resources'] if r['kind']=='backend_set')['backends'][0];b['ip_address']=None
        self.resolve(s,fail='get_instance')
        self.assertIsNone(b['ip_address']);self.assertEqual(b['target_ip_address'],'10.0.1.31')
        tag=next(r for r in diagram_graph(prepare_display(s))[0].values() if r['kind']=='backend_endpoint')
        self.assertIn('IP: 10.0.1.31',tag['display_details'])
