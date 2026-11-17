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

The renderer computes growing region/compartment/VCN/subnet containers and keeps
orthogonal edges in the nearest common ancestor. Compartment labels are aliases;
membership comes from the VCN compartment ID. Reference composition conventions
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
Unicode labels and creates native name/detail children. `visual_review` renders
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
