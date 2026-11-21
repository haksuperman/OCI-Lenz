"""GoldenGate infrastructure is observed, never a guessed replication flow."""
import copy,json,unittest
import xml.etree.ElementTree as E
from unittest.mock import Mock
from tests import test_collect as fixtures
from oci_lenz.model import graph
from oci_lenz.display import prepare_display
from oci_lenz.architecture import make_scene
from oci_lenz.draw import render,validate,ICONS

oci=fixtures.oci

@unittest.skipIf(oci is None,'OCI SDK required')
class GoldenGateTests(unittest.TestCase):
    def responses(self):
        m=oci.golden_gate.models
        return {'goldengate_list_deployments':m.DeploymentCollection(items=[m.DeploymentSummary(
            id='gg',display_name='Synthetic GoldenGate',compartment_id='c',subnet_id='s',
            private_ip_address='10.0.0.71',public_ip_address='192.0.2.71',is_public=True,
            load_balancer_subnet_id='unqueried-frontend',load_balancer_id='unqueried-lb',
            deployment_url='NEVER-STORE',fqdn='NEVER-STORE',freeform_tags={'private':'NEVER-STORE'})]),
            'goldengate_get_deployment':m.Deployment(id='gg',subnet_id='s',nsg_ids=['nsg'],
                private_ip_address='10.0.0.71',public_ip_address='192.0.2.71',is_public=True,
                ogg_data=m.OggDeployment(deployment_name='NEVER-STORE',admin_username='NEVER-STORE'),
                description='NEVER-STORE',deployment_url='NEVER-STORE',fqdn='NEVER-STORE')}
    def collect(self,fail=None,extra=None):
        data=self.responses();data.update(extra or {});requests=[]
        return fixtures.CollectorTests().run_collect(extra=data,fail=fail,request_log=requests)[0],requests
    def test_allowlisted_network_metadata_and_exact_api_evidence(self):
        s,requests=self.collect();nodes,edges=graph(s);r=nodes['gg']
        self.assertEqual(r['kind'],'goldengate_deployment');self.assertEqual(r['compartment_id'],'c')
        self.assertEqual(r['private_ips'],['10.0.0.71']);self.assertEqual(r['public_ip'],'192.0.2.71')
        self.assertEqual(r['subnet_id'],'s');self.assertEqual(r['nsg_ids'],['nsg']);self.assertEqual(r['nsg_status'],'ok')
        evidence={e['kind']:e['evidence'] for e in edges if e['source']=='gg'}
        self.assertEqual(evidence,{'subnet_id':'Deployment.subnet_id','nsg_ids':'Deployment.nsg_ids[]'})
        self.assertNotIn('NEVER-STORE',json.dumps(s));self.assertNotIn('unqueried-',json.dumps(s))
        calls=[(n,a,k) for n,a,k in requests if n.startswith('goldengate_')]
        self.assertEqual([c[0] for c in calls],['goldengate_list_deployments','goldengate_get_deployment'])
        self.assertEqual(calls[0][2],{'compartment_id':'c'});self.assertEqual(calls[1][2],{'deployment_id':'gg'})
    def test_zero_denied_and_failed_are_not_conflated(self):
        for fail,extra,status in [(None,{'goldengate_list_deployments':[]},'ok'),('goldengate_list_deployments',{},'permission_denied')]:
            s,_=self.collect(fail=fail,extra=extra);c=next(c for c in s['coverage'] if c['service']=='goldengate')
            self.assertEqual(c['status'],status)
            if status=='ok':self.assertEqual(c['count'],0)
            else:self.assertNotIn('count',c)
    def test_detail_denial_keeps_summary_and_marks_nsg_unavailable(self):
        s,_=self.collect(fail='goldengate_get_deployment');r=graph(s)[0]['gg']
        self.assertEqual(r['subnet_id'],'s');self.assertEqual(r['private_ips'],['10.0.0.71'])
        self.assertEqual(r['detail_status'],'unavailable');self.assertEqual(r['nsg_status'],'unavailable')
        self.assertEqual(r['public_ip'],'192.0.2.71');self.assertNotIn('sensitive error',json.dumps(s))
        self.assertEqual(next(e['evidence'] for e in graph(s)[1] if e['source']=='gg'),'DeploymentSummary.subnet_id')
        self.assertTrue(any(c['api']=='get_deployment' and c['status']=='permission_denied' and c['request_scope']=={'deployment_id':'gg'} for c in s['coverage']))
    def test_native_icon_caption_parent_redaction_and_exact_replay(self):
        s,_=self.collect();original=copy.deepcopy(s);d=prepare_display(s);xml=render(d,detail_pages=True);validate(xml,d)
        cells={c.get('id'):c for c in E.fromstring(xml).find('diagram/mxGraphModel/root')}
        self.assertEqual(cells['gg'].get('parent'),'s');self.assertIn('gg-icon',cells)
        self.assertEqual(ICONS['goldengate_deployment'],51)
        self.assertIn('Synthetic GoldenGate',cells['gg'].get('value'));self.assertIn('192.0.2.71',cells['gg'].get('value'))
        self.assertIn('ociNativeLabel=1;',cells['gg'].get('style'))
        self.assertEqual(xml,render(d,detail_pages=True));self.assertEqual(s,original)
        scene=make_scene(d,view='overview');request=json.dumps(scene['request'])
        for value in ('Synthetic GoldenGate','10.0.0.71','192.0.2.71'):self.assertNotIn(value,request)
        redacted=render(prepare_display(s,redact=True))
        for value in ('Synthetic GoldenGate','10.0.0.71','192.0.2.71'):self.assertNotIn(value,redacted)
    def test_missing_or_cross_compartment_subnet_is_resolved_only_by_id(self):
        s,_=self.collect();s['resources']=[r for r in s['resources'] if r['id']!='s']
        self.assertIn('unknown:s',graph(s)[0])
        s['resources'].append({'id':'s','kind':'subnet','name':'Synthetic Shared Subnet','vcn_id':'v','compartment_id':'other'})
        self.assertNotIn('unknown:s',graph(s)[0]);d=prepare_display(s);xml=render(d);validate(xml,d)
        cells={c.get('id'):c for c in E.fromstring(xml).find('diagram/mxGraphModel/root')}
        self.assertEqual(cells['gg'].get('parent'),'s')
    def test_observed_private_endpoint_resolves_backend_only_when_unique_in_same_vcn(self):
        s,_=self.collect();bs=next(r for r in s['resources'] if r['kind']=='backend_set');bs['backends']=[{'ip_address':'10.0.0.71','port':443}]
        n,e=graph(s);edge=next(e for e in e if e['kind']=='backend')
        self.assertEqual(edge['target'],'gg');self.assertIn('Deployment.private_ip_address',edge['evidence'])
        duplicate=copy.deepcopy(next(r for r in s['resources'] if r['id']=='gg'));duplicate['id']='gg2';s['resources'].append(duplicate)
        n,e=graph(s);edge=next(e for e in e if e['kind']=='backend');self.assertEqual(n[edge['target']]['kind'],'unknown')
        s['resources']=[r for r in s['resources'] if r['id']!='gg2'];next(r for r in s['resources'] if r['id']=='gg')['subnet_id']='outside'
        n,e=graph(s);edge=next(e for e in e if e['kind']=='backend');self.assertEqual(n[edge['target']]['kind'],'unknown')
    def test_missing_endpoint_never_uses_public_frontend_subnet_or_dns(self):
        m=oci.golden_gate.models
        s,_=self.collect(extra={'goldengate_list_deployments':m.DeploymentCollection(items=[m.DeploymentSummary(id='gg',display_name='Synthetic GoldenGate',compartment_id='c',load_balancer_subnet_id='s',fqdn='private.example.invalid')]),'goldengate_get_deployment':m.Deployment(id='gg',nsg_ids=[],private_ip_address='not-an-ip.example.invalid',public_ip_address='not-an-ip.example.invalid')})
        r=graph(s)[0]['gg'];self.assertIsNone(r['subnet_id']);self.assertEqual(r['private_ips'],[])
        self.assertIsNone(r['public_ip']);self.assertEqual(r['network_status'],'not_reported');self.assertEqual(r['nsg_status'],'ok')
        self.assertFalse(any(e['source']=='gg' for e in graph(s)[1]))
        self.assertNotIn('example.invalid',json.dumps(s))

    def test_sdk_list_pagination_and_detail_requests_are_get(self):
        client=oci.golden_gate.GoldenGateClient.__new__(oci.golden_gate.GoldenGateClient)
        client.retry_strategy=oci.retry.NoneRetryStrategy();client.circuit_breaker_callback=None
        client.base_client=Mock();client.base_client.get_preferred_retry_strategy.return_value=None
        pages=[];gets=[]
        def transport(**request):
            self.assertEqual(request['method'],'GET')
            if request['operation_name']=='list_deployments':
                q=request['query_params'];self.assertEqual(q['compartmentId'],'c');pages.append(q.get('page'))
                return oci.response.Response(200,{'opc-next-page':'next'} if len(pages)==1 else {},oci.golden_gate.models.DeploymentCollection(items=[oci.golden_gate.models.DeploymentSummary(id='gg'+str(len(pages)))]),None)
            self.assertEqual(request['operation_name'],'get_deployment');gets.append(request['path_params']['deploymentId'])
            return oci.response.Response(200,{},oci.golden_gate.models.Deployment(id=gets[-1]),None)
        client.base_client.call_api=transport
        result=oci.pagination.list_call_get_all_results(client.list_deployments,compartment_id='c').data
        rows=result if isinstance(result,list) else result.items
        for r in rows:client.get_deployment(deployment_id=r.id)
        self.assertEqual(pages,[None,'next']);self.assertEqual(gets,['gg1','gg2'])
