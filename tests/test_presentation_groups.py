import copy
import unittest
import xml.etree.ElementTree as E

from oci_lenz.model import sample, graph
from oci_lenz.draw import render, validate


class PresentationGroupTests(unittest.TestCase):
    def test_explicit_groups_and_compact_vertical_flow(self):
        s = sample('service-map')
        xml = render(s, style='architecture')
        validate(xml, s)
        root = E.fromstring(xml).find('diagram')
        cells = {c.get('id'): c for c in root.iter('mxCell')}
        self.assertEqual(len(s['presentation']['groups']), 4)
        for i, group in enumerate(s['presentation']['groups']):
            panel = cells[f'layout-service-{i}']
            for vcn in group['vcn_ids']:
                self.assertEqual(cells[vcn].get('parent'), panel.get('id'))
        # Explicit groups preserve native subnet and backend identities.
        self.assertEqual(cells['s1-public'].get('parent'),'s1-vcn')
        self.assertEqual(cells['s1-private'].get('parent'),'s1-vcn')
        nodes, edges = graph(s)
        self.assertTrue(any(e['kind'] == 'backend' for e in edges))
        self.assertTrue(all(c.get('source') in cells and c.get('target') in cells
                            for c in cells.values() if c.get('edge') == '1'))

    def test_unknown_or_duplicate_group_member_rejected(self):
        s = sample('service-map')
        s['presentation']['groups'][0]['vcn_ids'].append('not-a-vcn')
        with self.assertRaises(ValueError): render(s, style='architecture')
        s = sample('service-map')
        s['presentation']['groups'][1]['vcn_ids'].append('s1-vcn')
        with self.assertRaises(ValueError): render(s, style='architecture')

    def test_without_groups_does_not_guess_services(self):
        s = sample()
        xml = render(s, style='architecture')
        self.assertNotIn('layout-service-', xml)
        validate(xml, s)

    def test_large_inventory_and_automatic_compartment_groups(self):
        s = sample('overview')
        for i in range(24):
            s['resources'].extend([
                dict(id=f'extra-vm-{i}',name=f'VM {i}',kind='compute'),
                dict(id=f'extra-nic-{i}',name=f'VNIC {i}',kind='vnic',
                     instance_id=f'extra-vm-{i}',subnet_id='demo-1-private')])
        for i in range(7):
            s['resources'].append(dict(id=f'extra-subnet-{i}',name=f'Subnet {i}',
                                      kind='subnet',vcn_id='demo-1-vcn',public=False))
        xml = render(s, style='architecture')
        validate(xml, s)
        self.assertEqual(E.fromstring(xml).get('style'), 'architecture')
        self.assertNotIn('layout-service-', xml)
        self.assertEqual(xml, render(s, style='architecture'))
        cells={c.get('id'):c for c in E.fromstring(xml).find('diagram').iter('mxCell')}

    def test_many_vcns_wrap_with_bounded_spacing(self):
        s = sample('service-map')
        for i in range(12):
            rid=f'new-vcn-{i}'
            s['resources'].append(dict(id=rid,name=rid,kind='vcn',compartment_id='synthetic'))
            s['presentation']['groups'][0]['vcn_ids'].append(rid)
        xml=render(s,style='architecture');validate(xml,s)
        root=E.fromstring(xml).find('diagram')
        cells={c.get('id'):c for c in root.iter('mxCell')}
        ys={cells[k].find('mxGeometry').get('y') for k in s['presentation']['groups'][0]['vcn_ids']}
        self.assertGreater(len(ys),1)

    def test_unresolved_targets_and_secondary_vnic_are_preserved(self):
        s=sample()
        s['resources']=[r for r in s['resources'] if r['id']!='nat']
        s['resources'].append(dict(id='secondary',name='Secondary',kind='vnic',
                                  instance_id='compute',subnet_id='public'))
        next(r for r in s['resources'] if r['id']=='lb')['subnet_ids'].append('private')
        xml=render(s,style='architecture');validate(xml,s)
        self.assertIn('unknown:nat',xml)

    def test_unequal_shared_subnet_sizes_do_not_overlap(self):
        s=sample('service-map')
        for i in range(14):
            s['resources'].extend([
                dict(id=f'wide-vm-{i}',name='Synthetic VM',kind='compute'),
                dict(id=f'wide-nic-{i}',name='Synthetic NIC',kind='vnic',
                     instance_id=f'wide-vm-{i}',subnet_id='s5-public')])
        validate(render(s,style='architecture'),s)

    def test_information_index_preserves_many_attachments(self):
        s=sample()
        for i in range(30):
            s['resources'].append(dict(id=f'nic-{i}',name=f'NIC {i}',kind='vnic',
                subnet_id='private',instance_id='compute',nsg_ids=['app-nsg']))
        xml=render(s,style='architecture');validate(xml,s)
        index=E.fromstring(xml).find("diagram[@id='information-index']")
        rows=[c for c in index.iter('mxCell') if c.get('id','').startswith('information-')]
        self.assertEqual(len(rows),len(s['resources']))
        self.assertTrue(all('NIC '+str(i) in xml for i in range(30)))

    def test_shared_service_with_empty_public_subnet(self):
        s=sample('service-map')
        s['resources']=[r for r in s['resources'] if r['id'] not in ('s5-lb','s5-backend-set')]
        validate(render(s,style='architecture'),s)

    def test_deterministic_and_preserves_relationships(self):
        s = sample('service-map')
        self.assertEqual(render(s, style='architecture'), render(copy.deepcopy(s), style='architecture'))
        xml = render(s, style='architecture')
        doc = E.fromstring(xml)
        for page in doc.findall('diagram'):
            root = page.find('mxGraphModel/root')
            edge = next(c for c in root if c.get('edge') == '1')
            root.remove(edge)
            with self.assertRaises(ValueError): validate(E.tostring(doc, encoding='unicode'), s)
            break
