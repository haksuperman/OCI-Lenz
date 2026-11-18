# DB 소속 관계선 교차 회피
입력: AGENTS.md, docs/HARNESS.md, PRD.md, ARCHITECTURE.md, ADR.md,
oci_lenz/routing.py, quality.py, database_services.py, tests/test_routing.py,
tests/fixtures/synthetic-dedicated-adb-layout.json.
인터페이스: 근거 graph와 AI 배치 → native 직각 연결선 → Draw.io/PNG.
범위: Dedicated ADB 재현 실패 테스트를 먼저 추가한다. DB 관계선에도 공통 충돌
회피 및 제한된 재조정을 적용한다. 저장된 AI 도형 배치·부모·이름·IP·관계는 보존한다.
AC: index.json의 회귀 테스트 및 전체 unittest, Desktop PNG 별도 검수.
금지: 특정 OCID/좌표/고객 하드코딩, 평가 기준 완화, VIP/소속 추론,
컴파트먼트 재배치, 실제 OCI 조회, 자동 commit/push, 실행기 변경.
