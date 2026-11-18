# Direct DRG links without Attachment display

Read AGENTS.md, HARNESS/PRD/ARCHITECTURE/ADR docs, model.py, draw.py,
architecture.py, network_layout.py and graph/layout validation tests.
Input: unchanged allowlisted snapshot and canonical API graph.
Interface: diagram_graph/resources projection; native metadata on projected edges.
Scope: omit Attachment cards/names/frames on ALL diagram pages including index;
replace known Attachment.drg_id + network_details.id relationships with direct
DRG endpoint edges. Retain unknowns, aggregate duplicate provenance and avoid
redundant RPC owner/tunnel ownership lines. Keep VCN left, IPSec right, RPC above.
Remove obsolete Attachment frame/layout code and its superseded tests. Preserve
collector, coverage and raw evidence graph; no actual OCI Attachment is deleted.
AC: failing projection/provenance/unknown/tamper tests first; full suite, current
non-network replay, synthetic and private-snapshot Draw.io/PNG verification.
Prohibitions: inferred VCN-to-VCN transit/traffic, lost raw evidence, customer
files in Git, credentials, OCI writes, agents, commits/pushes, executor changes.
