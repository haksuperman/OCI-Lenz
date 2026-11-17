# Topology and label regression matrix

Read AGENTS.md, HARNESS, PRD, ARCHITECTURE, ADR, USAGE, diagram skills and
model/architecture/typography/routing modules with their tests.
Inputs: independently synthetic long-name/dense/fanout/cross-compartment/
unresolved/empty snapshots; existing local private snapshot for replay only.
Interfaces: sample --scenario, diagram scene footprints, check_plan, information
index validation, scripts/validate_scenarios.py with explicit output directory.
Scope: reproducible synthetic suite; detect and repair container-title and index
clipping without changing source membership, API endpoints or model positions.
AC: failures reproduced before fixes; all scenarios validate and replay
consistently; scene requests contain no source names/IPs; native evidence and
unknown targets remain; full tests and harness checks pass; synthetic Draw.io and
PNG are inspected, including an actual AI-designed representative case; private
replay is validated or a footprint mismatch is explicitly reported.
Prohibitions: no live OCI calls, service inference, original customer images sent
to models, customer assets in Git, subagents, automatic commits/pushes, manual
executor status changes or claims of universal aesthetic optimality.
