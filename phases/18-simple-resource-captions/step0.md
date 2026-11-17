# Simple resource captions

Read AGENTS.md, docs/HARNESS.md, PRD.md, ARCHITECTURE.md, ADR.md, USAGE.md,
architecture.py, display.py and readability tests. Inputs: synthetic fixtures and
an existing private snapshot. Interfaces: architecture captions and native labels.
Scope: resource name plus observed representative IPs only; keep CIDRs in network
boundaries. Remove information-index comments and listener/backend-port summaries
from resource cards. Keep original detailed information and API relationships in
the editable appendix/source model. Do not treat backend targets as an LB's own IP.
AC: failing tests first; full tests/harness checks; native Draw.io and PNG inspection,
no index comments on architecture, names/IPs and complete appendix preserved.
Validate newly generated AI geometry when caption footprints change; saved plans
must still reject mismatched signatures. Confirm final-plan replay equivalence.
Prohibitions: no live OCI calls, service inference, source snapshot mutation,
customer artifacts in Git, signature bypass, commits/pushes, agents or executor edits.
