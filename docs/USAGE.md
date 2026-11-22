# Install and run

For first-time setup and Codex/Hermes project workflows, read [ONBOARDING.md](ONBOARDING.md). Use `oci-lenz doctor --json` to check prerequisites without OCI/model requests.

Python 3.10+, Git, authenticated Codex CLI, and Draw.io Desktop are required for the full flow. OCI API credentials are only required by collect. Codex authentication is separate from OCI API signing; the app does not manage OAuth or customer accounts.

```sh
git clone https://github.com/haksuperman/OCI-Lenz.git
cd OCI-Lenz
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
oci-lenz sample --output /tmp/oci-lenz-sample
oci-lenz draw --snapshot /tmp/oci-lenz-sample/snapshot.json --output /tmp/oci-lenz-diagram
```

Project skills are available on the next Codex turn. The CLI also loads their pinned instructions explicitly. Default architecture design includes a bundled, independently synthetic composition image. To replace it add `--references /local/sanitized-reference-images`; supplied PNG/JPEGs become AI input. No customer reference pictures are bundled.

The default architecture style invokes the official jgraph Draw.io skill plus
the OCI adapter through the selected model provider. AI designs absolute
rectangles for every container and resource, plus optional edge waypoints.
Helpers apply those coordinates without replacing them with a fixed grid,
import native Oracle icons, apply real local labels, validate the graph and
export the same XML. Invalid geometry is returned to the model for up to two
repairs (three requests maximum); failure never silently switches to a template.
`--no-ai` explicitly uses a deterministic seed for diagnostics only.

## AI authentication on each installation

The default `--ai-provider codex` uses that user's local Codex CLI login:

```sh
codex login
codex login status
oci-lenz draw --snapshot /local/private-output/snapshot.json \
  --output /local/private-diagram --ai-provider codex --model YOUR_CODEX_MODEL
```

Omit --model to use the local Codex model. Architecture uses high reasoning
effort. Each user signs in
independently; the app does not copy OAuth tokens or register accounts. Codex CLI
is needed only for the Codex provider.

For a direct OpenAI Responses API connection, set OPENAI_API_KEY in the runtime
environment using a local secret manager. Do not put literal keys in commands,
project files, snapshots or logs. Choose a vision/structured-output capable
model available to that account:

```sh
oci-lenz draw --snapshot /local/private-output/snapshot.json \
  --output /local/private-diagram --ai-provider openai --model YOUR_API_MODEL
```

OCI_LENZ_AI_PROVIDER and OCI_LENZ_AI_MODEL provide optional non-secret defaults.
The API adapter uses https://api.openai.com/v1/responses with store=false; this
does not change provider retention policies. Reference images go to the selected
provider. Names, OCIDs, IPs and credential/config contents do not: only alias IDs,
relationship kinds, subnet public/private flags and label footprints are sent.
API failures never print response bodies. API live execution requires a user key
and model; the transport adapter is tested with mocks.

The editable information-index page retains all collected addresses and network
configuration. Architecture resource labels show the actual name and observed
representative private/public IPs only. Resources without an observed IP show
their name alone. Network boundaries retain CIDRs. Listener/backend port summaries
and information-index reminders are omitted from the architecture captions.
PNG output includes information-index.png. Replay requires matching inventory
IDs and label footprints; mismatched plans are rejected. Old hint-only layouts
from the retired inventory/service-map modes must be regenerated with the default
architecture renderer. Their original Draw.io files remain editable in Desktop.

The top heading shows tenancy name, selected compartment names and region from
snapshot scope metadata. New collection stores `scope.tenancy_name` and
`scope.compartment_names` using read-only identity APIs. Missing names in older
snapshots or denied lookups display `이름 미확인`, never an OCID or a guessed name.
Recollect to obtain names; draw/replay itself never reads OCI credentials or
requests identity metadata. `--redact` also hides these scope names, and AI
layout requests and masked previews never receive them. The overview PNG is
`architecture.png`; older output folders may still contain a previous
`region.png`, which is not updated by subsequent exports.

Default output is one whole-environment architecture canvas, with an editable
Resource information appendix. VCNs and subnets are boundaries inside the same
canvas; no separate VCN architecture pages are created unless --detail-pages is
specified. Version-3 plans use a dedicated AI overview scene, excluding technical
VNIC/NSG/route cards and unknown endpoints belonging only to hidden technical
relations from layout so they do not leave empty lanes or floating labels.
Unresolved LB/backend endpoints remain visible. Native hidden cells and all
evidence are retained. Optional VCN detail pages use an independent
AI scene with the complete network inventory. Only top-level version-3 layouts
are accepted; older layouts require regeneration.
Local orthogonal routing avoids visible resource content without changing model
placements, and keeps connectors clear of measured container title lines.
Connectors attach to the symbol or caption rather than an oversized invisible
card border. Backend Sets appear as compact editable name tags, preserving
their separate ownership/backend evidence without duplicating the LB icon.
IGW/NAT/Service gateways belonging to the same known VCN are placed together
along one edge with small gaps and content-sized cards. Larger groups can use a
compact grid. This is presentation based on VCN ownership, without a new service
group or a visible grouping frame. Scattered gateway proposals require repair.
Container borders remain traversable; rerender a saved layout to apply routing
fixes without another AI request. This checks geometry, not actual traffic reachability or universal
visual optimality. Sparse/dense, multiple compartments, unresolved targets, long
names and many secondary IPs are regression cases; new layouts still need visual
review before delivery.

Operational cards prioritize an observed primary-VNIC private address and public
address, when recorded; legacy snapshots use an observed representative address
without claiming it is primary. All addresses remain in the information index.
Listener protocol/ports and backend targets remain in the information appendix. New collection
uses GetLoadBalancer for allowlisted listener details and GetVnic primary fields.
Existing snapshots must be recollected for fields not previously stored.
Backend fanout shares a clear trunk only within one Backend Set; native evidence
edges are never merged. Mixed-direction layouts retain individual clear routes.

## Service presentation and visual review

Use explicit service groups when a business service spans multiple VCNs. The app
does not infer business ownership from resource names. Without group metadata it
keeps API-compartment grouping and evidenced backend flow. Store customer group
files outside the repository. Example local JSON:

```json
{"groups":[
  {"label":"Service A","vcn_ids":["VCN_OCID_1","VCN_OCID_2"]},
  {"label":"Shared services","role":"shared","vcn_ids":["VCN_OCID_3"]}
]}
```

Pass --groups /local/service-groups.json to draw. Resource membership and API
evidence are preserved; duplicate/unknown VCN assignments are rejected. Supply
the same group file on replay. Resource names and details are stored in the
resource shape's own editable text, not separate text boxes. Select the resource
and edit its label in Draw.io; dragging the resource carries the symbol and text
together. Names are bold; observed IP labels
are smaller and muted. Unicode-aware measurement computes card heights.

Fresh architecture generations with PNG output run model visual review by
default. A separately rendered preview masks names, addresses and group labels
while preserving geometry/text footprints. PNG textual metadata and embedded XML
are rejected. The model sees the preview plus the selected reference images and
may revise the complete overview geometry. Every revision undergoes evidence,
clipping and overlap validation. --review-rounds 1 (default) permits one revision
and a final inspection; 2 permits two revisions. Remaining issues are recorded
as needs_review in visual-review.json, not reported as a pass. Human acceptance
is still required for subjective quality.

