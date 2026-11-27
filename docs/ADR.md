# Decisions

## 001 — Codex harness
Python 3.10+ 표준 라이브러리로 하네스를 실행한다. 테스트에는 외부 패키지가 필요 없다.
Codex CLI를 별도 세션으로 호출하며 권한 우회 플래그는 사용하지 않는다.
하네스는 상태와 AC를 관리하고 에이전트는 구현만 담당한다.
Git 변경과 원격 쓰기는 자동화하지 않는다.

## 002 — Acceptance and privacy
실행 가능한 argv AC를 step index에 둔다. 에이전트 완료 보고만으로 통과하지 않는다.
원문 실행 출력은 보관하지 않아 진단 상세가 제한된다. 필요한 명령을 로컬에서 다시 실행한다.
실제 OCI 검증은 가상 데이터 phase와 분리한다.

## 003 — Draw.io skill and OCI collection
Use the official jgraph Codex Draw.io skill with OCI-specific adapter instructions. SDK is the sole v1 collector; OCI CLI remains an independent verification tool. Credentials remain local. Codex receives alias IDs and kinds, not SDK objects or OCI authentication. Keep the source XML when exporting PNG; omit embedded XML from shareable PNGs. Deterministic helpers enforce graph structure and replay saved layout.

## 004 — Operational labels and publication
Default local diagrams show real resource names and observed addresses. Redaction
is an explicit sharing option, not the operational pipeline. GitHub examples use
synthetic data. Neither real customer diagrams nor snapshots belong in Git, even
after visible-label redaction. Codex layout requests always remain alias-only.

## 005 — Model-owned architecture and user authentication
The default renderer applies full AI geometry, not bounded ordering hints.
Geometry/topology checks and bounded model repair are part of the product.
Each installation uses its own Codex login or runtime OpenAI API key/model.
Only aliases, topology and label footprints reach the model. A synthetic bundled
image supplies composition guidance. Address details remain in an editable
appendix. Deterministic obstacle-aware routing refines connectors without moving
resources; overview emphasizes backend flow and VCN pages show network links.
Objective checks cannot guarantee subjective quality for every topology; new
sparse/dense/complex cases must extend the regression suite.

## 006 — Compartment-only collection scope
Collection uses a region and one or more explicitly selected compartments.
Remove the VCN filter from both CLI and collector interface. Preserve every
supported resource returned for that scope and resolve cross-compartment
relationships after combining snapshots. This does not enable tenancy-wide
crawling or change optional VCN detail pages in diagram output.

## 007 — One public generation path
Use architecture rendering for both CLI and library calls. Remove the old
inventory/service-map renderers and their independent Codex ordering-hint
adapter. Keep the shared native XML scaffold and explicit user-group validation
separate. Build VCN pages only when a detail scene requests them. Current saved
version-3 AI plans must replay to exactly the same XML after this refactor;
legacy hint-only plans require regeneration. Preserve editable source files,
operational labels, optional details and the evidence graph.

## 008 — Current layout protocol and examples
Accept only version-3 top-level saved layouts. Remove old top-level geometry and
separate-label compatibility instead of retaining unused execution paths. Keep
per-scene metadata used by the current model adapter, source snapshot field
fallbacks, full appendix data and strict graph/geometry validation. Remove unused
scene boxes and port-summary calculations; do not change visible output or
current scene signatures. Retain current AI examples; earlier generated outputs
remain in Git history and dated reviews are explicitly historical records.

## 009 — Evidence-based DRG and peering expansion
Collect DRG, all attachment types, LPG and RPC within the specified region and
compartments. Preserve attachment and peer endpoints as API fields; prefer modern
network_details and retain an explicit deprecated-VCN fallback. Out-of-scope
endpoints remain unknown; never recurse into peer scopes or infer transitive
VCN connectivity. Use native official DRG/RPC art and editable logical labels
where the bundled toolkit has no dedicated stencil. Keep routing-policy analysis,
VPN/FastConnect, DB and OKE separate from this expansion.

