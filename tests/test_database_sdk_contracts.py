"""Exercise generated SDK methods and real pagination without network or profiles."""
import unittest
from unittest.mock import Mock

from tests.test_collect import oci
from oci_lenz import database_services as db
from oci_lenz.model import graph


@unittest.skipIf(oci is None, 'install OCI SDK')
class DatabaseSDKContracts(unittest.TestCase):
    def test_five_collectors_use_supported_sdk_arguments_and_every_page(self):
        m = oci.database.models
        cases = (
            ('mysql', db.collect_mysql, 'mysql_db_system', {
                'list_db_systems': ('DbSystemSummary', 'mysql_db_system'),
            }),
            ('database', db.collect_autonomous, 'autonomous_database', {
                'list_autonomous_databases': ('AutonomousDatabaseSummary', 'autonomous_database'),
                'list_autonomous_container_databases': ('AutonomousContainerDatabaseSummary', 'autonomous_container_database'),
                'list_autonomous_exadata_infrastructures': ('AutonomousExadataInfrastructureSummary', 'autonomous_exadata_infrastructure'),
                'list_autonomous_vm_clusters': ('AutonomousVmClusterSummary', 'autonomous_vm_cluster'),
                'list_cloud_autonomous_vm_clusters': ('CloudAutonomousVmClusterSummary', 'cloud_autonomous_vm_cluster'),
            }),
            ('database', db.collect_exacc, 'vm_cluster', {
                'list_exadata_infrastructures': ('ExadataInfrastructureSummary', 'exadata_infrastructure'),
                'list_vm_clusters': ('VmClusterSummary', 'vm_cluster'),
                'list_vm_cluster_networks': ('VmClusterNetworkSummary', 'vm_cluster_network'),
            }),
            ('database', db.collect_exaci, 'cloud_vm_cluster', {
                'list_cloud_exadata_infrastructures': ('CloudExadataInfrastructureSummary', 'cloud_exadata_infrastructure'),
                'list_cloud_vm_clusters': ('CloudVmClusterSummary', 'cloud_vm_cluster'),
            }),
            ('database', db.collect_exascale, 'exadb_vm_cluster', {
                'list_exascale_db_storage_vaults': ('ExascaleDbStorageVaultSummary', 'exascale_db_storage_vault'),
                'list_exadb_vm_clusters': ('ExadbVmClusterSummary', 'exadb_vm_cluster'),
            }),
        )
        for service, collector, expected, lists in cases:
            with self.subTest(service=expected):
                snapshot = {'resources': [], 'coverage': [], 'scope': {'region': 'synthetic'}}
                requests = []
                namespace = oci.mysql.models if service == 'mysql' else m

                def transport(**request):
                    self.assertEqual(request['method'], 'GET')
                    api = request['operation_name']
                    query = request.get('query_params', {})
                    requests.append((api, dict(query)))
                    if api == 'get_db_system':
                        return oci.response.Response(200, {}, oci.mysql.models.DbSystem(
                            id=request['path_params']['dbSystemId'], subnet_id='synthetic-subnet',
                            ip_address='10.0.0.42'), None)
                    self.assertEqual(query['compartmentId'], 'synthetic-compartment')
                    page = query.get('page')
                    self.assertIn(page, (None, 'synthetic-page-2'))
                    suffix = 'b' if page else 'a'
                    prefix = request.get('path_params', {}).get('exadataInfrastructureId', '')
                    if api == 'list_db_nodes':
                        self.assertIn(query['vmClusterId'], ('vm_cluster-a', 'vm_cluster-b',
                            'cloud_vm_cluster-a', 'cloud_vm_cluster-b',
                            'exadb_vm_cluster-a', 'exadb_vm_cluster-b'))
                        data = [m.DbNodeSummary(id=query['vmClusterId'] + '-node-' + suffix)]
                    else:
                        model, kind = lists[api]
                        data = [getattr(namespace, model)(id=prefix + kind + '-' + suffix,
                            compartment_id='synthetic-compartment', display_name='Synthetic ' + suffix)]
                    return oci.response.Response(200,
                        {} if page else {'opc-next-page': 'synthetic-page-2'}, data, None)

                cls = oci.mysql.DbSystemClient if service == 'mysql' else oci.database.DatabaseClient
                client = cls.__new__(cls)
                client.retry_strategy = oci.retry.NoneRetryStrategy()
                client.circuit_breaker_callback = None
                client.base_client = Mock()
                client.base_client.get_preferred_retry_strategy.return_value = None
                client.base_client.call_api = transport

                def call(actual_service, api, *args, **kwargs):
                    self.assertEqual(actual_service, service)
                    method = getattr(client, api)
                    if api.startswith('list_'):
                        return oci.pagination.list_call_get_all_results(method, *args, **kwargs).data
                    return method(*args, **kwargs).data

                def add(obj, kind, **fields):
                    snapshot['resources'].append(dict(id=obj.id, kind=kind,
                        name=getattr(obj, 'display_name', None) or kind, **fields))

                if collector in (db.collect_mysql, db.collect_autonomous):
                    collector(call, add, 'synthetic-compartment')
                else:
                    collector(call, add, snapshot, 'synthetic-compartment')
                for api, (_, kind) in lists.items():
                    self.assertGreaterEqual(sum(r['kind'] == kind for r in snapshot['resources']), 2)
                    pages = [q.get('page') for name, q in requests if name == api]
                    self.assertEqual(pages.count(None), pages.count('synthetic-page-2'))
                    self.assertGreater(pages.count(None), 0)
                nodes, edges = graph(snapshot)
                if collector in (db.collect_exacc, db.collect_exaci, db.collect_exascale):
                    self.assertEqual(sum(r['kind'] == 'db_node' for r in snapshot['resources']), 4)
                    self.assertEqual(sum(e['kind'] == 'vm_cluster_id' for e in edges), 4)
                self.assertEqual(sum(r['kind'] == expected for r in snapshot['resources']), 2)
