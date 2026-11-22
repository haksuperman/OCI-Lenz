# LB/NLB 등록 백엔드 관계 통일
입력: AGENTS.md, HARNESS/PRD/ARCHITECTURE/ADR/IAM/USAGE, load_balancers.py,
model.py, nlb_backends.py, diagram_model.py 및 관련 테스트.
인터페이스: ListBackendSets/ListBackends → 공통 IP 매칭 → Set→VM 화살표.
범위: NLB의 부가 target_id 조회 상태를 IP 관계의 필수 조건에서 제외한다.
알려진 정확한 ID를 우선 사용하고, 확인되지 않으면 LB와 같은 동일 VCN 유일 IP
규칙을 적용한다. IP가 있는 항목에 불필요한 신원 조회를 하지 않는다.
등록 백엔드는 정상 설정 항목으로 표시하고 `VM 확인 불가`를 제거한다.
AC: 공통 매칭/실패 상태 독립/중복 IP·다른 VCN 차단/두 포트/원본 근거·익명화/
추가 API 미호출 회귀 테스트, 전체 테스트, 가상 Draw.io·PNG·정확한 재생성 검증.
금지: 임의 VM 생성·이름/DNS 추정, 실제 트래픽 검증으로 해석, 알려진 ID의
관계를 버리기, 범위 밖 자동 인벤토리 수집, 실제 정보 공개, 자동 commit/push.
기존 미커밋 서비스 확장을 보존하며 이전 phase의 결정 변경을 ADR에 기록한다.