## 010 — Base DB System captions
Collect Base DB VM/BM systems, nodes and their client/backup network references
through read-only SDK calls. Overview displays each System's Display Name and
observed client Node IPs only, with one official DB System icon. Hide individual
hostname cards, retain physical data/relationships internally, and validate any
backend-to-System visual projection against the actual Node ownership. Reject
unknown/non-Base shapes as unsupported. Do not read secrets or connect to SQL;
DB catalog/PDBs, Exadata/Exascale and other engines remain follow-up scope.

## 011 — IPSec metadata without configuration secrets
Collect compartment CPEs and IPSec connections, then list each connection's
tunnels. Reuse actual tunnel OCIDs to resolve DRG attachments and record request
scope as ownership evidence. Never read PSKs, device configurations, templates
or BGP authentication data. Keep UP/DOWN and routing metadata separate from
traffic claims. Render CPE with native official art and connection/tunnel objects
as editable logical tags; do not misuse the toolkit's connector as a resource.

## 012 — Network alignment and crossing-aware connectors
Use API-evidenced alias-only alignment hints for peer pairs, DRG attachments and
VPN tunnel groups. Preserve every resource, attachment and original graph edge;
change placement instructions and connector costs, not topology. Favor separate
parallel corridors over overlapping paths. Keep AI rectangles authoritative,
measure remaining crossings/overlap and report them without claiming optimal
routing or traffic reachability. Do not hide Attachment cards in this change.

## 013 — DRG-centered directional convention
Use the user's explicit DRG composition: nearest VCN Attachment column left,
IPSec branch right and Remote Peering above. Encode observed members as aliases
and validate directions/gaps before accepting AI geometry or visual revisions.
Keep multiple DRGs independent, every resource visible and all API membership
unchanged. Generate diagnostic seeds under the same convention; never rotate or
repack AI rectangles locally. Regenerate older network plans for this contract.

## 014 — DRG Attachment backdrops without API reparenting
Draw a subtle native frame around a DRG and its actual Attachment cards, leaving
VCN/RPC/tunnel/VPN/CPE endpoints outside. Reserve the derived border/header in
the AI request and reject overlaps instead of repairing resource coordinates.
Keep resource parents, graph endpoints and source evidence unchanged. Verify
annotations independently before excluding them from base resource validation.
This is a visual relationship boundary, not an OCI container or traffic zone.

## 015 — Attachment-free diagram projection (supersedes 013/014 display details)
Remove Attachment cards/names/frames from all diagram pages. Keep collection and
canonical graph evidence unchanged. Derive direct DRG/network edges from the
same Attachment's two API references, retain sorted IDs/field evidence in native
metadata and reject forged/duplicate projected relationships. Deduplicate native
RPC ownership and redundant IPSec ownership chains without inferring transit or
traffic. VCN endpoints remain left, IPSec right and RPC above each DRG. Remove
obsolete frame code and replace its tests with projection/evidence tests.

## 016 — API-owned IPSec tunnel containment
Render each IPSec connection as its existing resource's native container, with
only observed ipsec_id tunnels inside. Keep DRG/CPE outside and preserve every
resource name/IP and source relationship. Hide redundant ownership arrows rather
than drawing a second connection card. Unknown owners stay unknown; duplicate
addresses do not establish membership. Validate native parents, header clearance
and exact source edge provenance. This is observed ownership, not a service or
traffic grouping. Regenerate older VPN layouts; do not repair model coordinates.

## 017 — FastConnect fields and official glyph provenance
Collect scoped VC/physical groups/ports through List APIs and preserve exact
OCID references. Keep public circuits and out-of-scope provider endpoints honest;
no CPE is inferred from peer addresses. Exclude every authentication/config field
before snapshots/logs/artifacts. Use the exact SVG symbol embedded in Oracle's
FastConnect connector, with decorative edges removed. Physical ports belong to
their API group container; VCs remain separate. Place the branch below its DRG
without altering existing non-FC plans. Do not treat BGP UP as traffic validation.

