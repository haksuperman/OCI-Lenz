# OCI Cache / PostgreSQL / OpenSearch
입력: AGENTS.md, docs/HARNESS.md, PRD.md, ARCHITECTURE.md, ADR.md,
collect.py, database_services.py, model.py, draw.py, tests/test_collect.py.
인터페이스: 명시 컴파트먼트 List/Get → allowlist 인프라 스냅샷 → API 근거
Subnet/NSG 관계 → 동일 Draw.io 생성기와 PNG.
범위: Cache 클러스터, PostgreSQL DB System/엔드포인트, OpenSearch 클러스터.
목록과 상세 실패를 구분하고 없는 Subnet/IP를 추측하지 않는다. 개별 데이터
노드를 가상 리소스로 만들지 않고 실제 관측 엔드포인트 주소만 표시한다.
AC: index.json의 실제 SDK 모델·페이지·거부·비밀 배제·관계·XML·재생성 테스트,
가상 세 서비스 PNG와 설치 패키지 smoke. 실제 OCI 조회는 이 단계에서 하지 않는다.
금지: SQL/Redis/OpenSearch 데이터 API, DNS/실제 엔드포인트 연결, IAM 쓰기,
사용자명·암호·인증서·토큰·원문 응답 저장, 컴파트먼트 밖 재귀 조회,
고객사 예제 공개, 자동 commit/push.
