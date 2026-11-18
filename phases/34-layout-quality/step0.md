# Objective layout quality and bounded revision selection

Read AGENTS.md, HARNESS/PRD/ARCHITECTURE/ADR, visual_review.py, architecture.py,
routing.py, cli.py, and presentation/routing/quality tests.
Input: unchanged selected-scope snapshot, alias scene, current version-3 layout.
Interface: deterministic quality assessment, revision decision, visual-review and
validation JSON. Keep all official icon assets, source evidence and parents.
Scope: assess the overview using all visible edges; crossing/overlap, resource and
title intrusion, minimum sibling spacing, detours/bends and canvas slack. Reject
invalid geometry; retain best-so-far layout on equal/worse model proposals, with
bounded existing review budget and alias-only concrete feedback. Record initial,
final metrics and decision reasons, including unresolved objective issues. Score
same-inventory candidates only, not an absolute aesthetic or traffic guarantee.
AC: tests first demonstrate rejection of regressing/invalid revisions and false
AI acceptance; deterministic/private-safe metrics; full suite; repeated fresh
synthetic Draw.io/PNG and objective reports with honest residual warnings.
Prohibitions: OCI calls/writes, new service/ownership inference, model rectangle
repacking or silent fallback, added unbounded model calls, customer artifacts in
Git, secrets/raw responses, commits/pushes, agents or manual completed statuses.
