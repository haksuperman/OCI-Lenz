# DRG-centered placement

Read AGENTS.md, docs/HARNESS.md, PRD.md, ARCHITECTURE.md, ADR.md,
network_layout.py, architecture.py, ai.py, visual_review.py and layout tests.
Input: observed per-DRG network relationships in the common snapshot.
Interface: alias-only network_groups direction contract and check_plan.
Scope: VCN Attachment immediately left of its DRG, IPSec members to the right,
Remote Peering members above. Apply independently to multiple DRGs. Retain all
resources and API parent/endpoints; no service inference or hidden cards.
Fresh AI geometry and visual revisions must satisfy the contract. Diagnostic
seed plans must also validate, without repacking model-owned rectangles.
AC: failing direction/nearby/multiple-DRG tests first; full suite, unchanged
non-network example replay; synthetic and authorized private-snapshot native
Draw.io/PNG generation, masked inspection and numeric orientation verification.
Prohibitions: OCI writes, inferred ownership/traffic, raw credentials, customer
files in Git, agents, automatic commit/push or manual phase completion.
