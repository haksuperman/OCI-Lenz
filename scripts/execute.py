#!/usr/bin/env python3
"""Codex phase executor, adapted from jha0313/harness_framework's workflow.

No automatic git operations. AC commands are trusted repository code.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
STATUSES = {'pending', 'completed', 'error', 'blocked'}


def stamp():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    # Replace atomically so interrupted writes do not truncate status files.
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                     delete=False) as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write('\n')
        temp = Path(handle.name)
    temp.replace(path)


def invoke_codex(root, prompt, timeout):
    # Only a status enum is returned; no free-form model output is persisted.
    with tempfile.TemporaryDirectory(prefix='oci-lenz-harness-') as folder:
        schema = Path(folder) / 'schema.json'
        result = Path(folder) / 'result.json'
        write(schema, {'type': 'object', 'properties': {
            'status': {'type': 'string', 'enum': ['completed', 'error', 'blocked']}},
            'required': ['status'], 'additionalProperties': False})
        cmd = ['codex', 'exec', '--sandbox', 'workspace-write', '--ephemeral',
               '--cd', str(root), '--output-schema', str(schema),
               '--output-last-message', str(result), '-']
        proc = subprocess.run(cmd, input=prompt, text=True, cwd=root,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                              timeout=timeout)
        if proc.returncode != 0 or not result.exists():
            return 'error'
        try:
            status = read(result)['status']
            return status if status in {'completed', 'error', 'blocked'} else 'error'
        except (ValueError, KeyError, TypeError):
            return 'error'


class StepExecutor:
    MAX_RETRIES = 3

    def __init__(self, phase, *, root=ROOT, timeout=1800):
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', phase):
            raise ValueError('phase must be a kebab-case directory name')
        self.root = Path(root).resolve()
        self.phase = phase
        self.directory = (self.root / 'phases' / phase).resolve()
        if not self.directory.is_relative_to(self.root / 'phases'):
            raise ValueError('phase escapes phases directory')
        self.index_path = self.directory / 'index.json'
        self.timeout = timeout
        index = read(self.index_path)
        if index.get('phase') != phase or not index.get('steps'):
            raise ValueError('phase mismatch or empty steps')
        for number, step in enumerate(index['steps']):
            if step['step'] != number or step['status'] not in STATUSES:
                raise ValueError('steps must be ordered from zero with valid status')
            if not (self.directory / f'step{number}.md').is_file():
                raise ValueError('missing step document')
            commands = step.get('ac')
            if not isinstance(commands, list) or not commands:
                raise ValueError('each step needs non-empty ac argv commands')
            for command in commands:
                if not isinstance(command, list) or not command or not all(
                        isinstance(arg, str) and arg for arg in command):
                    raise ValueError('AC must contain non-empty string argv lists')

    def update_top(self, status):
        path = self.root / 'phases/index.json'
        if path.exists():
            top = read(path)
            for phase in top['phases']:
                if phase['dir'] == self.phase:
                    phase['status'] = status
            write(path, top)

    def prompt(self, index, step, previous):
        paths = [self.root / 'AGENTS.md', *sorted((self.root / 'docs').glob('*.md'))]
        context = '\n\n'.join(p.read_text(encoding='utf-8') for p in paths if p.is_file())
        completed = [{ 'name': s['name'], 'summary': s.get('summary', '') }
                     for s in index['steps'] if s['status'] == 'completed']
        task = (self.directory / f"step{step['step']}.md").read_text(encoding='utf-8')
        return (f'{context}\nCompleted steps: {completed}\nPrevious attempt: {previous}\n'
                'Implement only the following step. Read its referenced files first. '
                'Write tests before implementation. Do not modify phase indexes, AC definitions, '
                'or harness execution code. Do not commit, push, or spawn other agents. '
                'Never print or store credentials, private keys, passwords, or raw OCI responses. '
                'If required authorization or credentials are unavailable, report blocked. '
                'Return only a JSON status matching the provided schema. The harness verifies AC.\n'
                f'{task}\nAC argv: {json.dumps(step["ac"])}')

    def run(self):
        # Exclusive phase lock also catches a second executor before any mutations.
        lock = self.directory / '.executor.lock'
        try:
            lock.mkdir()
        except FileExistsError:
            raise ValueError('phase locked; check for running executor before removing stale lock')
        try:
            return self._run()
        finally:
            lock.rmdir()

    def _run(self):
        index = read(self.index_path)
        for step in index['steps']:
            if step['status'] in {'blocked', 'error'}:
                self.update_top(step['status'])
                return 2 if step['status'] == 'blocked' else 1
        index.setdefault('created_at', stamp())
        write(self.index_path, index)
        for step in index['steps']:
            if step['status'] == 'completed':
                continue
            step['started_at'] = stamp()
            write(self.index_path, index)
            attempts = []
            previous = 'none'
            for attempt in range(1, self.MAX_RETRIES + 1):
                print(f"Step {step['step']}: {step['name']} (attempt {attempt}/3)", flush=True)
                codes = []
                try:
                    status = invoke_codex(self.root, self.prompt(index, step, previous), self.timeout)
                    if status == 'completed':
                        for command in step['ac']:
                            proc = subprocess.run(command, cwd=self.root, timeout=self.timeout,
                                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            codes.append(proc.returncode)
                        if any(codes):
                            status = 'error'
                    previous = f'agent status={status}; AC exit codes={codes}'
                except subprocess.TimeoutExpired:
                    status, previous = 'error', 'execution timeout'
                except OSError:
                    status, previous = 'error', 'executable unavailable or execution failed'
                attempts.append({'attempt': attempt, 'status': status, 'ac_exit_codes': codes,
                                 'diagnostic': previous})
                write(self.directory / f"step{step['step']}-output.json", {'attempts': attempts})
                if status in {'completed', 'blocked'}:
                    break
            step['status'] = status
            step[f'{status}_at'] = stamp()
            if status == 'completed':
                step['summary'] = f"{step['name']}: configured AC passed"
            else:
                step['blocked_reason' if status == 'blocked' else 'error_message'] = previous
            write(self.index_path, index)
            if status != 'completed':
                self.update_top(status)
                return 2 if status == 'blocked' else 1
        index['completed_at'] = stamp()
        write(self.index_path, index)
        self.update_top('completed')
        return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase')
    parser.add_argument('--timeout', type=int, default=1800, help='seconds per Codex call / AC command')
    parser.add_argument('--check', action='store_true', help='validate phase without invoking Codex')
    args = parser.parse_args()
    try:
        if args.timeout <= 0:
            raise ValueError('timeout must be positive')
        executor = StepExecutor(args.phase, timeout=args.timeout)
        return 0 if args.check else executor.run()
    except (ValueError, KeyError, FileNotFoundError):
        print('Invalid phase configuration or lock. See docs/HARNESS.md.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