--review-rounds 0 explicitly disables visual review. --no-ai, --no-png and saved
layout replay make no additional review calls. Review adds model latency/cost
and requires Draw.io Desktop for the masked preview. Original customer images
and unmasked customer output PNGs are not automatically uploaded.

```sh
oci-lenz draw --snapshot /tmp/oci-lenz-sample/snapshot.json --output /tmp/oci-lenz-repeat \
  --reuse-layout /tmp/oci-lenz-diagram/skill-layout.json
oci-lenz collect --profile READONLY --region REGION \
  --compartment-id COMPARTMENT_OCID --output /local/private-output
oci-lenz draw --snapshot /local/private-output/snapshot.json \
  --references /local/reference-images --output /local/private-diagram
```

Set `--config-file /path/to/config` on collect when needed. Collection is scoped by region and explicitly selected compartments, with no VCN selection/filter. All supported resources returned for those compartments are retained, including instances with no observed VNIC and references to networks outside the selected compartments. Repeat `--compartment-id` to explicitly include multiple compartments. Their snapshots are combined before relationship resolution; references outside that set stay unresolved. No automatic tenancy-wide crawl. An attached VNIC is fetched to establish instance relationships. Profile keys/passwords are read by the SDK only.

Default output is an operational customer diagram: actual names, observed private
and public VNIC addresses (including secondary VNICs), LB addresses, backend
endpoints, network CIDRs and route destinations are retained. Keep all real
snapshots, Draw.io files and PNGs outside Git. The collector stores only needed
fields; older snapshots lack public IP/LB/CIDR fields and must be recollected to
add them. Missing addresses are never inferred. Names/IPs are applied locally;
Codex still receives only alias IDs, types and relationship structure.

For a separate sharing PNG, explicitly use `draw --redact`: visible names, IPs,
group names and non-default route destinations are hidden. This is not a complete
anonymizer for Draw.io XML: cell IDs still contain internal identifiers. PNGs
never embed XML. GitHub examples must use synthetic data and undergo publication
review; do not publish customer-derived files merely because --redact was used.

Outputs: architecture.drawio, architecture.png, vcn-N.png, coverage.json, validation.json and (with AI) skill-layout.json. VCN PNG ordering follows VCN IDs. PNGs are exported from the same XML and the XML is retained. Region page currently shows the full scoped inventory; large inventories may need future pagination. Reference count and input image size should be kept modest for Codex.

## Draw.io on servers

Set `DRAWIO_BIN` to the Draw.io Desktop executable. macOS's standard installation is detected automatically. On Linux install the Draw.io Desktop package and Xvfb using the server's package manager. When no DISPLAY is set and `xvfb-run` is available, the exporter wraps Desktop with it. Do not disable the Electron sandbox. Linux server execution has not yet been exercised in this repository's validation.

## Diagnose

The draw command reports when AI layout starts and when PNG export starts.
Codex layout uses a temporary working directory and a JSON-only subtask with the
pinned skills explicitly provided; no project files or source names are needed
by the child. The default AI timeout is 600 seconds per request;
use `--skill-timeout 900` to allow 15 minutes. A timeout reports the stage without
printing the child command or output. There is no automatic AI bypass. For an
explicit local-only diagnostic run use `--no-ai`; this does not invoke Codex.
After a successful layout, `skill-layout.json` can be reused to retry PNG export
without another model call. PNG export still has a 120-second limit per page.

Run `python3 -m unittest discover -s tests -v`, `codex login status`, and `"$DRAWIO_BIN" --help` locally. Child output is suppressed to avoid persisting sensitive data; errors report only their class. SDK API failures are summarized in coverage by service/API/status, not raw exception text. A partial snapshot is still usable; coverage must be checked. Reuse a saved layout to avoid another model call. `--no-png` retains XML without requiring Desktop.

Current limitations: real OCI access and user reference-image style acceptance require their respective inputs; complex and large graph layouts need further visual evaluation. Backend Sets are logical name tags. Public/private subnet containers use VCN visual grouping. The model preserves all subnet associations even though a multi-subnet LB is placed once, in its first subnet.

## Synthetic architecture overview

```sh
python3 -m oci_lenz sample --scenario overview --output /tmp/oci-lenz-overview
python3 -m oci_lenz draw --snapshot /tmp/oci-lenz-overview/snapshot.json --output /tmp/oci-lenz-overview
python3 -m oci_lenz draw --snapshot /tmp/oci-lenz-overview/snapshot.json \
  --reuse-layout /tmp/oci-lenz-overview/skill-layout.json --output /tmp/oci-lenz-replay
```

This independently synthetic scenario contains two compartments and three VCNs.
The architecture canvas uses neutral region/compartment frames and orange dashed
network boundaries, with container sizes calculated from their contents. API
compartment membership controls VCN grouping; application service groups are not
guessed. A VCN without compartment metadata is grouped in an unspecified alias
compartment. Related resources from other compartments remain in their evidenced
network location. Dense cross-container edges may still need manual refinement.
The saved card layout reproduces XML exactly; PNG bytes may depend on Desktop and
fonts. No customer images or identifying text are bundled or required by this example.
Reference images passed with `--references` go to Codex, so sanitize them first;
the customer originals supplied in chat have not been passed to a child model.

## Explicit presentation groups

All diagrams use the architecture renderer. The former inventory/service-map
rendering styles and their ordering-hint AI adapter have been removed. The
`sample --scenario service-map` fixture remains as independently synthetic input
for explicit cross-VCN presentation groups; it uses the current renderer:

```sh
oci-lenz sample --scenario service-map --output /tmp/oci-lenz-explicit-groups
oci-lenz draw --snapshot /tmp/oci-lenz-explicit-groups/snapshot.json \
  --output /tmp/oci-lenz-group-diagram
```

Optional snapshot presentation metadata declares user-controlled service groups:

```json
{"presentation":{"groups":[
  {"label":"Example service","vcn_ids":["synthetic-vcn"]},
  {"label":"Shared services","role":"shared","vcn_ids":["synthetic-shared-vcn"]}
]}}
```

Groups are presentation metadata, not OCI resources or discovered application
semantics. The collector does not infer service membership. Without groups,
VCNs are automatically grouped by their API compartment IDs; unmatched VCNs in a
partial mapping also fall back to compartment groups. Explicit `--redact` outputs
alias group names as well as resource names. Normal diagrams group by API
compartment, VCN and subnet; services are never inferred.

The overview keeps editable technical cells and every relationship in XML but
hides VNIC/NSG/route-table shapes and technical edges. `--detail-pages` requests
additional VCN network pages. They are constructed only when requested.
The LB-to-Backend-Set display arrow expresses ownership while the XML source and
target retain the API evidence direction (`BackendSet.lb_id`). Backend arrows
represent configured targets, not proven traffic. Dense detail edges can still
share segments and may require editing. No DB or WAF resources are added from a
picture. Unknown targets remain visible. The fixture is independently synthetic;
no customer image is sent to the child Codex process.

Label wrapping prefers spaces and name separators before breaking identifiers.
LB ownership branches share a corridor when their evidenced Backend Sets sit
below the LB, while native API edge endpoints remain unchanged. Layout prompts
request compact containers, but new model outputs still require visual review.

## Synthetic topology regression matrix

`sample --scenario` also accepts long-names, dense, fanout, cross-compartment,
unresolved and empty. These are independent synthetic inventories, with no
inferred service groups. Run all diagnostic renders and PNG exports serially:

