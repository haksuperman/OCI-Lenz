# Actual AI quality matrix

Read AGENTS.md, docs/HARNESS.md, PRD.md, ARCHITECTURE.md, ADR.md, USAGE.md,
scripts/validate_scenarios.py, synthetic.py, ai.py and visual_review.py.
Inputs: independently synthetic basic, multi-VCN, dense and fanout inventories;
existing official Draw.io skill, Oracle icons and bundled synthetic references.
Scope: generate real AI layouts and the same XML's PNG, validate graph, label
bounds and exact replay, inspect images. Improve failures supported by evidence.
Interface: serial scenario runner records per-case failures without raw errors,
distinguishes diagnostic passes from AI visual acceptance and safely resumes
unchanged verified artifacts. Save coverage and reproducible public examples.
AC: tests first for runner failure/quality/resume behavior; full tests and harness
checks pass; record actual AI outcomes honestly, inspect generated PNGs and native
editable cells; document command, source provenance and remaining quality limits.
Prohibitions: no live OCI, collection expansion, inferred service membership,
silently substituted diagnostic layouts, customer data/reference files in Git or
model input, commits/pushes, agents or executor status edits.
