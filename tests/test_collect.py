import unittest
from contextlib import ExitStack
from types import SimpleNamespace as N
from unittest.mock import patch
try:
    import oci
except ImportError: oci=None
from oci_lenz.collect import collect

@unittest.skipIf(oci is None,'install project OCI dependency to test SDK adapter')
class CollectorTests(unittest.TestCase):
    def run_collect(self,fail=None,primary_ip='10.0.0.2',extra=None,request_log=None):
        def obj(id,**kw):return N(id=id,display_name=id,**kw)
        responses={
            'get_tenancy':N(name='Synthetic Tenant',description='not-needed',freeform_tags={'private':'not-needed'}),
            'list_compartments':[N(id='c',name='Synthetic Project',description='not-needed'),N(id='other',name='Unselected Identity')],
            'get_compartment':N(id='c',name='Synthetic Project',description='not-needed'),
            'list_vcns':[oci.core.models.Vcn(id='v',compartment_id='c',cidr_blocks=['10.0.0.0/16'])], 'list_subnets':[oci.core.models.Subnet(id='s',vcn_id='v',prohibit_public_ip_on_vnic=True,route_table_id='rt',cidr_block='10.0.0.0/24')],
            'list_route_tables':[obj('rt',vcn_id='v',route_rules=[N(destination='0.0.0.0/0',network_entity_id='nat')])],
            'list_nat_gateways':[obj('nat',vcn_id='v')], 'list_instances':[obj('instance')],
            'list_network_security_groups':[oci.core.models.NetworkSecurityGroup(id='nsg',vcn_id='v')],
            'list_vnic_attachments':[N(vnic_id='vn',instance_id='instance'),N(vnic_id='vn2',instance_id='instance')],
            'list_private_ips':[N(ip_address='10.0.0.2')],
            'list_load_balancers':[oci.load_balancer.models.LoadBalancer(id='lb',subnet_ids=['s'],network_security_group_ids=[],ip_addresses=[oci.load_balancer.models.IpAddress(ip_address='192.0.2.20',is_public=True)])],
            'get_load_balancer':oci.load_balancer.models.LoadBalancer(id='lb',listeners={'https':oci.load_balancer.models.Listener(name='https',protocol='TCP',port=443,default_backend_set_name='set')}),
            'list_backend_sets':[N(name='set')], 'list_backends':[N(ip_address='10.0.0.2',port=80)]}
        responses.update(extra or {})
        calls=[]
        class Client:
            def __init__(self,*a,**kw):pass
            # The real SDK NSG list method accepts keyword arguments only.
            def list_network_security_groups(self,**kwargs):
                compartment_scope=kwargs['compartment_id']
                if compartment_scope!='c':raise ValueError('unexpected synthetic scope')
                return self.__getattr__('list_network_security_groups')(**kwargs)
            def list_drg_attachments(self,*args,**kwargs):
                assert kwargs.get('attachment_type')=='ALL'
                return self.__getattr__('list_drg_attachments')(*args,**kwargs)
            def __getattr__(self,name):
                assert name.removeprefix('mysql_').startswith(('get_','list_','search_'))
                def call(*a,**kw):
                    calls.append(name.removeprefix('mysql_'))
                    if request_log is not None:request_log.append((name,a,kw))
                    if name==fail: raise oci.exceptions.ServiceError(403,'NotAuthorized',{},'sensitive error')
                    value=responses.get(name,[])
                    if name=='get_vnic':
                        value=oci.core.models.Vnic(id=a[0],subnet_id='s',nsg_ids=[],private_ip=primary_ip,public_ip='192.0.2.10',is_primary=a[0]=='vn')
                        if extra and callable(extra.get('get_vnic')):value=extra['get_vnic'](a[0])
                    return N(data=value)
                return call
        class MysqlClient(Client):
            def __getattr__(self,name):
                return super().__getattr__('mysql_'+name)
        class NlbClient(Client):
            def __getattr__(self,name):
                # Keep service-specific List APIs distinct from classic LB.
                def run(*a,**kw):
                    key='nlb_'+name
                    if request_log is not None:request_log.append((key,a,kw))
                    if key==fail:raise oci.exceptions.ServiceError(403,'NotAuthorized',{},'sensitive error')
                    return N(data=responses.get(key,[]))
                return run
        class WafClient(Client):
            def __getattr__(self,name):
                def run(*a,**kw):
                    key='waf_'+name
                    if request_log is not None:request_log.append((key,a,kw))
                    if key==fail:raise oci.exceptions.ServiceError(403,'NotAuthorized',{},'sensitive error')
                    return N(data=responses.get(key,[]))
                return run
        class WaasClient(Client):
            def __getattr__(self,name):
                def run(*a,**kw):
                    key='waas_'+name
                    if request_log is not None:request_log.append((key,a,kw))
                    if key==fail:raise oci.exceptions.ServiceError(403,'NotAuthorized',{},'sensitive error')
                    return N(data=responses.get(key,[]))
                return run
        def data_client(prefix):
            class DataClient(Client):
                def __getattr__(self,name):
                    assert name.startswith(('list_','get_'))
                    def run(*a,**kw):
                        key=prefix+'_'+name
                        if request_log is not None:request_log.append((key,a,kw))
                        if key==fail:raise oci.exceptions.ServiceError(403,'NotAuthorized',{},'sensitive error')
                        return N(data=responses.get(key,[]))
                    return run
            return DataClient
        with ExitStack() as stack:
            for item in (patch.object(oci.container_engine,'ContainerEngineClient',data_client('oke')),patch.object(oci.file_storage,'FileStorageClient',data_client('fss')),patch.object(oci.functions,'FunctionsManagementClient',data_client('functions')),patch.object(oci.apigateway,'GatewayClient',data_client('apigw')),patch.object(oci.apigateway,'DeploymentClient',data_client('apideploy')),patch.object(oci.golden_gate,'GoldenGateClient',data_client('goldengate')),patch.object(oci.object_storage,'ObjectStorageClient',data_client('object_storage')),patch.object(oci.artifacts,'ArtifactsClient',data_client('artifacts')),patch.object(oci.devops,'DevopsClient',data_client('devops')),patch.object(oci.nosql,'NosqlClient',data_client('nosql')),patch.object(oci.redis,'RedisClusterClient',data_client('redis')),patch.object(oci.psql,'PostgresqlClient',data_client('psql')),patch.object(oci.opensearch,'OpensearchClusterClient',data_client('opensearch')),patch.object(oci.waas,'WaasClient',WaasClient),patch.object(oci.waf,'WafClient',WafClient),patch.object(oci.network_load_balancer,'NetworkLoadBalancerClient',NlbClient),patch.object(oci.mysql,'DbSystemClient',MysqlClient),patch.object(oci.config,'from_file',return_value={'tenancy':'t','region':'r'}),patch.object(oci.identity,'IdentityClient',Client),patch.object(oci.core,'ComputeClient',Client),patch.object(oci.database,'DatabaseClient',Client),patch.object(oci.core,'VirtualNetworkClient',Client),patch.object(oci.load_balancer,'LoadBalancerClient',Client),patch.object(oci.resource_search,'ResourceSearchClient',Client),patch.object(oci.pagination,'list_call_get_all_results',side_effect=lambda fn,*a,**kw:fn(*a,**kw)),):stack.enter_context(item)
            return collect('P','r','c'),calls
    def test_allowlist_secondary_vnics_and_zero_results(self):
        s,calls=self.run_collect()
        self.assertEqual(len([r for r in s['resources'] if r['kind']=='vnic']),2)
        self.assertTrue(any(c['status']=='ok' and c['count']==0 for c in s['coverage']))
        self.assertTrue(all(n.startswith(('get_','list_','search_')) for n in calls))
    def test_scope_names_are_allowlisted_without_identity_payload(self):
        s,calls=self.run_collect()
        self.assertEqual(s['scope']['tenancy_name'],'Synthetic Tenant')
        self.assertEqual(s['scope']['compartment_names'],{'c':'Synthetic Project'})
        self.assertNotIn('not-needed',str(s));self.assertNotIn('Unselected Identity',str(s));self.assertIn('get_tenancy',calls)
    def test_scoped_get_compartment_is_fallback_when_listing_is_denied(self):
        s,calls=self.run_collect('list_compartments')
        self.assertEqual(s['scope']['compartment_names'],{'c':'Synthetic Project'})
        self.assertIn('get_compartment',calls)
    def test_denied_tenancy_name_does_not_discard_inventory(self):
        s,_=self.run_collect('get_tenancy')
        self.assertFalse(s['scope'].get('tenancy_name'))
        self.assertTrue(s['resources'])
        self.assertEqual(next(c for c in s['coverage'] if c.get('api')=='get_tenancy')['status'],'permission_denied')
    def test_permission_failure_is_not_empty_success(self):
        s,_=self.run_collect('list_instances')
        result=next(c for c in s['coverage'] if c['api']=='list_instances')
        self.assertEqual(result['status'],'permission_denied');self.assertNotIn('count',result)
        self.assertNotIn('sensitive',str(s))
    def test_real_sdk_vnic_primary_ip_when_private_ip_listing_denied(self):
        s,_=self.run_collect('list_private_ips')
        vnics=[r for r in s['resources'] if r['kind']=='vnic']
        self.assertEqual(len(vnics),2)
        self.assertTrue(all(v['private_ips']==['10.0.0.2'] for v in vnics))
        coverage=[c for c in s['coverage'] if c.get('api')=='list_private_ips']
        self.assertTrue(all(c['status']=='permission_denied' for c in coverage))
    def test_real_sdk_vnic_missing_primary_ip_keeps_listed_ips(self):
        s,_=self.run_collect(primary_ip=None)
        self.assertTrue(all(r['private_ips']==['10.0.0.2'] for r in s['resources'] if r['kind']=='vnic'))
    def test_nsg_list_uses_keyword_compartment_and_keeps_resources(self):
        s,_=self.run_collect()
        coverage=next(c for c in s['coverage'] if c.get('api')=='list_network_security_groups')
        self.assertEqual(coverage['status'],'ok')
        self.assertEqual(coverage['count'],1)
        self.assertEqual([r['id'] for r in s['resources'] if r['kind']=='nsg'],['nsg'])
    def test_operational_addresses_and_network_cidrs_are_allowlisted(self):
        s,_=self.run_collect()
        resources={r['id']:r for r in s['resources']}
        self.assertEqual(resources['v']['cidr_blocks'],['10.0.0.0/16'])
        self.assertEqual(resources['v']['compartment_id'],'c')
        self.assertEqual(resources['s']['cidr_block'],'10.0.0.0/24')
        self.assertEqual(resources['vn']['public_ip'],'192.0.2.10')
        self.assertEqual(resources['lb']['ip_addresses'],[{'ip_address':'192.0.2.20','is_public':True}])

    def test_primary_vnic_and_listener_fields_use_actual_sdk_models(self):
        s,_=self.run_collect();resources={r['id']:r for r in s['resources']}
        self.assertTrue(resources['vn']['is_primary'])
        self.assertFalse(resources['vn2']['is_primary'])
        self.assertEqual(resources['vn']['primary_private_ip'],'10.0.0.2')
        self.assertEqual(resources['lb']['listeners'],[{'name':'https','protocol':'TCP','port':443,'default_backend_set_name':'set'}])

    def test_denied_listener_detail_keeps_lb_and_records_coverage(self):
        s,_=self.run_collect('get_load_balancer')
        lb=next(r for r in s['resources'] if r['kind']=='lb')
        self.assertEqual(lb['listeners'],[])
        self.assertEqual(next(c for c in s['coverage'] if c.get('api')=='get_load_balancer')['status'],'permission_denied')

@unittest.skipIf(oci is None,'install OCI SDK')
class PaginationTests(unittest.TestCase):
    def test_sdk_follows_next_page(self):
        seen=[]
        def api(**kwargs):
            seen.append(kwargs.get('page'))
            if not kwargs.get('page'):
                return oci.response.Response(200,{'opc-next-page':'next'},['one'],None)
            return oci.response.Response(200,{},['two'],None)
        self.assertEqual(oci.pagination.list_call_get_all_results(api).data,['one','two'])
        self.assertEqual(seen,[None,'next'])
