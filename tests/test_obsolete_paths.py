"""Remove obsolete state without weakening current graph/privacy checks."""
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
from contextlib import redirect_stderr
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as E
from oci_lenz.model import sample
from oci_lenz.display import prepare_display
from oci_lenz.architecture import make_scene,seed_plan,apply_design
from oci_lenz.draw import render,validate
from oci_lenz.cli import main


class ObsoletePathTests(unittest.TestCase):
    def test_cli_retired_layout_has_safe_regeneration_guidance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);snapshot=root/'snapshot.json';snapshot.write_text(json.dumps(sample()))
            plan=root/'old-layout.json';plan.write_text(json.dumps({'version':2,'private':'PRIVATE-LAYOUT-SENTINEL'}))
            argv=['oci-lenz','draw','--snapshot',str(snapshot),'--reuse-layout',str(plan),'--output',str(root/'out')]
            errors=io.StringIO()
            with patch.object(sys,'argv',argv),patch('oci_lenz.cli.skill_layout') as model,redirect_stderr(errors):
                with self.assertRaises(SystemExit) as failure:main()
            self.assertEqual(failure.exception.code,1)
            self.assertIn('without --reuse-layout',errors.getvalue())
            self.assertNotIn('PRIVATE-LAYOUT-SENTINEL',errors.getvalue())
            model.assert_not_called()
            self.assertFalse((root/'out/architecture.drawio').exists())

    def test_scene_has_no_unused_precomputed_boxes(self):
        scene=make_scene(prepare_display(sample()),view='overview')
        self.assertFalse('boxes' in scene,'Unused scene boxes remain')
        self.assertTrue(seed_plan(scene)['placements'])

    def test_old_top_level_plan_is_rejected_before_building_a_scene(self):
        snapshot=prepare_display(sample())
        old=seed_plan(make_scene(snapshot))
        for plan in (old,{}, {'version':1}):
            with self.subTest(plan=plan.get('version')),patch('oci_lenz.architecture.make_scene') as build:
                with self.assertRaisesRegex(ValueError,'version-3.*regenerate'):
                    apply_design(snapshot,plan)
                build.assert_not_called()

    def test_summary_keeps_only_addresses_but_appendix_retains_ports(self):
        snapshot=sample();original=copy.deepcopy(snapshot)
        lb=next(r for r in snapshot['resources'] if r['kind']=='lb')
        lb['listeners']=[{'name':'Synthetic listener','protocol':'HTTP','port':8080,'default_backend_set_name':'Synthetic targets'}]
        before=copy.deepcopy(snapshot);display=prepare_display(snapshot)
        self.assertEqual(snapshot,before)
        for resource in display['resources']:
            self.assertFalse(any(v.startswith(('Listen ','Backend ports:')) for v in resource['summary_details']))
        doc=E.fromstring(render(display));index=E.tostring(doc.find("diagram[@id='information-index']"),encoding='unicode')
        self.assertIn('Synthetic listener HTTP:8080',index)
        self.assertIn('10.0.1.10:8080',index)
        self.assertEqual(original['resources'][0],snapshot['resources'][0])

    def test_detached_legacy_labels_are_rejected_as_extra_vertices(self):
        snapshot=prepare_display(sample());doc=E.fromstring(render(snapshot))
        root=doc.find('diagram/mxGraphModel/root')
        cell=E.SubElement(root,'mxCell',id='compute-label-name',value='Old detached label',vertex='1',parent='compute',style='text;')
        E.SubElement(cell,'mxGeometry',x='0',y='0',width='20',height='10',**{'as':'geometry'})
        with self.assertRaises(ValueError):validate(E.tostring(doc,encoding='unicode'),snapshot)
