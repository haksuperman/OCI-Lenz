# Architecture

현재 구조:
- `AGENTS.md`: Codex 프로젝트 규칙
- `scripts/execute.py`: 단계 실행, 독립 AC 검증, 상태 기록
- `tests/test_execute.py`: 네트워크 없는 하네스 회귀 테스트
- `docs/`: 요구사항, 설계, 결정, 실행 절차
- `phases/`: 독립 작업 지시와 실행 가능한 AC

향후 앱 경로: OCI collector / synthetic fixture → 공통 snapshot → 관계 모델 →
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

Legacy `service-map` rendering uses an adaptive service map (`service_map.py`). Optional
presentation groups are explicit; unassigned VCNs use API compartment grouping.
Grid and shelf dimensions derive from resource counts, and backend cluster order
derives from evidence edges. Summary pages retain hidden technical cells/edges;
detail pages expose them. All share the same model and validator. Canvas size is
an output of layout, never copied from reference imagery.

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
