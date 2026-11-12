# Upstream provenance

- Source: https://github.com/jha0313/harness_framework
- Inspected revision: `da676bc689f10f6db38ff194cf25e983f59ac231`
- Reviewed: CLAUDE.md, .claude/commands/harness.md, .claude/settings.json,
  scripts/execute.py, scripts/test_execute.py and docs templates.

This is a rewritten Codex adaptation of the phase/step workflow, not an unchanged vendor copy.
The inspected source tree contains no LICENSE file; no upstream license is asserted here.

## Changes
- CLAUDE.md → AGENTS.md; slash command workflow → docs/HARNESS.md.
- Claude CLI → Codex exec with workspace-write, ephemeral execution, stdin prompts,
  JSON Schema constrained status, and bounded timeout.
- Agent-maintained completion → executor-owned status and independently executed AC argv.
- Retain sequential steps, timestamps, resume, three attempts, blocked handling and top index.
- Remove permission bypass, automatic branching/staging/commits/push, npm hooks and raw output logs.
- Add atomic status writes, phase lock, path validation, Python tests and non-network example phase.
