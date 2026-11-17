"""Synthetic scope names and stable output filenames; no live OCI access."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as E
from oci_lenz.model import sample
from oci_lenz.display import prepare_display
from oci_lenz.architecture import make_scene
from oci_lenz.draw import render,export,validate
from oci_lenz.visual_review import masked_preview


class ScopeHeadingTests(unittest.TestCase):
    def snapshot(self):
        s=sample();s['scope'].update(tenancy_name='Synthetic Tenant',compartment_names={'sample':'Synthetic Project'})
        return s

    def test_operational_heading_displays_api_names_and_region(self):
        s=prepare_display(self.snapshot());xml=render(s,style='architecture');validate(xml,s)
        value=E.fromstring(xml).find("diagram/mxGraphModel/root/mxCell[@id='notice']").get('value')
        self.assertIn('Synthetic Tenant',value);self.assertIn('Synthetic Project',value)
        self.assertIn('sample-region',value);self.assertNotIn('Actual resource names',value)

    def test_legacy_scope_names_are_unknown_without_printing_ids(self):
        s=sample();s['scope']['compartments']=['ocid1.compartment.oc1..synthetic']
        s['scope'].pop('tenancy_name',None);s['scope'].pop('compartment_names',None)
        xml=render(prepare_display(s),style='architecture')
        value=E.fromstring(xml).find("diagram/mxGraphModel/root/mxCell[@id='notice']").get('value')
        self.assertIn('이름 미확인',value);self.assertNotIn('ocid1.',value)

    def test_names_stay_local_and_are_hidden_in_redacted_heading(self):
        s=self.snapshot();before=copy.deepcopy(s)
        safe=prepare_display(s);scene=make_scene(safe,view='overview')
        self.assertNotIn('Synthetic Tenant',json.dumps(scene['request']))
        self.assertNotIn('Synthetic Project',json.dumps(scene['request']))
        preview=masked_preview(render(safe,style='architecture'),safe,scene)
        redacted=render(prepare_display(s,redact=True),style='architecture')
        for xml in (preview,redacted):
            self.assertNotIn('Synthetic Tenant',xml);self.assertNotIn('Synthetic Project',xml)
        self.assertEqual(s,before)

    def test_long_multi_compartment_heading_stays_above_ai_region(self):
        s=self.snapshot();s['scope']['compartments']=['sample','second']
        s['scope']['compartment_names']['second']='가상 프로젝트 '*200
        xml=render(prepare_display(s),style='architecture');root=E.fromstring(xml).find('diagram/mxGraphModel/root')
        heading=root.find("mxCell[@id='notice']/mxGeometry");region=root.find("mxCell[@id='layout-region']/mxGeometry")
        self.assertLess(float(heading.get('y'))+float(heading.get('height')),float(region.get('y')))
        self.assertIn('Synthetic Project',root.find("mxCell[@id='notice']").get('value'))

    def test_whole_environment_png_is_architecture_png(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'architecture.drawio';source.write_text(render(prepare_display(self.snapshot()),style='architecture'))
            def write_png(cmd,**kwargs):Path(cmd[cmd.index('-o')+1]).write_bytes(b'\x89PNG\r\n\x1a\n')
            with patch('oci_lenz.draw.find_drawio',return_value='synthetic-drawio'),patch('oci_lenz.draw.subprocess.run',side_effect=write_png):
                files=export(source)
            self.assertEqual([p.name for p in files],['architecture.png','information-index.png'])
            self.assertFalse((Path(tmp)/'region.png').exists())
