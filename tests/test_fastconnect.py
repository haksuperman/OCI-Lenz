import copy
import json
import unittest
import xml.etree.ElementTree as E
from tests import test_collect as fixtures
from oci_lenz.model import sample,graph
from oci_lenz.diagram_model import diagram_graph
from oci_lenz.display import prepare_display
from oci_lenz.draw import render,validate,ICONS
from oci_lenz.architecture import make_scene,seed_plan,check_plan
oci=fixtures.oci


@unittest.skipIf(oci is None,'install OCI SDK')
class FastConnectCollectorTests(unittest.TestCase):
    def extra(self):
        m=oci.core.models
        return {'list_virtual_circuits':[m.VirtualCircuit(id='vc',display_name='Synthetic FastConnect',compartment_id='c',type='PRIVATE',gateway_id='outside-drg',bandwidth_shape_name='1 Gbps',bgp_session_state='UP',provider_service_key_name='DO-NOT-STORE',freeform_tags={'private':'DO-NOT-STORE'},cross_connect_mappings=[m.CrossConnectMapping(cross_connect_or_cross_connect_group_id='group',customer_bgp_peering_ip='192.0.2.0/31',oracle_bgp_peering_ip='192.0.2.1/31',vlan=100,bgp_md5_auth_key='DO-NOT-STORE')])],
            'list_cross_connect_groups':[m.CrossConnectGroup(id='group',compartment_id='c',display_name='Synthetic physical group',customer_reference_name='DO-NOT-STORE')],
            'list_cross_connects':[m.CrossConnect(id='port',compartment_id='c',display_name='Synthetic port',cross_connect_group_id='group',port_speed_shape_name='10 Gbps',customer_reference_name='DO-NOT-STORE')],
            'list_drg_attachments':[m.DrgAttachment(id='att',drg_id='outside-drg',network_details=m.VirtualCircuitDrgAttachmentNetworkDetails(id='vc'))]}

    def test_scoped_allowlist_and_exact_physical_references_exclude_authentication(self):
        s,calls=fixtures.CollectorTests().run_collect(extra=self.extra());nodes,edges=graph(s)
        self.assertEqual(nodes['vc']['kind'],'virtual_circuit');self.assertEqual(nodes['vc']['gateway_id'],'outside-drg')
        self.assertEqual(nodes['vc']['cross_connect_mappings'][0]['cross_connect_or_cross_connect_group_id'],'group')
        self.assertNotIn('DO-NOT-STORE',json.dumps(s));self.assertNotIn('bgp_md5_auth_key',json.dumps(s))
        self.assertTrue(any(e['source']=='vc' and e['target']=='group' and 'cross_connect_mappings' in e['evidence'] for e in edges))
        self.assertTrue(any(e['source']=='port' and e['target']=='group' and e['evidence']=='CrossConnect.cross_connect_group_id' for e in edges))
        _,projected=diagram_graph(s)
        self.assertEqual(len([e for e in projected if {e['source'],e['target']}=={'vc','unknown:outside-drg'}]),1)
        self.assertFalse(any(c.get('resource_type')=='VIRTUAL_CIRCUIT' and c['status']=='unsupported' for c in s['coverage']))
        self.assertTrue(all(n.startswith(('list_','get_','search_')) for n in calls))
        self.assertFalse(any('letter' in n or 'device_config' in n or n=='get_virtual_circuit' for n in calls))

    def test_denied_calls_keep_circuit_and_differ_from_successful_empty(self):
        s,_=fixtures.CollectorTests().run_collect(fail='list_cross_connects',extra=self.extra())
        self.assertTrue(any(r['kind']=='virtual_circuit' for r in s['resources']))
        self.assertEqual(next(c for c in s['coverage'] if c.get('api')=='list_cross_connects')['status'],'permission_denied')
        empty,_=fixtures.CollectorTests().run_collect()
        self.assertEqual(next(c for c in empty['coverage'] if c.get('api')=='list_virtual_circuits')['count'],0)

    def test_public_and_provider_managed_circuits_do_not_invent_gateways_or_cpes(self):
        m=oci.core.models
        s,_=fixtures.CollectorTests().run_collect(extra={'list_virtual_circuits':[m.VirtualCircuit(id='public-vc',type='PUBLIC',cross_connect_mappings=[]),m.VirtualCircuit(id='partner-vc',type='PRIVATE',gateway_id='external',cross_connect_mappings=[])]})
        nodes,edges=graph(s)
        self.assertFalse(any(e['source']=='public-vc' for e in edges))
        self.assertIn('unknown:external',nodes)
        self.assertFalse(any(e['source']=='partner-vc' and e['kind']!='gateway_id' for e in edges))


