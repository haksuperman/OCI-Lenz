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
