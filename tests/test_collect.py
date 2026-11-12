import unittest
from types import SimpleNamespace as N
from unittest.mock import patch
try:
    import oci
except ImportError: oci=None
from oci_lenz.collect import collect

@unittest.skipIf(oci is None,'install project OCI dependency to test SDK adapter')
class CollectorTests(unittest.TestCase):
    def run_collect(self,fail=None):
        def obj(id,**kw):return N(id=id,display_name=id,**kw)
        responses={
            'list_vcns':[obj('v')], 'list_subnets':[obj('s',vcn_id='v',prohibit_public_ip_on_vnic=True,route_table_id='rt')],
            'list_route_tables':[obj('rt',vcn_id='v',route_rules=[N(destination='0.0.0.0/0',network_entity_id='nat')])],
            'list_nat_gateways':[obj('nat',vcn_id='v')], 'list_instances':[obj('instance')],
            'list_vnic_attachments':[N(vnic_id='vn',instance_id='instance'),N(vnic_id='vn2',instance_id='instance')],
            'get_vnic':obj('vn',subnet_id='s',nsg_ids=[],private_ip_address='10.0.0.2'),
            'list_private_ips':[N(ip_address='10.0.0.2')],
            'list_load_balancers':[obj('lb',subnet_ids=['s'],network_security_group_ids=[])],
            'list_backend_sets':[N(name='set')], 'list_backends':[N(ip_address='10.0.0.2',port=80)]}
        calls=[]
        class Client:
            def __init__(self,*a,**kw):pass
            def __getattr__(self,name):
                assert name.startswith(('get_','list_','search_'))
                def call(*a,**kw):
                    calls.append(name)
                    if name==fail: raise oci.exceptions.ServiceError(403,'NotAuthorized',{},'sensitive error')
                    value=responses.get(name,[])
                    if name=='get_vnic': value=obj(a[0],subnet_id='s',nsg_ids=[],private_ip_address='10.0.0.2')
                    return N(data=value)
                return call
        with patch.object(oci.config,'from_file',return_value={'tenancy':'t','region':'r'}),patch.object(oci.identity,'IdentityClient',Client),patch.object(oci.core,'ComputeClient',Client),patch.object(oci.core,'VirtualNetworkClient',Client),patch.object(oci.load_balancer,'LoadBalancerClient',Client),patch.object(oci.resource_search,'ResourceSearchClient',Client),patch.object(oci.pagination,'list_call_get_all_results',side_effect=lambda fn,*a,**kw:fn(*a,**kw)):
            return collect('P','r','c'),calls
    def test_allowlist_secondary_vnics_and_zero_results(self):
        s,calls=self.run_collect()
        self.assertEqual(len([r for r in s['resources'] if r['kind']=='vnic']),2)
        self.assertTrue(any(c['status']=='ok' and c['count']==0 for c in s['coverage']))
        self.assertTrue(all(n.startswith(('get_','list_','search_')) for n in calls))
    def test_permission_failure_is_not_empty_success(self):
        s,_=self.run_collect('list_instances')
        result=next(c for c in s['coverage'] if c['api']=='list_instances')
        self.assertEqual(result['status'],'permission_denied');self.assertNotIn('count',result)
        self.assertNotIn('sensitive',str(s))

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
