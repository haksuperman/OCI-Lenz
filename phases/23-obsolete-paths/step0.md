# Remove obsolete state and examples

Read AGENTS.md, docs/HARNESS.md, PRD.md, ARCHITECTURE.md, ADR.md, USAGE.md,
architecture.py, display.py, draw.py, visual_review.py and generation tests.
Inputs: synthetic snapshots and current version-3 AI layouts in artifacts/ai-quality.
Scope: remove unused scene boxes/imports/port-summary calculations, top-level
pre-version-3 layout compatibility and detached resource-label compatibility.
Remove old committed example outputs and obsolete review documents; retain
current examples, supported snapshot field fallbacks and useful historical records.
Interface: reject obsolete layout formats before scene construction with a safe
regeneration hint; native resource labels only; full details stay in the appendix.
AC: tests first; full tests/harness pass; four current AI plans replay exactly;
six diagnostic PNG cases and optional detail exports pass; privacy checks pass.
Prohibitions: no live OCI/model calls, changing AI placements/scene signatures,
inferred service groups, lost evidence or observed addresses, credentials/customer
data in Git, commits/pushes, agents or executor status edits. Do not delete the
official library/reference, current validator, diagnostic mode or phase history.
