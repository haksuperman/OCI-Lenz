# Architecture

현재 구조:
- `AGENTS.md`: Codex 프로젝트 규칙
- `scripts/execute.py`: 단계 실행, 독립 AC 검증, 상태 기록
- `tests/test_execute.py`: 네트워크 없는 하네스 회귀 테스트
- `docs/`: 요구사항, 설계, 결정, 실행 절차
- `phases/`: 독립 작업 지시와 실행 가능한 AC

앱 실행 경로: OCI collector / synthetic fixture → 공통 snapshot → 관계 모델 →
Draw.io generator → 같은 파일의 PNG export. 수집과 렌더링은 분리한다.
연결에는 근거 API 필드를 보존하며 범위 밖·불명확한 대상은 미확인으로 표시한다.

## Implemented application flow

`oci-lenz sample` or `collect` → minimal snapshot → `model.graph` → `draw`.
Default `architecture` loads the pinned jgraph and OCI skills plus a synthetic
reference image. `ai.py` invokes per-user Codex login or the OpenAI Responses
API and requests complete absolute rectangles/edge waypoints under aliases.
`architecture.py` applies these coordinates directly, retains local real labels,
adds the information index and verifies evidence/geometry. Invalid geometry
receives up to two model repairs, without silent deterministic fallback. Saved
plans are bound to inventory IDs/label footprints. CLI remains the interface;
no credential registration service is added.

`scripts/validate_scenarios.py` exercises the same public CLI serially against
independent synthetic inventories. Diagnostic structure/replay passes and actual
AI visual acceptance are separate results. Per-case failures persist without raw
process output, remaining cases continue, and resume requires revalidated XML,
complete PNG payloads, matching snapshot/mode and unchanged artifact hashes.
No collection API is called by this validation path.

The renderer computes growing region/compartment/VCN/subnet containers and keeps
orthogonal edges in the nearest common ancestor. Known compartment names are
applied locally; membership comes from the VCN compartment ID. Reference composition conventions
are recorded without customer content. The overview synthetic fixture exercises
multiple VCNs and compartments without reproducing any supplied customer topology.

Only `architecture` is a public rendering mode. The former inventory/service-map
renderers and separate ordering-hint model adapter have been retired.
`draw.build_document` is the shared internal native XML scaffold; it builds just
the overview unless a detail scene explicitly requests VCN pages. The public
library renderer defaults to the same architecture flow as the CLI.
`presentation.validate_groups` validates explicit VCN assignments independently
of any legacy renderer. User groups remain optional and never inferred.

`display.prepare_display` copies the inventory for local operational labels,
including observed secondary VNIC addresses on their Compute. Names and address
labels are applied after alias-only model layout. Explicit --redact produces
sharing labels; it never changes relationship resolution or mutates the source
snapshot. Collector allowlists include VNIC public IP, LB address/public flag,
network CIDRs and compartment IDs. Older snapshots require recollection for
fields not originally stored.

Default version-3 plans design a single whole-environment overview without
reserving space for VNIC/NSG/route-table shapes. Their native cells and evidence
remain hidden/editable and all resource information remains in the appendix.
--detail-pages requests an additional independent AI scene for VCN pages.
Primary-VNIC placement and representative private/public addresses use SDK
evidence when available; legacy snapshots do not establish primary status.
GetLoadBalancer listener fields and backend target ports are labeled distinctly.
Same-Backend-Set fanout can share a clear trunk without merging evidence edges.

`presentation.service_frames` applies explicit cross-VCN service panels to the
overview without changing source membership or evidence. `typography` measures
Unicode labels and stores rich text on the resource cell itself. `visual_review` renders
a masked overview in an ephemeral directory, rejects PNG textual metadata,
requests a bounded visual critique/revision through the selected provider, and
revalidates revisions before use. It records accepted/needs_review explicitly;
replay performs no model call. It never uploads unmasked customer output.

Default visual boundaries follow collected OCI membership. Service membership is
a user decision; names, connectivity and customer reference diagrams are never
classification inputs. Explicit user groups are optional presentation overrides.
Editable reference files are inspected locally for typography/spacing/connector
conventions only and remain outside the repository and model requests.

Name wrapping prefers natural separators and avoids one-character trailing
identifier fragments. The native router handles LB ownership fanout in display
direction while retaining BackendSet.lb_id source/target and separate evidence
edges. Model prompts request content-sized containers; helpers never resize or
repack model placements to reduce whitespace.

`synthetic` provides a customer-free matrix for long labels, dense subnets,
fanout, cross-compartment networks, unresolved scope and empty inventories.
`scripts/validate_scenarios.py` serially exercises native PNG exports and replay.
Scene container footprints reserve measured title heights. Index text is wrapped
before measuring rows, and validation rejects clipping and row overlap.

