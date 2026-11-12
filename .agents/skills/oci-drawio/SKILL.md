---
name: oci-drawio
description: Draw OCI architecture from a local OCI-Lenz snapshot using Oracle's official Draw.io stencils and supplied architecture reference images. Use for OCI-Lenz sample or real inventory diagrams.
---

Read the project Draw.io skill at ../drawio/SKILL.md. OCI uses native editable XML, not flattened Mermaid images. Preserve both .drawio and PNG; do not delete the source.

Accept region, compartment, optional VCN and local SDK profile through `oci-lenz collect`. Never inspect or transmit credentials. Use `oci-lenz draw --snapshot PATH --references DIRECTORY --output DIRECTORY` to apply the skill. For deterministic rerenders use `--reuse-layout PREVIOUS/skill-layout.json`.

Source resources and relationships only from the snapshot graph. Reference pictures guide grouping, placement and visual hierarchy, never resource existence. Read reference images when supplied. OCI official editable stencils are supplied by the local `oci_lenz.draw` helper from assets/oci/library.xml. The helper maps resource types to the official library entries, preserves editable cells, validates graph structure and exports the same file with Draw.io Desktop.

Use VCN boundaries containing public/private subnet containers, with the load balancer in public and app compute in private when supported by evidence. Keep gateways distinct. Show backend sets, route destinations/next hops and NSG membership. Unknown targets stay unknown. Edges describe configuration, not proven connectivity. Card positions must fit their container and not overlap; retain a stable ordering. Supplied node IDs are aliases.

Do not alter relation topology to improve appearance. Do not auto-open browsers or send customer data to online diagram services. Do not spawn agents. When PNG generation fails retain XML and report the failure. Inspect PNGs for clipping and missing icons before delivery.