class FastConnectDiagramTests(unittest.TestCase):
    def test_official_fastconnect_glyph_is_imported_without_fake_connector_edges(self):
        s=prepare_display(sample('fastconnect'));xml=render(s);validate(xml,s)
        root=E.fromstring(xml).find('diagram/mxGraphModel/root');cells={c.get('id'):c for c in root}
        self.assertEqual(ICONS['virtual_circuit'],210);self.assertEqual(ICONS['cross_connect'],210)
        self.assertIn('qa-fc-icon',cells)
        glyphs=[c for c in root if c.get('id','').startswith('qa-fc-i-') and 'shape=image;' in c.get('style','')]
        self.assertEqual(len(glyphs),1);self.assertIn('image=data:image/svg+xml,',glyphs[0].get('style'))
        import base64,zlib,urllib.parse
        from oci_lenz.draw import ROOT
        library=json.loads(E.parse(ROOT/'assets/oci/library.xml').getroot().text)
        official=E.fromstring(urllib.parse.unquote(zlib.decompress(base64.b64decode(library[210]['xml']),-15).decode()))
        image=next(c for c in official.iter('mxCell') if 'shape=image;' in c.get('style',''))
        def image_data(c):return dict(p.split('=',1) for p in c.get('style').split(';') if '=' in p)['image']
        self.assertEqual(image_data(glyphs[0]),image_data(image))
        self.assertFalse(any(c.get('edge')=='1' and '-i-' in c.get('id','') for c in root))
        self.assertEqual(cells['qa-cross-connect'].get('parent'),'qa-cross-group')
        self.assertEqual(cells['qa-cross-group'].get('ociCrossConnectGroup'),'1')
        self.assertFalse(any(c.get('ociVisualFrame') for c in root))

    def test_fastconnect_alias_groups_and_labels_keep_credentials_and_ips_local(self):
        s=sample('fastconnect');before=copy.deepcopy(s);display=prepare_display(s)
        circuit=next(r for r in display['resources'] if r['id']=='qa-fc')
        self.assertIn('Customer: 192.0.2.0/31',circuit['summary_details'])
        self.assertIn('Oracle: 192.0.2.1/31',circuit['summary_details'])
        scene=make_scene(display,view='overview');a=scene['aliases']
        drg=next(g for g in scene['request']['network_groups'] if g['kind']=='drg')
        self.assertIn(a['qa-fc'],drg['fastconnect_members'])
        self.assertNotIn('192.0.2.',str(scene['request']));self.assertNotIn('Synthetic',str(scene['request']))
        self.assertEqual(check_plan(scene,seed_plan(scene)),[])
        self.assertEqual(s,before)
        self.assertFalse(any(r.get('summary_details') for r in prepare_display(s,redact=True)['resources']))

    def test_out_of_scope_physical_mapping_is_explicit_and_not_matched_by_ip(self):
        s=sample('fastconnect');s['resources']=[r for r in s['resources'] if r['id']!='qa-cross-group']
        nodes,edges=diagram_graph(s)
        self.assertIn('unknown:qa-cross-group',nodes)
        self.assertTrue(any(e['source']=='qa-fc' and e['target']=='unknown:qa-cross-group' for e in edges))
        self.assertFalse(any(e['source']=='qa-fc' and nodes[e['target']]['kind']=='cpe' for e in edges))
        xml=render(prepare_display(s));validate(xml,prepare_display(s))

    def test_direct_port_mapping_keeps_its_observed_group_and_siblings_together(self):
        s=sample('fastconnect')
        next(r for r in s['resources'] if r['id']=='qa-fc')['cross_connect_mappings'][0]['cross_connect_or_cross_connect_group_id']='qa-cross-connect'
        display=prepare_display(s);scene=make_scene(display,view='overview')
        self.assertEqual(check_plan(scene,seed_plan(scene)),[])
        xml=render(display);validate(xml,display)
        root=E.fromstring(xml).find('diagram/mxGraphModel/root')
        self.assertEqual(root.find("mxCell[@id='qa-cross-connect']").get('parent'),'qa-cross-group')
        self.assertTrue(any(e['source']=='qa-fc' and e['target']=='qa-cross-connect' and e['kind']=='cross_connect_mapping' for e in graph(s)[1]))