## 018 — Objective overview quality and best-so-far revisions
Keep AI-owned rectangles and source topology immutable locally. Evaluate native
overview output with deterministic alias-only measurements and supply concrete
issues to existing bounded visual review. Compare only the same scene signature.
Retain a candidate only when loss strictly improves without increased crossing,
overlap, intrusion or diagonals, or more than 25% canvas growth from the INITIAL
layout. Reject invalid/equal/worse proposals and preserve the previous layout.
AI acceptance cannot override measured warnings. Save honest needs_review states,
metrics and decision reasons rather than silently replacing AI with a grid.
Scores rank candidates for one scene; they are not aesthetic guarantees or a
claim of traffic reachability. Track repeated fresh synthetic runs including
failures. Incremental inventory-change layout remains a separate future feature.

## 019 — Normal arrow approaches and observed LB addresses
Orthogonal segments alone do not guarantee a readable arrowhead: a final segment
can run along the target border. Route via short outward face-normal stubs and
prefer facing ports for side-by-side network endpoints, including wide tunnel
tags. Preserve LB/backend vertical flow, title/card avoidance, graph evidence
and model placements. Synthetic examples supply a documentation-range LB IP;
operational labels use only observed addresses and never synthesize missing IPs.

## 020 — Content-aware composition rather than post-render repacking
Guide initial AI generation and bounded review with a shared spacing rhythm,
measured caption footprints and alias-only local improvement suggestions. Assess
symmetric/internal whitespace and the worst sparse container, card inflation,
same-kind alignment and actual one-to-one same-VCN LB/backend alignment. Preserve
real network corridors and variable container sizes. Never infer service owners
or force unrelated types into a grid. Upgrade the quality formula to version 2
and compare only like versions/scenes. Keep official native symbols, fixed source
evidence, previous arrow fixes and exact model rectangles. Repeat fresh synthetic
cases and report both objective and independent visual warnings honestly.

## 021 — Enforce painted connector axes on fresh generation
Normal arrowhead entry is insufficient when source glyph and container midpoint
are on different rows. Derive a generic single-content-container guide using
actual API ownership and measured glyph anchors. Mark all fresh plans with the
connector rule version and reject invalid geometry during generation/revision.
Use aligned body ports below headers and straight-first native routing. Preserve
legacy replay with explicit objective warnings; do not repair resource placement
locally or replace evidence endpoints with an assumed child connection.

## 022 — Scoped MySQL, Autonomous and Exadata service infrastructure
Extend database infrastructure collection in MySQL → Autonomous DB → ExaCC →
ExaCI → Exascale order. This supersedes 010's deferred-platform restriction;
Base DB labels and unknown-shape protection remain. Keep legacy Exadata DbSystems
separate from VM/BM Base DB. Use allowlisted SDK fields and exact reference IDs,
with ListDbNodes request scope as VM Cluster ownership evidence. Retain failed
children as unresolved references rather than losing their parent resources.
Do not connect to SQL or collect passwords, wallets, connection strings, tags,
SSH keys, contacts or raw responses. Keep catalog/PDB/Data Guard, replication,
HeatWave nodes and physical Exadata servers outside this infrastructure increment.

ExaCC physical client/backup networks are never OCI VCN/Subnet membership. List
networks in the selected compartment even if their observed infrastructure ID is
outside, without fetching that parent. Resolve cross-compartment relationships
only after merging selected scopes. Show DB client Node IPs at their owning
System/Cluster and retain validated physical backend targets in native XML.
A configured backend may resolve to an observed DB endpoint only if unique in
the LB VCN. Use official database artwork; absent dedicated Exascale/Vault art,
use Exadata for the cluster and a logical name tag for the vault. Synthetic XML
and denied/empty/allowlist SDK tests are independent from live API/PNG validation.


## 023 — Apply conflict routing to database ownership edges
Include DB-involved relationships in occupied-corridor routing and bounded
refinement without adding DB types to network layout groups. Dedicated ADB's
same-face incoming/outgoing ownership chain may choose alternate normal ports,
while retaining the AI rectangles, resource parents and original API endpoints.
Keep existing conflict metrics strict: no new shared-chain exemption or threshold
relaxation. Verify the synthetic failing layout, deterministic replay, unchanged
placements and regressions for other DBs and network branches. No new OCI fields
or live calls are required for this renderer correction.


