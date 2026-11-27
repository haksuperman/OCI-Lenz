"""OKE is represented by its observed network endpoint, not invented K8s traffic."""
import copy,json,unittest
import xml.etree.ElementTree as E
from types import SimpleNamespace as N
from unittest.mock import Mock
from tests import test_collect as fixtures
from oci_lenz.display import prepare_display
from oci_lenz.draw import render,validate,ICONS
from oci_lenz.model import graph,sample
from oci_lenz.architecture import make_scene
from oci_lenz.oke import endpoint_ip,network_parent
oci=fixtures.oci


@unittest.skipIf(oci is None,'OCI SDK required')
class OkeTests(unittest.TestCase):
    def data(self):
        m=oci.container_engine.models
        config=m.ClusterEndpointConfig(subnet_id='s',nsg_ids=['nsg'],is_public_ip_enabled=True)
        endpoints=m.ClusterEndpoints(private_endpoint='https://10.0.0.90:6443',public_endpoint='192.0.2.90:6443')
        pod=m.OciVcnIpNativeNodePoolPodNetworkOptionDetails(pod_subnet_ids=['s'],pod_nsg_ids=['nsg'])
        nc=m.NodePoolNodeConfigDetails(placement_configs=[m.NodePoolPlacementConfigDetails(subnet_id='s')],node_pool_pod_network_option_details=pod)
        return {'list_subnets':[oci.core.models.Subnet(id='s',vcn_id='v',prohibit_public_ip_on_vnic=False,route_table_id='rt',cidr_block='10.0.0.0/24')],
                'oke_list_clusters':[m.ClusterSummary(id='oke',name='Synthetic OKE',compartment_id='c',vcn_id='v',endpoint_config=config,endpoints=endpoints)],
                'oke_get_cluster':m.Cluster(id='oke',name='Synthetic OKE',compartment_id='c',vcn_id='v',endpoint_config=config,endpoints=endpoints,freeform_tags={'secret':'NEVER-STORE'},open_id_connect_discovery_endpoint='NEVER-STORE'),
                'oke_list_node_pools':[m.NodePoolSummary(id='pool',name='Synthetic pool',cluster_id='oke',compartment_id='c',node_config_details=nc)],
                'oke_get_node_pool':m.NodePool(id='pool',name='Synthetic pool',cluster_id='oke',compartment_id='c',node_config_details=nc,nodes=[m.Node(id='instance',subnet_id='s',private_ip='10.0.0.2')],ssh_public_key='NEVER-STORE',node_metadata={'secret':'NEVER-STORE'})}

    def collect(self,fail=None,changes=None):
        data=self.data();data.update(changes or {});req=[]
        s=fixtures.CollectorTests().run_collect(extra=data,fail=fail,request_log=req)[0]
        return s,req

    def test_allowlisted_network_collection_reuses_workers_and_records_scope(self):
        s,req=self.collect();nodes,edges=graph(s);r=nodes['oke']
        self.assertEqual(r['kind'],'oke_cluster');self.assertEqual(r['subnet_id'],'s')
        self.assertEqual(r['private_ips'],['10.0.0.90']);self.assertEqual(r['public_ip'],'192.0.2.90')
        self.assertEqual(nodes['instance']['oke_cluster_ids'],['oke'])
        self.assertEqual(nodes['s']['oke_pod_cluster_ids'],['oke'])
        self.assertEqual(sum(r['kind']=='compute' for r in s['resources']),1)
        self.assertNotIn('NEVER-STORE',json.dumps(s))
        self.assertFalse(any(c['service']=='oke' and c['status']=='unsupported' for c in s['coverage']))
        self.assertTrue(any('Cluster.endpoint_config.subnet_id' in e['evidence'] for e in edges if e['source']=='oke'))
        pool_call=next(k for n,a,k in req if n=='oke_list_node_pools')
        self.assertEqual(pool_call,dict(compartment_id='c',cluster_id='oke'))
        self.assertFalse(any(e['source']=='oke' and e['target']=='instance' for e in edges))

    def test_detail_failure_retains_summary_and_status(self):
        s,_=self.collect(fail='oke_get_cluster');r=next(r for r in s['resources'] if r['kind']=='oke_cluster')
        self.assertEqual(r['detail_status'],'unavailable');self.assertEqual(r['subnet_id'],'s')
        self.assertIn('ClusterSummary.endpoint_config.subnet_id',r['network_evidence']['subnet_id'])
        self.assertTrue(any(c['service']=='oke' and c['status']=='permission_denied' for c in s['coverage']))

    def test_partial_detail_retains_summary_fields_without_overwriting_explicit_empty(self):
        data=self.data();detail=data['oke_get_cluster']
        detail.endpoint_config=oci.container_engine.models.ClusterEndpointConfig(nsg_ids=[])
        detail.endpoints=oci.container_engine.models.ClusterEndpoints(public_endpoint='192.0.2.91:6443')
        s,_=self.collect(changes=data);r=next(r for r in s['resources'] if r['kind']=='oke_cluster')
        self.assertEqual(r['subnet_id'],'s');self.assertEqual(r['private_ips'],['10.0.0.90'])
        self.assertEqual(r['nsg_ids'],[]);self.assertEqual(r['public_ip'],'192.0.2.91')
        self.assertIn('ClusterSummary',r['network_evidence']['subnet_id'])
        self.assertEqual(r['network_evidence']['nsg_ids'],'Cluster.endpoint_config.nsg_ids[]')

    def test_zero_and_denied_cluster_list_are_distinct(self):
        for fail,status in [(None,'ok'),('oke_list_clusters','permission_denied')]:
            s,req=self.collect(fail=fail,changes={'oke_list_clusters':[]})
            entry=next(c for c in s['coverage'] if c['service']=='oke' and c['api']=='list_clusters')
            self.assertEqual(entry['status'],status)
            if fail is None:self.assertEqual(entry['count'],0)
            self.assertFalse(any(n=='oke_list_node_pools' for n,a,k in req))

    def test_node_pool_failure_does_not_drop_cluster_or_invent_workers(self):
        for api in ('oke_list_node_pools','oke_get_node_pool'):
            with self.subTest(api=api):
                s,_=self.collect(fail=api);self.assertTrue(any(r['kind']=='oke_cluster' for r in s['resources']))
                self.assertEqual(sum(r['kind']=='compute' for r in s['resources']),1)

    def test_endpoint_parser_only_returns_ip_never_host_or_credentials(self):
        for value,expected in [('https://10.0.0.9:6443','10.0.0.9'),('[2001:db8::9]:6443','2001:db8::9'),('2001:db8::9','2001:db8::9'),('https://cluster.example:6443',None),('https://user:secret@10.0.0.9',None),('bad',None)]:
            with self.subTest(value=value):self.assertEqual(endpoint_ip(value),expected)

    def test_official_icon_and_endpoint_label_in_real_subnet(self):
        s,_=self.collect();before=copy.deepcopy(s);safe=prepare_display(s);xml=render(safe);validate(xml,safe)
        cells={c.get('id'):c for c in E.fromstring(xml).find('diagram/mxGraphModel/root')}
        self.assertEqual(ICONS['oke_cluster'],74);self.assertEqual(cells['oke'].get('parent'),'s')
        self.assertIn('Container Engine for Kubernetes',cells['oke-icon'].get('ociOfficialIcon'))
        self.assertIn('OKE API Endpoint',cells['oke'].get('value'));self.assertIn('10.0.0.90',cells['oke'].get('value'))
        self.assertEqual(s,before)
        self.assertNotIn('Synthetic OKE',json.dumps(make_scene(safe,view='overview')['request']))
        redacted=render(prepare_display(s,redact=True))
        self.assertNotIn('10.0.0.90',redacted);self.assertNotIn('Synthetic OKE',redacted)

    def test_missing_subnet_falls_back_to_known_vcn_then_compartment(self):
        s,_=self.collect();r=next(r for r in s['resources'] if r['kind']=='oke_cluster');r['subnet_id']='unseen-subnet'
        self.assertEqual(network_parent(r,{v['id']:v for v in s['resources']}),'v')
        for remove,expected in [(False,'v'),(True,'layout-compartment-0')]:
            candidate=copy.deepcopy(s)
            if remove:candidate['resources']=[v for v in candidate['resources'] if v['kind'] not in ('vcn','subnet')]
            safe=prepare_display(candidate);xml=render(safe);validate(xml,safe)
            c=E.fromstring(xml).find("diagram/mxGraphModel/root/mxCell[@id='oke']")
            self.assertEqual(c.get('parent'),expected);self.assertIn('OKE Cluster',c.get('value'))

    def test_conflicting_vcn_never_places_endpoint_in_wrong_subnet(self):
        s,_=self.collect();r=next(r for r in s['resources'] if r['kind']=='oke_cluster');r['vcn_id']='other-vcn'
        self.assertIsNone(network_parent(r,{v['id']:v for v in s['resources']}))
        safe=prepare_display(s);xml=render(safe);validate(xml,safe)
        c=E.fromstring(xml).find("diagram/mxGraphModel/root/mxCell[@id='oke']")
        self.assertTrue(c.get('parent').startswith('layout-compartment-'))

    def test_conflicting_cluster_detail_uses_summary_without_persisting_foreign_data(self):
        data=self.data();data['oke_get_cluster'].compartment_id='outside'
        data['oke_get_cluster'].vcn_id='foreign-vcn'
        s,_=self.collect(changes=data);r=next(r for r in s['resources'] if r['kind']=='oke_cluster')
        self.assertEqual(r['vcn_id'],'v');self.assertEqual(r['detail_status'],'unavailable')
        self.assertNotIn('foreign-vcn',json.dumps(s))
        self.assertTrue(any(c.get('reason')=='response_identity_or_scope_mismatch' for c in s['coverage']))

    def test_endpoint_cannot_be_reparented_to_an_unrelated_subnet(self):
        s,_=self.collect();safe=prepare_display(s);doc=E.fromstring(render(safe))
        c=doc.find("diagram/mxGraphModel/root/mxCell[@id='oke']");c.set('parent','v')
        with self.assertRaisesRegex(ValueError,'OKE endpoint anchor'):validate(E.tostring(doc,encoding='unicode'),safe)

    def test_outside_or_conflicting_pool_does_not_mark_local_network(self):
        for field,value in [('compartment_id','outside'),('cluster_id','outside')]:
            data=self.data();setattr(data['oke_get_node_pool'],field,value)
            s,_=self.collect(changes=data);nodes,_=graph(s)
            self.assertFalse(nodes['s'].get('oke_pod_cluster_ids'));self.assertFalse(nodes['instance'].get('oke_cluster_ids'))
            self.assertTrue(any(c.get('reason')=='response_identity_or_scope_mismatch' for c in s['coverage']))

    def test_cross_compartment_pod_subnet_marks_only_exact_same_vcn_reference(self):
        s,_=self.collect();r=next(r for r in s['resources'] if r['kind']=='oke_cluster')
        r['node_pool_networks'][0]['pod_subnet_ids']=['shared-pod','other-vcn-pod']
        s['resources'].extend([dict(id='shared-pod',kind='subnet',name='Synthetic Shared Pod Subnet',vcn_id='v',compartment_id='other',cidr_block='10.1.0.0/24'),
                               dict(id='other-vcn-pod',kind='subnet',name='Synthetic Other Network',vcn_id='other',cidr_block='10.2.0.0/24')])
        before=copy.deepcopy(s);display=prepare_display(s);nodes={r['id']:r for r in display['resources']}
        self.assertIn('OKE Pod network',nodes['shared-pod']['summary_details'])
        self.assertFalse(nodes['other-vcn-pod'].get('oke_pod_cluster_ids'));self.assertEqual(s,before)

    def test_flannel_does_not_invent_a_pod_subnet(self):
        data=self.data();nc=data['oke_get_node_pool'].node_config_details
        nc.node_pool_pod_network_option_details=oci.container_engine.models.FlannelOverlayNodePoolPodNetworkOptionDetails()
        s,_=self.collect(changes=data);r=next(r for r in s['resources'] if r['kind']=='oke_cluster')
        self.assertEqual(r['node_pool_networks'][0]['pod_subnet_ids'],[])
        self.assertFalse(next(r for r in s['resources'] if r['id']=='s').get('oke_pod_cluster_ids'))

    def test_fallback_icon_keeps_observed_ip_only_in_information_index(self):
        s,_=self.collect();r=next(r for r in s['resources'] if r['kind']=='oke_cluster');r['subnet_id']='outside'
        safe=prepare_display(s);xml=render(safe);validate(xml,safe)
        c=E.fromstring(xml).find("diagram/mxGraphModel/root/mxCell[@id='oke']")
        self.assertNotIn('10.0.0.90',c.get('value'));self.assertIn('10.0.0.90',xml)

    def test_sdk_get_and_paginated_list_are_read_only(self):
        m=oci.container_engine.models
        cases=[('list_clusters',dict(compartment_id='c'),[m.ClusterSummary(id='oke')]),
               ('list_node_pools',dict(compartment_id='c',cluster_id='oke'),[m.NodePoolSummary(id='pool')]),
               ('get_cluster',dict(cluster_id='oke'),m.Cluster(id='oke')),
               ('get_node_pool',dict(node_pool_id='pool'),m.NodePool(id='pool'))]
        for api,args,data in cases:
            with self.subTest(api=api):
                c=oci.container_engine.ContainerEngineClient.__new__(oci.container_engine.ContainerEngineClient)
                c.retry_strategy=oci.retry.NoneRetryStrategy();c.circuit_breaker_callback=None;c.base_client=Mock();c.base_client.get_preferred_retry_strategy.return_value=None;pages=[]
                def transport(**r):
                    self.assertEqual(r['method'],'GET');pages.append(r.get('query_params',{}).get('page'))
                    if api.startswith('list_'):self.assertEqual(r['query_params']['compartmentId'],'c')
                    if api=='list_node_pools':self.assertEqual(r['query_params']['clusterId'],'oke')
                    return oci.response.Response(200,{'opc-next-page':'next'} if api.startswith('list_') and len(pages)==1 else {},data,None)
                c.base_client.call_api=transport;fn=getattr(c,api)
                result=oci.pagination.list_call_get_all_results(fn,**args).data if api.startswith('list_') else fn(**args).data
                if api.startswith('list_'):self.assertEqual(len(result),2);self.assertEqual(pages,[None,'next'])