`diagnostics.environment_report` checks package assets, SDK availability, local
AI configuration and renderer discovery without reading OCI profiles. Codex
login status is bounded and its output is discarded; the direct API check only
records runtime key/model presence. Shared `find_drawio` discovery supports PATH,
explicit DRAWIO_BIN and system/per-user macOS app locations. Standalone wheels
include runtime assets and user documentation; CI smoke runs outside checkout.

The native router treats each visible container title line as an obstacle, using
the same Unicode width estimate as wrapping plus a small clearance. Container
borders remain traversable. Single links and shared backend trunks avoid titles
without moving AI rectangles or changing evidence endpoints; saved geometry can
be replayed to apply connector fixes without another model request.

Collection stores only the tenancy name and selected compartment-name mapping
in scope metadata. Identity lookup failures remain in coverage and do not drop
resources. Architecture headings apply these names locally above the region;
legacy snapshots show an explicit unknown name. Sharing and model previews hide
the names. Long headings grow upward without moving AI placements. The first
page exports as architecture.png; information-index and optional VCN pages retain
their filenames.

Resource names and details use one native editable Draw.io label on the resource
group. No separate name/detail text vertices are created. Official vector symbols
exclude the cleared toolkit caption bounds, while keeping their painted scale.
The label starts three pixels below the symbol; HTML text is escaped and masked
as text nodes for model previews. Architecture captions include only names and
observed representative IPs, with CIDRs on network boundaries; listener/backend
details remain in the information appendix. No index reminder is appended.
Card reservations derive from current captions; changed footprints require a
new validated layout and never bypass the saved-plan signature check.

Card heights use the measured painted symbol, native caption and small padding.
Backend Sets are logical editable name tags with no duplicate LB symbol. Their
scene representation guides the model to keep them compact between the actual
LB and its API-linked targets. Connector ports attach to visible symbol sides,
symbol tops or caption bottoms with perimeter projection disabled. Small lateral
stubs lead to a clear corridor above the caption; obstacle avoidance uses visible
content bounds and title lines. API source/target direction remains unchanged.
VCN/subnet boundaries use distinct weights and heading sizes. The overview omits
unknown targets that participate only in hidden technical relations, while
unresolved LB/backend endpoints remain visible. All unknown cells and evidence
remain editable in XML and available in the complete network-detail scene.

Internet/NAT/Service Gateway cards use narrow measured captions and alias-only
groups derived from their actual VCN parent. Geometry validation keeps each group
connected by short aligned gaps near one VCN edge, rejects inflated gateway cards
and large sparse group bounds, and returns invalid proposals to the model. No
extra group box is drawn and no API membership changes. Diagnostic seed layouts
pack the gateway row separately; actual AI rectangles are never repacked locally.
Gateway name captions use 11px text within reservations measured at 12px to leave
clearance for bold suffixes and avoid extra wrapping in the narrow cards.

Current scenes contain topology, item footprints, aliases and the native XML
scaffold; unused precomputed coordinate boxes are not retained. Display summaries
contain observed addresses/CIDRs only; full listener/backend details stay in the
information appendix. Only native resource-owned labels are supported. Old
separate-label vertices and pre-version-3 top-level plans are rejected, not
silently interpreted as current geometry. Nested per-scene version-2 metadata
inside current version-3 plans is still part of the active model protocol.
Published examples live in artifacts/ai-quality; obsolete generated examples are
available in Git history. Dated publication reviews live under docs/history.

`network.collect_network` uses the shared scoped, paginated, bounded-retry API
wrapper for DRGs, all attachment types, LPGs and RPCs. Attachment network_details
take priority over deprecated vcn_id. Only allowlisted IDs/type/peering state and
peer region are stored. No remote region, tenant or compartment is traversed.
Graph edges retain exact field evidence; peers missing from the selected scope
stay unknown and visible in overview. DRG/RPC icons and logical LPG tags join the same alias-only AI pipeline.
Attachment records remain internal evidence; their cards are not drawn. No direct/transitive VCN peering edge
or traffic reachability is invented. DRG route/distribution policies remain
unsupported. Search reconciliation still covers the original supported types;
new network resources use their List API coverage, not assumed Search support.

