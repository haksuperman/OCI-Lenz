# Summary readability and operational information

Read AGENTS.md, HARNESS, PRD, ARCHITECTURE, ADR, USAGE, both diagram skills,
architecture/display/collect/routing/AI modules and tests.
Inputs: synthetic SDK models, synthetic sparse/dense inventories and existing
private snapshots outside Git. Interfaces: architecture plans version 3 with a
single whole-environment canvas by default, optional --detail-pages and
independent overview/detail scenes; representative details and full index.
Scope: hide technical VNIC/NSG/route shapes only in the overview and exclude them
from its AI layout; retain all native cells/evidence, the information appendix
and optional full VCN detail pages.
Keep observed primary VNIC/private IP metadata, public IPs and LB listener ports;
show listener and backend ports distinctly. Route backend fanout over a shared
clear trunk without merging evidence edges or unrelated backend sets.
AC: tests written first fail; scene isolation, complete information, public IP
priority, SDK contracts, permission denial and shared-trunk obstacle avoidance
pass. Run full unittest and harness checks. Generate actual model XML/PNGs and
verify private outputs without printing customer values. Keep old snapshots and
version-2 plan replay compatible; missing metadata must never be guessed.
Prohibitions: no IAM writes, raw responses/credential logs, customer assets in
Git or model input, reference topology copying, agents, automatic publication or
executor state edits. Structural verification is not traffic validation.
