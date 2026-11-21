# OCI GoldenGate 배포
입력: AGENTS.md, docs/HARNESS.md, PRD.md, ARCHITECTURE.md, ADR.md, collect.py,
managed_data.py, model.py, draw.py, tests/test_collect.py와 공식 library.xml.
인터페이스: 선택 리전·컴파트먼트 ListDeployments/GetDeployment → 최소 메타데이터
→ 실제 Private Endpoint Subnet/NSG 관계 → 공통 편집 가능 Draw.io/PNG.
범위: 이름·OCID·소속·상태·관측 IP와 공식 51번 GoldenGate 심벌. 상세 실패 시
목록 보존, NSG 0건/미확인 구분, 실제 API 필드 근거, 동일 VCN 유일 IP 매칭.
AC: index.json의 실제 SDK GET·페이지네이션·거부·허용목록·네이티브 편집/부모·
공유 익명화·별칭 AI 입력·교차 컴파트먼트·정확한 재생성, 가상 PNG 시각 검사.
금지: 접속정보·계정·비밀번호·원본 응답 저장, 연결/복제/소스·타깃 DB 흐름 추정,
public frontend Subnet으로 배포 위치 대체, 내부 LB 생성, IAM 쓰기, 자동 commit/push.
