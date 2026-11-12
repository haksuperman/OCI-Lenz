import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('executor', Path(__file__).parents[1] / 'scripts/execute.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.phase = self.root / 'phases/demo'
        self.phase.mkdir(parents=True)
        (self.root / 'AGENTS.md').write_text('project guardrail')
        (self.phase / 'step0.md').write_text('Implement demo')
        self.index = {'project': 'demo', 'phase': 'demo', 'steps': [
            {'step': 0, 'name': 'demo', 'status': 'pending',
             'ac': [['python3', '-c', 'pass']]}]}
        self.save()

    def save(self):
        (self.phase / 'index.json').write_text(json.dumps(self.index))

    def executor(self):
        return mod.StepExecutor('demo', root=self.root)

    def state(self):
        return json.loads((self.phase / 'index.json').read_text())

    def test_success_runs_ac_and_records_metadata_only(self):
        with patch.object(mod, 'invoke_codex', return_value='completed') as invoke:
            self.assertEqual(self.executor().run(), 0)
        self.assertIn('project guardrail', invoke.call_args.args[1])
        state = self.state()
        self.assertEqual(state['steps'][0]['status'], 'completed')
        self.assertIn('completed_at', state)
        output = json.loads((self.phase / 'step0-output.json').read_text())
        self.assertNotIn('stdout', output)
        self.assertEqual(output['attempts'][0]['ac_exit_codes'], [0])

    def test_failed_ac_retries_and_cannot_claim_completion(self):
        self.index['steps'][0]['ac'] = [['python3', '-c', 'raise SystemExit(1)']]
        self.save()
        with patch.object(mod, 'invoke_codex', return_value='completed') as invoke:
            self.assertEqual(self.executor().run(), 1)
        self.assertEqual(invoke.call_count, 3)
        self.assertEqual(self.state()['steps'][0]['status'], 'error')

    def test_blocked_stops_without_retry(self):
        with patch.object(mod, 'invoke_codex', return_value='blocked') as invoke:
            self.assertEqual(self.executor().run(), 2)
            self.assertEqual(self.executor().run(), 2)
        self.assertEqual(invoke.call_count, 1)

    def test_timeout_is_bounded(self):
        with patch.object(mod, 'invoke_codex', side_effect=subprocess.TimeoutExpired('codex', 1)):
            self.assertEqual(self.executor().run(), 1)
        self.assertEqual(self.state()['steps'][0]['status'], 'error')

    def test_resume_skips_completed(self):
        with patch.object(mod, 'invoke_codex', return_value='completed') as invoke:
            self.assertEqual(self.executor().run(), 0)
            self.assertEqual(self.executor().run(), 0)
        self.assertEqual(invoke.call_count, 1)

    def test_reject_missing_ac_and_traversal(self):
        self.index['steps'][0]['ac'] = []
        self.save()
        with self.assertRaises(ValueError):
            self.executor()
        with self.assertRaises(ValueError):
            mod.StepExecutor('../escape', root=self.root)

    def test_codex_command_uses_stdin_sandbox_and_ephemeral(self):
        def fake_run(cmd, **kwargs):
            self.assertEqual(cmd[:2], ['codex', 'exec'])
            self.assertIn('workspace-write', cmd)
            self.assertIn('--ephemeral', cmd)
            self.assertFalse(any('dangerously' in arg for arg in cmd))
            self.assertEqual(kwargs['input'], 'prompt')
            self.assertEqual(kwargs['stdout'], subprocess.DEVNULL)
            Path(cmd[cmd.index('--output-last-message') + 1]).write_text('{"status":"completed"}')
            return subprocess.CompletedProcess(cmd, 0)
        with patch.object(mod.subprocess, 'run', side_effect=fake_run):
            self.assertEqual(mod.invoke_codex(self.root, 'prompt', 60), 'completed')

    def test_nonzero_codex_exit_not_success(self):
        with patch.object(mod.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1)):
            self.assertEqual(mod.invoke_codex(self.root, 'prompt', 60), 'error')

    def test_real_subprocess_protocol_and_phase(self):
        # Exercise stdin/schema/result exchange across a real process boundary,
        # without invoking a paid model or requiring credentials.
        binary = self.root / 'bin'
        binary.mkdir()
        fake = binary / 'codex'
        fake.write_text('''#!/usr/bin/env python3
import json, pathlib, sys
args = sys.argv[1:]
assert args[0] == 'exec'
assert 'Implement demo' in sys.stdin.read()
schema = json.loads(pathlib.Path(args[args.index('--output-schema') + 1]).read_text())
assert schema['additionalProperties'] is False
pathlib.Path(args[args.index('--output-last-message') + 1]).write_text('{"status":"completed"}')
print('sensitive stdout must be discarded')
print('sensitive stderr must be discarded', file=sys.stderr)
''')
        fake.chmod(0o755)
        with patch.dict(os.environ, {'PATH': str(binary) + os.pathsep + os.environ['PATH']}):
            self.assertEqual(self.executor().run(), 0)
        self.assertNotIn('sensitive', (self.phase / 'step0-output.json').read_text())

    def test_invalid_model_output_rejected(self):
        def fake(cmd, **kwargs):
            Path(cmd[cmd.index('--output-last-message') + 1]).write_text('not json')
            return subprocess.CompletedProcess(cmd, 0)
        with patch.object(mod.subprocess, 'run', side_effect=fake):
            self.assertEqual(mod.invoke_codex(self.root, 'prompt', 60), 'error')

    def test_phase_lock_prevents_concurrent_run(self):
        (self.phase / '.executor.lock').mkdir()
        with self.assertRaises(ValueError):
            self.executor().run()


if __name__ == '__main__':
    unittest.main()
