# Independent user installation and publication audit

Read AGENTS.md, HARNESS, PRD, ARCHITECTURE, ADR, USAGE, packaging, AI adapters,
Draw.io discovery and CLI/tests. Inputs: current source, a separately built wheel,
new disposable virtualenv, synthetic inventory, per-user Codex login if available,
public Git history and existing private inventory for local comparison scans.
Interfaces: doctor command, safe dependency/auth diagnostics, wheel smoke test,
user onboarding guide. No OCI config contents or real OCI calls are needed.
Scope: verify assets outside the repository; diagnose absent executables/login/API
configuration without printing secrets; remove hard-coded user assumptions from
guides; inspect current and historical filenames/XML/images/metadata and report
findings by path/category. Keep existing product behavior except safe errors.
AC: tests first reproduce diagnostic gaps; full suite and harness checks pass;
clean wheel install passes pip check and synthetic XML/PNG generation outside the
repo; actual Codex synthetic generation succeeds if login is available; API
transport is mocked without requiring a key. Explicitly record untested platforms
and external agent behavior, plus unresolved historical identity metadata.
Prohibitions: no credential output/copy, live OCI requests, original customer
uploads, Git publication, history rewriting, auto installs of external services,
subagents, executor state edits or declaring mock-only/live-untested flows tested.
