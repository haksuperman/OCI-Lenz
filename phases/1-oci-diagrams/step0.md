# Step 0: snapshot-and-draw

Read AGENTS.md, docs/PRD.md, docs/ARCHITECTURE.md, docs/ADR.md and .agents/skills/oci-drawio/SKILL.md.

Implement sample/snapshot → evidence graph → Codex Draw.io skill → editable native XML → PNG. Collector uses SDK read-only local profiles. Interfaces: oci-lenz sample/collect/draw. Preserve .drawio. Use only Oracle toolkit icons. No credentials or raw SDK objects in outputs. Do not infer reachability or add resources from reference images. Keep actual OCI validation separate.

AC: `python3 -m unittest discover -s tests -v`. Also generate sample and invoke draw, inspect the resulting region and VCN PNGs and compare graph resources/edges with XML. Never alter tests merely to pass. No external OCI calls without supplied scope/profile.
