# Edge WAF (WAAS) 확장
입력: AGENTS.md, docs/HARNESS.md, PRD.md, ARCHITECTURE.md, ADR.md,
collect.py, model.py, waf.py, draw.py, architecture.py, tests/test_collect.py.
인터페이스: 선택 컴파트먼트 ListWaasPolicies/GetWaasPolicy → 최소 Origin 모델
→ Edge WAF→관측 대상 또는 논리 Origin → Draw.io/PNG.
범위: 기본 WafConfig.origin 및 선택 origin_groups의 참조만 보존한다.
Subnet 소속을 만들지 않고 Oracle WAF 아이콘으로 Edge 정책 이름을 표시한다.
공개 IP가 관측된 LB/NLB/Compute와 유일하게 일치할 때만 대상에 연결한다.
호스트명/비공개 IP/중복/범위 밖 대상은 구성된 논리 Origin으로 남긴다.
AC: index.json의 SDK·페이지·거부·Origin 그룹·비밀 배제·그래프·XML 테스트,
전체 unittest, AI PNG는 별도로 생성/검수하고 미통과 결과를 기록한다.
금지: DNS/외부 원본 연결, IAM/OCI 쓰기, 범위 밖 재귀 조회, 헤더/인증/URI
사용자정보·경로·쿼리/인증서/규칙 본문 저장, 미선택 Origin 연결, commit/push.
