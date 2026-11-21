"""Synthetic real-SDK contracts for the five database service expansions."""
import json
import re
from html import unescape
import unittest
import xml.etree.ElementTree as E
from tests import test_collect as fixtures
from oci_lenz.model import graph,sample
from oci_lenz.display import prepare_display
from oci_lenz.draw import render,validate
from oci_lenz.architecture import make_scene

oci=fixtures.oci


def collect(extra=None,fail=None,requests=None):
    return fixtures.CollectorTests().run_collect(extra=extra,fail=fail,request_log=requests)[0]


@unittest.skipIf(oci is None,'install OCI SDK')
class MySQLTests(unittest.TestCase):
    def responses(self):
        m=oci.mysql.models
        return {'mysql_list_db_systems':[m.DbSystemSummary(id='mysql',compartment_id='c',display_name='Synthetic MySQL',endpoints=[m.DbSystemEndpoint(ip_address='10.0.0.31',port=3306)],freeform_tags={'secret':'DO-NOT-STORE'})],
                'mysql_get_db_system':m.DbSystem(id='mysql',subnet_id='s',nsg_ids=['nsg'],ip_address='10.0.0.31',port=3306,mysql_version='8.4',description='DO-NOT-STORE')}

    def test_scoped_detail_and_allowlisted_network(self):
        req=[];s=collect(self.responses(),requests=req);nodes,edges=graph(s)
        self.assertEqual(nodes['mysql']['kind'],'mysql_db_system')
        self.assertEqual(nodes['mysql']['subnet_id'],'s')
        self.assertIn('10.0.0.31',nodes['mysql']['private_ips'])
        self.assertEqual(next(k for n,a,k in req if n=='mysql_list_db_systems'),{'compartment_id':'c'})
        self.assertTrue(any(e['source']=='mysql' and e['target']=='s' for e in edges))
        self.assertNotIn('DO-NOT-STORE',json.dumps(s))

    def test_denied_detail_retains_summary_endpoint_and_coverage(self):
        s=collect(self.responses(),fail='mysql_get_db_system')
        r=next(r for r in s['resources'] if r['id']=='mysql')
        self.assertEqual(r['private_ips'],['10.0.0.31'])
        self.assertFalse(r.get('subnet_id'))
        self.assertEqual(next(c for c in s['coverage'] if c.get('api')=='get_db_system')['status'],'permission_denied')

    def test_mysql_empty_and_denied_are_distinct(self):
        for fail,status in ((None,'ok'),('mysql_list_db_systems','permission_denied')):
            s=collect(fail=fail)
            c=next(c for c in s['coverage'] if c.get('service')=='mysql' and c.get('api')=='list_db_systems')
            self.assertEqual(c['status'],status)
            self.assertEqual(c.get('count'),0 if not fail else None)


@unittest.skipIf(oci is None,'install OCI SDK')
class AutonomousTests(unittest.TestCase):
    def responses(self):
        m=oci.database.models
        return {'list_autonomous_databases':[
            m.AutonomousDatabaseSummary(id='adb',display_name='Synthetic ADB',subnet_id='s',nsg_ids=['nsg'],private_endpoint_ip='10.0.0.41',autonomous_container_database_id='acd',connection_strings=m.AutonomousDatabaseConnectionStrings(high='DO-NOT-STORE')),
            m.AutonomousDatabaseSummary(id='adb-public',display_name='Synthetic public ADB',public_endpoint='not-an-ip.example.invalid')],
            'list_autonomous_container_databases':[m.AutonomousContainerDatabaseSummary(id='acd',cloud_autonomous_vm_cluster_id='acvm',freeform_tags={'secret':'DO-NOT-STORE'})],
            'list_cloud_autonomous_vm_clusters':[m.CloudAutonomousVmClusterSummary(id='acvm',subnet_id='s',cloud_exadata_infrastructure_id='outside')],
            'list_autonomous_vm_clusters':[m.AutonomousVmClusterSummary(id='accvm',exadata_infrastructure_id='outside-cc',vm_cluster_network_id='outside-network')]}

    def test_private_public_and_dedicated_membership(self):
        s=collect(self.responses());nodes,edges=graph(s)
        self.assertEqual(nodes['adb']['kind'],'autonomous_database')
        self.assertEqual(nodes['adb']['private_ips'],['10.0.0.41'])
        self.assertFalse(nodes['adb-public'].get('subnet_id'))
        self.assertTrue(any(e['source']=='adb' and e['target']=='acd' and e['evidence']=='AutonomousDatabase.autonomous_container_database_id' for e in edges))
        self.assertIn('unknown:outside',nodes)
        self.assertNotIn('DO-NOT-STORE',json.dumps(s))

    def test_denied_parent_list_retains_database_unknown_parent(self):
        s=collect(self.responses(),fail='list_autonomous_container_databases')
        nodes,_=graph(s);self.assertIn('adb',nodes);self.assertIn('unknown:acd',nodes)