## 024 — Scoped NLB with explicit backend targets
Represent NLB separately from classic LB while sharing native LB/Backend Set
flow and official generic LB artwork. Preserve the NLB single-subnet model and
API field evidence. Prefer explicit Backend.target_id and retain PrivateIp IDs
from observed VNIC lists; never substitute an IP guess for an unresolved ID.
Only IP-only targets require unique matching inside the owner's VCN. Normalize
NLB collection wrappers at the shared call boundary and test actual SDK-generated
methods with real pagination. Keep IAM mutation, health/reachability verification,
service membership inference and out-of-scope crawling excluded.


## 025 — Regional WAF outside subnet with explicit protection direction
Represent the regional WebAppFirewall enforcement point, not an invented proxy
inside the protected subnet. List summary subtype supplies load_balancer_id;
use this sole reference for WAF → LB and preserve unknown out-of-scope targets.
Policy ID is metadata only; do not query rules, address lists, logs, credentials
or add policy cards that duplicate protection endpoints. Use official WAF art.
Keep WAAS origin/domain mapping deferred rather than guessing LB relationships.
No source topology, resource placement or traffic-reachability inference is added.


## 026 — Evidence-limited Edge WAF origin support
Supersede 025's deferred-WAAS scope by adding separate edge_waf resources and
scoped List/Get WAAS metadata. Keep Regional WAF's exact LB OCID semantics intact.
Use only explicitly selected default origins/groups. Public IP equality may map
to a unique collected LB/NLB/Compute; never resolve DNS, match resource names or
place globally scoped private addresses into guessed VCNs. Retain logical origin
tags when identity is unknown, and retain policy-only data on detail failure.
Do not persist raw policy bodies, headers, certificate material or URI credentials.
Keep global service semantics explicit: the drawing region is query context.

## 027 — Common readable connection corridors
Apply conflict avoidance to all visible API relationships rather than a service
allowlist. Use geometric branch order and the same fanout-aware conflict score for
routing refinement and final quality. Preserve native endpoint normals and
vertical backend flow; do not use a shared owner as permission to merge unrelated
wires. Add alias-only proximity and fanout hints to new AI and review requests;
measure them in quality v3 as soft constraints because immutable OCI containment
can make perfect alignment impossible. Replay changes routes only, not stored
resource geometry. Never infer service groups, invent endpoints or add customer
coordinate exceptions. Test crossed ordinary backend wires, shared trunks,
unknown proximity, unchanged parents, exact replay and all existing services.

## 028 — Backend-owned annotations instead of floating unknown targets
Fold unresolved backend presentation into its Set's measured editable native
label, with count, while preserving canonical endpoints and hidden evidence
cells. This supersedes the generic proximity-only guidance for these targets;
other unknown types keep their own presentation. Distinguish empty success from
failed collection using a minimal status flag in both LB adapters. Treat legacy
empty data as unknown collection status; never retroactively claim success.
Known backend arrows stay visible; failed reads never create target arrows.
Do not reparent a guessed OCI resource into the Set's subnet or infer membership.

## 029 — Prefer short readable paths with explicit independent crossovers
Supersede 027's raw-crossing-first optimization with measured short paths and
native arc jumps. Retain raw independent-wire counts, distinguish clean interior crossovers from
unbridged contacts, and never relax resource/title intrusion or collinear overlap.
Allow only the initial shared prefix of API-confirmed same-DRG branches, with later reconvergence and other owners still counted. Use common fixed styling at the existing icon scale, not customer-specific pixel
coordinates. Keep API endpoints and same-owner branch evidence. Quality v4 guards
ambiguous contacts while permitting marked crossovers to avoid excessive detours.
Reference customer artwork stays outside the repository and supplies presentation
conventions only. No topology, customer layout, OCI credentials or raw source is
copied into examples. Validate a forced crossing PNG, existing saved layouts,
strict unsafe-contact tests and deterministic replay.

