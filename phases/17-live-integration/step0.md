# Fresh scoped collection and full diagram integration

Read AGENTS.md, docs/HARNESS.md, PRD.md, ARCHITECTURE.md, ADR.md, IAM.md, USAGE.md
and the project Draw.io skills. Inputs: an explicitly authorized local read-only
profile/region/compartments and private output paths outside Git. Reuse scope
selection from the previously authorized snapshot, not service-name inference.
Interfaces: collect CLI, fresh AI draw CLI, coverage and native XML/PNG validation.
Scope: refresh supported inventory, verify names/counts and selected relationships
against read-only API responses, generate a new AI layout without saved geometry,
inspect PNGs, and verify deterministic replay. Keep private evidence outside Git.
AC: full tests and harness structure pass; record coverage failures separately
from empty results and unsupported services; compare inventory/API evidence;
new geometry/visual-review results and native Draw.io/PNG exist, all resource
names/details/evidence remain represented, and saved final layout replays exactly.
Record unresolved quality issues honestly rather than treating model acceptance
as proof of universal quality. Fix reproducible defects with synthetic tests first.
Prohibitions: no IAM/resource mutation, scope expansion, raw responses/credentials
in logs or files, unmasked customer input to AI, customer artifacts or identities
in Git, service inference, automatic commits/pushes, agents or executor edits.
