"""Read-only Cache/PostgreSQL/OpenSearch infrastructure contracts, no live OCI."""
import copy,json,unittest
import xml.etree.ElementTree as E
from tests import test_collect as fixtures
from oci_lenz.model import sample,graph
from oci_lenz.display import prepare_display
from oci_lenz.architecture import make_scene
from oci_lenz.draw import render,validate

oci=fixtures.oci


@unittest.skipIf(oci is None,'OCI SDK required')
class ManagedDataTests(unittest.TestCase):
    def responses(self):
        r,p,o=oci.redis.models,oci.psql.models,oci.opensearch.models
        return {
            'redis_list_redis_clusters':r.RedisClusterCollection(items=[r.RedisClusterSummary(id='cache',display_name='Synthetic Cache',compartment_id='c',subnet_id='s',primary_endpoint_ip_address='10.0.0.41')]),
            'redis_get_redis_cluster':r.RedisCluster(id='cache',subnet_id='s',nsg_ids=['nsg'],primary_endpoint_ip_address='10.0.0.41',replicas_endpoint_ip_address='10.0.0.42',discovery_endpoint_ip_address='10.0.0.43',software_version='VALKEY_8_1',node_count=3,primary_fqdn='SECRET-DNS',freeform_tags={'secret':'NEVER-STORE'}),
            'psql_list_db_systems':p.DbSystemCollection(items=[p.DbSystemSummary(id='pg',display_name='Synthetic PostgreSQL',compartment_id='c')]),
            'psql_get_db_system':p.DbSystem(id='pg',network_details=p.NetworkDetails(subnet_id='s',nsg_ids=['nsg'],primary_db_endpoint_private_ip='10.0.0.51'),instance_count=2,db_version='16',admin_username='NEVER-STORE',description='NEVER-STORE'),
            'psql_get_connection_details':p.ConnectionDetails(ca_certificate='NEVER-STORE',primary_db_endpoint=p.Endpoint(ip_address='10.0.0.51',fqdn='SECRET-DNS',port=5432),reader_endpoint=p.Endpoint(ip_address='10.0.0.52'),instance_endpoints=[p.DbInstanceEndpoint(db_instance_id='pg-node',endpoint=p.Endpoint(ip_address='10.0.0.53'))]),
            'opensearch_list_opensearch_clusters':o.OpensearchClusterCollection(items=[o.OpensearchClusterSummary(id='search-cluster',display_name='Synthetic OpenSearch',compartment_id='c')]),
            'opensearch_get_opensearch_cluster':o.OpensearchCluster(id='search-cluster',subnet_id='s',vcn_id='v',nsg_id='nsg',opensearch_private_ip='10.0.0.61',opendashboard_private_ip='10.0.0.62',security_master_user_name='NEVER-STORE',security_master_user_password_hash='NEVER-STORE',opensearch_fqdn='SECRET-DNS',security_saml_config=None)}

    def collect(self,fail=None,extra=None,requests=None):
        data=self.responses();data.update(extra or {})
        return fixtures.CollectorTests().run_collect(extra=data,fail=fail,request_log=requests)[0]

    def test_network_fields_addresses_and_secret_allowlist(self):
        requests=[];s=self.collect(requests=requests);nodes,edges=graph(s)
        for key,kind,ip in [('cache','oci_cache','10.0.0.41'),('pg','postgresql_db_system','10.0.0.51'),('search-cluster','opensearch_cluster','10.0.0.61')]:
            self.assertEqual(nodes[key]['kind'],kind);self.assertEqual(nodes[key]['subnet_id'],'s')
            self.assertIn(ip,nodes[key]['private_ips']);self.assertEqual(nodes[key]['primary_private_ip'],ip)
            self.assertTrue(any(e['source']==key and e['target']=='s' and e['kind']=='subnet_id' for e in edges))
            self.assertTrue(any(e['source']==key and e['target']=='nsg' and e['kind']=='nsg_ids' for e in edges))
        self.assertTrue(any(e['source']=='pg' and e['evidence']=='DbSystem.network_details.subnet_id' for e in edges))
        self.assertTrue(any(e['source']=='search-cluster' and e['evidence']=='OpensearchCluster.nsg_id' for e in edges))
        encoded=json.dumps(s);self.assertNotIn('NEVER-STORE',encoded);self.assertNotIn('SECRET-DNS',encoded)
        for service,api in [('redis','list_redis_clusters'),('psql','list_db_systems'),('opensearch','list_opensearch_clusters')]:
            request=next((a,k) for n,a,k in requests if n==service+'_'+api)
            self.assertEqual(request[1].get('compartment_id') or request[0][0],'c')
        self.assertIn('10.0.0.53',nodes['pg']['private_ips'])

    def test_zero_success_and_denied_lists_are_distinct_for_all_services(self):
        for service,api in [('redis','list_redis_clusters'),('psql','list_db_systems'),('opensearch','list_opensearch_clusters')]:
            for fail,extra,status in [(None,{service+'_'+api:[]},'ok'),(service+'_'+api,{},'permission_denied')]:
                s=self.collect(fail=fail,extra=extra)
                c=next(c for c in s['coverage'] if c['service']==service and c.get('api')==api)
                self.assertEqual(c['status'],status)
                if status=='ok':self.assertEqual(c['count'],0)
                else:self.assertNotIn('count',c)

    def test_denied_details_keep_resources_and_never_infer_missing_subnet(self):
        for service,api,key in [('redis','get_redis_cluster','cache'),('psql','get_db_system','pg'),('opensearch','get_opensearch_cluster','search-cluster')]:
            s=self.collect(fail=service+'_'+api);nodes,edges=graph(s)
            self.assertIn(key,nodes);self.assertEqual(nodes[key]['detail_status'],'unavailable')
            if service=='redis':self.assertEqual(nodes[key]['subnet_id'],'s')
            else:self.assertFalse(nodes[key].get('subnet_id'))
            self.assertNotIn('sensitive error',json.dumps(s))

    def test_denied_postgres_connection_keeps_observed_primary_address(self):
        s=self.collect(fail='psql_get_connection_details');n=graph(s)[0]['pg']
        self.assertEqual(n['private_ips'],['10.0.0.51'])
        self.assertTrue(any(c.get('api')=='get_connection_details' and c['status']=='permission_denied' for c in s['coverage']))

    def test_subnet_resolution_uses_ids_across_selected_compartments(self):
        s=self.collect();s['resources']=[r for r in s['resources'] if r['id']!='s']
        self.assertIn('unknown:s',graph(s)[0])
        s['resources'].append({'id':'s','kind':'subnet','name':'Synthetic shared network','vcn_id':'v','compartment_id':'other'})
        self.assertNotIn('unknown:s',graph(s)[0])
        scene=make_scene(prepare_display(s),view='overview')
        for key in ('cache','pg','search-cluster'):
            self.assertEqual(scene['items'][scene['aliases'][key]]['parent'],scene['aliases']['s'])

    def test_native_editable_output_redaction_and_replay(self):
        s=self.collect();original=copy.deepcopy(s);display=prepare_display(s);xml=render(display);validate(xml,display)
        cells={c.get('id'):c for c in E.fromstring(xml).find('diagram/mxGraphModel/root')}
        for key in ('cache','pg','search-cluster'):
            self.assertEqual(cells[key].get('parent'),'s');self.assertIn('ociNativeLabel=1;',cells[key].get('style'))
        self.assertIn('pg-icon',cells);self.assertIn('search-cluster-icon',cells)
        self.assertIn('cache-icon',cells)
        self.assertIn('Cache reuse per Oracle reference',cells['cache-icon'].get('ociOfficialIcon',''))
        self.assertIn('Oracle OCI Toolkit v24.2 PostgreSQL',cells['pg-icon'].get('ociOfficialIcon',''))
        scene=make_scene(display,view='overview')
        self.assertEqual(scene['items'][scene['aliases']['cache']]['representation'],'icon_label')
        self.assertEqual(render(display),xml);self.assertEqual(s,original)
        redacted=render(prepare_display(s,redact=True))
        self.assertNotIn('10.0.0.41',redacted);self.assertNotIn('Synthetic PostgreSQL',redacted)

    def test_backend_ip_resolution_requires_unique_same_vcn_observation(self):
        for kind in ('oci_cache','postgresql_db_system','opensearch_cluster'):
            s=sample();s['resources'].append({'id':'endpoint','kind':kind,'name':'Synthetic endpoint','subnet_id':'private','private_ips':['10.0.1.90']})
            next(r for r in s['resources'] if r['kind']=='backend_set')['backends']=[{'ip_address':'10.0.1.90','port':1234}]
            edge=next(e for e in graph(s)[1] if e['kind']=='backend')
            self.assertEqual(edge['target'],'endpoint')
            self.assertIn('same-VCN',edge['evidence'])
            s['resources'].append({'id':'duplicate','kind':kind,'name':'Synthetic duplicate','subnet_id':'private','private_ips':['10.0.1.90']})
            self.assertTrue(next(e['target'] for e in graph(s)[1] if e['kind']=='backend').startswith('unknown:'))
            s['resources'].pop();s['resources'][-1]['subnet_id']='unobserved-subnet'
            self.assertTrue(next(e['target'] for e in graph(s)[1] if e['kind']=='backend').startswith('unknown:'))

    def test_postgres_actual_connection_primary_takes_precedence_and_invalid_ips_are_ignored(self):
        p=oci.psql.models;r=oci.redis.models
        s=self.collect(extra={'psql_get_connection_details':p.ConnectionDetails(primary_db_endpoint=p.Endpoint(ip_address='2001:db8::5')),
                              'redis_get_redis_cluster':r.RedisCluster(id='cache',subnet_id='s',primary_endpoint_ip_address='not-an-ip.example.invalid',discovery_endpoint_ip_address='2001:db8::8')})
        nodes=graph(s)[0]
        self.assertEqual(nodes['pg']['primary_private_ip'],'2001:db8::5')
        self.assertNotIn('10.0.0.51',nodes['pg']['private_ips'])
        self.assertNotIn('not-an-ip.example.invalid',json.dumps(s))
        self.assertIn('2001:db8::8',nodes['cache']['private_ips'])

    def test_real_generated_sdk_methods_paginate_collection_wrappers(self):
        from unittest.mock import Mock
        from oci_lenz.managed_data import collect_managed_data
        clients={};requests=[];resources=[]
        for service,cls in [('redis',oci.redis.RedisClusterClient),('psql',oci.psql.PostgresqlClient),('opensearch',oci.opensearch.OpensearchClusterClient)]:
            client=cls.__new__(cls);client.retry_strategy=oci.retry.NoneRetryStrategy();client.circuit_breaker_callback=None
            client.base_client=Mock();client.base_client.get_preferred_retry_strategy.return_value=None
            def transport(service=service,**request):
                self.assertEqual(request['method'],'GET');name=request['operation_name'];requests.append((service,name))
                if name.startswith('list_'):
                    query=request['query_params'];self.assertEqual(query['compartmentId'],'synthetic-compartment')
                    suffix='b' if query.get('page') else 'a'
                    namespace=getattr(oci,service).models
                    collection,summary={'redis':('RedisClusterCollection','RedisClusterSummary'),'psql':('DbSystemCollection','DbSystemSummary'),'opensearch':('OpensearchClusterCollection','OpensearchClusterSummary')}[service]
                    data=getattr(namespace,collection)(items=[getattr(namespace,summary)(id=service+'-'+suffix,display_name='Synthetic '+service)])
                    headers={} if query.get('page') else {'opc-next-page':'synthetic-next'}
                else:
                    paths=request['path_params'];self.assertTrue(any(str(v).startswith(service+'-') for v in paths.values()))
                    headers={}
                    if service=='redis':data=oci.redis.models.RedisCluster(subnet_id='s',primary_endpoint_ip_address='10.0.0.41')
                    elif service=='opensearch':data=oci.opensearch.models.OpensearchCluster(subnet_id='s',opensearch_private_ip='10.0.0.61')
                    elif name=='get_db_system':data=oci.psql.models.DbSystem(network_details=oci.psql.models.NetworkDetails(subnet_id='s'))
                    else:data=oci.psql.models.ConnectionDetails(primary_db_endpoint=oci.psql.models.Endpoint(ip_address='10.0.0.51'))
                return oci.response.Response(200,headers,data,None)
            client.base_client.call_api=transport;clients[service]=client
        def call(service,api,**kwargs):
            fn=getattr(clients[service],api)
            data=(oci.pagination.list_call_get_all_results(fn,**kwargs) if api.startswith('list_') else fn(**kwargs)).data
            return data if not api.startswith('list_') or isinstance(data,list) else data.items
        def add(obj,kind,**fields):resources.append(dict(id=obj.id,name=obj.display_name,kind=kind,**fields))
        collect_managed_data(call,add,'synthetic-compartment')
        self.assertEqual(len(resources),6)
        for service,api in [('redis','list_redis_clusters'),('psql','list_db_systems'),('opensearch','list_opensearch_clusters')]:
            self.assertEqual(requests.count((service,api)),2)
