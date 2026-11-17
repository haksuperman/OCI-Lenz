import io
import json
import os
from pathlib import Path
import sys
import tempfile
import subprocess
import unittest
from contextlib import redirect_stdout,redirect_stderr
from types import SimpleNamespace as N
from unittest.mock import patch
from oci_lenz.cli import main
from oci_lenz.ai import request_json,AIConfigurationError


class OnboardingTests(unittest.TestCase):
    def test_doctor_runs_without_output_directory_or_network_collection(self):
        report={'ready':True,'checks':[{'name':'python','status':'ok'}]}
        with patch.object(sys,'argv',['oci-lenz','doctor','--json']),patch('oci_lenz.diagnostics.environment_report',return_value=report),patch('oci_lenz.collect.collect') as collect,redirect_stdout(io.StringIO()) as output:
            main()
        self.assertEqual(json.loads(output.getvalue()),report)
        collect.assert_not_called()

    def test_missing_codex_has_actionable_static_error(self):
        with patch('oci_lenz.ai.subprocess.run',side_effect=FileNotFoundError('PRIVATE-SENTINEL')):
            with self.assertRaises(AIConfigurationError) as exc:request_json('task',{},[])
        self.assertIn('Codex',str(exc.exception));self.assertNotIn('PRIVATE-SENTINEL',str(exc.exception))

    def test_openai_doctor_needs_no_codex_and_never_prints_runtime_values(self):
        from oci_lenz.diagnostics import environment_report
        with patch.dict(os.environ,{'OPENAI_API_KEY':'PRIVATE-KEY-SENTINEL'},clear=True),patch('oci_lenz.diagnostics.subprocess.run') as run:
            result=environment_report('openai',model='synthetic-model',require_png=False)
        self.assertTrue(result['ready'])
        self.assertNotIn('PRIVATE-KEY-SENTINEL',json.dumps(result))
        run.assert_not_called()

    def test_openai_doctor_distinguishes_missing_key_and_model(self):
        from oci_lenz.diagnostics import environment_report
        with patch.dict(os.environ,{},clear=True):result=environment_report('openai',require_png=False)
        self.assertFalse(result['ready'])
        checks={c['name']:c for c in result['checks']}
        self.assertEqual(checks['api_key']['status'],'missing')
        self.assertEqual(checks['api_model']['status'],'missing')

    def test_doctor_suppresses_codex_output_and_handles_unavailable_login(self):
        from oci_lenz.diagnostics import environment_report
        with patch('oci_lenz.diagnostics.shutil.which',return_value='/synthetic/codex'),patch('oci_lenz.diagnostics.subprocess.run',return_value=N(returncode=1)) as run:
            result=environment_report('codex',require_png=False)
        self.assertFalse(result['ready'])
        self.assertEqual(run.call_args.kwargs['stdout'],-3)
        self.assertEqual(run.call_args.kwargs['stderr'],-3)
        self.assertEqual(next(c for c in result['checks'] if c['name']=='codex_login')['status'],'unavailable')

    def test_doctor_cli_exit_code_reports_unready_environment(self):
        report={'ready':False,'checks':[{'name':'codex','status':'missing','hint':'Install Codex CLI.'}]}
        with patch.object(sys,'argv',['oci-lenz','doctor','--json']),patch('oci_lenz.diagnostics.environment_report',return_value=report),redirect_stdout(io.StringIO()) as output:
            with self.assertRaises(SystemExit) as exc:main()
        self.assertEqual(exc.exception.code,2)
        self.assertFalse(json.loads(output.getvalue())['ready'])

    def test_missing_assets_are_detected_without_exposing_paths(self):
        from oci_lenz.diagnostics import environment_report
        with tempfile.TemporaryDirectory() as tmp,patch('oci_lenz.diagnostics.ROOT',Path(tmp)),patch.dict(os.environ,{'OPENAI_API_KEY':'TEST-SENTINEL'},clear=True):
            result=environment_report('openai',model='test-model',require_png=False)
            self.assertNotIn(tmp,json.dumps(result))
        self.assertFalse(result['ready'])
        self.assertEqual(next(c for c in result['checks'] if c['name']=='stencils')['status'],'missing')

    def test_login_timeout_is_reported_without_child_command_or_output(self):
        from oci_lenz.diagnostics import environment_report
        with patch('oci_lenz.diagnostics.shutil.which',return_value='/synthetic/codex'),patch('oci_lenz.diagnostics.subprocess.run',side_effect=subprocess.TimeoutExpired(['PRIVATE-COMMAND'],15,output='PRIVATE-OUTPUT')):
            result=environment_report('codex',require_png=False)
        self.assertFalse(result['ready'])
        self.assertNotIn('PRIVATE',json.dumps(result))

    def test_invalid_explicit_drawio_path_is_not_silently_replaced(self):
        from oci_lenz.draw import find_drawio
        with patch.dict(os.environ,{'DRAWIO_BIN':'/synthetic/missing-binary'}),patch('oci_lenz.draw.shutil.which',return_value=None):
            self.assertIsNone(find_drawio())

    def test_per_user_macos_drawio_location_is_supported(self):
        from oci_lenz.draw import find_drawio
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp);candidate=home/'Applications/draw.io.app/Contents/MacOS/draw.io'
            candidate.parent.mkdir(parents=True);candidate.write_text('');candidate.chmod(0o700)
            with patch.dict(os.environ,{},clear=True),patch('oci_lenz.draw.sys.platform','darwin'),patch('oci_lenz.draw.shutil.which',return_value=None),patch('oci_lenz.draw.Path.home',return_value=home),patch('oci_lenz.draw.Path.is_file',lambda value:value==candidate):
                self.assertEqual(find_drawio(),str(candidate))