@unittest.skipIf(oci is None,'install OCI SDK')
class ExaccTests(unittest.TestCase):
    def responses(self):
        m=oci.database.models
        return {'list_exadata_infrastructures':[m.ExadataInfrastructureSummary(id='cc',compartment_id='c',display_name='Synthetic ExaCC',rack_serial_number='DO-NOT-STORE')],
            'list_vm_clusters':[m.VmClusterSummary(id='ccvm',exadata_infrastructure_id='cc',vm_cluster_network_id='ccnet',ssh_public_keys=['DO-NOT-STORE'])],
            'list_vm_cluster_networks':[m.VmClusterNetworkSummary(id='ccnet',exadata_infrastructure_id='cc',vm_networks=[m.VmNetworkDetails(network_type='CLIENT',nodes=[m.NodeDetails(ip='10.20.0.5')]),m.VmNetworkDetails(network_type='BACKUP',nodes=[m.NodeDetails(ip='10.21.0.5')])])],
            'list_db_nodes':[m.DbNodeSummary(id='ccnode',hostname='Synthetic node')]}

    def test_on_prem_network_and_query_owned_nodes_without_fake_vcn(self):
        req=[];s=collect(self.responses(),requests=req);nodes,edges=graph(s)
        self.assertEqual(nodes['cc']['kind'],'exadata_infrastructure')
        self.assertEqual(nodes['ccvm']['kind'],'vm_cluster')
        self.assertFalse(nodes['ccvm'].get('subnet_id'))
        self.assertTrue(any(e['source']=='ccnode' and e['target']=='ccvm' and e['evidence']=='ListDbNodes.vm_cluster_id request filter' for e in edges))
        self.assertEqual(next(k for n,a,k in req if n=='list_db_nodes')['vm_cluster_id'],'ccvm')
        self.assertEqual(next(k for n,a,k in req if n=='list_vm_cluster_networks'),{'exadata_infrastructure_id':'cc','compartment_id':'c'})
        display=prepare_display(s);r=next(r for r in display['resources'] if r['id']=='ccvm')
        self.assertIn('IP: 10.20.0.5',r['summary_details']);self.assertNotIn('10.21.0.5',str(r['summary_details']))
        self.assertNotIn('DO-NOT-STORE',json.dumps(s))

    def test_denied_network_keeps_cluster_reference(self):
        s=collect(self.responses(),fail='list_vm_cluster_networks');nodes,_=graph(s)
        self.assertIn('ccvm',nodes);self.assertIn('unknown:ccnet',nodes)


@unittest.skipIf(oci is None,'install OCI SDK')
class ExaciTests(unittest.TestCase):
    def responses(self):
        m=oci.database.models
        return {'list_cloud_exadata_infrastructures':[m.CloudExadataInfrastructureSummary(id='ci',display_name='Synthetic ExaCI')],
            'list_cloud_vm_clusters':[m.CloudVmClusterSummary(id='civm',subnet_id='s',backup_subnet_id='outside-backup',cloud_exadata_infrastructure_id='ci',scan_ip_ids=['scan-ip'],ssh_public_keys=['DO-NOT-STORE'])],
            'list_db_nodes':[m.DbNodeSummary(id='cinode',vnic_id='civnic')],
            'get_private_ip':oci.core.models.PrivateIp(id='scan-ip',ip_address='10.0.0.51',subnet_id='s')}

    def test_cloud_membership_client_backup_and_scan_evidence(self):
        req=[];s=collect(self.responses(),requests=req);nodes,edges=graph(s)
        self.assertEqual(nodes['civm']['kind'],'cloud_vm_cluster')
        self.assertEqual(nodes['cinode']['vm_cluster_id'],'civm')
        self.assertTrue(any(e['source']=='civm' and e['target']=='ci' for e in edges))
        self.assertIn('unknown:outside-backup',nodes)
        self.assertIn('10.0.0.51',nodes['civm']['private_ips'])
        self.assertNotIn('DO-NOT-STORE',json.dumps(s))
        self.assertTrue(all(n.removeprefix('mysql_').removeprefix('nlb_').removeprefix('waf_').removeprefix('waas_').removeprefix('redis_').removeprefix('psql_').removeprefix('opensearch_').removeprefix('nosql_').removeprefix('object_storage_').removeprefix('artifacts_').removeprefix('devops_').removeprefix('goldengate_').startswith(('list_','get_','search_')) for n,a,k in req))

    def test_denied_nodes_does_not_discard_cluster_or_infra(self):
        s=collect(self.responses(),fail='list_db_nodes');nodes,_=graph(s)
        self.assertIn('ci',nodes);self.assertIn('civm',nodes);self.assertNotIn('cinode',nodes)


