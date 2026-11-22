"""NLB SDK shapes, explicit/unique targets and native presentation."""
import copy
import json
import unittest
import xml.etree.ElementTree as E
from unittest.mock import Mock
from tests import test_collect as fixtures
oci=fixtures.oci
from oci_lenz.model import graph,sample
from oci_lenz.display import prepare_display
from oci_lenz.draw import render,validate


@unittest.skipIf(oci is None, 'install OCI SDK')
class NLBCollectorTests(unittest.TestCase):
    def test_generated_sdk_methods_and_collection_pagination(self):
        from oci_lenz.load_balancers import collect_nlb
        m=oci.network_load_balancer.models
        requests=[];snapshot={'resources':[]}
        client=oci.network_load_balancer.NetworkLoadBalancerClient.__new__(oci.network_load_balancer.NetworkLoadBalancerClient)
        client.retry_strategy=oci.retry.NoneRetryStrategy();client.circuit_breaker_callback=None
        client.base_client=Mock();client.base_client.get_preferred_retry_strategy.return_value=None
        def transport(**request):
            self.assertEqual(request['method'],'GET')
            name=request['operation_name'];query=request['query_params'];page=query.get('page')
            self.assertIn(page,(None,'synthetic-page-2'));requests.append((name,page))
            suffix='b' if page else 'a'
            if name=='list_network_load_balancers':
                self.assertEqual(query['compartmentId'],'synthetic-compartment')
                data=m.NetworkLoadBalancerCollection(items=[m.NetworkLoadBalancerSummary(id='nlb-'+suffix,
                    subnet_id='synthetic-subnet',display_name='Synthetic NLB '+suffix)])
            else:
                self.assertIn(request['path_params']['networkLoadBalancerId'],('nlb-a','nlb-b'))
                if name=='list_listeners':data=m.ListenerCollection(items=[m.ListenerSummary(name='tcp-'+suffix,port=443,protocol='TCP')])
                elif name=='list_backend_sets':data=m.BackendSetCollection(items=[m.BackendSetSummary(name='servers-'+suffix)])
                else:
                    self.assertEqual(name,'list_backends')
                    self.assertIn(request['path_params']['backendSetName'],('servers-a','servers-b'))
                    data=m.BackendCollection(items=[m.BackendSummary(name='node-'+suffix,ip_address='10.0.1.'+('11' if page else '10'),port=443)])
            return oci.response.Response(200,{} if page else {'opc-next-page':'synthetic-page-2'},data,None)
        client.base_client.call_api=transport
        def call(service,api,*args,**kwargs):
            self.assertEqual(service,'nlb')
            data=oci.pagination.list_call_get_all_results(getattr(client,api),*args,**kwargs).data
            return data if isinstance(data,list) else data.items
        def add(obj,kind,**fields):snapshot['resources'].append(dict(id=obj.id,name=obj.display_name,kind=kind,**fields))
        collect_nlb(call,add,snapshot,'synthetic-compartment')
        self.assertEqual(sum(r['kind']=='nlb' for r in snapshot['resources']),2)
        self.assertEqual(sum(r['kind']=='backend_set' for r in snapshot['resources']),4)
        self.assertTrue(all(len(r['backends'])==2 for r in snapshot['resources'] if r['kind']=='backend_set'))
        for api in ('list_network_load_balancers','list_listeners','list_backend_sets','list_backends'):
            pages=[p for n,p in requests if n==api]
            self.assertEqual(pages.count(None),pages.count('synthetic-page-2'))

    def responses(self):
        m=oci.network_load_balancer.models
        return {
            'nlb_list_network_load_balancers':m.NetworkLoadBalancerCollection(items=[
                m.NetworkLoadBalancerSummary(id='nlb',display_name='Synthetic NLB',compartment_id='c',
                    subnet_id='s',network_security_group_ids=['nsg'],is_private=True,
                    ip_addresses=[m.IpAddress(ip_address='10.0.0.90',is_public=False)],
                    freeform_tags={'private':'DO-NOT-STORE'})]),
            'nlb_list_listeners':m.ListenerCollection(items=[m.ListenerSummary(name='tcp',port=443,
                    protocol='TCP',default_backend_set_name='servers')]),
            'nlb_list_backend_sets':m.BackendSetCollection(items=[m.BackendSetSummary(name='servers')]),
            'nlb_list_backends':m.BackendCollection(items=[m.BackendSummary(name='node',
                    target_id='instance',ip_address='10.0.0.2',port=443)]),
        }

    def test_collections_fields_ownership_and_explicit_backend(self):
        req=[];s,_=fixtures.CollectorTests().run_collect(extra=self.responses(),request_log=req)
        nodes,edges=graph(s)
        self.assertEqual(nodes['nlb']['kind'],'nlb')
        self.assertEqual(nodes['nlb']['subnet_id'],'s')
        self.assertEqual(nodes['nlb']['nsg_ids'],['nsg'])
        self.assertTrue(any(e['source']=='nlb' and e['target']=='s' and
            e['evidence']=='NetworkLoadBalancer.subnet_id' for e in edges))
        self.assertTrue(any(e['source']=='nlb' and e['target']=='nsg' and
            e['evidence']=='NetworkLoadBalancer.network_security_group_ids[]' for e in edges))
        self.assertTrue(any(e['source']=='nlb/backend-set/servers' and e['target']=='instance' and
            'target_id' in e['evidence'] for e in edges))
        display=prepare_display(s);nlb=next(r for r in display['resources'] if r['id']=='nlb')
        self.assertIn('Private: 10.0.0.90',nlb['summary_details'])
        self.assertNotIn('DO-NOT-STORE',json.dumps(s))
        self.assertEqual(next(k for n,a,k in req if n=='nlb_list_network_load_balancers'),{'compartment_id':'c'})

    def test_denied_children_retain_parent_and_distinguish_empty_list(self):
        for api in ('list_network_load_balancers','list_listeners','list_backend_sets','list_backends'):
            with self.subTest(api=api):
                s,_=fixtures.CollectorTests().run_collect(extra=self.responses(),fail='nlb_'+api)
                entry=next(c for c in s['coverage'] if c['service']=='nlb' and c['api']==api)
                self.assertEqual(entry['status'],'permission_denied')
                if api!='list_network_load_balancers':self.assertIn('nlb',graph(s)[0])
        s,_=fixtures.CollectorTests().run_collect()
        entry=next(c for c in s['coverage'] if c.get('service')=='nlb')
        self.assertEqual((entry['status'],entry['count']),('ok',0))

    def test_collected_private_ip_ocid_resolves_target_without_ip_string(self):
        from types import SimpleNamespace as N
        responses=self.responses();m=oci.network_load_balancer.models
        responses.update(list_vnic_attachments=[N(vnic_id='vn',instance_id='instance')],
            list_private_ips=[oci.core.models.PrivateIp(id='synthetic-private-ip',ip_address='10.0.0.2')],
            nlb_list_backends=m.BackendCollection(items=[m.BackendSummary(name='private-target',
                target_id='synthetic-private-ip',port=443)]))
        snapshot,_=fixtures.CollectorTests().run_collect(extra=responses)
        nodes,edges=graph(snapshot)
        self.assertEqual(nodes['vn']['private_ip_ids'],['synthetic-private-ip'])
        self.assertTrue(any(e['source']=='nlb/backend-set/servers' and e['target']=='instance' for e in edges))


