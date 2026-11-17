import unittest
import xml.etree.ElementTree as E
from oci_lenz.model import sample,graph
from oci_lenz.display import prepare_display
from oci_lenz.architecture import make_scene,seed_plan,apply_design,compact_snapshot
from oci_lenz.draw import validate


class ReadabilityTests(unittest.TestCase):
    def test_overview_has_independent_ai_scene_and_preserves_full_detail(self):
        s=prepare_display(sample())
        overview=make_scene(s,view='overview');detail=make_scene(s)
        self.assertFalse(any(r['kind'] in ('route','nsg','vnic') for r in overview['items'].values()))
        self.assertTrue(any(r['kind']=='vnic' for r in detail['items'].values()))
        plan={'version':3,'overview':seed_plan(overview),'detail':seed_plan(detail)}
        xml=apply_design(s,plan,detail_pages=True);validate(xml,s)
        doc=E.fromstring(xml)
        summary={c.get('id'):c for c in doc.find('diagram').iter('mxCell')}
        details={c.get('id'):c for c in doc.findall('diagram')[1].iter('mxCell')}
        for key in ('vnic','app-nsg','private-rt'):
            self.assertEqual(summary[key].get('visible'),'0')
            self.assertNotEqual(details[key].get('visible'),'0')
        self.assertTrue(set(graph(s)[0])<=set(summary))

    def test_default_output_has_one_architecture_canvas_and_information_appendix(self):
        s=prepare_display(sample('overview'))
        xml=apply_design(s);validate(xml,s)
        doc=E.fromstring(xml)
        self.assertEqual([p.get('id') for p in doc.findall('diagram')],['region','information-index'])
        self.assertEqual(doc.get('pageMode'),'single')

    def test_public_and_primary_ip_survive_many_secondary_ips(self):
        s=sample();v=next(r for r in s['resources'] if r['kind']=='vnic')
        v.update(private_ips=['10.0.1.'+str(i) for i in range(10,50)],
                 primary_private_ip='10.0.1.49',is_primary=True,public_ip='192.0.2.10')
        s=prepare_display(s);compact=compact_snapshot(s)
        compute=next(r for r in compact['resources'] if r['kind']=='compute')
        self.assertIn('Private: 10.0.1.49',compute['display_details'])
        self.assertIn('Public: 192.0.2.10',compute['display_details'])
        full=next(r for r in s['resources'] if r['kind']=='compute')
        self.assertTrue(all(any(ip in d for d in full['display_details']) for ip in v['private_ips']))

    def test_cards_show_names_and_observed_ips_without_detail_comments(self):
        s=sample();lb=next(r for r in s['resources'] if r['kind']=='lb')
        lb['listeners']=[{'name':'https','protocol':'TCP','port':443,'default_backend_set_name':'backend-set'}]
        lb['ip_addresses']=[{'ip_address':'192.0.2.10','is_public':True}]
        s=prepare_display(s);compact=compact_snapshot(s)
        labels={r['kind']:r['display_details'] for r in compact['resources']}
        self.assertEqual(labels['lb'],['Public: 192.0.2.10'])
        self.assertEqual(labels['backend_set'],[])
        xml=apply_design(s);validate(xml,s)
        doc=E.fromstring(xml)
        overview_values='\n'.join(c.get('value','') for c in doc.find('diagram').iter('mxCell'))
        for comment in ('More: information index','Listen TCP','Backend ports:'):
            self.assertNotIn(comment,overview_values)
        index_values='\n'.join(c.get('value','') for c in doc.find("diagram[@id='information-index']").iter('mxCell'))
        self.assertIn('TCP:443',index_values);self.assertIn('10.0.1.10:8080',index_values)

    def test_network_cidrs_remain_and_no_ip_resource_has_no_extra_text(self):
        s=sample();next(r for r in s['resources'] if r['kind']=='vcn')['cidr_blocks']=['10.0.0.0/16']
        s=prepare_display(s);compact=compact_snapshot(s)
        resources={r['id']:r for r in compact['resources']}
        self.assertEqual(resources['vcn']['display_details'],['10.0.0.0/16'])
        self.assertEqual(resources['nat']['display_details'],[])

    def test_redacted_cards_do_not_leak_prior_summary_fields(self):
        s=prepare_display(sample())
        s['resources'][0]['summary_details']=['PRIVATE-SENTINEL']
        safe=compact_snapshot(prepare_display(s,redact=True))
        self.assertNotIn('PRIVATE-SENTINEL',str([r.get('display_details') for r in safe['resources']]))

    def test_compute_placement_uses_primary_vnic_evidence(self):
        s=sample();next(r for r in s['resources'] if r['kind']=='vnic')['is_primary']=True
        s['resources'].append({'id':'aaa-secondary','kind':'vnic','name':'Synthetic secondary NIC',
                               'instance_id':'compute','subnet_id':'public','vcn_id':'vcn','is_primary':False})
        scene=make_scene(prepare_display(s),view='overview')
        self.assertEqual(scene['items'][scene['aliases']['compute']]['parent'],scene['aliases']['private'])
