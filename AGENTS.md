# OCI-Lenz

## Scope
- Python 3.10+ application and standard library development harness. Read docs/USAGE.md for OCI SDK and Draw.io integration.
- Read `docs/HARNESS.md`, `docs/PRD.md`, `docs/ARCHITECTURE.md`, and `docs/ADR.md` before changes.
- Use the phase/step workflow from `docs/HARNESS.md`. Each step must specify readable inputs, interfaces, scope, executable AC, and concrete prohibitions.

## Rules
- Write meaningful tests before implementing features. Run `python3 -m unittest discover -s tests -v`.
- Keep OCI access read-only and explicitly scoped. Never change IAM policies.
- Never print, commit, or persist private keys, passwords, credentials, or raw OCI responses. Use local runtime profiles.
- Before creating a branch and again before creating a PR, inspect the working tree, staged changes, and commits intended for publication for customer information, personal information, and credentials. Repeat before every push. Inspect filenames, images, diagram XML, metadata, fixtures, generated artifacts, and PR/branch text as well as source text. Do not publish until findings are removed and rechecked; report only affected paths and categories, never sensitive values.
- Keep customer reference images, real snapshots, local profile/config files, and customer-derived diagrams outside the repository. Use clearly synthetic data for committed examples. Ignore rules and automated pattern scans alone are not proof that publication is safe.
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
