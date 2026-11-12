# OCI-Lenz

## Scope
- Python 3.10+ standard library harness; OCI SDK and Draw.io integration are future work.
- Read `docs/HARNESS.md`, `docs/PRD.md`, `docs/ARCHITECTURE.md`, and `docs/ADR.md` before changes.
- Use the phase/step workflow from `docs/HARNESS.md`. Each step must specify readable inputs, interfaces, scope, executable AC, and concrete prohibitions.

## Rules
- Write meaningful tests before implementing features. Run `python3 -m unittest discover -s tests -v`.
- Keep OCI access read-only and explicitly scoped. Never change IAM policies.
- Never print, commit, or persist private keys, passwords, credentials, or raw OCI responses. Use local runtime profiles.
- Missing OCI credentials do not block synthetic snapshot work; keep live validation in a separate phase.
- Keep resources and relationships evidence-based and layout deterministic.
- Do not bypass sandbox/approval controls. Do not spawn agents unless explicitly requested.
- Do not automatically commit or push. When requested, use conventional commit messages.
- Phase status belongs to the executor; do not change AC or executor code to make a task pass.

## Checks
```sh
python3 -m unittest discover -s tests -v
python3 scripts/execute.py 0-harness-check --check
```