## 030 — Scoped managed data services without data-plane access
Add Cache/PostgreSQL/OpenSearch as resource cards in their explicitly observed
subnets. Use List/Get metadata and PostgreSQL GetConnectionDetails IP allowlists;
never serialize its CA or access SQL, Redis/Valkey, indices/documents or credentials.
Keep denied summary resources and unavailable network state distinct from empty
successful lists. Canonical graph evidence preserves nested and singular SDK
network fields. Endpoint uniqueness is scoped to an observed VCN; no DNS, name
matching or service grouping inference. Retain official OpenSearch art, extract
PostgreSQL native geometry from the newer official toolkit without altering the
pinned library, and use an explicit logical Cache tag when no dedicated artwork
exists in that bundle. Real-SDK pagination, denied/zero, privacy, native editing,
redaction and synthetic PNG validation precede live customer verification.

## 031 — Official Cache symbol reuse and regional NoSQL inventory
Supersede 030's Cache-tag fallback with the existing official NoSQL symbol used
for Cache in Oracle reference material. Do not claim a dedicated Cache stencil.
Add NoSQL as actual table OCIDs with ListTables metadata only; avoid GetTable and
its schema/DDL exposure and extra read permission. Regional tables belong to
their observed compartment outside VCN/subnet boundaries, including compartments
without VCNs. Do not synthesize endpoint IPs, backend matches, service gateway
access or client usage links. Native validation enforces the compartment parent.
Retain pagination/coverage/privacy, source artwork, exact replay and shared
connector styling. Same glyph does not imply identical resource kinds or topology.

## 032 — Regional storage and developer metadata without guessed flows
Keep Object Storage buckets, OCIR repositories and DevOps control-plane resources
in their API compartment outside network boundaries. Share the NoSQL regional
placement contract rather than add another renderer. Preserve project_id ownership
evidence only; never infer application/service groups or execution/image-pull paths.
ListBuckets omits OCIDs, so obtain identity through GetBucket. If denied preserve
the visible list summary with an explicit stable non-OCID identity and coverage.
No contents, source URLs, pipeline parameters, credentials or histories are saved.
Reuse unchanged official service stencils, with shared DevOps artwork for its child
resource kinds. Validate generated SDK pagination, privacy, denied/empty/dependency
coverage, native ownership and deterministic XML/PNG before live collection.

## 033 — GoldenGate endpoint placement without inferred replication
Extend the shared managed-data collector with GoldenGate List/Get metadata rather
than a separate renderer. Use the exact deployment private endpoint subnet, not
its public frontend subnet. Preserve summary fields on denied details, explicitly
distinguish unqueried NSG state and retain actual field provenance. Use official
editable GoldenGate entry 51. Do not fetch connections, assignments, process/data
state or synthesize source/target database relationships or managed LB internals.
Retain unique same-VCN endpoint matching, privacy, redaction and deterministic
replay. Actual customer inventory verification remains separate from synthetic QA.


## 034 — Application services without data-plane inference
Collect FSS, Functions and API Gateway through scoped read-only metadata APIs and
share the existing snapshot/graph/renderer rather than introducing a second path.
Keep file systems outside VCNs and place only observed mount endpoints in subnets.
Join exports on actual export_set_id and retain file_system_id, never infer client
mounts. Use Function summaries without config/image/code/invoke reads; visual child
anchors do not assert execution placement. Retain every Application subnet relation.
API Deployments attach to actual gateway_id. Extract only configured Function IDs
and sanitized HTTP host/port; match IPs uniquely within the applicable observed
network scope, leaving hostnames/ambiguous targets unresolved without DNS. Do not
persist policies, headers, URL userinfo/path/query or raw SDK responses. Report
prerequisite failures and detail failures distinctly from successful empty lists.
Reuse official native service art and explicit logical tags; do not revive OSN.


