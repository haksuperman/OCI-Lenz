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
Draw explicitly loads the pinned jgraph Draw.io skill and OCI project skill; Codex returns bounded alias-keyed card positions. Local helpers apply official editable stencils, create XML and validate graph consistency before Desktop export. Saved layout can be replayed. CLI is the first interface; no web UI or credential registration service.

The renderer computes growing region/compartment/VCN/subnet containers and keeps
orthogonal edges in the nearest common ancestor. Compartment labels are aliases;
membership comes from the VCN compartment ID. Reference composition conventions
are recorded without customer content. The overview synthetic fixture exercises
multiple VCNs and compartments without reproducing any supplied customer topology.

Default CLI rendering now uses an adaptive service map (`service_map.py`). Optional
presentation groups are explicit; unassigned VCNs use API compartment grouping.
Grid and shelf dimensions derive from resource counts, and backend cluster order
derives from evidence edges. Summary pages retain hidden technical cells/edges;
detail pages expose them. All share the same model and validator. Canvas size is
an output of layout, never copied from reference imagery.
