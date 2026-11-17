# Fresh AI validation after generation cleanup

Read AGENTS.md, docs/HARNESS.md, PRD.md, ARCHITECTURE.md, ADR.md, USAGE.md,
ai.py, architecture.py, cli.py, visual_review.py and current validation tests.
Inputs: an existing user-authorized private snapshot outside Git, official native
Oracle stencils, pinned Draw.io skills and the bundled synthetic reference.
Scope: confirm merged main and prerequisites, generate a fresh model-owned
architecture (no reused layout), render the same XML through Desktop, compare
resource counts/names/IPs/backend evidence with the snapshot and inspect PNG.
Interface: draw --snapshot PRIVATE_PATH --output PRIVATE_DIRECTORY; only aliases,
topology and footprints reach the model. All real labels are applied locally.
AC: record model/review outcomes honestly; full tests/harness pass; validate graph,
native editability, exact saved-plan replay and absence of clipped/missing icons;
record any remaining whitespace/crossing issues. Keep evidence outside Git.
Prohibitions: no live OCI collection, IAM changes, expanded resource scope,
inferred service membership, silent diagnostic fallback, raw customer data in
Git/model requests/logs, commits/pushes, agents or executor status edits. Snapshot
validation does not claim that current live tenancy state has been rechecked.
