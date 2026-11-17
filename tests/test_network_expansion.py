import copy
import unittest
import xml.etree.ElementTree as E
from tests import test_collect as fixtures
oci=fixtures.oci
from oci_lenz.model import sample,graph
from oci_lenz.display import prepare_display
from oci_lenz.draw import render,validate
from oci_lenz.architecture import make_scene


@unittest.skipIf(oci is None,'install OCI SDK')
class NetworkCollectorTests(unittest.TestCase):
    def test_network_fields_are_allowlisted_using_real_sdk_models(self):
        m=oci.core.models
        extra={'list_drgs':[m.Drg(id='drg',display_name='Synthetic DRG',compartment_id='c',freeform_tags={'secret':'omitted'})],
               'list_drg_attachments':[m.DrgAttachment(id='att',drg_id='drg',vcn_id='deprecated',network_details=m.VcnDrgAttachmentNetworkDetails(id='v'),display_name='Synthetic attachment')],
               'list_local_peering_gateways':[m.LocalPeeringGateway(id='lpg',vcn_id='v',peer_id='external-lpg',peering_status='PEERED')],
               'list_remote_peering_connections':[m.RemotePeeringConnection(id='rpc',drg_id='drg',peer_id='external-rpc',peer_region_name='other-region',peer_tenancy_id='omitted',peering_status='PEERED')]}
        s,calls=fixtures.CollectorTests().run_collect(extra=extra);nodes,edges=graph(s)
        self.assertEqual(nodes['att']['network_id'],'v')
        self.assertEqual(nodes['att']['network_type'],'VCN')
        self.assertEqual(nodes['rpc']['peer_region_name'],'other-region')
        self.assertNotIn('omitted',str(s));self.assertNotIn('deprecated',str(s))
        self.assertTrue(any(e['kind']=='attachment_network' and e['target']=='v' for e in edges))
        self.assertIn('unknown:external-rpc',nodes)
        self.assertTrue(all(n.startswith(('get_','list_','search_')) for n in calls))
        self.assertFalse(any(c['service'] in ('drg','peering') and c['status']=='unsupported' for c in s['coverage']))

    def test_permission_denied_and_empty_network_are_distinct(self):
        s,_=fixtures.CollectorTests().run_collect(fail='list_drg_attachments')
        self.assertEqual(next(c for c in s['coverage'] if c.get('api')=='list_drg_attachments')['status'],'permission_denied')
        self.assertEqual(next(c for c in s['coverage'] if c.get('api')=='list_drgs')['count'],0)

    def test_legacy_vcn_attachment_and_unsupported_transport_are_explicit(self):
        m=oci.core.models
        extra={'list_drg_attachments':[
            m.DrgAttachment(id='legacy',drg_id='drg',vcn_id='v'),
            m.DrgAttachment(id='circuit',drg_id='drg',network_details=m.VirtualCircuitDrgAttachmentNetworkDetails(id='outside-circuit'))]}
        s,_=fixtures.CollectorTests().run_collect(extra=extra);nodes,edges=graph(s)
        self.assertEqual(nodes['legacy']['network_type'],'VCN')
        self.assertEqual(next(e for e in edges if e['source']=='legacy' and e['kind']=='attachment_network')['evidence'],'DrgAttachment.vcn_id')
        self.assertIn('unknown:outside-circuit',nodes)
        self.assertTrue(any(c['status']=='unsupported' and c.get('resource_type')=='VIRTUAL_CIRCUIT' for c in s['coverage']))


class NetworkGraphTests(unittest.TestCase):
    def snapshot(self):
        s=sample();s['resources'] += [
            {'id':'drg','name':'Synthetic DRG','kind':'drg'},
            {'id':'att','name':'Synthetic VCN attachment','kind':'drg_attachment','drg_id':'drg','network_id':'vcn','network_type':'VCN'},
            {'id':'rpc','name':'Synthetic RPC','kind':'rpc','drg_id':'drg','peer_id':'outside','peering_status':'PEERED'},
            {'id':'lpg','name':'Synthetic LPG','kind':'lpg','vcn_id':'vcn','peer_id':'other-lpg','peering_status':'PEERED'}]
        return s

    def test_configured_network_edges_keep_api_evidence_and_unknown_peers(self):
        s=self.snapshot();original=copy.deepcopy(s);nodes,edges=graph(s)
        for source,target,kind in [('att','drg','drg_id'),('att','vcn','attachment_network'),('rpc','drg','drg_id'),('rpc','unknown:outside','peer_id')]:
            edge=next(e for e in edges if e['source']==source and e['target']==target)
            self.assertEqual(edge['kind'],kind);self.assertTrue(edge['evidence'])
        self.assertEqual(s,original)
        scene=make_scene(prepare_display(s),view='overview')
        self.assertIn('unknown:outside',scene['aliases'])
        xml=render(prepare_display(s));validate(xml,prepare_display(s))
        cells={c.get('id'):c for c in E.fromstring(xml).find('diagram').iter('mxCell')}
        self.assertIn('drg-icon',cells);self.assertIn('rpc-icon',cells)
        for i,edge in enumerate(edges):
            if edge['kind'] in ('drg_id','attachment_network','peer_id'):
                self.assertNotEqual(cells['edge-'+str(i)].get('visible'),'0')
                self.assertIn('textOpacity=0;',cells['edge-'+str(i)].get('style'))

    def test_peer_in_another_selected_compartment_resolves_without_inference(self):
        s=self.snapshot();s['resources'].append({'id':'other-lpg','kind':'lpg','name':'Synthetic peer','compartment_id':'other','vcn_id':'external-vcn'})
        nodes,edges=graph(s)
        self.assertTrue(any(e['source']=='lpg' and e['target']=='other-lpg' for e in edges))
        self.assertIn('unknown:external-vcn',nodes)

    def test_missing_peer_id_and_missing_attachment_network_stay_unknown(self):
        s=self.snapshot()
        next(r for r in s['resources'] if r['id']=='rpc').pop('peer_id')
        next(r for r in s['resources'] if r['id']=='att').pop('network_id')
        nodes,edges=graph(s)
        self.assertIn('unknown:peer:rpc',nodes)
        self.assertIn('unknown:missing-attachment-network:att',nodes)
        s['resources'].append({'id':'unconnected','name':'Synthetic unused LPG','kind':'lpg','peering_status':'NEW'})
        _,edges=graph(s)
        self.assertFalse(any(e['source']=='unconnected' and e['kind']=='peer_id' for e in edges))

    def test_route_target_is_resolved_without_inventing_transitive_vcn_links(self):
        s=self.snapshot()
        next(r for r in s['resources'] if r['id']=='private-rt')['rules'][0]['network_entity_id']='drg'
        nodes,edges=graph(s)
        self.assertTrue(any(e['source']=='private' and e['target']=='drg' and e['kind']=='route' for e in edges))
        self.assertNotIn('unknown:drg',nodes)
        self.assertFalse(any(nodes[e['source']]['kind']=='vcn' and nodes[e['target']]['kind']=='vcn' for e in edges))
