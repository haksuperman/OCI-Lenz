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
unsupported endpoints; DRG route-policy evaluation is not implemented. Other database platforms and OKE remain follow-up scope. IAM policies are never changed.

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
VM.BaseDB.x86 and older VM shapes are accepted; Exadata or unknown shapes are
recorded unsupported. No DB Home, logical database/PDB, Data Guard or database
connection is queried. Other database engines/platforms remain follow-up scope.

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