## 035 — NLB target identity before owned unresolved registration display
Supplement absent NLB references through scoped read-only IP/VNIC/attachment/instance
APIs, reusing existing evidence and caching repeats. Reject out-of-scope nodes,
inconsistent IDs/subnets/addresses and ambiguous attachments. Do not infer VM identity
from health or names; do not overwrite contradictory OCIDs using an IP fallback.
Keep unresolved registered addresses visible as logical tags adjacent to their exact
Backend Set rather than count-only NLB badges. Keep canonical unknown identity,
source/target edges and registration metadata intact; visual anchoring is not an
assertion of subnet placement. Use native labels, existing proximity/fanout/connector
quality, alias-only AI, redaction and exact replay. Do not introduce synthetic VMs,
OCI writes, IAM changes or automatically enumerate another compartment.


## 036 — Shared configured backend relationships for LB and NLB
Supersede 035's requirement that unavailable NLB target identity block a configured
IP relation. Both services use load_balancers.match_backend_ip: one observed
same-VCN VNIC/endpoint maps to its resource; ambiguity never invents a VM. Exact
known NLB IDs remain stronger evidence and raw target_id/IP/port stay unchanged.
IP-derived configuration edges do not assert successful target OCID resolution.
Do not require supplementary identity calls for records with a provided IP. Retain
scoped enrichment only for OCID registrations without an address. Remove the VM
failure caption from normal registered Backend tags. Reuse existing editable
shapes, actual API parents, routing, privacy and deterministic replay contracts.


## 037 — Readable arrows before compact canvas
Apply a relationship-derived visibility contract to every future diagram. Reserve
72px connected gaps/row lanes and 96px network space while keeping unrelated cards
compact. Use validated same-owner row/side-bus trees and independent owner landing
ports, normal shafts and foreign-card clearance. Never substitute a chain through
one target for two source-owned branches. Measure heads, shafts and corridor/row
obstructions even when old crossing/overlap metrics are zero.
Allow a larger canvas and higher scalar loss when those readability metrics improve
without protected regressions, while rejecting unrelated blank-frame inflation.
Preserve the old area guard when no readability gain exists. Keep OCI membership,
all API edges, editable geometry and deterministic replay. Keep legacy plan boxes
unchanged and report their new deficits; obtain more room through fresh AI geometry.
No customer picture coordinates, resource names or manual one-off offsets are used.


## 038 — Crop unused borders without undoing readable arrows
Keep the relationship-derived arrow contract from 037. Measure outer frame slack
using current child boxes plus native wire endpoints/bends, including foreign
wire turns. Supply alias-only per-side trim and bounds to AI visual review.
Reserve measured headers, 16px child padding and 8px bend clearance; 72/96px
corridors are flow lanes, not universal border padding. Preserve existing leaf
positions and branches before considering internal compaction. No automatic
resize/repack of model-owned geometry is introduced. Revalidate all candidates;
without a genuine visibility repair, additional bends/detours cannot be purchased
with lower area/loss. Saved-plan replay remains unchanged. Quality v6 separates
wire-aware outer slack from projection estimates of internal whitespace.


## 039 — OKE network endpoint, not an invented control-plane deployment
Use the official Container Engine for Kubernetes stencil for a cluster's observed
API endpoint in its exact subnet, with a local role label and IPs. Keep missing
endpoint anchors at a known VCN or actual compartment with icon/name only. Use
existing Compute instances and exact native-CNI Pod Subnet references, preserving
API compartment/VCN ownership. Store Node Pool network metadata without adding
frames or OKE-to-worker/LB/gateway traffic arrows. Read only scoped Cluster/NodePool
List/Get APIs; never request kubeconfig or serialize tags, SSH/node metadata/OIDC.
Preserve summary fields when detail reads fail and distinguish failed versus zero.


## 040 — Pod Subnet role badge without invented deployment boundaries
Replace the reserved Pod network text row with a compact editable rounded badge
and official OKE stencil. Retain the actual Subnet identity, name, CIDR and API
parent. Do not create a Pod resource or infer traffic. Decorate after applying
model geometry, preserving scene signatures and saved layouts. Route around the
full badge rectangle and include it in title intrusion assessment.
