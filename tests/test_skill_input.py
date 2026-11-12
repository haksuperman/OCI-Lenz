import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from oci_lenz.cli import skill_layout
from oci_lenz.model import sample


class SkillInputTests(unittest.TestCase):
    def test_service_metadata_and_resource_identifiers_are_aliased(self):
        snapshot=sample('service-map')
        snapshot['presentation']['groups'][0]['label']='PRIVATE-LABEL-SENTINEL'
        def fake_run(command,**kwargs):
            prompt=kwargs['input']
            self.assertNotIn('PRIVATE-LABEL-SENTINEL',prompt)
            self.assertNotIn('s1-vcn',prompt)
            self.assertNotIn('10.0.1.10',prompt)
            request=json.loads(prompt.split('\n')[-1])
            self.assertEqual(request['style'],'service-map')
            self.assertTrue(all(k.startswith('r') for g in request['service_groups'] for k in g['vcn_ids']))
            Path(command[command.index('-o')+1]).write_text('{"positions":[]}')
            return SimpleNamespace(returncode=0)
        with tempfile.TemporaryDirectory() as tmp,patch('oci_lenz.cli.subprocess.run',side_effect=fake_run):
            self.assertEqual(skill_layout(snapshot,Path(tmp),[],style='service-map'),{})
