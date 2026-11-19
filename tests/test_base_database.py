import json
import unittest
import xml.etree.ElementTree as E
from tests import test_collect as fixtures
from oci_lenz.model import sample,graph
from oci_lenz.display import prepare_display
from oci_lenz.draw import render,validate
from oci_lenz.architecture import make_scene


@unittest.skipIf(fixtures.oci is None,'install OCI SDK')
class BaseDatabaseCollectorTests(unittest.TestCase):
    def responses(self):
        oci=fixtures.oci;m=oci.database.models
        return {'list_db_systems':[m.DbSystemSummary(id='db-system',display_name='Synthetic Base DB',compartment_id='c',shape='VM.BaseDB.x86',subnet_id='s',backup_subnet_id='backup-subnet',nsg_ids=['nsg'],ssh_public_keys=['DO-NOT-STORE'],freeform_tags={'private':'DO-NOT-STORE'})],
                'list_db_nodes':[m.DbNodeSummary(id='db-node',db_system_id='db-system',hostname='Synthetic DB node',vnic_id='db-client',backup_vnic_id='db-backup',additional_details='DO-NOT-STORE')],
                'get_vnic':lambda key:oci.core.models.Vnic(id=key,subnet_id='backup-subnet' if key=='db-backup' else 's',private_ip='10.9.0.10' if key=='db-backup' else '10.0.0.20',nsg_ids=['nsg'])}

    def test_base_system_nodes_and_network_fields_are_allowlisted(self):
        s,calls=fixtures.CollectorTests().run_collect(extra=self.responses());nodes,edges=graph(s)
        self.assertEqual(nodes['db-system']['kind'],'db_system')
        self.assertEqual(nodes['db-node']['kind'],'db_node')
        self.assertEqual(nodes['db-client']['db_node_id'],'db-node')
        self.assertIn('10.0.0.20',nodes['db-client']['private_ips'])
        self.assertIn('db_system_id',[e['kind'] for e in edges if e['source']=='db-node'])
        self.assertNotIn('DO-NOT-STORE',json.dumps(s))
        self.assertTrue(all(name.startswith(('list_','get_','search_')) for name in calls))

    def test_node_failure_keeps_system_and_differs_from_zero(self):
        s,_=fixtures.CollectorTests().run_collect(fail='list_db_nodes',extra=self.responses())
        self.assertTrue(any(r['kind']=='db_system' for r in s['resources']))
        self.assertEqual(next(c for c in s['coverage'] if c.get('api')=='list_db_nodes')['status'],'permission_denied')
        empty,_=fixtures.CollectorTests().run_collect()
        self.assertEqual(next(c for c in empty['coverage'] if c.get('api')=='list_db_systems')['count'],0)

    def test_legacy_exadata_is_distinct_from_base_and_unknown_shapes(self):
        extra=self.responses();m=fixtures.oci.database.models
        extra['list_db_systems']=[m.DbSystemSummary(id='exa',shape='Exadata.Quarter3.100'),m.DbSystemSummary(id='unknown')]
        s,calls=fixtures.CollectorTests().run_collect(extra=extra)
        self.assertFalse(any(r['kind']=='db_system' for r in s['resources']))
        self.assertEqual(next(r['kind'] for r in s['resources'] if r['id']=='exa'),'exadata_db_system')
        self.assertIn('list_db_nodes',calls)
        self.assertEqual(sum(c.get('resource_type')=='db_system_shape' and c['status']=='unsupported' for c in s['coverage']),1)

    def test_denied_vnic_keeps_node_and_unresolved_network_evidence(self):
        s,_=fixtures.CollectorTests().run_collect(fail='get_vnic',extra=self.responses());nodes,edges=graph(s)
        self.assertIn('db-node',nodes)
        self.assertTrue(any(e['source']=='db-node' and e['target']=='unknown:db-client' for e in edges))

    def test_node_parent_fallback_records_the_scoped_query_evidence(self):
        extra=self.responses();extra['list_db_nodes'][0].db_system_id=None
        s,_=fixtures.CollectorTests().run_collect(extra=extra)
        edge=next(e for e in graph(s)[1] if e['source']=='db-node' and e['kind']=='db_system_id')
        self.assertEqual(edge['target'],'db-system')
        self.assertEqual(edge['evidence'],'ListDbNodes.db_system_id request filter')


