# Native resource labels

Read AGENTS.md, docs/HARNESS.md, PRD.md, ARCHITECTURE.md, ADR.md, typography.py,
draw.py, architecture.py, visual_review.py and presentation/routing tests.
Inputs: synthetic labels, official toolkit and existing private snapshot/layout.
Interfaces: resource mxCell.value rich text; native alignment below its vector
symbol; unchanged CLI. Remove detached name/detail text cells and exclude the
toolkit's cleared caption area from the icon bounds. Keep source artwork editable.
AC: failing tests first; full suite and harness checks; Unicode/HTML escaping,
masked preview privacy, native label overflow rejection; actual XML/PNG export,
same-layout replay and local visual inspection. Keep measured card reservations
compatible with saved AI geometry; preserve evidence and complete information index.
Prohibitions: no new OCI/model calls, customer artifacts in Git, rasterized icons,
service inference, geometry signature bypass, commits/pushes, agents or executor edits.