`database.collect_base_database` lists scoped DbSystemSummary objects and per-system
DbNodeSummary objects. VM./BM. shapes are classified as Base DB; other/unknown
shapes are recorded unsupported rather than mislabeled. Client/backup subnets,
NSGs and observed VNIC fields retain exact SDK evidence. No database credentials,
keys, tags, connection strings or SQL access are used. Denied node/network calls
do not discard the System; zero and failed calls remain distinct in coverage.
The overview aggregates Base DB into one official System symbol with its actual
Display Name and all observed client Node IPs (no backup IPs or hostname cards).
Node/VNIC cells and API edges remain hidden/editable; the appendix and optional
details retain them. A backend whose physical target is a hidden Node displays
against its known System; ociEvidenceTarget stores the original Node ID and the
validator checks both API evidence and the Node-to-System membership. Original
graph endpoints are never mutated. Prior scene signatures/outputs are unchanged
for snapshots without Base DB resources. DB catalog/PDB/Data Guard and other
database platforms remain separate follow-up scope.

`vpn.collect_vpn` uses the same scoped, paginated, bounded-retry wrapper for
ListCpes, ListIPSecConnections and per-connection ListIPSecConnectionTunnels.
No Get call is needed: the tunnel List response already contains the allowed
endpoints/status/routing fields. Membership evidence is the request's ipsc_id,
not an invented response field. IPSecConnection.cpe_id/drg_id and attachment
network_details.id resolve only against selected resources; outside endpoints
stay unknown. An unreadable tunnel list retains its connection and unresolved
attachments with failed coverage, distinct from successful zero results.
CPE uses official editable art; VPN connections/tunnels use compact logical tags
(the toolkit's VPN connector is not a standalone resource icon). Display names
and observed VPN/CPE IPs are applied locally; status/routing/static routes stay
in the appendix. These are configured relations, not validated packet paths or
BGP route analysis. Search reconciliation remains limited to its original types.

The collector and `model.graph` retain the canonical API inventory/evidence.
`diagram_model.diagram_graph` derives a separate diagram projection for ALL
pages. Attachment nodes/names are omitted, including information/detail pages;
`diagram_resources` filters index rows. Each direct DRG/network edge requires
both references from the SAME Attachment record (drg_id + network_details.id,
or the explicitly recorded legacy VCN field). Outside/missing endpoints remain
unknown. No VCN-to-VCN transit or packet reachability is inferred.

Native projected edges store exact sorted `ociAttachmentIds` and `ociEvidence`;
validation independently recomputes the projection from the snapshot and rejects
forged endpoints, provenance, missing or duplicate relationship IDs. Repeated
attachments for the same endpoint pair share one line while retaining all IDs.
An already-present RPC owner edge absorbs the same attachment evidence rather
than creating a duplicate. The direct IPSec owner line is omitted only when an
observed attached-tunnel chain expresses that same DRG/connection relationship.
The canonical source graph and coverage are never changed by this projection.

Network layout requests contain aliases of actual endpoints only: VCNs left of
each DRG, IPSec members right, RPC/peers above, with branch_gap clearance. No
Attachment names, placement slots, badges or frames remain. The old frame
module/validator/diagnostic arrangement has been removed. Fresh AI, visual
revisions and replay validate these directions; diagnostic seeds are separate
and never repair model-owned rectangles. Older network plans require fresh
geometry; non-network scene signatures/current example replays are unchanged.

The native router keeps model rectangles and actual projected endpoints fixed.
It penalizes crossings/collinear overlap, evaluates alternative network target
ports and makes at most two refinement passes, retaining only better conflict
scores. Resource/title avoidance stays mandatory. Genuine shared endpoint stubs
and reciprocal pairs are exempted from ambiguity counts; unrelated connections
are never joined. `validation.json.routing_quality` reports residual network
crossings and overlap length, independently of graph validity and AI review.
This bounded greedy routing does not guarantee a global optimum.

IPSec connection resources are native containers (`ociVPNContainer=1`) on the
overview and optional network pages. A tunnel's parent is its known ipsec_id,
which the collector records from the ListIPSecConnectionTunnels request scope.
No ownership is inferred from names/IPs. Unknown owners remain explicit root
resources/edges; empty known VPNs retain their named container. Network detail
pages close over observed VPN families so a selected tunnel cannot lose its
known parent or siblings. CPEs remain outside the container.

AI scenes treat ipsec as a measured-header container and retain immutable
API-owned child parents. Each child keeps its editable native label and IPs.
Known tunnel-owner wires are hidden in native XML and omitted from the AI edge
request because containment expresses ownership; their original API edge IDs
remain validated. DRG/tunnel projected edges and the connection/CPE edge stay
visible. The router traverses container bodies while avoiding VPN titles and
unrelated child cards. Container moves in diagnostic seeds translate descendants;
AI rectangles are applied without local regrouping/repacking. Native validation
rejects parent changes even if a forged child would geometrically fit elsewhere.
Older VPN layouts require regeneration; non-VPN example XML is unchanged.

`fastconnect.collect_fastconnect` reuses the shared scoped/paginated/bounded-retry
wrapper for ListVirtualCircuits, ListCrossConnectGroups and ListCrossConnects.
Allowlisted VC metadata includes type, gateway_id, bandwidth/lifecycle/BGP state
and mapping target IDs/VLAN/peer IPs only. BGP MD5, MACsec, provider/account keys,
tags and customer-reference fields never persist. No Get/LOA/config APIs or
remote-scope expansion is needed. Successful zero and failed calls remain
separate coverage entries; Search reconciliation retains its original scope.

Canonical relationships use VirtualCircuit.gateway_id, each mapping's
cross_connect_or_cross_connect_group_id and CrossConnect.cross_connect_group_id.
The Attachment-free projection merges an equivalent VC gateway relation with
its DRG Attachment evidence. Unknown/missing mapping targets remain explicit;
public/provider-managed circuits never gain an inferred DRG/CPE/provider path.
CrossConnectGroup is a native container for its observed physical CrossConnect
children; owner wires remain hidden/validated. VC resources stay outside those
groups. FastConnect branches sit below their DRG with actual mapped endpoints
nearby, leaving VCN-left/VPN-right/RPC-above conventions intact. No new group
field is added when no FastConnect member exists, preserving prior non-FC plans.

Virtual Circuit and physical CrossConnect resource icons reuse the unmodified
FastConnect SVG image cell from official Oracle library entry 210. The enclosing
stock connector line/caption are excluded so no decorative edge is mistaken for
an API relationship. Physical group rectangles, resource captions and API edges
are separate editable native cells. The same .drawio is exported to PNG. BGP
states are appendix metadata, not a reachability test. VPN-over-FastConnect
transport associations, advertised-route analysis and provider physical inventory
outside scope are not inferred by this version.

## Objective overview quality

`quality.assess` validates native labels, graph structure and scene geometry, then
measures ALL visible-edge crossings/overlap, card/title intrusions, diagonals,
sibling spacing shortfall, bends/detours, canvas area relative to measured leaf
footprints and trailing container slack. It never changes coordinates, evidence,
API membership or official icon assets. Sub-micropixel anchor noise is rounded
before intersection tests. Reports contain numeric measurements, fixed issue
codes and scene aliases only. Optional detail pages retain structural validation
but are not scored by this overview selector.

The base loss terms (introduced in quality version 1) are lower-is-better for the SAME scene signature:
1000 × (card/title intrusions + diagonals), 100 × crossings,
20 × overlap / sqrt(measured leaf area), 5 × normalized spacing shortfall,
4 × excess route-length ratio, 0.5 × bends / visible-edge count,
0.5 × canvas-area / measured-leaf-area, and 2 × container-slack ratio.
Spacing targets are 16px for ordinary siblings, 24px when a container is involved
and 8px within API-owned gateway clusters. Slack above 35% or route detours above
100% produce warnings alongside any crossing/overlap/intrusion/spacing violation.
These are geometry heuristics, not an absolute aesthetic score.

Visual review receives objective metrics and affected aliases. Candidates must
pass native/scene validation, strictly reduce loss, never increase crossing,
overlap, intrusion or diagonal metrics, and stay within 125% of INITIAL canvas
area across the entire review budget. Equal, regressing or invalid proposals
leave the incumbent unchanged. Existing review budgets remain unchanged; no
automatic multi-candidate generation or extra model calls are added. Initial
and final measurements and decision reasons go to visual-review.json. Fresh
validation.json.layout_quality is written even for replay, --no-ai and --no-png.
Objective warnings prevent visual acceptance; artifacts remain as needs_review.
AI review remains necessary for concerns these heuristics cannot measure.

`scripts/validate_repeatability.py` runs 2–10 independent fresh synthetic CLI
generations without layout reuse, verifies XML/PNG and persists all failures and
warnings plus min/max/mean metrics in repeatability-report.json. The scenario
verifier recomputes objective metrics on resume instead of trusting older AI
acceptance. Diagnostic-only runs are explicitly distinct from fresh AI evidence.

Native connector ports use short outward approach corridors. The first/last
segment meets the chosen resource face normally rather than running along that
face and turning the arrowhead sideways. Side-by-side network resources prefer
facing sides regardless of a wide tunnel tag's aspect ratio. LB/backend flow
keeps its vertical port contract; fanout and alternative network ports retain
normal approaches. Obstacles, source/target evidence and model rectangles stay
unchanged. Replaying saved layouts can change connector geometry after this fix.
The synthetic basic fixture includes a documentation-range public LB address;
real resources still display only API-observed IPs, never a sample fallback.

## Content-aware composition (quality version 2)

`composition.policy` supplies one shared design rhythm to the initial alias-only
AI request: 24px ordinary/container gaps, 12–16px inner padding, 32px connector
corridors, 64px network corridors, 8px alignment tolerance and at most 8px card
size allowance. These are design guides, not fixed region dimensions or a local
packing engine. Existing minimum/ownership/direction constraints remain hard.

`composition.measure` looks inside each actual container. It merges child X/Y
projections, caps avoidable internal gaps at a 24px content rhythm (64px for the
network region), adds measured headers/padding and compares content-sized area
with current area. This detects empty margins on all sides and large blank bands
without rewarding an artificial spreading/translation of children. Large empty
subnets are measured against their own header minima; an entirely empty region
is not assigned fictional content. Worst-container whitespace is recorded so a
sparse subnet cannot disappear in a large region's weighted average.

Quality v2 adds 20 × average avoidable whitespace, 8 × worst-container whitespace,
6 × excess gap ratio (beyond 32px, or 96px for regional network branches),
8 × normalized card inflation beyond the 8px allowance,
4 × sibling alignment error, 6 × observed flow alignment error and
20 × fully reversed flows. Same-kind siblings and actual gateway siblings are
measured for alignment; unrelated kinds do not imply a row or service. Only
observed one-to-one LB/backend edges in the SAME known VCN guide flow centering;
fanout and cross-VCN edges are not forced into a made-up application column.

Warnings use average/worst whitespace >20%/30%, excess gap ratio >0.25, card
inflation >0.15, sibling alignment >0.35, flow alignment >0.20 or any reversed
flow. Alias-only design_feedback contains affected IDs and content-derived sizes
so review can revise the smallest affected area. Existing best-so-far rejection
protects flow reversals as well as crossing/intrusion. Different quality versions
are not compared. Old layouts remain replayable with freshly computed v2 metrics;
policy-only changes do not alter inventory/footprint scene signatures.

The renderer still applies AI rectangles exactly. Neither metrics nor guidance
resize, reparent, hide or delete resources/edges. Native arrow approaches and
observed LB IPs remain intact. AI visual critique remains independent of numeric
acceptance; required headers/network corridors are not automatically treated as
excess whitespace, and remaining subjective concerns stay needs_review.

Single API-evidenced network branches also receive center-axis guidance: a sole
Virtual Circuit below its DRG and a sole RPC above it align center X within 8px.
The single unknown peer above that RPC may share the axis. Multiple circuits or
RPCs are not collapsed into one column. Network alignment adds 6 × mean and
4 × worst normalized offset to v2 loss; warnings use mean >0.15 or worst >0.20.
This prevents a nominally downward branch from drifting sideways into VPN wires
without inventing relationships or moving model rectangles locally.

Quality conflict measurement respects the renderer's intentional Backend Set/LB
fanout trunks. For the SAME API-evidenced owner, it trims only the contiguous
shared prefix (including intermediate bends) before comparing diverged branches.
Crossings/overlap after divergence and between different owners still count.
Original native paths remain intact for label/title intrusion checks and XML
evidence validation. The low-level network router's metrics are unchanged. Wide
containers spanning several narrow sibling columns are not forced to align with
every individual column; same-kind comparable rows/columns still are measured.

## Common native connector contract

`connector_rules` derives row guides from actual visible configured edges and
immutable API parents. A one-to-one external edge to an API container with one
visible leaf aligns the external glyph with that leaf's glyph row, not the
container's full midpoint. The edge still ends at the SAME container; no child
edge or inferred membership is created. Multiple children/targets remain
ambiguous and do not imply one chosen port. Guides carry alias IDs and measured
official glyph offsets (or half the height for a logical tag).

Every fresh AI scene plan receives connector_rule_version=1 before validation.
check_plan rejects row mismatches and sends them through bounded design repair;
visual revisions inherit the same contract. Legacy unmarked plans remain
structurally replayable but quality reports connector_alignment_errors and
connector_feedback instead of claiming compliance. The loss adds 1000 per
mismatch and revisions cannot increase this metric. Guide-only metadata does
not change inventory/label footprint signatures or move old rectangles.

The common router uses source-aligned body ports below real container headers,
regardless of service type. When endpoints/corridors are collinear and clear,
it emits a straight connection even if an older/model route supplied doglegs.
Headers, unrelated cards, occupied routes and real branching still justify
orthogonal turns. Actual icons/labels/parents/API endpoints remain unchanged.
This rule applies during every render, not as a patch to a particular PNG.
