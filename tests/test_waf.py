"""Scoped regional WAF protection is a configured LB reference, not traffic."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import Mock
import xml.etree.ElementTree as E
from tests import test_collect as fixtures
from oci_lenz.model import graph,sample
from oci_lenz.display import prepare_display
from oci_lenz.draw import render,validate
from oci_lenz.architecture import make_scene

oci=fixtures.oci


@unittest.skipIf(oci is None,'install OCI SDK')
class WAFCollectorTests(unittest.TestCase):
    def response(self):
        return {'waf_list_web_app_firewalls':oci.waf.models.WebAppFirewallCollection(items=[
            oci.waf.models.WebAppFirewallLoadBalancerSummary(id='waf',compartment_id='c',
                display_name='Synthetic WAF',load_balancer_id='lb',web_app_firewall_policy_id='policy',
                freeform_tags={'secret':'DO-NOT-STORE'},lifecycle_details='DO-NOT-STORE')])}

    def test_scoped_list_minimal_fields_and_exact_lb_evidence(self):
        req=[];s,_=fixtures.CollectorTests().run_collect(extra=self.response(),request_log=req)
        nodes,edges=graph(s);r=nodes['waf']
        self.assertEqual(r['kind'],'waf')
        self.assertEqual(r['web_app_firewall_policy_id'],'policy')
        self.assertNotIn('subnet_id',r);self.assertNotIn('vcn_id',r)
        e=next(e for e in edges if e['source']=='waf')
        self.assertEqual((e['target'],e['kind'],e['evidence']),
            ('lb','waf_protection','WebAppFirewallLoadBalancer.load_balancer_id'))
        self.assertEqual([(a,k) for n,a,k in req if n=='waf_list_web_app_firewalls'],[((),{'compartment_id':'c'})])
        self.assertNotIn('DO-NOT-STORE',json.dumps(s));self.assertNotIn('unknown:policy',nodes)

    def test_empty_and_denied_are_distinct_and_other_services_survive(self):
        for fail,status in ((None,'ok'),('waf_list_web_app_firewalls','permission_denied')):
            s,_=fixtures.CollectorTests().run_collect(fail=fail)
            c=next(c for c in s['coverage'] if c.get('service')=='waf')
            self.assertEqual(c['status'],status)
            if fail:self.assertNotIn('count',c)
            else:self.assertEqual(c['count'],0)
            self.assertIn('lb',graph(s)[0]);self.assertNotIn('sensitive error',json.dumps(s))

    def test_real_sdk_collection_pagination_has_only_scoped_get_requests(self):
        from oci_lenz.waf import collect_waf
        client=oci.waf.WafClient.__new__(oci.waf.WafClient)
        client.retry_strategy=oci.retry.NoneRetryStrategy();client.circuit_breaker_callback=None
        client.base_client=Mock();client.base_client.get_preferred_retry_strategy.return_value=None
        pages=[]
        def transport(**request):
            self.assertEqual(request['method'],'GET')
            self.assertEqual(request['operation_name'],'list_web_app_firewalls')
            self.assertEqual(request['query_params']['compartmentId'],'synthetic-compartment')
            page=request['query_params'].get('page');pages.append(page)
            return oci.response.Response(200,{} if page else {'opc-next-page':'page-2'},
                oci.waf.models.WebAppFirewallCollection(items=[oci.waf.models.WebAppFirewallLoadBalancerSummary(
                    id='synthetic-waf-'+str(len(pages)),load_balancer_id='synthetic-lb')]),None)
        client.base_client.call_api=transport
        def call(service,api,**kwargs):
            self.assertEqual(service,'waf')
            data=oci.pagination.list_call_get_all_results(getattr(client,api),**kwargs).data
            return data if isinstance(data,list) else data.items
        s={'resources':[],'coverage':[],'scope':{'region':'synthetic'}}
        def add(obj,kind,**fields):s['resources'].append(dict(id=obj.id,kind=kind,**fields))
        collect_waf(call,add,s,'synthetic-compartment')
        self.assertEqual(pages,[None,'page-2']);self.assertEqual(len(s['resources']),2)


class WAFDiagramTests(unittest.TestCase):
    def snapshot(self):
        s=sample();s['resources'].append({'id':'waf','kind':'waf','name':'Synthetic WAF',
            'load_balancer_id':'lb','backend_type':'LOAD_BALANCER'})
        return s

    def test_waf_is_outside_vcn_subnets_and_arrow_points_to_protected_lb(self):
        s=prepare_display(self.snapshot());original=copy.deepcopy(graph(s));xml=render(s);validate(xml,s)
        cells={c.get('id'):c for c in E.fromstring(xml).find('diagram').iter('mxCell')}
        self.assertEqual(cells['waf'].get('parent'),'layout-region');self.assertIn('waf-icon',cells)
        edge=next(c for c in cells.values() if c.get('edge')=='1' and c.get('source')=='waf')
        self.assertEqual(edge.get('target'),'lb');self.assertNotEqual(edge.get('visible'),'0')
        self.assertIn('endArrow=open;',edge.get('style'));self.assertNotIn('startArrow=open;',edge.get('style'))
        self.assertEqual(graph(s),original);self.assertEqual(render(s),xml)
        scene=make_scene(s,view='overview');self.assertEqual(scene['items'][scene['aliases']['waf']]['parent'],scene['region'])
        self.assertNotIn('Synthetic WAF',json.dumps(scene['request']))
        self.assertNotIn('Synthetic WAF',render(prepare_display(self.snapshot(),redact=True)))

    def test_cross_compartment_lb_is_unknown_until_selected_snapshot_merge(self):
        s=self.snapshot();r=s['resources'][-1];r['load_balancer_id']='outside-lb'
        self.assertIn('unknown:outside-lb',graph(s)[0])
        s['resources'].append({'id':'outside-lb','kind':'lb','name':'Synthetic remote LB','compartment_id':'other'})
        self.assertEqual(next(e['target'] for e in graph(s)[1] if e['source']=='waf'),'outside-lb')

    def test_no_lb_reference_or_unsupported_target_does_not_invent_connection(self):
        s=self.snapshot();s['resources'][-1].pop('load_balancer_id')
        nodes,edges=graph(s);e=next(e for e in edges if e['source']=='waf')
        self.assertEqual(nodes[e['target']]['kind'],'unknown')
        s['resources'][-1]['load_balancer_id']='compute'
        nodes,edges=graph(s);e=next(e for e in edges if e['source']=='waf')
        self.assertEqual(nodes[e['target']]['kind'],'unknown')