class NLBGraphTests(unittest.TestCase):
    def snapshot(self):
        s=sample();lb=next(r for r in s['resources'] if r['kind']=='lb')
        lb.update(kind='nlb',subnet_id='public');lb.pop('subnet_ids')
        return s

    def target(self,s):
        return next(e for e in graph(s)[1] if e['kind']=='backend')['target']

    def test_ip_matching_is_unique_and_scoped_to_nlb_vcn(self):
        s=self.snapshot();self.assertEqual(self.target(s),'compute')
        s['resources'].append(dict(id='duplicate',kind='vnic',name='Synthetic duplicate',
            subnet_id='private',private_ips=['10.0.1.10']))
        self.assertTrue(self.target(s).startswith('unknown:'))
        s['resources'][-1]['subnet_id']='outside'
        self.assertEqual(self.target(s),'compute')

    def test_explicit_instance_and_private_ip_ids_take_precedence_without_ip_guessing(self):
        s=self.snapshot();backend=next(r for r in s['resources'] if r['kind']=='backend_set')['backends'][0]
        backend.update(target_id='compute',ip_address=None)
        self.assertEqual(self.target(s),'compute')
        next(r for r in s['resources'] if r['kind']=='vnic')['private_ip_ids']=['synthetic-private-ip']
        backend['target_id']='synthetic-private-ip'
        self.assertEqual(self.target(s),'compute')
        backend.update(target_id='outside-target',ip_address='10.0.1.10')
        self.assertEqual(self.target(s),'compute')

    def test_cross_scope_targets_remain_unknown_and_private_ip_ambiguity_is_not_guessed(self):
        s=self.snapshot();backend=next(r for r in s['resources'] if r['kind']=='backend_set')['backends'][0]
        vnic=next(r for r in s['resources'] if r['kind']=='vnic')
        vnic['private_ip_ids']=['synthetic-private-ip']
        duplicate=copy.deepcopy(vnic);duplicate['id']='other-vnic'
        s['resources'].append(duplicate);backend['target_id']='synthetic-private-ip'
        self.assertTrue(self.target(s).startswith('unknown:'))
        backend['target_id']='outside-instance'
        self.assertTrue(self.target(s).startswith('unknown:'))

    def test_native_subnet_backend_set_symbol_labels_and_redaction(self):
        s=self.snapshot();d=prepare_display(s);xml=render(d);validate(xml,d)
        cells={c.get('id'):c for c in E.fromstring(xml).find('diagram').iter('mxCell')}
        self.assertEqual(cells['lb'].get('parent'),'public')
        self.assertEqual(cells['backend-set'].get('parent'),'public')
        self.assertIn('lb-icon',cells)
        self.assertIn('192.0.2.20',xml)
        self.assertNotIn('192.0.2.20',render(prepare_display(s,redact=True)))
        self.assertEqual(render(d),xml)
