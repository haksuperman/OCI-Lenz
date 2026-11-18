# IPSec VPN containers

Read AGENTS.md, HARNESS/PRD/ARCHITECTURE/ADR docs, draw.py, architecture.py,
network_layout.py, routing.py, diagram_model.py, visual_review.py and tests.
Input: existing snapshot with request-scoped tunnel.ipsec_id ownership.
Interface: native IPSec connection container with editable tunnel children;
alias-only parent/minimum-header reservations and validated native hierarchy.
Scope: observed tunnels inside their own known connection only; DRG/CPE remain
outside. Hide redundant tunnel-owner wires because containment expresses them,
while preserving source graph, projected DRG/tunnel API evidence and hidden
native ownership edges. Unknown owners remain explicit; empty VPN stays named.
AC: meaningful failing containment/unknown/same-IP/tamper/detail tests first;
full suite, unchanged non-VPN examples, synthetic and existing private snapshot
Draw.io/PNG generation, masked inspection and exact plan replay.
Prohibitions: inferred ownership by IP/name, invented containers for unknowns,
Attachment cards/frames, OCI writes, source-evidence mutation, customer data in
Git, agents, automatic commits/pushes or manual executor completion.