```sh
python scripts/validate_scenarios.py --output /tmp/oci-lenz-topology-matrix
python scripts/validate_scenarios.py --case long-names --ai --output /tmp/oci-lenz-topology-ai
# Actual AI designs at several scales; consumes the current user's model quota.
python scripts/validate_scenarios.py --ai --case basic --case overview --case fanout --case dense --output /tmp/oci-lenz-quality
# Revalidate unchanged passing cases without another model call.
python scripts/validate_scenarios.py --ai --resume --case basic --case overview --case fanout --case dense --output /tmp/oci-lenz-quality
```

The default matrix uses the deterministic diagnostic seed, not AI design.
`--ai` explicitly invokes the configured Codex model and visual review.
`matrix-report.json` records resource counts, validation, exact XML replay,
PNG dimensions and visual-review status. It also saves each snapshot's
`coverage.json`, artifact SHA-256 hashes and native label/vector counts. PNG
checks include complete chunks/CRC, decompressed scanlines and absence of textual
or embedded diagram metadata. Inspect PNGs separately for quality.
The runner continues after a failed case and saves each completed result.
Exit code 1 means at least one case failed or still needs visual review; diagnostic
passes are explicitly `diagnostic_pass`, never AI acceptance. `--skill-timeout 900`
sets each model-attempt timeout. Failed reports contain only error type/exit code,
not raw model responses; rerun the individual `draw` command for local guidance.
`--resume` revalidates replay and hashes against the same synthetic snapshot and
AI/diagnostic mode before reuse. Changed or failed cases run again. It does not
silently adopt a diagnostic layout as an AI-generated result.
Long container titles contribute an alias-only `header_height` footprint so
children cannot occupy the title area. Information-index rows wrap and grow;
clipped/overlapping rows are rejected. Changed footprints require a new layout.

Diagnostic matrix success certifies structure, bounds and replay, not aesthetic
quality. Dense or mixed-direction fanout may still have crowded/crossing lines
and requires AI and human visual review. Empty snapshots display a coverage
reminder rather than claiming that collection succeeded with zero resources.

Plans generated before container header footprint metadata was introduced must
be regenerated. Reuse never silently changes an incompatible saved placement.

Saved real-AI synthetic examples and their inspection notes are in
[`artifacts/ai-quality`](../artifacts/ai-quality/README.md). `accepted` records a
model's judgment of that particular preview, not a guarantee for every inventory.

## DRG and peering scope

Collection includes scoped DRGs, DRG Attachments, Local Peering Gateways (LPG) and
Remote Peering Connections (RPC). `ListDrgAttachments` explicitly requests ALL
attachment types; the SDK default is VCN-only. `network_details.id/type` take
priority over deprecated VCN attachment fields. Permission failures and successful
empty lists remain distinct coverage records. Shared SDK pagination/retry applies.

The graph preserves attachment → DRG/network and peer_id relationships with API
field evidence. It does not infer a direct VCN-to-VCN relationship or traffic
reachability. Only resources returned for selected compartments are resolved;
remote regions/tenancies/compartments are never fetched automatically. An API
reports PEERED but omits the peer ID → the peer remains explicitly unknown.
Other attachment network types (beyond VCN/RPC/IPSec-tunnel/VirtualCircuit) are retained as references and recorded as
unsupported endpoints; DRG route-policy evaluation is not implemented. DB catalog/PDB/Data Guard and OKE remain follow-up scope. IAM policies are never changed.

DRG and RPC use official native toolkit icons; LPG uses a logical editable tag.
Attachment names/cards/frames are omitted from all diagram pages. Direct DRG
links retain exact Attachment API-field provenance in native edge metadata and
the original snapshot. Peering state and peer region stay in the information
appendix. Source collection/coverage are unchanged. Older snapshots without
network data still render without invented connections.

```sh
oci-lenz sample --scenario network-peering --output /tmp/oci-lenz-network-sample
oci-lenz draw --snapshot /tmp/oci-lenz-network-sample/snapshot.json --output /tmp/oci-lenz-network-diagram
# Explicit diagnostic run without model calls:
oci-lenz draw --snapshot /tmp/oci-lenz-network-sample/snapshot.json --output /tmp/oci-lenz-network-diagnostic --no-ai
```

