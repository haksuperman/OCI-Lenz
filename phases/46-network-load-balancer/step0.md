# Network Load Balancer 확장
입력: AGENTS.md, docs/HARNESS.md, PRD.md, ARCHITECTURE.md, ADR.md,
collect.py, model.py, draw.py, display.py, routing.py 및 기존 LB/DB 테스트.
인터페이스: scoped SDK List → 최소 snapshot → 근거 graph → AI Draw.io/PNG.
범위: NLB 목록/Listener/Backend Set/Backend, Subnet·NSG·IP 및 명시적
Instance/PrivateIp 대상과 유일 IP 매칭. 실제 SDK Collection·페이지네이션 검증.
AC: index.json의 NLB 테스트 및 전체 unittest, 가상 AI PNG 별도 검수.
공식 번들 LB 심볼을 재사용하며 전용 NLB 스텐실이라고 주장하지 않는다.
금지: IAM/OCI 쓰기, 범위 밖 재귀 조회, 서비스 소속/도달성 추론, 비밀/원문 응답,
고객 산출물 저장소 포함, 기존 LB·DB·네트워크 규칙 훼손, commit/push.
