# Operational diagram labels

Read AGENTS.md, HARNESS, PRD, ARCHITECTURE, ADR, USAGE, diagram skills and
collector/render/CLI tests. Inputs: synthetic tests and existing private snapshot.
Interface: draw defaults to private operational names/IPs; --redact generates
sharing labels. prepare_display creates a copy; graph topology is unchanged.
Scope: names, observed Compute VNIC/private/public IPs, LB addresses, backend
endpoints and subnet/VCN CIDRs. Collector stores only these allowlisted fields.
Grow cards/rows for multiline labels; keep model input aliases only.
AC: private and redacted regression tests first fail, then pass, including
secondary VNICs, long labels, missing fields and real SDK models. All unittest
and harness checks pass; rerender existing private snapshot outside Git and
verify label presence without printing customer values.
Prohibitions: no invented/missing IP guesses, credential reads, customer values
in logs/Git, customer images sent to models, IAM changes, silent topology edits,
agents or executor state changes. Git publication is a separate operation.
