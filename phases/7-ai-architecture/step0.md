# Model-designed architecture

Read AGENTS.md, HARNESS, PRD, ARCHITECTURE, ADR, USAGE, both diagram skills,
collector/model/display/render/CLI and tests. Input: snapshot evidence graph,
label dimensions, synthetic style image; explicit sanitized user images optional.
Interfaces: draw --style architecture (default), --ai-provider codex|openai,
--model NAME, --skill-timeout SECONDS, --reuse-layout PATH, explicit --no-ai.
Scope: AI decides full container/card rectangles and edge waypoints. Local code
applies native icons and real labels, verifies geometry/topology, and asks for up
to two repairs. Per-user Codex login or runtime OPENAI_API_KEY; no stored keys.
Compact architecture labels link to a complete editable information appendix.
AC: tests first; model coordinates survive rendering; invalid/missing/overlapping
placements cannot silently pass; API/CLI adapters preserve credentials; alias
input has no names/addresses; examples default to bundled synthetic reference;
tests and harness pass; actual model-generated Draw.io and PNG visually checked.
Prohibitions: no inferred resources/relationships, secret/raw response logs,
customer assets in Git/default references, approval bypass, agents or manual
executor state edits. No silent deterministic fallback on model failure. Report
API live validation unavailable without a user-provided API runtime environment.
