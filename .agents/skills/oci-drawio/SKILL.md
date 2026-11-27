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
LPG uses a logical name tag; DRG/RPC use official stencils. Attachment records
are internal evidence only; never draw their cards, names or frames. Leave out-of-scope peers unknown. Do not infer direct or transitive
VCN connectivity, traverse peer scopes or treat configured peering as verified
traffic. DRG route-policy evaluation remains separate.

LPGs belong to their actual VCN. Peer links are dashed configured relations;
API field names stay hidden on the canvas.

For Base DB, overview items are DB Systems with actual Display Name and observed
client Node IP captions applied locally. Individual DB Node hostname cards are
hidden. Use the supplied projected backend endpoint as a display aggregate;
physical target evidence remains in XML. Do not add database names, ports,
versions, backup addresses or inferred application-to-DB connections to captions.

IPSec VPN uses observed connection.cpe_id/drg_id, request-scoped tunnel ownership
and attachment tunnel IDs only. CPE uses official art. Each connection is a native IPSec VPN container;
its observed tunnels are editable child tags with locally applied names/IPs. Keep them outside
arbitrary VCN ownership; never invent direct CPE-to-VCN or transitive traffic
links. Status/routing belong to metadata, not reachability styling. No secrets
or device configurations are queried or sent to the model.

When network_groups are supplied, place actual VCN endpoints LEFT of each DRG,
IPSec members RIGHT and RPC/peer endpoints ABOVE with branch_gap clearance.
LPG pairs face across their existing VCN boundaries. Keep parallel VPN tunnels
near their supplied connection and CPE. These are API relationships, not inferred
service membership. Never draw Attachment cards/names/badges/frames, even on
information or detail pages. Direct DRG links retain verified Attachment field
provenance locally; never invent VCN-to-VCN transit or actual packet paths.

IPSec connection boxes are actual API-owned containers, not inferred service
panels. Respect tunnel parent IDs and measured header_height. Arrange tunnels
as compact parallel rows inside their own VPN box. DRG links enter toward the
observed child tunnels; the VPN container connects outward to CPE. Keep CPE/DRG
outside, with no duplicate VPN card or visible tunnel-to-parent ownership arrow.
Unknown VPN owners do not become invented containers. Empty known VPNs retain
their named box. Do not group by addresses, name similarity or inferred traffic.

FastConnect uses the official library FastConnect SVG symbol on Virtual Circuit
and CrossConnect port resources. Keep its branch BELOW the evidenced DRG, leaving
VPN RIGHT and RPC ABOVE. Arrange virtual circuits and their exact mapped physical
endpoints nearby. CrossConnectGroup is the actual physical-port parent container,
not a service panel: only API-owned CrossConnect children go inside; VCs/DRG/CPE
stay outside. Public/provider-managed circuits never imply a guessed DRG, CPE or
provider inventory. Preserve unresolved mapping IDs. BGP state is metadata, not
proof of traffic reachability; no MD5/MACsec credentials enter the model.


File Storage / Functions / API Gateway follow observed ownership, never inferred
traffic. File systems are AD resources in their real compartment outside VCNs;
Mount Targets use actual subnets and official File Storage art. Exports are logical
tags joined by export_set_id to targets and file_system_id to systems. Do not infer
VM NFS mounts. Application/Function share official Functions art; display an app
once while retaining every subnet edge, and anchor its functions visually without
asserting execution placement. Deployment tags stay near their actual API Gateway.
Draw only configured Function IDs or uniquely observed HTTP IP backends; hostnames,
ambiguous and out-of-scope targets remain unknown. Do not add OSN or invoke services.


NLB registered backends without an observed VM match are supplied as backend_endpoint logical tags with
native local IP captions. Keep each beside its exact Backend Set using the supplied
nearby/fanout relations; never move them to an external unknown column or draw VM
icons for them. Their Set-derived visual subnet anchor is not a verified VM subnet.
Retain backend arrows and all evidence. Classic LB status badges stay inside their
Set label; do not invent additional targets for those badges. Redaction is local.

LB and NLB share configured-IP matching and arrows. An NLB target identity lookup
is not a prerequisite for displaying a configured Backend. Preserve supplied VM
arrows and normal registered-IP tags; never add VM-confirmation-failure wording,
health-based exclusions or invented VM names. Raw target IDs remain local evidence.


Readable-arrow contract (applies to EVERY future generation, superseding compact
spacing guidance where they conflict): reserve 72px between connected items and
successive fanout rows, 96px network corridors, and side-bus space inside the
actual parent. Unrelated resources can stay compact. Enlarge the canvas/containers
rather than squeeze lines, stretch cards or move resources to another OCI parent.
Prefer same-owner targets side by side with one shared stem and row branch; for
multi-row targets use a clear side bus and visible row lanes, never a chain through
another target. Independent owners use separate landing ports/shafts; shared
wire segments are allowed only for the same evidenced origin. Retain normal
24px terminal shafts, 8px resource-border clearance, 24px unrelated lane spacing,
open 10px arrowheads and 1.8px strokes. Clear independent crossings use native
jumps. Preserve every configured edge and native source/target evidence. More
area is acceptable only for measured connector readability gain; reject resource,
label, ambiguous contact and arrowhead regressions. Existing plans are not silently
repacked: report new visibility deficits and generate a fresh AI layout for room.
Reference pictures inform these generic principles, never hardcoded coordinates.

After protecting that arrow structure, trim unused OUTER frame margins. Use 16px
around children, measured header_height above them and 8px around routed wire
bends/side buses. The 72/96px corridors belong between connected objects/rows;
they are not padding required on every frame edge. Prefer cropping boundaries
without moving leaf absolute positions or changing branch/landing geometry.
Quality unused_boundary_space feedback gives child-and-wire-aware bounds and
per-side trim, not a command to repack. Ordinary projection-based suggested sizes
must not override occupied paths. Revalidate titles, endpoints and parents after
any candidate. A whitespace-only revision that adds bends/detours or reduces
connector readability is rejected. Saved layout replay stays unchanged.

OKE uses official Container Engine for Kubernetes art. Preserve the supplied
endpoint Subnet parent and OKE API Endpoint role; this does not locate Oracle's
managed control-plane VMs there. Missing anchors fall back to a known VCN or
actual compartment, with icon/name only. Use existing worker Compute cards; do
not create Node Pool frames, Pod/virtual-node cards or OKE-to-worker/LB/gateway
traffic. Only actual backend/route evidence defines those arrows. VCN-native Pod
Subnet roles come from exact API references; preserve actual subnet names/CIDRs.

Confirmed Pod Subnets use a native editable rounded `OKE Pods` badge with the
official OKE glyph in the reserved header row. Keep actual subnet name/CIDR and
API membership; this annotation creates no inventory node or traffic edge. Routing
and quality treat its full rectangle as a title obstacle. Saved scene signatures
and resource placements remain compatible.
