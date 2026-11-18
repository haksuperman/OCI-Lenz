import copy
import unittest
import xml.etree.ElementTree as E
from oci_lenz.model import sample,graph
from oci_lenz.display import prepare_display
from oci_lenz.draw import render,validate
from oci_lenz.architecture import make_scene,seed_plan,check_plan
from oci_lenz.diagram_model import diagram_graph


class VpnContainerTests(unittest.TestCase):
    def test_native_vpn_contains_tunnels_and_keeps_external_endpoints_outside(self):
        s=prepare_display(sample('drg-centered'));before=copy.deepcopy(s);xml=render(s,detail_pages=True);validate(xml,s)
        for page in E.fromstring(xml).findall('diagram'):
            if page.get('id')=='information-index':continue
            cells={c.get('id'):c for c in page.iter('mxCell')}
            for key in ('qa-tunnel-0','qa-tunnel-1'):
                if key not in cells:continue
                self.assertIn('qa-vpn',cells)
                self.assertEqual(cells[key].get('parent'),'qa-vpn')
                self.assertEqual(cells['qa-vpn'].get('ociVPNContainer'),'1')
                self.assertIn('Syntheticsite-to-siteVPN',''.join(cells['qa-vpn'].get('value').split()))
            if 'qa-cpe' in cells:self.assertEqual(cells['qa-cpe'].get('parent'),'layout-region')
            self.assertEqual(cells['qa-drg'].get('parent'),'layout-region')
            for i,e in enumerate(diagram_graph(s)[1]):
                if e['kind']=='ipsec_id' and 'edge-'+str(i) in cells:self.assertEqual(cells['edge-'+str(i)].get('visible'),'0')
        self.assertEqual(s,before);self.assertEqual(graph(s),graph(before))

    def test_ai_scene_has_api_owned_containers_and_no_redundant_membership_wires(self):
        s=prepare_display(sample('drg-centered'));scene=make_scene(s,view='overview');a=scene['aliases']
        self.assertTrue(scene['items'][a['qa-vpn']]['container'])
        for key in ('qa-tunnel-0','qa-tunnel-1'):
            self.assertEqual(scene['items'][a[key]]['parent'],a['qa-vpn'])
        self.assertFalse(any(e['kind']=='ipsec_id' for e in scene['request']['edges']))
        self.assertEqual(check_plan(scene,seed_plan(scene)),[])

    def test_native_tunnel_parent_cannot_be_changed_without_api_evidence(self):
        s=prepare_display(sample('drg-centered'));doc=E.fromstring(render(s));root=doc.find('diagram/mxGraphModel/root')
        root.find("mxCell[@id='qa-tunnel-0']").set('parent','layout-region')
        with self.assertRaisesRegex(ValueError,'tunnel parent'):validate(E.tostring(doc,encoding='unicode'),s)

    def test_same_address_does_not_merge_vpns_and_unknown_owner_is_not_guessed(self):
        s=sample('drg-centered')
        s['resources'].extend([
            {'id':'second-vpn','kind':'ipsec','name':'Synthetic second VPN','drg_id':'qa-drg','cpe_id':'qa-cpe'},
            {'id':'second-tunnel','kind':'ipsec_tunnel','name':'Synthetic second tunnel','ipsec_id':'second-vpn','ip_addresses':['198.51.100.10']},
            {'id':'outside-tunnel','kind':'ipsec_tunnel','name':'Synthetic outside owner','ipsec_id':'unselected-vpn'}])
        s=prepare_display(s);xml=render(s);validate(xml,s);cells={c.get('id'):c for c in E.fromstring(xml).find('diagram').iter('mxCell')}
        self.assertEqual(cells['second-tunnel'].get('parent'),'second-vpn')
        self.assertEqual(cells['qa-tunnel-0'].get('parent'),'qa-vpn')
        self.assertEqual(cells['outside-tunnel'].get('parent'),'layout-region')
        self.assertIn('unknown:unselected-vpn',cells)
        self.assertNotIn('unselected-vpn',cells)

    def test_empty_vpn_remains_a_named_container_without_invented_tunnels(self):
        s=sample();s['resources'].append({'id':'empty-vpn','kind':'ipsec','name':'Synthetic empty VPN'})
        s=prepare_display(s);xml=render(s);validate(xml,s);cells={c.get('id'):c for c in E.fromstring(xml).find('diagram').iter('mxCell')}
        self.assertEqual(cells['empty-vpn'].get('ociVPNContainer'),'1')
        self.assertFalse(any(c.get('parent')=='empty-vpn' for c in cells.values()))

    def test_drg_and_cpe_cannot_be_reparented_into_the_vpn(self):
        for kind in ('drg','cpe'):
            with self.subTest(endpoint=kind):
                s=sample('empty');s['resources']=[{'id':'vpn','kind':'ipsec','name':'Synthetic isolated VPN'},
                    {'id':'endpoint','kind':kind,'name':'Synthetic regional endpoint'}]
                s=prepare_display(s);doc=E.fromstring(render(s));root=doc.find('diagram/mxGraphModel/root')
                region=root.find("mxCell[@id='layout-region']/mxGeometry");region.set('width','2000');region.set('height','800')
                vpn=root.find("mxCell[@id='vpn']/mxGeometry");vpn.set('width','600');vpn.set('height','400')
                endpoint=root.find("mxCell[@id='endpoint']");endpoint.set('parent','vpn')
                geometry=endpoint.find('mxGeometry');geometry.set('x','350');geometry.set('y','80')
                with self.assertRaisesRegex(ValueError,'outside VPN'):validate(E.tostring(doc,encoding='unicode'),s)
