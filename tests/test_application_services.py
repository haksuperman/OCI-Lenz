"""File Storage, API Gateway and Functions are metadata-only configured relations."""
import copy,json,unittest
import xml.etree.ElementTree as E
from types import SimpleNamespace as N
from unittest.mock import Mock,patch
from tests import test_collect as fixtures
from oci_lenz.model import graph,sample
from oci_lenz.display import prepare_display
from oci_lenz.draw import render,validate,ICONS
oci=fixtures.oci

@unittest.skipIf(oci is None,'OCI SDK required')
class ApplicationServicesTests(unittest.TestCase):
    def responses(self):
        f,a,n=oci.file_storage.models,oci.apigateway.models,oci.functions.models
        return {'list_availability_domains':[N(name='Synthetic AD')],
          'fss_list_file_systems':[f.FileSystemSummary(id='fs',display_name='Synthetic File System',compartment_id='c',availability_domain='Synthetic AD',freeform_tags={'secret':'NEVER-STORE'})],
          'fss_list_mount_targets':[f.MountTargetSummary(id='mt',display_name='Synthetic Mount Target',compartment_id='c',subnet_id='s',export_set_id='es',private_ip_ids=['mt-ip'],nsg_ids=['nsg'])],
          'get_private_ip':oci.core.models.PrivateIp(id='mt-ip',ip_address='10.0.0.81'),
          'fss_list_exports':[f.ExportSummary(id='export',file_system_id='fs',export_set_id='es',path='/NEVER-STORE')],
          'functions_list_applications':[n.ApplicationSummary(id='app',display_name='Synthetic Application',compartment_id='c',subnet_ids=['s'],network_security_group_ids=['nsg'])],
          'functions_list_functions':[n.FunctionSummary(id='fn',display_name='Synthetic Function',application_id='app',compartment_id='c',invoke_endpoint='NEVER-STORE',freeform_tags={'secret':'NEVER-STORE'})],
          'apigw_list_gateways':a.GatewayCollection(items=[a.GatewaySummary(id='gateway',display_name='Synthetic API Gateway',compartment_id='c',subnet_id='s',network_security_group_ids=['nsg'],endpoint_type='PRIVATE')]),
          'apigw_get_gateway':a.Gateway(id='gateway',subnet_id='s',network_security_group_ids=['nsg'],endpoint_type='PRIVATE',ip_addresses=[a.IpAddress(ip_address='10.0.0.91')],hostname='NEVER-STORE'),
          'apideploy_list_deployments':a.DeploymentCollection(items=[a.DeploymentSummary(id='api-deploy',display_name='Synthetic API Deployment',gateway_id='gateway',compartment_id='c',endpoint='NEVER-STORE')]),
          'apideploy_get_deployment':a.Deployment(id='api-deploy',gateway_id='gateway',specification=a.ApiSpecification(routes=[
            a.ApiSpecificationRoute(path='/NEVER-STORE',backend=a.OracleFunctionBackend(function_id='fn')),
            a.ApiSpecificationRoute(path='/NEVER-STORE',backend=a.HTTPBackend(url='https://user:NEVER-STORE@10.0.0.2:8443/NEVER-STORE?token=NEVER-STORE'))]))}
    def collect(self,fail=None,extra=None):
        data=self.responses();data.update(extra or {});requests=[]
        s=fixtures.CollectorTests().run_collect(extra=data,fail=fail,request_log=requests)[0]
        return s,requests
    def test_scoped_minimal_fields_no_contents_config_or_credentials(self):
        s,req=self.collect();nodes,edges=graph(s)
        for key,kind in [('fs','file_system'),('mt','mount_target'),('export','file_export'),('app','functions_application'),('fn','function'),('gateway','api_gateway'),('api-deploy','api_deployment')]:
            self.assertEqual(nodes[key]['kind'],kind);self.assertEqual(nodes[key]['compartment_id'],'c')
        self.assertEqual(nodes['mt']['private_ips'],['10.0.0.81']);self.assertEqual(nodes['gateway']['private_ips'],['10.0.0.91'])
        self.assertNotIn('NEVER-STORE',json.dumps(s))
        for name,args,kw in req:
            if name.startswith(('fss_list_','apigw_list_','apideploy_list_','functions_list_applications')):self.assertEqual(kw['compartment_id'],'c')
        self.assertFalse(any(n in ('functions_get_application','functions_get_function','fss_get_export','fss_get_mount_target') for n,a,k in req))
        self.assertEqual(next(k['application_id'] for n,a,k in req if n=='functions_list_functions'),'app')
    def test_evidenced_file_export_and_application_gateway_relations(self):
        s,_=self.collect();nodes,edges=graph(s)
        expected=[('mt','export','mount_export'),('export','fs','file_system_id'),('fn','app','application_id'),('api-deploy','gateway','api_gateway_id'),('api-deploy','fn','api_backend'),('api-deploy','instance','api_backend')]
        for source,target,kind in expected:
            e=next(e for e in edges if (e['source'],e['target'],e['kind'])==(source,target,kind));self.assertTrue(e['evidence'])
        self.assertFalse(any(e['source']=='instance' and e['target'] in ('mt','fs') for e in edges))
    def test_native_labels_icons_actual_parents_redaction_and_replay(self):
        s,_=self.collect();original=copy.deepcopy(s);d=prepare_display(s);xml=render(d,detail_pages=True);validate(xml,d)
        cells={c.get('id'):c for c in E.fromstring(xml).find('diagram/mxGraphModel/root')}
        for key in ('mt','export','app','fn','gateway','api-deploy'):self.assertEqual(cells[key].get('parent'),'s')
        self.assertTrue(cells['fs'].get('parent').startswith('layout-compartment-'))
        for key in ('fs','mt','app','fn','gateway'):self.assertIn(key+'-icon',cells)
        self.assertEqual(ICONS['file_system'],10);self.assertEqual(ICONS['api_gateway'],79);self.assertEqual(ICONS['function'],2)
        self.assertNotIn('layout-osn',cells);self.assertEqual(render(d,detail_pages=True),xml);self.assertEqual(s,original)
        redacted=render(prepare_display(s,redact=True));self.assertNotIn('Synthetic Function',redacted);self.assertNotIn('10.0.0.91',redacted)
    def test_denied_and_empty_services_are_distinct_and_other_services_survive(self):
        for api in ('fss_list_file_systems','fss_list_mount_targets','fss_list_exports','functions_list_applications','functions_list_functions','apigw_list_gateways','apideploy_list_deployments'):
            s,_=self.collect(fail=api);entry=next(c for c in s['coverage'] if c.get('api')==api.split('_',1)[1] and c['service']==api.split('_',1)[0])
            self.assertEqual(entry['status'],'permission_denied');self.assertNotIn('count',entry)
            s,_=self.collect(extra={api:[]});entry=next(c for c in s['coverage'] if c.get('api')==api.split('_',1)[1] and c['service']==api.split('_',1)[0])
            self.assertEqual(entry['status'],'ok');self.assertEqual(entry['count'],0)
        s,_=self.collect(fail='apigw_get_gateway');self.assertEqual(graph(s)[0]['gateway']['subnet_id'],'s')
        s,_=self.collect(fail='apideploy_get_deployment');r=graph(s)[0]['api-deploy'];self.assertEqual(r['backends_status'],'unavailable');self.assertIn('fs',graph(s)[0])
    def test_ad_prerequisite_failure_does_not_claim_file_system_zero_and_exports_still_list(self):
        s,req=self.collect(fail='list_availability_domains')
        self.assertFalse(any(n in ('fss_list_file_systems','fss_list_mount_targets') for n,a,k in req))
        self.assertTrue(any(c['service']=='fss' and c.get('api')=='list_file_systems' and c['status']=='skipped' for c in s['coverage']))
        self.assertIn('export',graph(s)[0]);self.assertIn('unknown:fs',graph(s)[0])
    def test_multi_subnet_application_and_cross_compartment_references_are_not_inferred(self):
        s,_=self.collect();app=next(r for r in s['resources'] if r['id']=='app');app['subnet_ids']=['other-subnet','s']
        s['resources'].append({'id':'other-subnet','kind':'subnet','name':'Synthetic Shared Subnet','vcn_id':'v','compartment_id':'other'})
        nodes,edges=graph(s);self.assertEqual(sum(e['source']=='app' and e['kind']=='subnet_ids' for e in edges),2)
        self.assertFalse(any(e['source']=='fn' and e['kind']=='subnet_id' for e in edges))
        validate(render(prepare_display(s)),prepare_display(s))
        s['resources']=[r for r in s['resources'] if r['id'] not in ('app','gateway','fs')]
        nodes,edges=graph(s)
        for target in ('unknown:app','unknown:gateway','unknown:fs'):self.assertIn(target,nodes)
    def test_http_backend_ambiguity_outside_vcn_hostname_and_dynamic_selection(self):
        a=oci.apigateway.models
        backend=a.DynamicRoutingBackend(routing_backends=[a.DynamicRoutingTypeRoutingBackend(backend=a.OracleFunctionBackend(function_id='fn')),a.DynamicRoutingTypeRoutingBackend(backend=a.HTTPBackend(url='https://external.example.invalid/NEVER-STORE?secret=NEVER-STORE'))])
        detail=a.Deployment(id='api-deploy',specification=a.ApiSpecification(routes=[a.ApiSpecificationRoute(backend=backend)]))
        with patch('socket.getaddrinfo',side_effect=AssertionError('No DNS')):
            s,_=self.collect(extra={'apideploy_get_deployment':detail});nodes,edges=graph(s)
        self.assertNotIn('NEVER-STORE',json.dumps(s));self.assertTrue(any(e['source']=='api-deploy' and e['target']=='fn' for e in edges))
        self.assertTrue(any(e['source']=='api-deploy' and nodes[e['target']]['kind']=='unknown' for e in edges))
        s,_=self.collect();s['resources'].append({'id':'other-instance','kind':'compute','name':'Synthetic Other Instance'});s['resources'].append({'id':'duplicate-nic','kind':'vnic','name':'Synthetic Duplicate','subnet_id':'s','instance_id':'other-instance','private_ips':['10.0.0.2']})
        nodes,edges=graph(s);self.assertTrue(any(e['kind']=='api_backend' and nodes[e['target']]['kind']=='unknown' for e in edges))
    def test_mount_target_address_failure_and_ipv6_preserve_endpoint(self):
        s,_=self.collect(fail='get_private_ip');node=graph(s)[0]['mt']
        self.assertEqual(node['subnet_id'],'s');self.assertEqual(node['private_ips'],[])
        self.assertEqual(node['address_status'],'unavailable')
        data=self.responses();data['fss_list_mount_targets'][0].mount_target_ipv6_ids=['ip6']
        data['get_ipv6']=oci.core.models.Ipv6(id='ip6',ip_address='2001:db8::81')
        s,_=self.collect(extra=data);self.assertIn('2001:db8::81',graph(s)[0]['mt']['private_ips'])
    def test_private_backend_does_not_resolve_outside_gateway_vcn(self):
        from oci_lenz.application_services import api_backend_targets
        s,_=self.collect();nodes,_=graph(s);deployment=nodes['api-deploy']
        for r in s['resources']:
            if r['kind']=='vnic':r.update(subnet_id='outside-subnet',vcn_id='outside-vcn')
        targets=dict(api_backend_targets(deployment,s['resources']))
        self.assertNotIn('instance',targets)
        self.assertTrue(any(k.startswith('api-backend:') for k in targets))
        s,_=self.collect();nodes,_=graph(s);deployment=nodes['api-deploy']
        deployment['backends']=[{'type':'HTTP_BACKEND','host':'192.0.2.20'}]
        self.assertEqual(next(iter(dict(api_backend_targets(deployment,s['resources'])))),'lb')
    def test_unavailable_owner_places_tags_in_actual_compartment(self):
        s,_=self.collect();s['resources']=[r for r in s['resources'] if r['id'] not in ('app','gateway','mt')]
        display=prepare_display(s);xml=render(display);validate(xml,display)
        cells={c.get('id'):c for c in E.fromstring(xml).find('diagram/mxGraphModel/root')}
        for key in ('fn','api-deploy','export'):self.assertTrue(cells[key].get('parent').startswith('layout-compartment-'))
    def test_unknown_backend_type_is_reported_without_raw_fields(self):
        data=self.responses();data['apideploy_get_deployment'].specification.routes=[N(backend=N(type='UNKNOWN_BACKEND_ENUM_VALUE',password='NEVER-STORE'))]
        s,_=self.collect(extra=data)
        self.assertNotIn('NEVER-STORE',json.dumps(s));self.assertNotIn('UNKNOWN_BACKEND_ENUM_VALUE',json.dumps(s))
        self.assertTrue(any(c['service']=='apideploy' and c['status']=='unsupported' for c in s['coverage']))
    def test_generated_sdk_detail_methods_are_get_only(self):
        cases=[(oci.apigateway.GatewayClient,'get_gateway',{'gateway_id':'gateway'}),
               (oci.apigateway.DeploymentClient,'get_deployment',{'deployment_id':'deployment'}),
               (oci.core.VirtualNetworkClient,'get_private_ip',{'private_ip_id':'ip'}),
               (oci.core.VirtualNetworkClient,'get_ipv6',{'ipv6_id':'ip6'})]
        for cls,method,kwargs in cases:
            with self.subTest(method=method):
                client=cls.__new__(cls);client.retry_strategy=oci.retry.NoneRetryStrategy();client.circuit_breaker_callback=None
                client.base_client=Mock();client.base_client.get_preferred_retry_strategy.return_value=None;requests=[]
                def transport(**request):
                    requests.append(request);return oci.response.Response(200,{},N(),None)
                client.base_client.call_api=transport;getattr(client,method)(**kwargs)
                self.assertEqual(len(requests),1);self.assertEqual(requests[0]['method'],'GET')
                self.assertEqual(list(requests[0]['path_params'].values()),list(kwargs.values()))
    def test_generated_sdk_list_methods_paginate_get_only_with_explicit_scope(self):
        cases=[(oci.file_storage.FileStorageClient,'list_file_systems',dict(compartment_id='c',availability_domain='Synthetic AD'),lambda:[oci.file_storage.models.FileSystemSummary(id='a')]),
          (oci.file_storage.FileStorageClient,'list_mount_targets',dict(compartment_id='c',availability_domain='Synthetic AD'),lambda:[oci.file_storage.models.MountTargetSummary(id='a')]),
          (oci.file_storage.FileStorageClient,'list_exports',dict(compartment_id='c'),lambda:[oci.file_storage.models.ExportSummary(id='a')]),
          (oci.functions.FunctionsManagementClient,'list_applications',dict(compartment_id='c'),lambda:[oci.functions.models.ApplicationSummary(id='a')]),
          (oci.functions.FunctionsManagementClient,'list_functions',dict(application_id='app'),lambda:[oci.functions.models.FunctionSummary(id='a')]),
          (oci.apigateway.GatewayClient,'list_gateways',dict(compartment_id='c'),lambda:oci.apigateway.models.GatewayCollection(items=[oci.apigateway.models.GatewaySummary(id='a')])),
          (oci.apigateway.DeploymentClient,'list_deployments',dict(compartment_id='c'),lambda:oci.apigateway.models.DeploymentCollection(items=[oci.apigateway.models.DeploymentSummary(id='a')]))]
        for cls,method,kwargs,data in cases:
            with self.subTest(method=method):
                client=cls.__new__(cls);client.retry_strategy=oci.retry.NoneRetryStrategy();client.circuit_breaker_callback=None
                client.base_client=Mock();client.base_client.get_preferred_retry_strategy.return_value=None;pages=[]
                def transport(**request):
                    self.assertEqual(request['method'],'GET');q=request['query_params'];pages.append(q.get('page'))
                    self.assertEqual(q.get('compartmentId') or q.get('applicationId'),'c' if 'compartment_id' in kwargs else 'app')
                    return oci.response.Response(200,{'opc-next-page':'next'} if len(pages)==1 else {},data(),None)
                client.base_client.call_api=transport;rows=oci.pagination.list_call_get_all_results(getattr(client,method),**kwargs).data
                self.assertEqual(len(rows if isinstance(rows,list) else rows.items),2);self.assertEqual(pages,[None,'next'])