@unittest.skipIf(oci is None,'install OCI SDK')
class ExascaleTests(unittest.TestCase):
    def responses(self):
        m=oci.database.models
        return {'list_exascale_db_storage_vaults':[m.ExascaleDbStorageVaultSummary(id='vault',display_name='Synthetic Exascale Vault',freeform_tags={'secret':'DO-NOT-STORE'})],
            'list_exadb_vm_clusters':[m.ExadbVmClusterSummary(id='xsvm',subnet_id='s',exascale_db_storage_vault_id='vault',ssh_public_keys=['DO-NOT-STORE'])],
            'list_db_nodes':[m.DbNodeSummary(id='xsnode',vnic_id='xsvnic')]}

    def test_vault_cluster_and_nodes_with_exact_reference(self):
        s=collect(self.responses());nodes,edges=graph(s)
        self.assertEqual(nodes['vault']['kind'],'exascale_db_storage_vault')
        self.assertEqual(nodes['xsvm']['kind'],'exadb_vm_cluster')
        self.assertEqual(nodes['xsnode']['vm_cluster_id'],'xsvm')
        self.assertTrue(any(e['source']=='xsvm' and e['target']=='vault' and e['evidence']=='ExadbVmCluster.exascale_db_storage_vault_id' for e in edges))
        self.assertNotIn('DO-NOT-STORE',json.dumps(s))

    def test_vault_failure_keeps_out_of_scope_reference(self):
        s=collect(self.responses(),fail='list_exascale_db_storage_vaults');nodes,_=graph(s)
        self.assertIn('xsvm',nodes);self.assertIn('unknown:vault',nodes)


class DatabaseDiagramTests(unittest.TestCase):
    def test_each_service_native_icon_network_parent_labels_and_alias_privacy(self):
        for case,kind in [('mysql','mysql_db_system'),('autonomous-db','autonomous_database'),('exacc','vm_cluster'),('exaci','cloud_vm_cluster'),('exascale','exadb_vm_cluster')]:
            with self.subTest(case=case):
                s=sample(case);d=prepare_display(s);xml=render(d);validate(xml,d)
                resources=[r for r in s['resources'] if r['kind']==kind];self.assertTrue(resources)
                cells={c.get('id'):c for c in E.fromstring(xml).find('diagram').iter('mxCell')}
                for r in resources:
                    self.assertIn(r['id']+'-icon',cells)
                    self.assertIn(r['name'],unescape(re.sub('<[^>]+>','',cells[r['id']].get('value'))))
                    if r.get('subnet_id'):self.assertEqual(cells[r['id']].get('parent'),r['subnet_id'])
                private='10.0.1.61'
                request=json.dumps(make_scene(d,view='overview')['request'])
                self.assertNotIn(private,request);self.assertNotIn(resources[0]['name'],request)
                redacted=render(prepare_display(s,redact=True));self.assertNotIn(private,redacted)
                self.assertNotIn(resources[0]['name'],redacted)

    def test_hidden_cluster_nodes_preserve_backend_evidence_and_both_client_ips(self):
        for case in ('exaci','exascale'):
            with self.subTest(case=case):
                s=sample(case);d=prepare_display(s);xml=render(d);validate(xml,d)
                cells={c.get('id'):c for c in E.fromstring(xml).find('diagram').iter('mxCell')}
                nodes,edges=graph(s)
                node=next(r for r in s['resources'] if r['kind']=='db_node')
                self.assertEqual(cells[node['id']].get('visible'),'0')
                owner=node['vm_cluster_id']
                self.assertIn('10.0.1.61',cells[owner].get('value'))
                self.assertIn('10.0.1.62',cells[owner].get('value'))
                i=next(i for i,e in enumerate(edges) if e['kind']=='backend')
                self.assertEqual(cells['edge-'+str(i)].get('target'),owner)
                self.assertEqual(cells['edge-'+str(i)].get('ociEvidenceTarget'),edges[i]['target'])
                cells['edge-'+str(i)].set('target','compute')
                with self.assertRaisesRegex(ValueError,'invalid DB node display projection'):
                    # Mutate a freshly parsed document so parent/edge metadata remain real.
                    doc=E.fromstring(xml)
                    doc.find("diagram/mxGraphModel/root/mxCell[@id='edge-"+str(i)+"']").set('target','compute')
                    validate(E.tostring(doc,encoding='unicode'),d)


