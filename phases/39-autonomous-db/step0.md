# Autonomous DB 서비스 확장

입력: AGENTS.md, docs/HARNESS.md, PRD.md, ARCHITECTURE.md, ADR.md, IAM.md,
oci_lenz/collect.py, database.py, model.py, display.py, draw.py, architecture.py,
tests/test_collect.py, test_base_database.py와 앞 단계의 구현 및 테스트.
인터페이스: 명시적 리전·컴파트먼트, 공유 read-only pagination/retry/coverage,
최소 allowlist snapshot → 근거 graph → alias-only scene → 편집 가능한 Draw.io/PNG.
범위: Autonomous DB의 인프라·네트워크·소속 관계 수집 및 공식 아이콘/명확한 논리 태그,
실제 이름과 관측 IP, synthetic sample·회귀 테스트·사용법 및 권한 문서.
MySQL → Autonomous DB → ExaCC → ExaCI → Exascale 순서로 구현한다.
실행 가능한 AC: index.json의 SDK 모델 기반 서비스별 테스트와 전체 unittest.
먼저 실패 테스트를 작성하고 성공/0건/권한 거부/범위 밖 대상/비밀정보 배제,
관계 근거 및 native XML·익명화·alias-only 요청을 검증한다.
합성 CLI Draw.io/PNG 렌더는 별도로 검사하며 실제 API 검증과 구분한다.
금지: OCI/IAM 쓰기, 인증·wallet·SQL·접속 문자열/원문 응답 보관,
IP·이름으로 서비스 소속 추론, 범위 밖 재귀 조회, 고객 데이터 저장,
기존 배치 품질 변경 덮어쓰기, 에이전트, commit/push, 실행기/AC 완화.
