# Step 0: synthetic reference layout

Read AGENTS.md, docs/HARNESS.md, docs/PRD.md, docs/ARCHITECTURE.md, docs/ADR.md,
both Draw.io skills, oci_lenz/draw.py, model.py, cli.py and tests.

Inputs: synthetic snapshots and non-identifying visual conventions abstracted from
user reference pictures. Interface: existing sample/draw commands; add sample
--scenario overview. Scope: region/compartment/VCN/subnet nesting, orange dashed
network boundaries, editable official icons, expandable deterministic containers,
orthogonal configuration edges. No inferred application tiers or reachability.

Write regression tests first. AC: unittest discovery passes; generate overview
snapshot, invoke Codex skill, export same XML with Desktop to region and VCN PNGs;
validate relationships, editability, bounds and replay determinism; visually inspect
PNG files. Keep actual OCI collection separate.

Prohibitions: no customer reference files, names, IPs, metadata or topology copied
into repo or model input. No credential reads, IAM changes, agents, automatic Git
publication or executor status changes. Use only independently synthetic fixtures.
