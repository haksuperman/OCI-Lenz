# Bounded layout execution

Read AGENTS.md, docs/HARNESS.md, PRD, ARCHITECTURE, ADR, USAGE, both diagram
skills, oci_lenz/cli.py and tests/test_skill_input.py. Inputs: synthetic snapshots,
mock child processes, and an already collected local snapshot outside Git.
Interface: draw --skill-timeout SECONDS; skill_layout(..., timeout=600).
Scope: bounded configurable Codex wait, stage-specific safe diagnostics, progress
messages, isolated temporary child working directory and explicit JSON-only task.
AC: tests first fail before implementation; timeout and command/prompt privacy
regressions pass; all unittest and harness structure checks pass. Exercise actual
skill generation and same-file PNG export when available; report limits honestly.
Prohibitions: no silent AI fallback, credential reads, raw child/SDK output,
customer-derived files in Git, topology changes, agents, or IAM changes. Do not
change executor state or bypass approvals. Git publication is a separate action.