@unittest.skipIf(oci is None,'install OCI SDK')
class DatabaseCoverageTests(unittest.TestCase):
    def test_all_service_lists_distinguish_empty_and_denied(self):
        apis=('list_autonomous_databases','list_autonomous_container_databases',
            'list_autonomous_exadata_infrastructures','list_autonomous_vm_clusters',
            'list_cloud_autonomous_vm_clusters','list_exadata_infrastructures',
            'list_vm_clusters','list_cloud_exadata_infrastructures','list_cloud_vm_clusters',
            'list_exascale_db_storage_vaults','list_exadb_vm_clusters')
        empty=collect()
        for api in apis:
            with self.subTest(api=api):
                self.assertEqual(next(c for c in empty['coverage'] if c.get('api')==api)['count'],0)
                denied=collect(fail=api)
                c=next(c for c in denied['coverage'] if c.get('api')==api)
                self.assertEqual(c['status'],'permission_denied');self.assertNotIn('count',c)
                self.assertNotIn('sensitive error',json.dumps(denied))

    def test_cross_compartment_infrastructure_is_resolved_only_after_merge(self):
        m=oci.database.models
        first=collect({'list_cloud_vm_clusters':[m.CloudVmClusterSummary(id='cross-vm',cloud_exadata_infrastructure_id='cross-infra')]})
        self.assertIn('unknown:cross-infra',graph(first)[0])
        other=collect({'list_cloud_exadata_infrastructures':[m.CloudExadataInfrastructureSummary(id='cross-infra',compartment_id='other')]})
        first['resources'] += [r for r in other['resources'] if r['id']=='cross-infra']
        nodes,edges=graph(first)
        self.assertNotIn('unknown:cross-infra',nodes)
        self.assertTrue(any(e['source']=='cross-vm' and e['target']=='cross-infra' for e in edges))

    def test_exacc_networks_in_selected_compartment_when_infra_is_outside(self):
        m=oci.database.models;req=[]
        s=collect({'list_vm_clusters':[m.VmClusterSummary(id='cross-ccvm',exadata_infrastructure_id='outside',vm_cluster_network_id='local-net')],
            'list_vm_cluster_networks':[m.VmClusterNetworkSummary(id='local-net',exadata_infrastructure_id='outside',compartment_id='c')]},requests=req)
        nodes,_=graph(s)
        self.assertIn('local-net',nodes);self.assertIn('unknown:outside',nodes)
        self.assertEqual(next(k for n,a,k in req if n=='list_vm_cluster_networks')['compartment_id'],'c')



class DatabaseEndpointTests(unittest.TestCase):
    def test_backend_matches_only_unique_observed_database_endpoint_in_lb_vcn(self):
        s=sample();s['resources'].append({'id':'mysql-endpoint','kind':'mysql_db_system','name':'Synthetic MySQL','subnet_id':'private','private_ips':['10.0.1.61']})
        backend=next(r for r in s['resources'] if r['kind']=='backend_set')
        backend['backends']=[{'ip_address':'10.0.1.61','port':3306}]
        edge=next(e for e in graph(s)[1] if e['kind']=='backend')
        self.assertEqual(edge['target'],'mysql-endpoint')
        self.assertIn('database endpoint',edge['evidence'])
        s['resources'].append({'id':'duplicate','kind':'autonomous_database','name':'Synthetic duplicate','subnet_id':'private','private_ips':['10.0.1.61']})
        edge=next(e for e in graph(s)[1] if e['kind']=='backend')
        self.assertTrue(edge['target'].startswith('unknown:'))
        s['resources'].pop();s['resources'][-1]['subnet_id']='outside-subnet'
        edge=next(e for e in graph(s)[1] if e['kind']=='backend')
        self.assertTrue(edge['target'].startswith('unknown:'))

    def test_database_backend_fanout_uses_existing_shared_trunk_rule(self):
        from oci_lenz.quality import edge_conflicts
        paths=[{'source':'set','target':'a','network':False,'points':[(0,0),(0,50),(100,50),(100,100)]},
            {'source':'set','target':'b','network':False,'points':[(0,0),(0,50),(60,50),(60,100)]}]
        for kind in ('mysql_db_system','autonomous_database','cloud_vm_cluster','exadb_vm_cluster'):
            with self.subTest(kind=kind):
                nodes={'set':{'kind':'backend_set'},'a':{'kind':kind},'b':{'kind':kind}}
                self.assertEqual(edge_conflicts(paths,nodes),{'edge_crossings':0,'edge_overlap_length':0})
