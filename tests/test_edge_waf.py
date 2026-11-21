"""Synthetic SDK contracts for configured Edge WAF origins; never use DNS."""
import copy
import json
import unittest
from unittest.mock import Mock,patch
import xml.etree.ElementTree as E
from tests import test_collect as fixtures
from oci_lenz.model import sample,graph
from oci_lenz.display import prepare_display
from oci_lenz.draw import render,validate
from oci_lenz.architecture import make_scene

oci=fixtures.oci


@unittest.skipIf(oci is None,'install OCI SDK')
class EdgeCollectorTests(unittest.TestCase):
    def responses(self):
        m=oci.waas.models
        return {'waas_list_waas_policies':[m.WaasPolicySummary(id='edge',display_name='Synthetic Edge WAF',compartment_id='c',domain='do-not-use-as-origin.example.invalid',freeform_tags={'secret':'DO-NOT-STORE'})],
            'waas_get_waas_policy':m.WaasPolicy(id='edge',
                origins={'primary':m.Origin(uri='https://user:DO-NOT-STORE@192.0.2.20/path?secret=DO-NOT-STORE',http_port=80,https_port=443,custom_headers=[m.Header(name='Authorization',value='DO-NOT-STORE')]),
                         'backup':m.Origin(uri='external.example.invalid'),
                         'unused':m.Origin(uri='198.51.100.99')},
                origin_groups={'pool':m.OriginGroup(origins=[m.OriginGroupOrigins(origin='backup',weight=1)])},
                waf_config=m.WafConfig(origin='primary',origin_groups=['pool']))}

    def test_minimal_active_origins_and_secrets_never_persist(self):
        req=[];s,_=fixtures.CollectorTests().run_collect(extra=self.responses(),request_log=req)
        r=next(r for r in s['resources'] if r['kind']=='edge_waf')
        self.assertEqual(r['origin_status'],'ok')
        self.assertEqual({o['key'] for o in r['origins']},{'primary','backup'})
        self.assertEqual(next(o['host'] for o in r['origins'] if o['key']=='primary'),'192.0.2.20')
        for secret in ('DO-NOT-STORE','198.51.100.99','do-not-use-as-origin','/path','custom_headers'):
            self.assertNotIn(secret,json.dumps(s))
        self.assertEqual(next(k for n,a,k in req if n=='waas_list_waas_policies'),{'compartment_id':'c'})
        nodes,edges=graph(s)
        self.assertTrue(any(e['source']=='edge' and e['target']=='lb' and 'origins' in e['evidence'] for e in edges))
        self.assertEqual(sum(r['kind']=='edge_origin' for r in nodes.values()),1)

    def test_denied_detail_keeps_policy_and_unknown_origin_not_empty_success(self):
        s,_=fixtures.CollectorTests().run_collect(extra=self.responses(),fail='waas_get_waas_policy')
        nodes,edges=graph(s);self.assertIn('edge',nodes)
        self.assertEqual(nodes['edge']['origin_status'],'unavailable')
        self.assertEqual(nodes[next(e['target'] for e in edges if e['source']=='edge')]['kind'],'edge_origin')
        self.assertEqual(next(c['status'] for c in s['coverage'] if c.get('api')=='get_waas_policy'),'permission_denied')

    def test_empty_list_denial_and_successful_unconfigured_policy_are_distinct(self):
        for fail,status in ((None,'ok'),('waas_list_waas_policies','permission_denied')):
            s,_=fixtures.CollectorTests().run_collect(fail=fail)
            c=next(c for c in s['coverage'] if c.get('service')=='waas')
            self.assertEqual(c['status'],status)
            if not fail:self.assertEqual(c['count'],0)
        r=self.responses();r['waas_get_waas_policy']=oci.waas.models.WaasPolicy(id='edge',origins={'unused':oci.waas.models.Origin(uri='192.0.2.20')})
        s,_=fixtures.CollectorTests().run_collect(extra=r)
        self.assertEqual(graph(s)[0]['edge']['origin_status'],'not_configured')
        self.assertFalse(any(e['source']=='edge' for e in graph(s)[1]))

    def test_missing_selected_origin_group_stays_unknown_without_using_other_origins(self):
        r=self.responses();r['waas_get_waas_policy'].waf_config=oci.waas.models.WafConfig(origin_groups=['missing'])
        s,_=fixtures.CollectorTests().run_collect(extra=r)
        nodes,edges=graph(s)
        targets=[e['target'] for e in edges if e['source']=='edge']
        self.assertEqual(len(targets),1);self.assertEqual(nodes[targets[0]]['kind'],'edge_origin')
        self.assertNotIn('192.0.2.20',str(nodes['edge']['origins']))

    def test_real_sdk_methods_paginate_and_get_only_selected_policy_ids(self):
        from oci_lenz.edge_waf import collect_edge_waf
        m=oci.waas.models;client=oci.waas.WaasClient.__new__(oci.waas.WaasClient)
        client.retry_strategy=oci.retry.NoneRetryStrategy();client.circuit_breaker_callback=None
        client.base_client=Mock();client.base_client.get_preferred_retry_strategy.return_value=None
        pages=[];gets=[]
        def transport(**request):
            self.assertEqual(request['method'],'GET')
            if request['operation_name']=='list_waas_policies':
                q=request['query_params'];self.assertEqual(q['compartmentId'],'synthetic-compartment')
                page=q.get('page');pages.append(page)
                return oci.response.Response(200,{} if page else {'opc-next-page':'second'},[m.WaasPolicySummary(id='edge-'+str(len(pages)))],None)
            self.assertEqual(request['operation_name'],'get_waas_policy')
            key=request['path_params']['waasPolicyId'];gets.append(key)
            return oci.response.Response(200,{},m.WaasPolicy(id=key),None)
        client.base_client.call_api=transport
        def call(service,api,**kwargs):
            self.assertEqual(service,'waas');fn=getattr(client,api)
            return (oci.pagination.list_call_get_all_results(fn,**kwargs) if api.startswith('list_') else fn(**kwargs)).data
        s={'resources':[]}
        def add(obj,kind,**fields):s['resources'].append(dict(id=obj.id,kind=kind,**fields))
        collect_edge_waf(call,add,s,'synthetic-compartment')
        self.assertEqual(pages,[None,'second']);self.assertEqual(gets,['edge-1','edge-2'])


