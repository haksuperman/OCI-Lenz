---
name: oci-drawio
description: Draw OCI architecture from a local OCI-Lenz snapshot using Oracle's official Draw.io stencils and supplied architecture reference images. Use for OCI-Lenz sample or real inventory diagrams.
---

Read the project Draw.io skill at ../drawio/SKILL.md. OCI uses native editable XML, not flattened Mermaid images. Preserve both .drawio and PNG; do not delete the source.

Accept region, one or more explicit compartments and local SDK profile through `oci-lenz collect`. Collect all supported resources in those compartments without a VCN filter. Never inspect or transmit credentials. Use `oci-lenz draw --snapshot PATH --references DIRECTORY --output DIRECTORY` to apply the skill. For deterministic rerenders use `--reuse-layout PREVIOUS/skill-layout.json`.

Operational captions show actual resource names and observed representative IPs;
network boundaries retain CIDRs. Complete backend details stay in the appendix. Apply labels locally after the alias-only model
layout. Never replace customer operational names with aliases by default.
`--redact` is an explicit option for separate sharing PNGs; GitHub examples must
use synthetic data. Keep every customer-derived artifact outside the repository.

Source resources and relationships only from the snapshot graph. Reference pictures guide spacing, connector presentation and visual hierarchy, never resource existence or service membership. Read reference images when supplied. OCI official editable stencils are supplied by the local `oci_lenz.draw` helper from assets/oci/library.xml. The helper maps resource types to the official library entries, preserves editable cells, validates graph structure and exports the same file with Draw.io Desktop.

Use VCN boundaries containing public/private subnet containers, with the load balancer in public and app compute in private when supported by evidence. Keep gateways distinct. Show backend sets, route destinations/next hops and NSG membership. Unknown targets stay unknown. Edges describe configuration, not proven connectivity. Card positions must fit their container and not overlap; retain a stable ordering. Supplied node IDs are aliases.

Do not alter relation topology to improve appearance. Do not auto-open browsers or send customer data to online diagram services. Do not spawn agents. When PNG generation fails retain XML and report the failure. Inspect PNGs for clipping and missing icons before delivery.

Reference composition: region outer frame, API compartment membership inside it,
then orange dashed VCN and subnet boundaries. Use restrained neutral backgrounds,
teal official icons, readable labels below icons and orthogonal configuration
connectors. Expand containers to fit content. Keep operational notes separate.
Do not infer service groups or application flows from resource names. Never send
unredacted customer reference pictures to the model or copy them into the repo;
use these non-identifying visual conventions or sanitized local examples.

The default composition follows collected region, API compartment, VCN and subnet
membership. Do not classify VCNs into services or shared services from names,
addresses, connectivity or reference diagrams. Only the user can decide service
membership; apply service panels solely when the user explicitly supplies groups.
Never fix region dimensions or panel count to a picture. VCNs may use parallel columns;
public LB subnets sit above private backend subnets. Place backend server pairs
side by side. Keep icon-to-label spacing short and avoid oversized empty cards.
The summary hides VNIC/NSG/route-table shapes and technical links; keep their
editable cells and full detail pages. This is visual aggregation, not discovery.
Use only snapshot.presentation.groups for service membership; when absent, group
by API compartment ID without inventing services. Let card rows/columns and
container dimensions grow with counts; keep backends of the same set adjacent.
Default architecture mode requires AI to design absolute rectangles for all
containers/resources and optional edge bend points. The renderer applies this
plan directly; it must not discard it or replace it with a grid. Label footprints
and the evidence graph are provided under aliases. Return invalid geometry to
the model for bounded repair; never silently fall back after AI failure. Use the
bundled synthetic reference image or explicitly supplied sanitized references.
The editable information-index page retains complete data without caption reminders.
Keep actual names and all collected data in local output. Use the architecture
renderer; inventory/service-map rendering modes are retired. Backend evidence direction
stays in XML even where its display arrow expresses LB ownership.

The default is one whole-environment architecture canvas. VCNs/subnets remain
boundaries in it. VCN detail pages require --detail-pages; do not create them by
default. Exclude technical VNIC/NSG/route cards from overview geometry so hidden
cards do not leave empty lanes; retain their cells/evidence and information index.
Prioritize observed primary/private and public addresses on operational cards.
Distinguish listener protocol/ports from backend ports. Never infer unrecorded
ports, primary status or routing policy behavior. Group fanout only for the same
evidenced Backend Set and retain separate editable source/target edges.

Explicit service groups can span VCNs; these are visual panels, not inferred
business ownership. Preserve API membership in source data. Use bold editable
names with quieter observed IP labels. During visual review, X/0 labels are
privacy placeholders preserving real footprints: evaluate geometry/hierarchy,
not literal words. Revise only known rectangles/routes. Never add resources or
change immutable parent memberships. Report remaining issues as needs_review.

DRG and peering items use only observed attachment and peer_id relationships.
DRGs are regional resources, not children of one arbitrarily selected VCN.
DRG Attachment and LPG name tags are logical objects; DRG/RPC use official
stencils. Leave out-of-scope peers unknown. Do not infer direct or transitive
VCN connectivity, traverse peer scopes or treat configured peering as verified
traffic. DRG route-policy evaluation, VPN/FastConnect and DB/OKE remain separate.

LPGs belong to their actual VCN. Peer links are dashed configured relations;
API field names stay hidden on the canvas.