This independently synthetic case includes cross-compartment attachments, two
known LPG endpoints and an unresolved remote RPC. For semantics/permissions see
[Oracle SDK](https://docs.oracle.com/en-us/iaas/tools/python/latest/api/core/client/oci.core.VirtualNetworkClient.html)
and [Core IAM reference](https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/corepolicyreference.htm).

## Oracle Base Database Service

The collector supports VM./BM. Base DB shapes through scoped ListDbSystems and
per-system ListDbNodes using the shared pagination/retry/coverage wrapper.
VM.BaseDB.x86 and older VM shapes are accepted. Legacy Exadata.* systems use a
distinct exadata_db_system kind; unknown shapes are recorded unsupported. No DB Home, logical database/PDB, Data Guard or database
connection is queried. Additional database infrastructure platforms are described
in the expanded DB service section below.

Default architecture: ONE official DB System icon, the actual System Display Name,
and observed client Node IPs. Two-node systems show both addresses. Node hostname
cards and backup addresses are not shown on the overview. If network reads fail,
no IP is fabricated. Client/backup VNIC and NSG/subnet relations stay in the minimal
snapshot, native XML, appendix and optional --detail-pages output. A backend to
an observed Node may visually connect to its owning System; its physical target
ID and API relation are retained and validated in XML. This is aggregation, not
an inferred application flow or traffic reachability result.

```sh
oci-lenz sample --scenario base-database --output /tmp/oci-lenz-base-db
oci-lenz draw --snapshot /tmp/oci-lenz-base-db/snapshot.json --output /tmp/oci-lenz-base-db-diagram
```

The independent synthetic example has one two-node System, distinct client/backup
networks and an explicit LB backend to a DB Node. `--no-ai` remains available for
diagnostic rendering. [Oracle Base DB shapes](https://docs.oracle.com/en/cloud/paas/base-database/guide/dbs-about.html)
and [IAM requirements](https://docs.oracle.com/en/cloud/paas/base-database/guide/policy-details.html)
are separate from any deployment/IAM changes; this app performs neither.

### IPSec VPN

기존 `collect` 명령으로 지정 컴파트먼트의 CPE, IPSec 연결, 각 연결의 터널을
함께 수집합니다. `draw` 명령은 변경 없이 같은 스냅샷을 사용합니다. CPE·VPN
게이트웨이 IP와 이름을 표시하며 상태·라우팅 방식·정적 경로는 정보 페이지에
보존합니다. UP은 실제 트래픽 도달성을 보장하지 않습니다. 범위 밖 CPE/DRG와
조회하지 못한 터널은 대상 미확인으로 남깁니다. PSK·장비 설정은 조회하지 않습니다.

가상 데이터 재현:
```sh
oci-lenz sample --scenario ipsec-vpn --output "$HOME/oci-lenz-validation/ipsec-vpn"
oci-lenz draw --snapshot "$HOME/oci-lenz-validation/ipsec-vpn/snapshot.json" --output "$HOME/oci-lenz-validation/ipsec-vpn/diagrams"
```

### DRG 직접 연결과 배치

Attachment 상자·이름·경계는 본문, 정보 페이지, VCN 상세 페이지에서 모두
표시하지 않습니다. 기존 스냅샷을 그대로 사용할 수 있으며, 수집기와 원본 API
관계는 유지합니다. 하나의 Attachment에서 확인된 DRG와 네트워크 끝점을 직접
연결하고, 연결선 메타데이터에 그 Attachment ID와 API 필드를 보존합니다.
RPC 소속 선 등과 중복되면 한 선으로 표현하되 모든 근거를 유지합니다.

VCN은 DRG 왼쪽, IPSec은 오른쪽, Remote Peering은 위쪽에 배치합니다. 여러
DRG에도 각각 적용하며 서비스 소속이나 VCN 간 전이 통신을 추론하지 않습니다.
대상이 범위 밖이거나 확인되지 않으면 `대상 미확인`으로 유지합니다.
실제 OCI Attachment를 삭제하거나 IAM 정책을 변경하는 작업은 하지 않습니다.
기존 Attachment 표시용 저장 배치는 `--reuse-layout` 없이 다시 생성하세요.

`validation.json.routing_quality.network_edge_crossings`는 네트워크와 관련된
선 사이의 교차·접촉 수, `network_overlap_length`는 겹친 길이(페이지 좌표)
입니다. 실제 공통 끝점 접속 구간과 역방향 같은 끝점 쌍은 제외합니다.
DRG 포트 대안과 최대 두 번의 배선 재검토로 교차·겹침을 줄이지만 전체 최적
배치나 트래픽 도달성을 보장하지 않습니다. 원본 리소스 위치는 AI 계획대로
유지하며, 실패 시 임의 배치로 대체하지 않습니다.

가상 예제:
```sh
oci-lenz sample --scenario drg-centered --output "$HOME/oci-lenz-validation/direct-drg"
oci-lenz draw --snapshot "$HOME/oci-lenz-validation/direct-drg/snapshot.json" --output "$HOME/oci-lenz-validation/direct-drg/diagrams"
```

### IPSec VPN 내부 터널 표시

IPSec 연결은 실제 이름을 제목으로 가진 편집 가능한 VPN 컨테이너로 표시합니다.
`ListIPSecConnectionTunnels` 요청 범위로 확인된 터널만 그 VPN 안에 배치하며,
각 터널 이름·IP를 유지합니다. 같은 IP나 이름으로 소속을 추론하지 않습니다.
DRG와 CPE는 컨테이너 밖에 두고 기존 API 근거의 선으로 연결합니다.

컨테이너를 이동하면 소속 터널도 함께 이동하고, 터널은 개별 편집할 수 있습니다.
소속 관계를 보여주는 중복 화살표는 숨기지만 원본 API 관계와 연결선 메타데이터는
보존합니다. 터널이 0개인 알려진 VPN도 이름 있는 빈 박스로 표시하며 조회 실패와
0건의 구분은 coverage.json에 남습니다. 소속 VPN이 범위 밖이면 가짜 컨테이너를
만들지 않고 터널과 대상 미확인을 유지합니다. 기존 VPN 저장 배치는 재생성하세요.

### FastConnect

기존 `collect` 명령으로 같은 리전·컴파트먼트의 Virtual Circuit, Cross-Connect
Group, Cross-Connect를 함께 수집합니다. DRG의 아래쪽에 FastConnect 분기를
배치하고 Oracle 공식 FastConnect SVG 심볼을 사용합니다. VC의 gateway_id와
물리 매핑 ID만 연결 근거로 쓰며, Cross-Connect 포트는 실제 소속 그룹 안에
표시합니다. CPE나 공급자 장비를 IP·이름으로 추정해서 연결하지 않습니다.

Public 회선에 DRG 참조가 없으면 독립 리소스로 유지합니다. 공급자 관리 회선의
물리 참조가 범위 밖이면 대상 미확인으로 표시하며, 매핑 자체가 없으면 물리
장비를 임의로 추가하지 않습니다. BGP 상태·VLAN·속도는 정보 페이지에 보존하고,
본문에는 실제 이름과 관측된 Customer/Oracle 피어링 IP를 표시합니다.
BGP UP이나 ACTIVE는 실제 애플리케이션 통신 검증 결과가 아닙니다.
BGP MD5 키, MACsec·장비 설정, LOA와 공급자 키는 저장하지 않습니다.
VPN-over-FastConnect의 터널 연계나 BGP 경로 분석은 이번 범위에 포함하지 않습니다.

가상 예제:
```sh
oci-lenz sample --scenario fastconnect --output "$HOME/oci-lenz-validation/fastconnect"
oci-lenz draw --snapshot "$HOME/oci-lenz-validation/fastconnect/snapshot.json" --output "$HOME/oci-lenz-validation/fastconnect/diagrams"
```

## 배치 품질과 반복 신규 생성 검증

기본 실행은 기존과 동일하다. `validation.json`의 `layout_quality`에서 코드가
측정한 교차·겹침·리소스/제목 침범·간격 부족·연결선 우회·여백을 확인할 수 있다.
`loss`는 같은 스냅샷/라벨의 후보끼리 비교하며 낮을수록 좋다. 다른 고객사나 다른
리소스 개수의 결과를 이 값으로 비교하지 않는다.

AI 수정본은 기존보다 점수가 낮아지고 모호한 교차·겹침·침범·비직각 구간이 늘지 않을 때만
채택한다. 최초 캔버스 대비 면적 25% 초과 증가도 거절한다. `visual-review.json`에
최초/최종 평가와 `decisions`의 채택·거절 이유가 남는다. 기본 수정 예산은 1회이며
`--review-rounds 0/1/2`로 지정한다. 자동 AI 호출 횟수는 추가하지 않았다.

AI가 수용하더라도 코드가 측정한 문제가 남으면 `needs_review`다. 실패를 숨기거나
리소스/연결선을 삭제해서 점수를 맞추지 않으며 편집 가능한 산출물은 보존한다.
`--reuse-layout`, `--no-ai`, `--no-png`에서도 코드 평가는 수행하되 추가 AI 검토는
호출하지 않는다. 코드는 글꼴별 실제 픽셀 렌더링이나 미적 완성도를 보장하지 않는다.

같은 가상 스냅샷으로 배치 재사용 없이 3번 신규 생성하려면:

```sh
python scripts/validate_repeatability.py --case fastconnect --repeats 3 \
  --output /tmp/oci-lenz-repeatability
```

복잡한 사례는 `--case dense` 또는 `--case fanout`으로 검증한다. 각 실행의
Draw.io·PNG·검증 JSON과 상위 `repeatability-report.json`을 확인한다. 실패와
검토 필요 결과도 포함하며, 문제가 남으면 명령은 0이 아닌 종료 코드를 반환한다.
`--no-ai`는 구조 진단용으로 AI 균등성 검증 결과로 해석하지 않는다. 실행별로
AI 사용량이 발생하므로 기본 반복은 3회, 허용 범위는 2~10회다.

디자인 평가 v2는 `layout_quality.metrics`에 컨테이너별 최악/평균 불필요 여백,
큰 내부 간격, 카드 크기 과장, 정렬 및 실제 LB/backend 관계의 흐름 정렬을 추가한다.
`design_feedback`의 리소스 ID는 AI용 별칭이며, `suggested_width/height`는 수집된
리소스 개수와 라벨에서 계산한 참고 크기다. 코드가 이 값으로 도형을 자동 재배치하지
않는다. 실제 이름·IP와 모든 API 관계는 유지한다.

최초 생성과 검토에 같은 간격 기준을 전달하며, 리소스가 적은 Subnet을 큰 형제
Subnet 크기에 맞춰 늘리지 않도록 한다. 필요한 DRG 연결 공간과 긴 제목 공간은
보존한다. v1/v2 점수는 직접 비교하지 말고 같은 버전으로 다시 평가해야 한다.

공통 연결 규칙은 새 생성 때마다 적용한다. `skill-layout.json`의 장면별
`connector_rule_version: 1`은 실제 아이콘 접속 축 검증을 거쳤음을 나타낸다.
화살촉 진입 방향뿐 아니라, 단일 내부 리소스가 있는 API 컨테이너와 외부 리소스의
접속 높이도 맞춘다. 장애물 없이 같은 축에 놓인 선은 불필요한 꺾임 없이 그린다.

예전 저장 배치가 이 기준을 어기면 `connector_alignment_errors`로 표시한다.
새 규칙으로 다시 배치하려면 `--reuse-layout` 없이 생성한다. 코드가 기존 리소스
좌표를 임의로 이동시키거나 특정 고객사·리소스 이름별 예외를 넣지는 않는다.
분기나 제목·다른 리소스를 피해야 하는 구간의 필요한 직각 꺾임은 유지한다.

## 확장 DB 서비스

기존 `collect` 명령에 MySQL → Autonomous DB → ExaCC → ExaCI → Exascale 수집을
추가했다. SDK 최소 버전은 `oci>=2.191,<3`이며 기존 설치는 `python -m pip install -e .`
명령으로 의존성도 갱신한다. 서비스별 권한이 없으면 해당 API 실패를 coverage에
기록하고 다른 수집을 계속한다. 성공 0건과 실패는 구분한다. Search 비교는 기존
리소스만 대상으로 하며 새 DB 서비스의 완전성을 보장하지 않는다.

| 서비스 | 수집·표시 범위 |
| --- | --- |
| MySQL | DB System 목록과 개별 GetDbSystem의 Subnet·NSG·IP·포트·버전·HA 및 HeatWave 연결 여부. 개별 조회 실패 시 목록의 System/IP 유지 |
| Autonomous DB | Serverless/public/private 및 Dedicated DB, Container DB, Autonomous VM Cluster와 Cloud Autonomous VM Cluster, 레거시 Autonomous Exadata Infrastructure. 실제 private_endpoint_ip와 소속 ID만 사용 |
| ExaCC | Exadata Infrastructure, VM Cluster, VM Cluster Network의 client/backup 주소와 SCAN, 요청 범위로 확인한 DB Node. 온프레미스 네트워크를 OCI Subnet/VCN으로 추정하지 않음 |
| ExaCI | Cloud Exadata Infrastructure, Cloud VM Cluster, DB Node/VNIC, client/backup Subnet·NSG 및 GetPrivateIp로 확인한 SCAN IP. 레거시 Exadata.* DbSystem은 Base DB와 별도 종류로 유지 |
| Exascale | Exadb VM Cluster, Exascale DB Storage Vault, DB Node/VNIC 및 client/backup 네트워크. 기존 CloudVmCluster/VmCluster의 Vault 참조도 보존 |

기본 구성도는 실제 Display Name과 관측 IP를 표시한다. DB Node는 소속 System/VM
Cluster로 모아 client IP를 표시하고 개별 Node/VNIC는 XML·정보 페이지와 선택한
상세 페이지에 보존한다. Backup 주소·포트·버전·상태는 정보 페이지에 둔다.
클러스터의 SCAN 조회가 실패하면 주소를 만들지 않는다. 공개 Autonomous DB의
DNS/접속 문자열로 IP나 Subnet을 만들지 않는다. Dedicated DB가 Subnet을 제공하지
않으면 부모 클러스터의 Subnet을 DB 자체의 소속으로 복사하지 않는다.

MySQL/Autonomous/클러스터의 실제 private endpoint가 LB VCN 안에서 유일하게
확인되면 설정된 Backend IP를 연결한다. 주소가 중복되거나 VCN 소속이 미확인이면
`대상 미확인`으로 남긴다. Node로 향하는 Backend의 화면상 끝점만 소속 Cluster로
모으며 `ociEvidenceTarget`에는 원래 Node를 유지·검증한다. 도달성을 뜻하지 않는다.

MySQL·Autonomous·Exadata·ExaCC는 번들 Oracle 공식 아이콘을 사용한다. 번들에
전용 Exascale/Vault 심볼이 없어 Exadb VM Cluster에는 Exadata 아이콘을 사용하고
Storage Vault와 온프레미스 VM Cluster Network는 편집 가능한 논리 태그로 표시한다.
인프라와 클러스터는 소속 ID로 연결하며 이를 임의의 VCN 컨테이너로 만들지 않는다.

DB 암호·wallet·접속 문자열·태그·SSH 키·고객 연락처·장비 설정은 보존하지 않는다.
SQL 접속, DB Home/일반 Database/PDB 카탈로그, Data Guard, MySQL 복제/Channel과
개별 HeatWave 노드, Exadata 물리 DB Server 및 저장 서버 인벤토리는 이번 범위가 아니다.
명시한 컴파트먼트 밖의 부모는 추가 조회하지 않으며, 선택된 다른 컴파트먼트에서
수집된 부모는 병합 후 연결한다. ExaCC Network List에는 부모 Infrastructure ID와
현재 선택 컴파트먼트 필터를 함께 적용한다.

각 서비스의 독립 합성 예제는 `mysql`, `autonomous-db`, `exacc`, `exaci`, `exascale`이다.

```sh
oci-lenz sample --scenario mysql --output /tmp/oci-lenz-mysql
oci-lenz draw --snapshot /tmp/oci-lenz-mysql/snapshot.json --output /tmp/oci-lenz-mysql/diagrams
python scripts/validate_scenarios.py --case mysql --case autonomous-db --case exacc --case exaci --case exascale --output /tmp/oci-lenz-db-validation
```

행렬 명령의 기본 실행은 모델 없는 구조 진단이며 실제 AI 품질 합격이 아니다.
Draw.io Desktop을 실행할 수 없는 환경에서는 `draw --no-ai --no-png`로 XML만
검증한다. 이 결과는 PNG 시각 검수나 실제 OCI API 검증을 대신하지 않는다.


Dedicated ADB의 Container DB·VM Cluster·Infrastructure는 API에서 수집된 참조가
있을 때만 관계선으로 표시한다. Serverless ADB에 이를 임의로 추가하지 않는다.
DB 관계선은 공통 교차 회피와 접속 면 선택을 사용한다. 기존 저장 배치를
`--reuse-layout`으로 다시 그려도 도형 위치·크기·Subnet 소속은 유지하고 연결선을
현재 규칙으로 재생성한다. 복잡한 배치에서 모든 교차 제거를 보장하지 않으며
남은 문제는 `validation.json`의 품질 경고로 확인한다.


## Network Load Balancer (NLB)

`collect`는 기존 LB와 별도로 Network Load Balancer, Listener, Backend Set 및
Backend를 읽기 전용으로 수집한다. NLB의 실제 단일 Subnet과 NSG 연결을 보존하고,
기본 구성도에는 이름·관측 IP를 표시한다. Backend Set은 기존 네모 태그로 표시한다.
Listener·포트·대상 상세는 정보 페이지에 보존한다. 번들에 전용 NLB 심볼이 없어
Oracle 공식 일반 Load Balancer 심볼을 사용한다.

백엔드에 Instance/Private IP OCID가 지정되면 수집된 리소스와 정확히 대조한다.
대상이 조회 범위 밖이거나 ID가 중복/미확인이면 `대상 미확인`으로 남기며, 같은
IP가 보인다는 이유로 다른 리소스에 연결하지 않는다. IP만 지정된 경우에는
NLB와 같은 VCN에서 유일한 관측 VNIC/DB endpoint가 있을 때 연결한다. Private IP
OCID는 새 수집부터 저장되므로 기존 스냅샷은 재수집이 필요하다. 구성 관계를
보여주는 것이며 소스 IP 보존·보안 규칙·헬스 상태·실제 트래픽 도달성을 검증하지 않는다.

```sh
oci-lenz sample --scenario network-load-balancer --output /tmp/oci-lenz-nlb
oci-lenz draw --snapshot /tmp/oci-lenz-nlb/snapshot.json --output /tmp/oci-lenz-nlb/diagrams
python scripts/validate_scenarios.py --ai --case network-load-balancer --output /tmp/oci-lenz-nlb-validation
```


## Regional Web Application Firewall (WAF)

`collect`는 선택 컴파트먼트의 Regional WAF 연결을 수집한다. 구성도에서는 WAF를
VCN·Subnet 밖에 두고, API의 `load_balancer_id`가 가리키는 LB를 향해 화살표를
그린다. WAF에는 실제 이름과 Oracle 공식 WAF 아이콘을 표시하며 IP를 만들지 않는다.
LB가 조회 범위 밖이면 `대상 미확인`으로 남기고 추가 조회하지 않는다. 여러
컴파트먼트를 명시해서 함께 수집하면 병합된 실제 LB OCID로 연결한다.
화살표는 WAF 보호 설정 관계이며 별도 프록시 홉이나 트래픽 검증 결과가 아니다.

정책 ID는 최소 메타데이터로 보존한다. 규칙·로그·인증정보·정책 본문은 조회/저장하지
않는다. Edge WAF(WAAS)는 아래의 별도 수집 경로를 사용한다. Regional WAF에는
도메인·IP·이름을 이용한 LB 추정 연결을 적용하지 않는다.

```sh
oci-lenz sample --scenario regional-waf --output /tmp/oci-lenz-waf
oci-lenz draw --snapshot /tmp/oci-lenz-waf/snapshot.json --output /tmp/oci-lenz-waf/diagrams
python scripts/validate_scenarios.py --ai --case regional-waf --output /tmp/oci-lenz-waf-validation
```


## Edge WAF (WAAS)

`collect`는 지정한 리전 API와 컴파트먼트에서 Edge 정책 목록과 해당 정책의 상세를
조회한다. Edge WAF는 전역 서비스이며, 그림의 리전 프레임은 조회 범위를 나타낼 뿐
물리 배치 리전을 뜻하지 않는다. Edge WAF에는 VCN·Subnet 소속을 만들지 않는다.
Regional WAF와 구분한 리소스로 실제 정책 이름과 Oracle 공식 WAF 아이콘을 표시한다.

기본 `waf_config.origin`과 선택된 `origin_groups`의 Origin만 연결한다. 사용되지 않은
Origin은 그리지 않는다. Origin의 IP가 수집된 공개 LB/NLB 또는 Compute IP와 유일하게
일치하면 해당 리소스로 연결한다. Regional WAF의 직접 LB OCID 연결과 달리, 이는
설정된 Origin과 관측 주소의 대조 결과다. DNS 조회·포트/헬스/도달성 검증은 하지 않는다.
호스트명·비공개 IP·중복·범위 밖 대상은 `대상 미확인` 논리 Origin 태그에 설정된
호스트만 표시한다. 도메인/CNAME이나 리소스 이름으로 대상 LB를 추정하지 않는다.

상세 조회가 실패해도 정책은 보존하고 coverage와 Origin 상태에 미확인으로 기록한다.
성공했지만 선택된 Origin이 없는 경우는 `not_configured`로 구분한다. URI의 사용자명·
암호·경로·쿼리·fragment와 커스텀 헤더·인증서·규칙 본문은 저장하지 않는다.
기존 `waas: unsupported` 스냅샷은 재수집해야 새 리소스가 추가된다.

```sh
oci-lenz sample --scenario edge-waf --output /tmp/oci-lenz-edge-waf
oci-lenz draw --snapshot /tmp/oci-lenz-edge-waf/snapshot.json --output /tmp/oci-lenz-edge-waf/diagrams
python scripts/validate_scenarios.py --ai --case edge-waf --output /tmp/oci-lenz-edge-waf-validation
```

### 연결선 규칙과 기존 배치

새 생성에는 미확인 대상 근접 배치·병렬 분기 정렬 힌트와 전체 연결선의
교차 회피가 공통 적용된다. 기존 저장 배치를 재사용하면 리소스 위치는
유지하고 연결 경로만 다시 계산한다. 미확인 대상이 멀리 배치된 기존 결과의
리소스 위치까지 개선하려면 새 AI 배치를 생성한다. 품질 결과의
`remote_unknown_targets`, `fanout_misalignment`는 경계 제약을 고려해 검토할
항목이며, 직각 연결이나 AI 검수 통과가 트래픽 도달성을 뜻하지 않는다.

### 백엔드셋 하단 상태 표시

- 백엔드 등록 0개(조회 성공): 백엔드셋만 표시한다.
- LB의 등록된 백엔드 리소스를 식별하지 못함: Set 하단에 `백엔드 대상 미확인 (N)`.
- NLB의 등록 백엔드: VM IP가 유일하게 일치하면 VM에 연결하고, 그 외에는 Set 인접 IP 태그로 표시한다.
- 백엔드 목록 조회 실패: `백엔드 조회 불가`.
- 기존 빈 스냅샷에 조회 상태가 없음: `백엔드 조회 상태 미확인`.

표시는 백엔드셋 도형 자체의 네이티브 라벨에 포함되므로 외부에 별도 배치되지
않는다. 알려진 대상의 화살표와 모든 원본 관계 근거는 보존한다. 이 변경은
카드 높이와 배치 서명을 바꾸므로 이전 `skill-layout.json`을 재사용하지 말고
같은 스냅샷에서 새 배치를 생성한다. 상태를 새로 확인하려는 경우에만 collect를
재수행하며, 구성도 변경 자체에는 OCI 재조회가 필요하지 않다.

### 짧은 경로와 점프 아치

연결선은 열린 화살표와 일정한 굵기를 사용하며, 독립적인 선의 명확한 수직
교차는 점프 아치로 구분한다. 아치는 연결 지점이 아니다. 같은 부모의 실제
분기만 공통선을 사용한다. 리소스·글자 관통과 서로 다른 선의 겹침은 계속
검토 대상이며, 끝점이나 꺾임 근처·밀집 교차는 아치 스타일만으로 통과하지 않는다.

품질 v4에서 `edge_crossings`는 원래 교차 수, `bridged_crossings`는 아치를
표시할 공간이 있는 교차 수, `unbridged_crossings`는 남은 모호한 교차 수다.
안전하게 표시된 교차 수가 늘더라도 경로와 꺾임이 줄어 품질이 개선될 수 있다.
기존 배치의 좌표는 그대로 두고 재렌더링해 새 연결선 규칙을 적용할 수 있다.
이전 품질 버전과 새 점수의 숫자를 직접 비교하지 말고 길이·꺾임·침범 및
모호한 교차 지표와 PNG를 함께 확인한다.

### OCI Cache · PostgreSQL · OpenSearch

기존 collect에 세 서비스가 자동 포함된다. 리전·컴파트먼트·프로필 입력과
다이어그램 생성 명령은 동일하며, 서비스별 List/Get 실패는 coverage에 남는다.
정상 목록 0건과 권한 부족/호출 실패를 구분한다. 상세 읽기에 실패하면 목록의
이름과 ID는 유지하지만 Subnet이 확인되지 않은 리소스를 임의 배치하지 않는다.
`network_status=unavailable|not_reported`는 정보 페이지에서 확인할 수 있다.

| 서비스 | API/관계 | 기본 표시 |
| --- | --- | --- |
| OCI Cache | ListRedisClusters/GetRedisCluster의 subnet_id, nsg_ids 및 Primary/Replica/Discovery IP | 공식 심벌·클러스터 이름·대표 IP |
| PostgreSQL | ListDbSystems/GetDbSystem의 network_details, GetConnectionDetails의 Primary/Reader/Instance IP | 공식 PostgreSQL 도형·System 이름·대표 IP |
| OpenSearch | ListOpensearchClusters/GetOpensearchCluster의 subnet_id, vcn_id, nsg_id 및 Search/Dashboard IP | 공식 OpenSearch 도형·클러스터 이름·대표 IP |

대표 IP 외 주소는 정보 페이지에 유지한다. PostgreSQL은 실제 연결 상세의
Primary를 우선하고 연결 조회 실패 시 관측된 network_details 주소를 유지한다.
FQDN을 DNS로 풀거나 개별 데이터 노드를 가상 Compute로 만들지 않는다.
서로 다른 서비스 사이 연결은 API 근거 없이 추가하지 않는다.
Cache는 Oracle 공식 발표자료에서 Cache 표현에 사용한 기존 NoSQL 심벌을 재사용한다. 전용 Cache 도형을 새로 만든 것은 아니며, Cache와 NoSQL 서비스의 kind·소속·관계는 별도로 유지한다.

가상 예제는 `sample --scenario managed-data`, `oci-cache`, `postgresql`,
`opensearch`로 생성한다. `scripts/validate_scenarios.py --case managed-data`
등으로 실제 OCI 없이 동일 생성기와 PNG 내보내기를 검증할 수 있다.
실제 환경은 권한과 해당 리소스가 준비되면 별도로 수/주소/관계를 대조한다.

### OCI Cache 공식 심벌 · NoSQL

Cache는 태그 대신 공식 library 46번 심벌을 사용한다. 기존 태그 배치와 크기가
달라지므로 Cache가 포함된 이전 skill-layout.json은 새 배치로 생성한다.
NoSQL도 같은 공식 심벌을 쓰며 테이블 이름만 표시한다. ListTables에 IP나
Subnet 정보가 없으므로 주소를 만들어 표시하거나 DNS 조회를 하지 않는다.

기존 collect에 NoSQL ListTables가 자동 포함된다. 필요한 추가 권한은
`inspect nosql-tables`이며 앱이 정책을 적용하지 않는다. 테이블 OCID·이름·
컴파트먼트·lifecycle만 저장하고 스키마·DDL·행·인덱스·사용량·리전 간 복제는
조회하지 않는다. NoSQL 테이블은 실제 소유 컴파트먼트 안, VCN/Subnet 밖에
표시한다. VCN이 없는 NoSQL 단독 컴파트먼트도 지원한다. SGW가 존재한다고
테이블에 연결선을 추가하지 않으며 애플리케이션 사용 관계도 추론하지 않는다.

가상 예제: `sample --scenario cache-nosql`, `nosql`, `nosql-only`와 --output을
사용한다. 동일 이름의 `scripts/validate_scenarios.py --case ...`로 API 호출 없이
Draw.io/PNG와 재생성을 검증한다. 운영용 collect/draw 명령은 기존과 동일하다.

## Object Storage / Container Registry / DevOps
기존 `oci-lenz collect` 명령에 자동 포함된다. Object Storage 버킷, OCIR 저장소,
DevOps 프로젝트·코드 저장소·빌드/배포 파이프라인·배포 환경을 수집한다. 실제
컴파트먼트 안·VCN 밖에 공식 아이콘과 이름으로 표시한다. 이 메타데이터에 IP는
없으므로 임의 IP나 SGW 연결을 추가하지 않는다. DevOps 선은 API가 확인한 프로젝트
소속이며 실행 순서가 아니다. 스테이지·실행 이력·배포 대상 상세는 이번 범위 밖이다.

버킷 OCID 확인에는 GetBucket 권한이 필요하다. 실패하면 ListBuckets에서 확인한
이름을 유지하고 `identity_status=list_summary`로 구분하며 coverage에 실패를 남긴다.
GetNamespace 실패 시 ListBuckets는 `skipped`로 기록한다. 실제 조회 0건과 다르다.
객체 내용·이미지·소스코드·파이프라인 변수·로그는 읽거나 저장하지 않는다.

가상 검증 시나리오는 `regional-services`, `regional-services-only`이며 기존
`python scripts/validate_scenarios.py --case regional-services --output PATH`와
동일 경로로 재현한다. AI 배치/검토를 함께 검증하려면 `--ai`를 추가한다.

## OCI GoldenGate (OCIGG)
기존 collect 명령으로 GoldenGate 배포도 수집한다. ListDeployments와 GetDeployment의
최소 메타데이터만 저장하고 공식 아이콘 아래 실제 이름과 관측된 Private/Public IP를
표시한다. 도형의 Subnet 소속은 고객 VCN Private Endpoint의 subnet_id 기준이다.
공개 프런트엔드용 load_balancer_subnet_id로 대체하거나 내부 LB를 새로 그리지 않는다.

상세 조회가 거부되어도 목록에서 확인한 이름·OCID·Subnet·IP는 유지한다.
`detail_status=unavailable`, `nsg_status=unavailable`는 NSG가 없다는 뜻이 아니다.
상세 응답에 NSG가 생략되면 not_reported, 성공한 빈 목록이면 ok로 구분한다.
Subnet이 미확인일 때 이름·IP·공개 여부로 임의 Subnet을 찾거나 DNS 조회를 하지 않는다.
DB 연결 설정·접속 계정·복제 프로세스·소스/타깃 흐름·데이터는 수집하지 않는다.

```sh
python scripts/validate_scenarios.py --ai --case goldengate --output /tmp/oci-lenz-goldengate
```
기존 스냅샷에는 자동으로 리소스가 추가되지 않으므로 실제 OCIGG 반영에는 collect를
다시 수행한다. 구성도 재배치만 하려는 경우에는 기존 snapshot을 그대로 사용할 수 있다.


## File Storage · API Gateway · OCI Functions
기존 `collect` 명령으로 세 서비스도 함께 수집한다. 리전·컴파트먼트·로컬 프로필
지정 방식은 같다. API별 추가 권한은 [IAM](IAM.md#file-storage--api-gateway--oci-functions)을
참고한다. IAM 정책은 앱에서 변경하지 않는다. 기존 snapshot에는 새 서비스가
없으므로 실제 환경 반영 시 사용자가 collect를 다시 수행해야 한다.

- File Storage: AD별 File System/Mount Target, Export와 실제 Subnet/NSG/IP.
  File System은 컴파트먼트 안 VCN 밖, Mount Target은 실제 Subnet에 둔다.
  ExportSet ID 조인으로 Export 관계를 표시한다. NFS 클라이언트 마운트나
  Compute의 파일 사용 관계는 조회/추정하지 않는다. Export 경로/옵션은 제외한다.
- Functions: Application/Function 소속, Application의 모든 Subnet/NSG.
  다중 Subnet Application과 Function은 한 번 표시하며 관측 Subnet ID의 안정된
  정렬로 시각적 기준점을 고른다. Function 위치는 실제 실행 Subnet 확정이 아니다.
  함수 코드·환경·이미지·설정·호출 URL은 저장하지 않고 함수를 실행하지 않는다.
- API Gateway: Gateway의 관측 IP/Subnet/NSG, Deployment의 실제 Gateway 소속과
  설정된 Function/HTTP 백엔드. HTTP는 안전한 host/port만 저장하고 인증정보·경로·
  쿼리·헤더·정책은 제외한다. Dynamic Routing도 설정된 후보만 추출한다.
  HTTP Private IP는 Gateway의 관측 VCN에서 유일한 VNIC/Compute 또는 LB/NLB에만,
  공개 IP는 수집된 공개 엔드포인트 중 유일한 대상에만 연결한다. DNS 조회 없이
  호스트명/모호한 IP/범위 밖 대상은 `대상 미확인`으로 둔다.

목록 0건은 coverage의 `ok/count: 0`, 실패는 `failed/permission_denied`다.
AD 조회가 실패하면 File System/Mount Target 목록은 `skipped`로 기록하며
Export 목록은 독립적으로 시도한다. 상세 조회 실패 시 목록 리소스를 보존하고
`detail_status`/`backends_status`/`address_status`로 미확인을 구분한다.
연결선은 구성 관계이며 실제 통신 도달성 검증 결과가 아니다.

Oracle 공식 File Storage(10), Functions(2), API Gateway(79) 아이콘을 사용한다.
Mount Target은 File Storage 심벌을 재사용하며 전용 아이콘이라고 주장하지 않는다.
Export/Deployment는 편집 가능한 논리 태그다. OSN 영역은 추가하지 않는다.

가상 검증(실제 OCI 조회 없음):
```sh
python scripts/validate_scenarios.py --case file-storage --case functions --case api-gateway --case application-services --output /tmp/oci-lenz-app-services
python scripts/validate_scenarios.py --ai --case application-services --output /tmp/oci-lenz-app-services-ai
```
기본 CLI 경로로 단일 문서를 생성하려면:
```sh
oci-lenz sample --scenario application-services --output /tmp/oci-lenz-app-snapshot
oci-lenz draw --snapshot /tmp/oci-lenz-app-snapshot/snapshot.json --output /tmp/oci-lenz-app-diagram
```


## LB와 NLB의 백엔드 연결
LB와 NLB 모두 Backend Set의 등록 IP를 수집된 VNIC/Private IP와 같은 규칙으로
대조한다. 동일 VCN에서 유일하게 일치하는 VM 또는 지원 엔드포인트로 화살표를
연결한다. NLB의 정확한 target_id가 이미 수집된 Instance/PrivateIp와 일치하면
그 관계를 우선 사용할 수 있다. target_id의 보완 조회 성공은 IP 매칭의 필수
조건이 아니다. 같은 IP가 여러 대상에 있거나 범위 밖이면 임의로 연결하지 않는다.

VM과 일치하지 않아도 등록 Backend는 OCI에 설정된 정상 항목으로 Set 가까이에
IP 태그와 화살표를 표시한다. `VM 확인 불가`나 개수만 있는 NLB 배지를 붙이지
않는다. 이 태그의 시각적 기준점은 Set이며 실제 VM Subnet을 주장하지 않는다.
기존 스냅샷 재렌더링만으로 새 규칙을 적용할 수 있다. 태그 라벨 높이가 달라져
이전 배치가 거부되면 새 AI 배치를 생성한다. 공유 `--redact`는 IP를 숨긴다.

IP가 이미 있으면 불필요한 GetPrivateIp/GetVnic/GetInstance를 호출하지 않는다.
IP가 없는 OCID 등록은 범위 내 읽기 전용 보완 조회가 가능하며, 그 진단은
`target_resolution_status`/`target_resolution_stage`에 남긴다. 원래 등록 ID·IP·포트는
보존하고 연결 근거에 ID 관계인지 등록 IP 관계인지 명시한다. 원본 응답·키·암호·
Instance metadata/userdata는 저장하지 않는다. 연결은 실제 트래픽 도달성 검증이 아니다.

가상 검증:
```sh
python scripts/validate_scenarios.py --ai --case nlb-backends --output /tmp/oci-lenz-nlb-backends
```


## 화살표 가독성과 공간 사용
새 구성도에는 서비스 공통 화살표 규칙 v2를 적용한다. 연결된 항목/분기 행 사이
72px, 네트워크 통로 96px를 권장하고 같은 출발점의 분기는 행 버스 또는 측면
버스로 정리한다. 서로 다른 출발점의 화살촉을 분리하며 아이콘/라벨 근처에는
정상 진입 구간을 둔다. 캔버스가 커져도 실제로 연결 가독성이 좋아지는 쪽을
우선한다. 필요 없는 빈 컨테이너나 카드 자체를 크게 만드는 것은 개선이 아니다.

`validation.json`의 품질 v5는 다음 항목을 추가로 확인한다.
- `connector_clearance_shortfall`: 연결 통로 부족
- `fanout_row_obstructions`: 앞선 대상 뒤로 좁게 겹친 분기 행
- `crowded_arrowheads`: 서로 다른 출발점의 화살촉 혼잡
- `short_arrow_shafts`: 너무 짧은 끝 진입 구간

이전 `--reuse-layout`은 위치를 보존하고 새 라우터/품질 검사만 적용하므로 좁은
배치의 문제가 남을 수 있다. 공간까지 확보하려면 기존 snapshot으로 새 AI 배치를
생성한다. 새 규칙을 위해 실제 OCI를 다시 조회할 필요는 없다. 관계나 부모를
바꾸거나 선을 숨겨 가독성을 개선하지 않는다. 코드 품질과 AI 시각 검토는 별도
결과이며 needs_review를 통과로 표시하지 않는다.

여백 보정 시 `validation.json`의 quality v6 `unused_boundary_area_ratio`와
`design_feedback`의 `unused_boundary_space`를 확인한다. `bounds`와 `trim`은
현재 자식과 선 경로를 보존할 수 있는 경계 축소 지침이다. 기존 배치를
몰래 재배치하지 않으며 `--reuse-layout`은 저장된 위치를 그대로 재생한다.
새 AI 생성의 시각 검토는 먼저 바깥 여백을 줄이고 연결 통로·화살표 구조가
퇴행한 수정안은 거부한다. 지침만으로 시각 품질 통과를 보증하지 않는다.

각 Draw.io 페이지와 PNG 하단에는 다음 검증 안내가 표시된다.
“AI를 활용해 생성한 구성도입니다. 실제 OCI 리소스 및 설정과 대조·검증한 후 사용해 주세요.”
안내는 편집 가능한 텍스트이며 프레임/연결선 밖에 배치된다. AI provider가
확인되지 않은 진단/수동 배치에는 “자동 생성된 구성도입니다.”로 구분한다.
기존 파일을 수정하지는 않으며 다시 draw하면 새 안내가 포함된다.
