import copy
import unittest
import xml.etree.ElementTree as E

from oci_lenz.model import sample
from oci_lenz.draw import render, validate


class ReferenceLayoutTests(unittest.TestCase):
    def test_expand_many_subnets_and_resources(self):
        snapshot = sample()
        for i in range(8):
            snapshot['resources'].append(dict(id=f'sub-{i}', name=f'Subnet {i}',
                kind='subnet', vcn_id='vcn', public=False))
        for i in range(18):
            snapshot['resources'].append(dict(id=f'vm-{i}', name=f'VM {i}', kind='compute'))
            snapshot['resources'].append(dict(id=f'nic-{i}', name=f'NIC {i}',
                kind='vnic', instance_id=f'vm-{i}', subnet_id='sub-0'))
        xml = render(snapshot)
        self.assertTrue(validate(xml, snapshot))
        self.assertEqual(xml, render(snapshot))

    def test_region_compartment_nesting_and_local_edge_parent(self):
        snapshot = sample()
        for resource in snapshot['resources']:
            resource['compartment_id'] = 'synthetic-compartment'
        doc = E.fromstring(render(snapshot))
        cells = {c.get('id'): c for c in doc.find('diagram').iter('mxCell')}
        vcn = cells['vcn']
        compartment = cells[vcn.get('parent')]
        region = cells[compartment.get('parent')]
        self.assertIn('Compartment', compartment.get('value'))
        self.assertIn('Region', region.get('value'))
        self.assertIn('dashed=1', vcn.get('style'))
        self.assertIn('#C66B3D', vcn.get('style'))
        for cell in cells.values():
            if cell.get('edge') and cell.get('source') == 'backend-set' and cell.get('target') == 'compute':
                self.assertEqual(cell.get('parent'), 'vcn')

    def test_overview_fixture_has_multiple_explicit_compartments(self):
        snapshot = sample('overview')
        self.assertEqual(sum(r['kind'] == 'vcn' for r in snapshot['resources']), 3)
        self.assertEqual(len(snapshot['scope']['compartments']), 2)
        self.assertTrue(all(c['source'] == 'synthetic' for c in snapshot['coverage']))
        validate(render(snapshot), snapshot)

    def test_reversed_inventory_has_same_layout(self):
        snapshot = sample()
        reversed_snapshot = copy.deepcopy(snapshot)
        reversed_snapshot['resources'].reverse()
        def geometry(s):
            doc = E.fromstring(render(s))
            return {c.get('id'): E.tostring(c.find('mxGeometry'))
                    for c in doc.find('diagram').iter('mxCell')
                    if c.get('vertex') == '1'}
        self.assertEqual(geometry(snapshot), geometry(reversed_snapshot))

    def test_structural_container_bounds_are_checked(self):
        snapshot = sample()
        doc = E.fromstring(render(snapshot))
        region = next(c for c in doc.find('diagram').iter('mxCell')
                      if c.get('id') == 'layout-region')
        region.find('mxGeometry').set('width', '1')
        with self.assertRaises(ValueError):
            validate(E.tostring(doc, encoding='unicode'), snapshot)

    def test_detail_page_cannot_drop_relationships(self):
        snapshot = sample()
        doc = E.fromstring(render(snapshot))
        root = doc.findall('diagram')[1].find('mxGraphModel/root')
        edge = next(c for c in root if c.get('edge') == '1')
        root.remove(edge)
        with self.assertRaises(ValueError):
            validate(E.tostring(doc, encoding='unicode'), snapshot)
