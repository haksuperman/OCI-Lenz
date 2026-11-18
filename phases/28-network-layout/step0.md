# Network placement and connector readability

Read AGENTS.md, docs/HARNESS.md, PRD.md, ARCHITECTURE.md, ADR.md,
network_layout.py, routing.py, architecture.py, ai.py, cli.py and their tests.
Input: common snapshot with observed DRG/attachment/peer/VPN references.
Interfaces: alias-only network_groups in the AI request; orthogonal router;
validation.json numeric network crossing/overlap diagnostics.
Scope: facing LPG pairs, neighboring RPC/unknown peers, attachments near their
DRG and parallel tunnel rows per actual IPSec connection. Keep ALL resources,
Attachment cards, actual parents and API endpoints; no visual aggregation.
Use deterministic crossing/overlap costs against already routed edges, keeping
resource/title avoidance mandatory and allowing reported unavoidable crossings.
AC: tests first for exact aliases/evidence, peer hint dedup without graph changes,
unknown peers, obstacle avoidance, crossing/overlap metrics, native geometry and
endpoint preservation. Full tests, unchanged non-network example replay, real
Draw.io/PNG synthetic export and masked private-snapshot inspection/comparison.
Prohibitions: inferred service ownership/transitive traffic, changed parent
membership, hidden Attachment resources, post-hoc rectangle repacking, secrets,
OCI writes, customer data in Git, agents, commits/pushes or executor changes.