class EdgeGraphTests(unittest.TestCase):
    def snapshot(self,host='192.0.2.20'):
        s=sample();s['resources'].append(dict(id='edge',kind='edge_waf',name='Synthetic Edge WAF',origin_status='ok',
            origins=[dict(key='primary',host=host,http_port=80,https_port=443,selected_by=['WaasPolicy.waf_config.origin'])]))
        return s

    def target(self,s):
        nodes,edges=graph(s)
        e=next(e for e in edges if e['source']=='edge')
        return nodes,e

    def test_unique_public_lb_server_and_ambiguity(self):
        s=self.snapshot();self.assertEqual(self.target(s)[1]['target'],'lb')
        dup=copy.deepcopy(next(r for r in s['resources'] if r['kind']=='lb'));dup['id']='other-lb';s['resources'].append(dup)
        n,e=self.target(s);self.assertEqual(n[e['target']]['kind'],'edge_origin')
        s=self.snapshot('198.51.100.20');next(r for r in s['resources'] if r['kind']=='vnic')['public_ip']='198.51.100.20'
        self.assertEqual(self.target(s)[1]['target'],'compute')

    def test_hostname_and_private_ip_never_trigger_dns_or_private_network_guess(self):
        with patch('socket.getaddrinfo',side_effect=AssertionError('DNS must not run')):
            for host in ('external.example.invalid','10.0.1.10','2001:db8::99',None):
                s=self.snapshot(host);n,e=self.target(s);self.assertEqual(n[e['target']]['kind'],'edge_origin')

    def test_ipv6_nlb_and_multiple_origin_refs_preserve_one_target_relationship(self):
        s=self.snapshot('2001:db8::20');lb=next(r for r in s['resources'] if r['kind']=='lb')
        lb.update(kind='nlb',ip_addresses=[{'ip_address':'2001:0db8:0:0::20','is_public':True}])
        duplicate=copy.deepcopy(s['resources'][-1]['origins'][0]);duplicate['key']='backup'
        s['resources'][-1]['origins'].append(duplicate)
        nodes,edges=graph(s)
        self.assertEqual([e['target'] for e in edges if e['source']=='edge'],['lb'])
        self.assertFalse(any(r['kind']=='edge_origin' for r in nodes.values()))

    def test_origin_names_with_quotes_are_safe_native_identifiers(self):
        s=self.snapshot('external.example.invalid');s['resources'][-1]['origins'][0]['key']="origin's/key"
        d=prepare_display(s);xml=render(d);validate(xml,d)
        self.assertEqual(render(d),xml)

    def test_native_waf_is_outside_subnets_and_origin_data_is_redacted_from_shared_output(self):
        s=self.snapshot('external.example.invalid');d=prepare_display(s);xml=render(d);validate(xml,d)
        cells={c.get('id'):c for c in E.fromstring(xml).find('diagram').iter('mxCell')}
        self.assertEqual(cells['edge'].get('parent'),'layout-region');self.assertIn('edge-icon',cells)
        self.assertIn('external.example.invalid',xml)
        scene=make_scene(d,view='overview');self.assertNotIn('external.example.invalid',json.dumps(scene['request']))
        from oci_lenz.visual_review import masked_preview
        self.assertNotIn('external.example.invalid',masked_preview(xml,d,scene))
        redacted=render(prepare_display(s,redact=True));self.assertNotIn('external.example.invalid',redacted)
        self.assertEqual(render(d),xml)
