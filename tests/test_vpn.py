import unittest
from tests import test_collect as fixtures
from oci_lenz.model import graph, sample
from oci_lenz.display import prepare_display
from oci_lenz.architecture import make_scene
oci=fixtures.oci


@unittest.skipIf(oci is None,'install OCI SDK')
class VpnCollectorTests(unittest.TestCase):
    def extra(self):
        m=oci.core.models
        return {'list_cpes':[m.Cpe(id='cpe',compartment_id='c',display_name='Synthetic CPE',ip_address='192.0.2.1',freeform_tags={'private':'never-store'})],
            'list_ip_sec_connections':[m.IPSecConnection(id='vpn',compartment_id='c',display_name='Synthetic VPN',cpe_id='cpe',drg_id='outside-drg',static_routes=['10.20.0.0/16'])],
            'list_ip_sec_connection_tunnels':[m.IPSecConnectionTunnel(id='tun',display_name='Synthetic tunnel',vpn_ip='198.51.100.1',cpe_ip='192.0.2.1',status='UP',routing='BGP')],
            'list_drg_attachments':[m.DrgAttachment(id='att',drg_id='outside-drg',network_details=m.IpsecTunnelDrgAttachmentNetworkDetails(id='tun'))]}

    def test_allowlisted_scoped_tunnels_resolve_attachment(self):
        s,calls=fixtures.CollectorTests().run_collect(extra=self.extra());nodes,edges=graph(s)
        self.assertEqual(nodes['tun']['ipsec_id'],'vpn')
        self.assertEqual(nodes['tun']['status'],'UP')
        self.assertEqual(set(nodes['tun']),{'id','kind','name','ipsec_id','ip_addresses','cpe_ip','status','routing','lifecycle_state'})
        self.assertTrue(any(e['source']=='att' and e['target']=='tun' for e in edges))
        membership=next(e for e in edges if e['source']=='tun' and e['kind']=='ipsec_id')
        self.assertEqual(membership['evidence'],'ListIPSecConnectionTunnels.ipsc_id (request scope)')
        self.assertIn('unknown:outside-drg',nodes)
        self.assertTrue(any(e['source']=='vpn' and e['target']=='cpe' for e in edges))
        self.assertNotIn('never-store',str(s))
        self.assertFalse(any('secret' in n or 'config' in n or n.startswith(('create_','update_','delete_')) for n in calls))
        self.assertFalse(any(c.get('resource_type')=='IPSEC_TUNNEL' and c['status']=='unsupported' for c in s['coverage']))

    def test_denied_tunnels_preserve_connection_and_unknown_target(self):
        s,_=fixtures.CollectorTests().run_collect(fail='list_ip_sec_connection_tunnels',extra=self.extra());nodes,_=graph(s)
        self.assertIn('vpn',nodes);self.assertIn('unknown:tun',nodes)
        self.assertEqual(next(c for c in s['coverage'] if c.get('api')=='list_ip_sec_connection_tunnels')['status'],'permission_denied')
        empty,_=fixtures.CollectorTests().run_collect()
        self.assertEqual(next(c for c in empty['coverage'] if c.get('api')=='list_ip_sec_connections')['count'],0)

    def test_each_connection_uses_its_own_tunnel_request_scope(self):
        from oci_lenz.vpn import collect_vpn
        from types import SimpleNamespace as N
        seen=[];resources=[]
        def call(service,api,*args,**kwargs):
            seen.append((api,args,kwargs))
            if api=='list_cpes':return []
            if api=='list_ip_sec_connections':return [N(id=x,cpe_id='external',drg_id='drg') for x in ('a','b')]
            return [N(id=args[0]+'-tunnel')]
        collect_vpn(call,lambda obj,kind,**fields:resources.append(dict(id=obj.id,kind=kind,**fields)),'scope')
        self.assertEqual([x[1] for x in seen if x[0]=='list_ip_sec_connection_tunnels'],[('a',),('b',)])
        self.assertEqual({r['id']:r['ipsec_id'] for r in resources if r['kind']=='ipsec_tunnel'},{'a-tunnel':'a','b-tunnel':'b'})


class VpnDisplayTests(unittest.TestCase):
    def test_synthetic_caption_privacy_and_evidence(self):
        s=sample('ipsec-vpn');nodes,edges=graph(s)
        self.assertEqual(sum(r['kind']=='ipsec_tunnel' for r in nodes.values()),2)
        self.assertTrue(all(e['evidence'] for e in edges))
        visible=prepare_display(s)
        tunnel=next(r for r in visible['resources'] if r['kind']=='ipsec_tunnel')
        self.assertIn('IP: 198.51.100.10',tunnel['summary_details'])
        self.assertNotIn('Status: UP',tunnel['summary_details'])
        self.assertIn('Status: UP',tunnel['display_details'])
        redacted=prepare_display(s,redact=True)
        self.assertFalse(any(r.get('summary_details') or r.get('display_details') for r in redacted['resources']))
        scene=make_scene(visible)
        self.assertNotIn('198.51.100.10',str(scene['request']))

    def test_native_editable_vpn_cells_and_edges_preserve_scope(self):
        import xml.etree.ElementTree as E
        from oci_lenz.draw import render,validate,ICONS
        s=prepare_display(sample('ipsec-vpn'))
        xml=render(s);validate(xml,s)
        cells={c.get('id'):c for c in E.fromstring(xml).find('diagram').iter('mxCell')}
        self.assertEqual(ICONS['cpe'],21)
        self.assertIn('qa-cpe-icon',cells)
        self.assertTrue(any(k.startswith('qa-cpe-i-') for k in cells))
        for key in ('qa-vpn','qa-tunnel-0','qa-tunnel-1'):
            self.assertEqual(cells[key].get('vertex'),'1')
            self.assertNotEqual(cells[key].get('visible'),'0')
            self.assertIn('rounded=1;',cells[key].get('style'))
            if key=='qa-vpn':self.assertEqual(cells[key].get('ociVPNContainer'),'1')
            else:self.assertIn('ociNativeLabel=1;',cells[key].get('style'))
        from oci_lenz.diagram_model import diagram_graph
        _,edges=diagram_graph(s)
        for i,e in enumerate(edges):
            if e['kind'] in ('cpe_id','ipsec_id'):
                c=cells['edge-'+str(i)]
                self.assertEqual(c.get('source'),e['source'])
                self.assertEqual(c.get('target'),e['target'])
                self.assertEqual(c.get('visible')=='0',e['kind']=='ipsec_id')
                self.assertIn('textOpacity=0;',c.get('style'))
        external=sample('ipsec-vpn')
        external['resources']=[r for r in external['resources'] if r['kind']!='cpe']
        scene=make_scene(prepare_display(external),view='overview')
        self.assertIn('unknown:qa-cpe',scene['aliases'])
