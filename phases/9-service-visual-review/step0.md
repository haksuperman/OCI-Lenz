# Service presentation and rendered visual review

Read AGENTS.md, HARNESS, PRD, ARCHITECTURE, ADR, USAGE, diagram skills and
architecture/display/routing/AI/CLI modules and tests.
Inputs: explicitly supplied presentation groups, API evidence, synthetic style
images and snapshots; private runtime snapshots stay outside Git.
Interfaces: draw --groups FILE, --review-rounds 0..2; native separate name/detail
labels; bounded AI review of an alias-only rendered preview.
Scope: explicit service panels over VCNs without inventing ownership/connectivity;
weighted text measurement and editable typographic hierarchy; render/inspect/
revise loop through the selected per-user model. No extra model calls on replay.
AC: tests first; grouping and source evidence invariants, literal text escaping,
label bounds, Unicode wrapping, PNG-preview privacy, repair/rejection/budget and
replay behavior pass; full tests and harness checks pass; actual model-generated
synthetic and private XML/PNG are validated and visual-review status is recorded.
Prohibitions: no name-based guessed service roles, raw customer/model output in
logs, original customer images uploaded, hidden credential reads, IAM changes,
agents, automatic Git publication or executor state changes. Do not claim a
subjective optimality guarantee or hide a review still requiring attention.