class BaseDatabaseGraphTests(unittest.TestCase):
    def test_native_db_icons_labels_api_membership_and_ip_privacy(self):
        s=sample();s['resources'] += [
            {'id':'db-system','name':'Synthetic Base DB','kind':'db_system','subnet_id':'private','nsg_ids':['app-nsg']},
            {'id':'db-node','name':'Synthetic DB host','kind':'db_node','db_system_id':'db-system','vnic_id':'db-vnic'},
            {'id':'db-vnic','name':'Synthetic DB VNIC','kind':'vnic','db_node_id':'db-node','subnet_id':'private','vcn_id':'vcn','private_ips':['10.0.1.20'],'network_role':'client'}]
        display=prepare_display(s);xml=render(display);validate(xml,display)
        cells={c.get('id'):c for c in E.fromstring(xml).find('diagram').iter('mxCell')}
        self.assertEqual(cells['db-node'].get('parent'),'private')
        self.assertIn('db-system-icon',cells);self.assertIn('db-node-icon',cells)
        self.assertEqual(cells['db-node'].get('visible'),'0')
        self.assertIn('Synthetic Base DB',cells['db-system'].get('value'))
        self.assertIn('10.0.1.20',cells['db-system'].get('value'))
        self.assertNotIn('Synthetic DB host',cells['db-system'].get('value'))
        self.assertNotIn('10.0.1.20',json.dumps(make_scene(display,view='overview')['request']))
        self.assertNotIn('10.0.1.20',render(prepare_display(s,redact=True)))
        s['resources'] += [
            {'id':'second-node','name':'Second hidden hostname','kind':'db_node','db_system_id':'db-system','vnic_id':'second-vnic'},
            {'id':'second-vnic','name':'Second client VNIC','kind':'vnic','db_node_id':'second-node','subnet_id':'private','vcn_id':'vcn','private_ips':['10.0.1.21'],'network_role':'client'},
            {'id':'backup-vnic','name':'Backup VNIC','kind':'vnic','db_node_id':'second-node','subnet_id':'private','private_ips':['10.9.0.21'],'network_role':'backup'}]
        s['resources'][-3]['backup_vnic_id']='backup-vnic'
        display=prepare_display(s);xml=render(display);validate(xml,display)
        cell=E.fromstring(xml).find("diagram/mxGraphModel/root/mxCell[@id='db-system']")
        self.assertIn('10.0.1.20',cell.get('value'));self.assertIn('10.0.1.21',cell.get('value'))
        self.assertNotIn('10.9.0.21',cell.get('value'))

    def test_backend_to_hidden_node_displays_system_without_losing_evidence(self):
        s=sample();s['resources'] += [
            {'id':'db-system','name':'Synthetic Base DB','kind':'db_system','subnet_id':'private'},
            {'id':'db-node','name':'Hidden DB hostname','kind':'db_node','db_system_id':'db-system','vnic_id':'db-vnic'},
            {'id':'db-vnic','name':'Synthetic DB VNIC','kind':'vnic','db_node_id':'db-node','subnet_id':'private','vcn_id':'vcn','private_ips':['10.0.1.20'],'network_role':'client'}]
        next(r for r in s['resources'] if r['kind']=='backend_set')['backends']=[{'ip_address':'10.0.1.20','port':1521}]
        display=prepare_display(s);edges=graph(s)[1];xml=render(display);validate(xml,display)
        cells={c.get('id'):c for c in E.fromstring(xml).find('diagram').iter('mxCell')}
        i=next(i for i,e in enumerate(edges) if e['kind']=='backend')
        self.assertEqual(edges[i]['target'],'db-node')
        self.assertEqual(cells['edge-'+str(i)].get('target'),'db-system')
        self.assertEqual(cells['edge-'+str(i)].get('ociEvidenceTarget'),'db-node')
        tampered=E.fromstring(xml)
        tampered.find("diagram/mxGraphModel/root/mxCell[@id='edge-"+str(i)+"']").set('target','compute')
        with self.assertRaisesRegex(ValueError,'invalid DB node display projection'):
            validate(E.tostring(tampered,encoding='unicode'),display)
