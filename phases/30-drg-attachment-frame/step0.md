# DRG attachment visual boundary

Read AGENTS.md, HARNESS/PRD/ARCHITECTURE/ADR docs, network_layout.py,
architecture.py, draw.py, routing.py, visual_review.py and related tests.
Input: selected snapshot and exact Attachment.drg_id edges.
Interface: alias-only attachment_frame reservations, computed editable native
backdrop, graph-preserving XML validation and common PNG export.
Scope: overview frame around each known DRG and its actual Attachment cards
only. Keep VCN, RPC, tunnel, IPSec connection and CPE outside. Preserve left VCN
Attachment, right IPSec Attachment and above RPC Attachment directions. Frame
is a visual annotation, not an OCI container or traffic/reachability claim.
AC: meaningful failing membership/parents/tamper/redaction tests first; reject
frames covering unrelated endpoints, overlapping frames or clipped headers;
full suite, unchanged non-network examples, synthetic and existing private
snapshot Draw.io/PNG export plus masked visual inspection and exact replay.
Prohibitions: changed API parents or topology, inferred service membership,
hidden resources, moving AI rectangles to fit frames, raw credentials/customer
artifacts in Git, agents, automatic commit/push or manual executor completion.
