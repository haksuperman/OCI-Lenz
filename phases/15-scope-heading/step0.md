# Scope heading and architecture PNG

Read AGENTS.md, docs/HARNESS.md, PRD.md, ARCHITECTURE.md, ADR.md, IAM.md,
collect.py, cli.py, display.py, architecture.py, draw.py and associated tests.
Inputs: scoped read-only profile, snapshots and saved AI geometry; synthetic tests.
Interfaces: allowlisted scope names from GetTenancy/GetCompartment and existing
ListCompartments; default overview export architecture.png; local scope heading.
Scope: show tenancy, selected compartment names and region above architecture;
merge multiple selected compartment names; keep old snapshots readable with an
explicit unknown-name label; hide these names in sharing/AI previews. Grow title
area without changing AI placements. Document required inspect permissions.
AC: failing tests first, full tests/harness checks, real PNG/XML and saved-layout
replay; if authorized profile is available retrieve only name metadata for the
already specified scope and save a private enriched copy, never raw responses.
Prohibitions: no IAM mutation, resource-scope expansion or full recollection,
customer metadata in Git/model requests/logs, subagents, commits or pushes,
executor status edits or inventing names from profile/resource labels.
