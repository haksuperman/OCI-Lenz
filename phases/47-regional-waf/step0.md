# Regional WAF 보호 대상 LB 연결
입력: AGENTS.md, docs/HARNESS.md, PRD.md, ARCHITECTURE.md, ADR.md,
collect.py, model.py, draw.py, architecture.py, routing.py, tests/test_collect.py.
인터페이스: scoped ListWebAppFirewalls → allowlist snapshot → WAF→LB 근거선.
범위: Regional WAF를 VCN/Subnet 밖에 공식 WAF 아이콘으로 표시한다.
OCID load_balancer_id만 보호 대상 근거로 쓰며 정책은 ID만 보존한다.
테스트 먼저: SDK Collection·다중 페이지·0건/거부·범위 밖 LB·방향·부모·익명화.
AC: index.json의 WAF 및 전체 unittest, AI Draw.io/PNG 별도 생성/시각 점검.
금지: WAAS Origin/DNS/IP로 LB 추론, 정책규칙/비밀/원문 응답 보관,
범위 밖 재귀 조회, WAF를 대상 Subnet 안에 배치, 트래픽 경로·도달성 주장,
IAM 쓰기, 고객 산출물 Git 추가, commit/push, 실행기/AC 완화.
