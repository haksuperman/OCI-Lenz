"""Synthetic Dedicated ADB regression; no model or OCI calls."""
import copy
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as E

from oci_lenz.model import sample, graph
from oci_lenz.display import prepare_display
from oci_lenz.draw import render, validate
from oci_lenz.architecture import make_scene
from oci_lenz.quality import assess
from oci_lenz.routing import path_quality, conflict_aware


class DatabaseRoutingTests(unittest.TestCase):
    def test_db_conflicts_participate_in_refinement_without_becoming_network_topology(self):
        for kind in ('autonomous_database', 'autonomous_container_database',
                     'cloud_autonomous_vm_cluster', 'vm_cluster', 'cloud_vm_cluster',
                     'exadb_vm_cluster', 'mysql_db_system', 'db_system'):
            with self.subTest(kind=kind):
                self.assertTrue(conflict_aware({'db': {'kind': kind}}, 'db', 'unknown'))
        paths = [dict(source='a', target='b', network=False, conflict_aware=True,
                      points=[(0, 50), (100, 50)]),
                 dict(source='c', target='d', network=False,
                      points=[(50, 0), (50, 100)])]
        self.assertEqual(path_quality(paths)['network_edge_crossings'], 1)
        self.assertFalse(any(p['network'] for p in paths))

    def test_dedicated_adb_ownership_chain_avoids_crossing_and_preserves_ai_geometry(self):
        snapshot = prepare_display(sample('autonomous-db'))
        plan = json.loads((Path(__file__).parent / 'fixtures/synthetic-dedicated-adb-layout.json').read_text())
        original = copy.deepcopy((snapshot, plan, graph(snapshot)))
        xml = render(snapshot, plan)
        validate(xml, snapshot)
        result = assess(snapshot, plan, xml=xml)
        for field in ('edge_crossings', 'edge_overlap_length', 'resource_intersections',
                      'title_intersections', 'nonorthogonal_segments'):
            with self.subTest(metric=field):
                self.assertEqual(result['metrics'][field], 0)
        self.assertEqual((snapshot, plan, graph(snapshot)), original)
        self.assertEqual(render(snapshot, plan), xml)
        cells = {c.get('id'): c for c in E.fromstring(xml).find('diagram').iter('mxCell')}

        def box(key):
            c = cells[key]
            g = c.find('mxGeometry')
            x, y, w, h = (float(g.get(k, 0)) for k in ('x', 'y', 'width', 'height'))
            parent = c.get('parent')
            if parent in cells and cells[parent].find('mxGeometry') is not None:
                px, py, _, _ = box(parent)
                x += px
                y += py
            return x, y, w, h

        scene = make_scene(snapshot, view='overview')
        for placement in plan['overview']['placements']:
            key = scene['keys'][placement['id']]
            self.assertEqual(box(key), tuple(placement[k] for k in ('x', 'y', 'width', 'height')))
