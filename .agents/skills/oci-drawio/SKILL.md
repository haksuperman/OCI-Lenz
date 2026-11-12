---
name: oci-drawio
description: Draw OCI architecture from a local OCI-Lenz snapshot using Oracle's official Draw.io stencils and supplied architecture reference images. Use for OCI-Lenz sample or real inventory diagrams.
---

Read the project Draw.io skill at ../drawio/SKILL.md. OCI uses native editable XML, not flattened Mermaid images. Preserve both .drawio and PNG; do not delete the source.

Accept region, compartment, optional VCN and local SDK profile through `oci-lenz collect`. Never inspect or transmit credentials. Use `oci-lenz draw --snapshot PATH --references DIRECTORY --output DIRECTORY` to apply the skill. For deterministic rerenders use `--reuse-layout PREVIOUS/skill-layout.json`.

Source resources and relationships only from the snapshot graph. Reference pictures guide grouping, placement and visual hierarchy, never resource existence. Read reference images when supplied. OCI official editable stencils are supplied by the local `oci_lenz.draw` helper from assets/oci/library.xml. The helper maps resource types to the official library entries, preserves editable cells, validates graph structure and exports the same file with Draw.io Desktop.

Use VCN boundaries containing public/private subnet containers, with the load balancer in public and app compute in private when supported by evidence. Keep gateways distinct. Show backend sets, route destinations/next hops and NSG membership. Unknown targets stay unknown. Edges describe configuration, not proven connectivity. Card positions must fit their container and not overlap; retain a stable ordering. Supplied node IDs are aliases.

Do not alter relation topology to improve appearance. Do not auto-open browsers or send customer data to online diagram services. Do not spawn agents. When PNG generation fails retain XML and report the failure. Inspect PNGs for clipping and missing icons before delivery.

Reference composition: region outer frame, API compartment membership inside it,
then orange dashed VCN and subnet boundaries. Use restrained neutral backgrounds,
teal official icons, readable labels below icons and orthogonal configuration
connectors. Expand containers to fit content. Keep operational notes separate.
Do not infer service groups or application flows from resource names. Never send
unredacted customer reference pictures to the model or copy them into the repo;
use these non-identifying visual conventions or sanitized local examples.

The primary composition is a compact, adaptive service map: pack service panels
based on actual contents, place explicit shared services below and reading/scope
notes alongside. Never fix the region dimensions or panel count to a picture.
Within a service panel, VCNs wrap into parallel narrow columns;
public LB subnets sit above private backend subnets. Place backend server pairs
side by side. Keep icon-to-label spacing short and avoid oversized empty cards.
The summary hides VNIC/NSG/route-table shapes and technical links; keep their
editable cells and full detail pages. This is visual aggregation, not discovery.
Use only snapshot.presentation.groups for service membership; when absent, group
by API compartment ID without inventing services. Let card rows/columns and
container dimensions grow with counts; keep backends of the same set adjacent.
In service-map
mode, card positions returned by Codex define stable order; the compact helper
fits that order to its smaller grid. Backend evidence direction stays in XML.
