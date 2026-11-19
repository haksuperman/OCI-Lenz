# DB 5종 확장 검증

입력: AGENTS.md, docs/HARNESS.md, PRD.md, ARCHITECTURE.md, ADR.md,
oci_lenz/database.py, database_services.py, model.py, display.py, draw.py,
tests/test_database_services.py 및 scripts/validate_scenarios.py.
인터페이스: scoped read-only SDK → 최소 snapshot → 근거 graph → Draw.io/PNG.
범위: 실제 SDK 메서드 인자와 실제 pagination의 2페이지 수집을 네트워크 없는
회귀 테스트로 확인한다. 기존 5종 가상 시나리오는 실제 AI와 Desktop으로 별도
생성하고, 지정 프로필/리전/컴파트먼트의 실수집은 로컬 비공개 경로에서 대조한다.
실행 가능한 AC: index.json의 unittest, 전체 테스트와 하네스 구조 검사.
실제 API 성공/0건/권한 미확인을 구분하고 AI needs_review를 성공으로 바꾸지 않는다.
금지: OCI/IAM 쓰기, VIP 수집 추가, 컴파트먼트 배치 변경, 서비스 소속 추론,
고객 원문/키/접속 문자열 저장, 고객 산출물 Git 추가, 커밋/푸시, 실행기 변경.
