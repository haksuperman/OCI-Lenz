# NLB 백엔드 VM 확인과 등록 IP 표시
입력: AGENTS.md, docs/HARNESS.md, PRD.md, ARCHITECTURE.md, ADR.md, IAM.md,
collect.py, load_balancers.py, nlb_backends.py, model.py, diagram_model.py,
draw.py, architecture.py, typography.py, connector_rules.py와 NLB/배지 테스트.
인터페이스: 기존 collect의 관측 NLB target_id → GetPrivateIp → VNIC → 범위 내
VNIC Attachment → Instance. 공통 snapshot/graph/Draw.io/PNG 경로를 유지한다.
범위: 성공·거부·404·부족한 정보·범위 밖·모호한 Attachment 상태 기록,
유일하고 충돌 없는 IP-only 근거, 미확인 NLB 등록 IP의 Backend Set 인접 논리
태그와 원본 target_id/포트/근거 보존. 실제 VM 소속을 추측하지 않는다.
AC: index.json 테스트, 전체 회귀, 가상 혼합 백엔드 Draw.io/PNG 생성·시각 검사,
원본 그래프 보존/저장 레이아웃 재실행/익명화/alias-only AI/공통 직각 연결 검증.
금지: OCI 설정·IAM 변경, 다른 컴파트먼트 자동 목록 조회, 명칭·DNS·Health로
VM 소속 추정, 충돌 OCID를 무시한 IP 재연결, 원본 응답·키·암호 저장,
미확인 논리 태그를 실제 VM/Subnet 배포로 해석, 고객사 산출물 저장소 복사,
자동 commit/push. 기존 미커밋 서비스 확장 변경은 보존한다.
