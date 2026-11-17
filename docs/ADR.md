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
