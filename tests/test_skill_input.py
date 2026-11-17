import json
import subprocess
import io
import sys
from contextlib import redirect_stderr
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from oci_lenz.cli import skill_layout,main,SkillLayoutTimeout
from oci_lenz.model import sample
from oci_lenz.display import prepare_display
from oci_lenz.architecture import make_scene,seed_plan


class SkillInputTests(unittest.TestCase):
    def test_layout_timeout_cli_reports_stage_without_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);snapshot=root/'snapshot.json'
            snapshot.write_text(json.dumps(sample()))
            err=io.StringIO()
            argv=['oci-lenz','draw','--snapshot',str(snapshot),'--output',str(root/'out'),'--skill-timeout','900']
            with patch.object(sys,'argv',argv),patch('oci_lenz.cli.skill_layout',side_effect=SkillLayoutTimeout()),patch('oci_lenz.cli.export') as export,redirect_stderr(err):
                with self.assertRaises(SystemExit) as caught:main()
            self.assertEqual(caught.exception.code,1)
            self.assertIn('Codex layout timed out',err.getvalue())
            self.assertIn('--skill-timeout 900',err.getvalue())
            export.assert_not_called()
            self.assertFalse((root/'out/architecture.drawio').exists())

    def test_png_timeout_cli_keeps_xml_and_redacts_child_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);snapshot=root/'snapshot.json'
            snapshot.write_text(json.dumps(sample()))
            err=io.StringIO();secret='PRIVATE-EXPORT-SENTINEL'
            argv=['oci-lenz','draw','--snapshot',str(snapshot),'--output',str(root/'out'),'--no-ai']
            with patch.object(sys,'argv',argv),patch('oci_lenz.cli.export',side_effect=subprocess.TimeoutExpired([secret],120,output=secret)),redirect_stderr(err):
                with self.assertRaises(SystemExit) as caught:main()
            self.assertEqual(caught.exception.code,1)
            self.assertIn('PNG export timed out',err.getvalue())
            self.assertNotIn(secret,err.getvalue())
            self.assertTrue((root/'out/architecture.drawio').exists())

    def test_nonpositive_timeout_rejected_before_generation(self):
        for value in ('0','-1'):
            with patch.object(sys,'argv',['oci-lenz','draw','--snapshot','unused','--output','unused','--skill-timeout',value]),redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as caught:main()
            self.assertEqual(caught.exception.code,2)

    def test_child_timeout_and_working_directory_are_explicit(self):
        snapshot=prepare_display(sample());geometry=seed_plan(make_scene(snapshot,view='overview'))
        def fake_run(command,**kwargs):
            self.assertEqual(kwargs['timeout'],900)
            self.assertNotEqual(Path(kwargs['cwd']).resolve(),Path.cwd())
            self.assertIn('--skip-git-repo-check',command)
            self.assertIn('--sandbox',command)
            self.assertIn('read-only',command)
            self.assertTrue(Path(command[command.index('-i')+1]).is_absolute())
            Path(command[command.index('-o')+1]).write_text(json.dumps(geometry))
            return SimpleNamespace(returncode=0)
        with tempfile.TemporaryDirectory() as tmp,patch('oci_lenz.cli.subprocess.run',side_effect=fake_run):
            self.assertEqual(skill_layout(snapshot,Path(tmp),[Path('synthetic-reference.png')],timeout=900)['version'],3)

    def test_timeout_error_does_not_expose_child_command_or_output(self):
        secret='PRIVATE-CHILD-ERROR-SENTINEL'
        failure=subprocess.TimeoutExpired([secret],240,output=secret,stderr=secret)
        with tempfile.TemporaryDirectory() as tmp,patch('oci_lenz.cli.subprocess.run',side_effect=failure):
            with self.assertRaises(TimeoutError) as caught:
                skill_layout(sample(),Path(tmp),[])
            self.assertNotIn(secret,str(caught.exception))
            self.assertFalse((Path(tmp)/'skill-layout.json').exists())

    def test_service_metadata_and_resource_identifiers_are_aliased(self):
        snapshot=prepare_display(sample('service-map'))
        geometry=seed_plan(make_scene(snapshot,view='overview'))
        snapshot['presentation']['groups'][0]['label']='PRIVATE-LABEL-SENTINEL'
        def fake_run(command,**kwargs):
            prompt=kwargs['input']
            self.assertNotIn('PRIVATE-LABEL-SENTINEL',prompt)
            self.assertNotIn('s1-vcn',prompt)
            self.assertNotIn('10.0.1.10',prompt)
            request=json.loads(prompt[prompt.index('{"view":'):])
            self.assertTrue(all(k.startswith('n') for k in request['items']))
            self.assertTrue(any(v['kind']=='service_group' for v in request['items'].values()))
            Path(command[command.index('-o')+1]).write_text(json.dumps(geometry))
            return SimpleNamespace(returncode=0)
        with tempfile.TemporaryDirectory() as tmp,patch('oci_lenz.cli.subprocess.run',side_effect=fake_run):
            self.assertEqual(skill_layout(snapshot,Path(tmp),[])['version'],3)
