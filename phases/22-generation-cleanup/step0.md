# Unify generation and skip unused pages

Read AGENTS.md, docs/HARNESS.md, PRD.md, ARCHITECTURE.md, ADR.md, USAGE.md,
draw.py, architecture.py, cli.py, presentation.py and generation/layout tests.
Inputs: independently synthetic fixtures, current saved version-3 AI layouts,
official native Oracle cells and existing Draw.io skill instructions.
Scope: separate shared XML construction from public rendering, build VCN detail
pages only on request, retire inventory/service-map public renderers and duplicate
legacy model adapter. Preserve explicit user groups through shared validation.
Interfaces: architecture-only CLI/library render; internal XML document builder
with explicit detail-page switch; common group validator outside legacy renderer.
AC: failing tests first; tests/harness pass; exact XML replay of current AI layouts
and graph evidence unchanged; synthetic PNG export and visual inspection pass;
optional detail pages, redaction, operational labels and grouping remain tested.
Update current usage/skills so users cannot be directed to retired modes.
Prohibitions: no live OCI/model calls, customer data or credentials in repository,
inferred service membership, altered AI placements, commits/pushes, agents or
executor status edits. Historical records are not runtime implementation.
